# Qwen-MT Tool

A CLI tool for translating markdown files using Qwen-MT (via OpenAI compatible API).

## Features

- **Recursive Scanning**: Automatically finds all `.md` files in a directory.
- **Dependency Awareness**: Skips files that have already been translated (ending in `_zh_CN.md`).
- **Concurrency**: Translates multiple files in parallel for faster processing.
- **Smart Splitting**: Splits long documents into chunks to avoid token limits while preserving code blocks.
- **Usage Tracking**: Logs token usage to `usage.log`.

## Installation

```bash
pip install qwen-mt-tool
```

## Usage

### Prerequisites

You need a DashScope API Key. You can set it as an environment variable or pass it via command line.

```bash
export DASHSCOPE_API_KEY="sk-..."
```

### Basic Usage

Translate a single file:

```bash
qwen-mt path/to/file.md
```

Translate all markdown files in a directory (recursive):

```bash
qwen-mt path/to/directory
```

### Options

- `--workers <N>`: Number of concurrent workers (default: 1).
- `--api-key <KEY>`: Explicitly provide the API key.

```bash
qwen-mt . --workers 4 --api-key "sk-..."
```

## Output

Translated files will be created in the same directory with a `_zh_CN.md` suffix.
For example, `README.md` -> `README_zh_CN.md`.
