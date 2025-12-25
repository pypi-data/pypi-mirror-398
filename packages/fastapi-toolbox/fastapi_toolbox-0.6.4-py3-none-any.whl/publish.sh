#!/bin/bash

# 从文件读取 PyPI token
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOKEN_FILE="$SCRIPT_DIR/.pypi_token"

if [ ! -f "$TOKEN_FILE" ]; then
    echo "错误: 未找到 token 文件: $TOKEN_FILE"
    echo "请创建该文件并写入你的 PyPI token"
    exit 1
fi

export UV_PUBLISH_TOKEN=$(cat "$TOKEN_FILE")

uv build && uv publish
