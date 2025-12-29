# -*- coding: utf-8 -*-
"""
工具模块 - 文本分片和文件查找等通用工具函数
"""

import glob
import os


def split_text_into_chunks(text: str, max_chars: int = 5000):
    """
    按行将文本分割成块，避免超过 token 限制。
    
    尽量保持代码块完整性（不在 ```...``` 内部分割），
    但如果代码块过大，会强制分割。
    
    Args:
        text: 要分割的文本
        max_chars: 每个块的最大字符数（默认 5000）
    
    Yields:
        str: 文本块
    """
    lines = text.splitlines(keepends=True)
    current_chunk = []
    current_length = 0
    in_code_block = False
    
    # 代码块内允许最多 1.2 倍的 max_chars，超过则强制分割
    hard_limit = int(max_chars * 1.2)
    
    for line in lines:
        # 检测 Markdown 代码块标记
        if line.lstrip().startswith("```"):
            in_code_block = not in_code_block
        
        current_chunk.append(line)
        current_length += len(line)
        
        # 达到硬限制时强制分割（即使在代码块中）
        if current_length > hard_limit:
            yield "".join(current_chunk)
            current_chunk = []
            current_length = 0
        # 正常分割：超过限制且不在代码块中
        elif current_length > max_chars and not in_code_block:
            yield "".join(current_chunk)
            current_chunk = []
            current_length = 0
            
    if current_chunk:
        yield "".join(current_chunk)


def find_markdown_files(root_dir: str) -> list:
    """
    递归查找 Markdown 文件，排除已翻译的文件。
    
    Args:
        root_dir: 根目录路径
    
    Returns:
        list: Markdown 文件路径列表
    """
    md_files = []
    all_md_files = glob.glob(os.path.join(root_dir, "**", "*.md"), recursive=True)

    for f in all_md_files:
        # 排除已翻译的文件
        if f.endswith("_zh_cn.md") or f.endswith("_zh_CN.md"):
            continue
        md_files.append(f)

    return md_files
