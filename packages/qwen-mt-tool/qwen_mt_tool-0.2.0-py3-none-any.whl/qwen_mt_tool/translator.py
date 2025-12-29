# -*- coding: utf-8 -*-
"""
翻译模块 - 核心翻译逻辑
"""

import concurrent.futures
import datetime
import os

from openai import OpenAI, APIStatusError

from .config import DEFAULT_MODEL, TRANSLATION_OPTIONS
from .key_pool import KeyPool
from .logging_setup import logger, usage_logger
from .utils import split_text_into_chunks


def translate_text(text: str, api_key_or_pool):
    """
    调用翻译 API 翻译文本，支持重试逻辑。
    
    Args:
        text: 要翻译的文本
        api_key_or_pool: API Key 字符串或 KeyPool 实例
    
    Returns:
        tuple: (翻译结果, 使用量统计) 或 (None, None)
    """
    max_retries = 1
    if isinstance(api_key_or_pool, KeyPool):
        with api_key_or_pool._lock:
            max_retries = len(api_key_or_pool.active_keys)

    for attempt in range(max_retries):
        if isinstance(api_key_or_pool, KeyPool):
            with api_key_or_pool.acquire() as api_key:
                if not api_key:
                    # 池可能为空或 Key 已被移除
                    if not api_key_or_pool.active_keys:
                        logger.error("没有可用的 API Key。")
                        return None, None
                    continue

                res_content, res_usage = _perform_translation(text, api_key, api_key_or_pool)
                if res_content is not None or res_usage is not None:
                    return res_content, res_usage
                continue
        else:
            # 单个 API Key
            return _perform_translation(text, api_key_or_pool, None)

    return None, None


def _perform_translation(text: str, api_key: str, api_key_or_pool):
    """
    执行实际的 API 调用并处理错误。
    
    Args:
        text: 要翻译的文本
        api_key: API Key
        api_key_or_pool: KeyPool 实例（用于在认证错误时移除 Key）
    
    Returns:
        tuple: (翻译结果, 使用量统计) 或 (None, None)
    """
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # 调试：记录文本长度
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
    logger.debug(f"API 调用: Key {masked_key}, 文本长度: {len(text)} 字符")
    
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        messages = [{"role": "user", "content": text}]

        completion = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            extra_body={
                "translation_options": TRANSLATION_OPTIONS
            }
        )

        return completion.choices[0].message.content, completion.usage

    except Exception as e:
        error_msg = str(e)
        
        # 判断错误类型
        is_auth_error = False  # 认证错误（应移除 Key）
        is_param_error = False  # 参数错误（不应移除 Key）
        
        if isinstance(e, APIStatusError):
            if e.status_code in (401, 403):
                is_auth_error = True
            elif e.status_code == 400:
                # 400 可能是认证问题或参数问题，检查消息内容
                if "Parameter limit exceeded" in error_msg or "invalid_parameter" in error_msg:
                    is_param_error = True
                elif "Unauthorized" in error_msg or "Invalid API" in error_msg:
                    is_auth_error = True
                else:
                    is_param_error = True
        elif "401" in error_msg or "403" in error_msg or "Unauthorized" in error_msg:
            is_auth_error = True

        if is_auth_error and api_key_or_pool and isinstance(api_key_or_pool, KeyPool):
            logger.error(f"认证错误: Key {api_key}. 正在移除并重试。")
            api_key_or_pool.remove_key(api_key)
            return None, None
        elif is_param_error:
            logger.error(f"参数错误 (文本长度: {len(text)} 字符): {e}")
            logger.error("文本可能过长，请尝试减小 --max-chars 参数。")
            return None, None
        else:
            logger.error(f"翻译失败 (文本长度: {len(text)} 字符): {e}")
            return None, None


def translate_file(file_path: str, api_key_or_pool, shared_executor, max_chars: int = 5000):
    """
    翻译单个文件，支持分片和跳过逻辑。
    
    Args:
        file_path: 文件路径
        api_key_or_pool: API Key 字符串或 KeyPool 实例
        shared_executor: 共享的 ThreadPoolExecutor
        max_chars: 每个块的最大字符数
    
    Returns:
        tuple: (文件路径, 是否成功)
    """
    # 检查输出文件是否已存在
    output_path = f"{file_path[:-3]}_zh_CN.md"
    
    if os.path.exists(output_path):
        logger.info(f"跳过 {file_path}: 翻译文件已存在于 {output_path}")
        return file_path, True

    logger.info(f"处理文件: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            logger.warning(f"文件 {file_path} 为空，跳过。")
            return file_path, True

        chunks = list(split_text_into_chunks(content, max_chars=max_chars))
        total_chunks = len(chunks)
        
        if total_chunks > 1:
            logger.info(f"文件 {file_path} 被分割为 {total_chunks} 个块。")

        # 确定块级并发数
        chunk_workers = 1
        if isinstance(api_key_or_pool, KeyPool):
            chunk_workers = len(api_key_or_pool.keys)
        
        # 并行翻译块
        translated_chunks_map = {}
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        failure_occurred = False

        def process_chunk(index, chunk_text):
            """处理单个文本块的翻译。"""
            nonlocal failure_occurred
            if failure_occurred:
                return None
            
            if total_chunks > 1:
                logger.info(f"[{file_path}] 正在翻译块 {index}/{total_chunks}...")
            
            res_content, res_usage = translate_text(chunk_text, api_key_or_pool=api_key_or_pool)
            
            if res_content:
                return index, res_content, res_usage
            else:
                logger.error(f"翻译块 {index} 失败: {file_path}")
                failure_occurred = True
                return None

        # 块索引从 1 开始
        future_to_chunk = {
            shared_executor.submit(process_chunk, i, chunk): i 
            for i, chunk in enumerate(chunks, 1)
        }
        
        for future in concurrent.futures.as_completed(future_to_chunk):
            result = future.result()
            if result:
                idx, content, usage = result
                translated_chunks_map[idx] = content
                if usage:
                    total_input_tokens += usage.prompt_tokens
                    total_output_tokens += usage.completion_tokens
                    total_tokens += usage.total_tokens
            else:
                failure_occurred = True

        if failure_occurred:
            return file_path, False

        # 按顺序组装翻译结果
        final_translated_content = [translated_chunks_map[i] for i in range(1, total_chunks + 1)]

        # 写入输出文件
        full_content = "\n\n".join(final_translated_content)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_content)
        
        logger.info(f"翻译已保存到 {output_path}")
        
        # 记录使用量
        usage_msg = f"文件: {file_path}, 输入: {total_input_tokens}, 输出: {total_output_tokens}, 总计: {total_tokens}"
        logger.info(f"翻译成功 [{file_path}]。使用量 - {usage_msg}")
        
        # 写入 CSV 使用统计日志
        if usage_logger.hasHandlers():
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if "," in file_path:
                file_path_safe = f'"{file_path}"'
            else:
                file_path_safe = file_path
            csv_msg = f"{now},{file_path_safe},{total_input_tokens},{total_output_tokens},{total_tokens}"
            usage_logger.info(csv_msg)
            
        return file_path, True

    except Exception as e:
        logger.error(f"处理文件出错 {file_path}: {e}")
        return file_path, False
