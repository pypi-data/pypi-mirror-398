# -*- coding: utf-8 -*-
"""
配置模块 - 存放常量和默认配置
"""

# 默认翻译模型
DEFAULT_MODEL = "qwen-mt-plus"

# 默认并发工作线程数
MAX_WORKERS = 1

# 翻译选项（源语言和目标语言）
TRANSLATION_OPTIONS = {
    "source_lang": "English",
    "target_lang": "Chinese",
}

# 翻译提示词模板（备用，当前使用 DashScope 翻译专用 API）
PROMPT_TEMPLATE = """
# Role
You are a senior software development engineer, proficient in multiple programming languages, including but not limited to Python, Java, C++, Go, JavaScript, and others. You have a deep understanding of professional terminology in the field of software engineering.

# Task
I need you to translate the following English document, which may contain code, into professional, precise, and formal Chinese.

# Translation Requirements
1. **Strictly preserve formatting**: Do not arbitrarily change the formatting, including but not limited to paragraphs, numbering, and code.
2. **Be faithful to the original text**: Translate strictly according to the meaning and intent of the original text, without adding or removing any information.
3. **Use precise terminology**: Use professional terminology from the Chinese software development field. For proper nouns, retain the original text.
4. **Ensure clear sentences**: The translation must be clear, unambiguous, and consistent with the expression conventions of Chinese software development documentation.
5. **Preserve formatting**: Maintain the original text's paragraphs, numbering, and basic formatting.
6. **Preserve code**: Retain the original text's code format and content. The content within the code, including but not limited to the code itself and its comments, must remain unchanged.

# Text to translate
{text_to_translate}
"""
