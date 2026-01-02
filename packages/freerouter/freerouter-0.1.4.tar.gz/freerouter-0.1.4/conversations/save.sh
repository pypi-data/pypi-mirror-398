#!/bin/bash
# 一键保存并加密对话

set -e

if [ $# -eq 0 ]; then
    echo "Usage: ./save.sh <conversation-file.txt>"
    echo ""
    echo "This script will:"
    echo "  1. Encrypt the file"
    echo "  2. Delete the original"
    echo "  3. Stage the encrypted file for commit"
    echo ""
    echo "Example: ./save.sh 2025-12-26-pypi-release.txt"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="${INPUT_FILE}.enc"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File '$INPUT_FILE' not found"
    exit 1
fi

echo "📦 Encrypting conversation..."
./encrypt.sh "$INPUT_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "🔥 Deleting original file for security..."
    rm "$INPUT_FILE"

    echo "📝 Staging encrypted file..."
    git add "$OUTPUT_FILE"

    echo ""
    echo "✅ Done! Ready to commit:"
    echo "   git commit -m \"docs: add conversation $(basename ${INPUT_FILE%.txt})\""
    echo "   git push"
else
    echo "❌ Encryption failed"
    exit 1
fi
