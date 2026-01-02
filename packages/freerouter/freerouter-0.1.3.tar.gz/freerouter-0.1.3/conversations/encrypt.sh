#!/bin/bash
# Encrypt conversation files

set -e

if [ $# -eq 0 ]; then
    echo "Usage: ./encrypt.sh <file>"
    echo "Example: ./encrypt.sh conversation.txt"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="${INPUT_FILE}.enc"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File '$INPUT_FILE' not found"
    exit 1
fi

echo "Encrypting: $INPUT_FILE -> $OUTPUT_FILE"
openssl enc -aes-256-cbc -salt -pbkdf2 -in "$INPUT_FILE" -out "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "✓ Encryption successful"
    echo "✓ Created: $OUTPUT_FILE"
    echo ""
    echo "You can now safely commit: $OUTPUT_FILE"
    echo "Remember to delete the original if it contains sensitive info:"
    echo "  rm $INPUT_FILE"
else
    echo "✗ Encryption failed"
    exit 1
fi
