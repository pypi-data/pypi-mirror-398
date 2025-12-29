# -*- coding: utf-8 -*-
"""
Qwen-MT 命令行工具 - 使用通义千问翻译 Markdown 文件
"""

import argparse
import concurrent.futures
import json
import os
import shutil
import sys

from .config import MAX_WORKERS
from .key_pool import KeyPool
from .logging_setup import logger, setup_logging, setup_usage_logging
from .translator import translate_file, translate_text, _perform_translation
from .utils import find_markdown_files, split_text_into_chunks


def main():
    """主入口函数。"""
    parser = argparse.ArgumentParser(description="Qwen-MT 翻译工具 - 翻译和管理 Markdown 文件")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # translate 子命令
    translate_parser = subparsers.add_parser("translate", help="翻译 Markdown 文件")
    translate_parser.add_argument("path", nargs="?", default=os.getcwd(), help="要翻译的文件或目录路径")
    translate_parser.add_argument("--workers", type=int, default=MAX_WORKERS, help=f"并发工作线程数（默认: {MAX_WORKERS}）")
    translate_parser.add_argument("--api-key", type=str, help="DashScope API Key（覆盖环境变量 DASHSCOPE_API_KEY）")
    translate_parser.add_argument("--log-enable", action="store_true", help="启用文件日志")
    translate_parser.add_argument("--log-file", type=str, default="translation.log", help="日志文件路径（默认: translation.log）")
    translate_parser.add_argument("--usage-log-enable", action="store_true", help="启用使用统计日志（CSV 格式）")
    translate_parser.add_argument("--usage-log-file", type=str, default="usage.csv", help="使用统计日志路径（默认: usage.csv）")
    translate_parser.add_argument("--max-chars", type=int, default=5000, help="每个块的最大字符数（默认: 5000）")

    # copy 子命令
    copy_parser = subparsers.add_parser("copy", help="递归复制翻译后的文件到目标目录")
    copy_parser.add_argument("src", help="源目录")
    copy_parser.add_argument("dst", help="目标目录")

    # check 子命令
    check_parser = subparsers.add_parser("check", help="检查 API Key 可用性")
    check_parser.add_argument("--api-key", type=str, help="要检查的单个 API Key（忽略 ~/.qwen.json）")
    check_parser.add_argument("--test-file", type=str, help="用于测试的文件路径（使用第一个块）")
    check_parser.add_argument("--max-chars", type=int, default=8000, help="测试文本的最大字符数（默认: 8000）")

    # 向后兼容：如果第一个参数不是子命令，默认使用 translate
    if len(sys.argv) > 1 and sys.argv[1] not in ["translate", "copy", "check", "-h", "--help"]:
        sys.argv.insert(1, "translate")

    args = parser.parse_args()

    if args.command == "copy":
        handle_copy(args)
    elif args.command == "translate":
        handle_translate(args)
    elif args.command == "check":
        handle_check(args)
    else:
        parser.print_help()


def handle_check(args):
    """check 命令处理函数 - 检查 API Key 可用性。"""
    
    # 确定要检查的 Key
    keys_to_check = []
    
    if args.api_key:
        keys_to_check = [args.api_key]
        logger.info("正在检查命令行参数指定的 API Key...")
    else:
        # 从配置文件加载
        config_path = os.path.expanduser("~/.qwen.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    keys_to_check = config.get("api_keys", [])
                    if keys_to_check:
                        logger.info(f"从 {config_path} 加载了 {len(keys_to_check)} 个 API Key")
            except Exception as e:
                logger.error(f"加载配置文件失败 {config_path}: {e}")
                return
        
        if not keys_to_check:
            # 尝试环境变量
            env_key = os.getenv("DASHSCOPE_API_KEY")
            if env_key:
                keys_to_check = [env_key]
                logger.info("使用环境变量中的 API Key。")
    
    if not keys_to_check:
        logger.error("未找到 API Key。请通过 --api-key、~/.qwen.json 或 DASHSCOPE_API_KEY 环境变量提供。")
        return
    
    # 准备测试文本
    test_text = "Hello, this is a test message for API key validation."
    
    if args.test_file:
        test_file_path = os.path.abspath(args.test_file)
        if not os.path.exists(test_file_path):
            logger.error(f"测试文件不存在: {test_file_path}")
            return
        try:
            with open(test_file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
            if file_content.strip():
                chunks = list(split_text_into_chunks(file_content, max_chars=args.max_chars))
                test_text = chunks[0] if chunks else test_text
                logger.info(f"使用测试文件 {test_file_path}（{len(test_text)} 字符）")
        except Exception as e:
            logger.error(f"读取测试文件失败: {e}")
            return
    
    # 检查每个 Key
    valid_keys = []
    invalid_keys = []
    
    for i, key in enumerate(keys_to_check, 1):
        masked_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
        logger.info(f"[{i}/{len(keys_to_check)}] 正在检查 Key: {masked_key}")
        
        try:
            result, usage = _perform_translation(test_text, key, None)
            if result is not None:
                logger.info(f"  ✓ Key {masked_key} 可用")
                valid_keys.append(key)
            else:
                logger.warning(f"  ✗ Key {masked_key} 无效（无响应）")
                invalid_keys.append(key)
        except Exception as e:
            logger.warning(f"  ✗ Key {masked_key} 无效: {e}")
            invalid_keys.append(key)
    
    # 汇总
    logger.info("=" * 50)
    logger.info(f"检查完成: {len(valid_keys)} 个有效, {len(invalid_keys)} 个无效")
    
    if invalid_keys:
        logger.warning(f"无效 Key: {len(invalid_keys)}")
        for key in invalid_keys:
            masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
            logger.warning(f"  - {masked}")
    
    if valid_keys:
        logger.info(f"有效 Key: {len(valid_keys)}")
        for key in valid_keys:
            masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
            logger.info(f"  + {masked}")


def handle_translate(args):
    """translate 命令处理函数 - 翻译 Markdown 文件。"""
    
    # API Key 优先级：
    # 1. --api-key 参数（单 Key 模式 -> 强制串行）
    # 2. ~/.qwen.json（Key 池模式 -> 并行）
    # 3. DASHSCOPE_API_KEY 环境变量（单 Key 模式 -> 强制串行）
    
    api_key_or_pool = None
    use_pool = False
    
    # 1. 检查 --api-key
    if args.api_key:
        api_key_or_pool = args.api_key
        logger.info("使用命令行参数指定的 API Key。")
    
    # 2. 检查配置文件
    if not api_key_or_pool:
        config_path = os.path.expanduser("~/.qwen.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    api_keys = config.get("api_keys", [])
                    if api_keys:
                        logger.info(f"从 {config_path} 加载了 {len(api_keys)} 个 API Key")
                        api_key_or_pool = KeyPool(api_keys)
                        use_pool = True
            except Exception as e:
                logger.warning(f"加载配置文件失败 {config_path}: {e}")

    # 3. 检查环境变量
    if not api_key_or_pool:
        env_key = os.getenv("DASHSCOPE_API_KEY")
        if env_key:
            api_key_or_pool = env_key
            logger.info("使用环境变量中的 API Key。")

    if not api_key_or_pool:
        logger.error(
            "未找到 API Key。请通过 --api-key 参数、~/.qwen.json 或 DASHSCOPE_API_KEY 环境变量提供。"
        )
        return
    
    # 配置日志
    setup_logging(args.log_enable, args.log_file)
    setup_usage_logging(args.usage_log_enable, args.usage_log_file)
    
    # 显示 Key 信息
    if use_pool:
        logger.info(f"使用 API Key 池，共 {len(api_key_or_pool.keys)} 个 Key")
    else:
        k = api_key_or_pool
        masked = f"{k[:4]}...{k[-4:]}" if len(k) > 8 else "***"
        logger.info(f"使用单个 API Key: {masked}")

    target_path = os.path.abspath(args.path)

    files_to_translate = []

    if os.path.isfile(target_path):
        if target_path.endswith(".md") and not (target_path.endswith("_zh_cn.md") or target_path.endswith("_zh_CN.md")):
            files_to_translate = [target_path]
        else:
            logger.error(f"无效文件: {target_path}。必须是 .md 文件且不能是翻译输出文件。")
            return
    elif os.path.isdir(target_path):
        logger.info(f"正在扫描目录 {target_path} 中的 Markdown 文件...")
        files_to_translate = find_markdown_files(target_path)
    else:
        logger.error(f"路径不存在: {target_path}")
        return

    count = len(files_to_translate)
    logger.info(f"找到 {count} 个待翻译文件。")

    if count == 0:
        logger.info("没有找到文件，退出。")
        return

    # 确定工作线程数
    file_workers = 1
    shared_workers = 10
    
    if use_pool:
        num_keys = len(api_key_or_pool.keys)
        # 共享执行器用于所有 API 调用
        # 严格匹配 Key 数量，防止任务空等待 Key
        shared_workers = max(num_keys, 1)
        
        # 自动调整文件级并发
        if num_keys <= 1:
            # 池中只有 1 个 Key：强制串行
            if args.workers != 1:
                logger.warning("池中只有单个 Key。强制 workers=1 以确保独占使用。")
            file_workers = 1
        else:
            file_workers = args.workers
            if file_workers == MAX_WORKERS:
                file_workers = num_keys
                logger.info(f"自动将文件并发数增加到 {file_workers}，以充分利用 {num_keys} 个 API Key。")
    else:
        # 单 Key 严格串行
        if args.workers != 1:
            logger.warning("检测到单个 API Key。强制 workers=1 以确保独占使用。")
        file_workers = 1
        shared_workers = 1
        logger.info("单 Key 串行模式运行。")

    logger.info(f"开始翻译：{file_workers} 个文件并发，{shared_workers} 个 API 并发...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=shared_workers) as shared_executor:
        with concurrent.futures.ThreadPoolExecutor(max_workers=file_workers) as file_executor:
            future_to_file = {
                file_executor.submit(translate_file, f, api_key_or_pool, shared_executor, max_chars=args.max_chars): f 
                for f in files_to_translate
            }
            
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_file):
                completed_count += 1
                try:
                    file_path, success = future.result()
                    remaining = count - completed_count
                    logger.info(f"进度: [{completed_count}/{count}] 文件完成。（剩余 {remaining}）")
                except Exception as e:
                    logger.error(f"文件处理失败: {e}")


def handle_copy(args):
    """copy 命令处理函数 - 递归复制翻译后的文件。"""
    import glob
    
    src_dir = os.path.abspath(args.src)
    dst_dir = os.path.abspath(args.dst)

    if not os.path.isdir(src_dir):
        logger.error(f"源目录不存在: {src_dir}")
        return

    logger.info(f"正在从 {src_dir} 复制翻译文件到 {dst_dir}...")

    # 翻译文件的模式
    patterns = ["**/*_zh_CN.md", "**/*_zh_cn.md"]
    files_to_copy = []
    for pattern in patterns:
        files_to_copy.extend(glob.glob(os.path.join(src_dir, pattern), recursive=True))

    if not files_to_copy:
        logger.info("未找到需要复制的翻译文件。")
        return

    logger.info(f"找到 {len(files_to_copy)} 个翻译文件。")
    copy_count = 0

    for src_file in files_to_copy:
        try:
            # 计算相对路径
            rel_path = os.path.relpath(src_file, src_dir)
            
            # 移除后缀并重命名
            if rel_path.endswith("_zh_CN.md"):
                new_rel_path = rel_path[:-10] + ".md"
            elif rel_path.endswith("_zh_cn.md"):
                new_rel_path = rel_path[:-10] + ".md"
            else:
                continue

            dst_file = os.path.join(dst_dir, new_rel_path)

            # 确保目标目录存在
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)

            # 复制文件
            shutil.copy2(src_file, dst_file)
            logger.info(f"已复制: {rel_path} -> {new_rel_path}")
            copy_count += 1
        except Exception as e:
            logger.error(f"复制失败 {src_file}: {e}")

    logger.info(f"成功复制 {copy_count} 个文件。")


if __name__ == "__main__":
    main()
