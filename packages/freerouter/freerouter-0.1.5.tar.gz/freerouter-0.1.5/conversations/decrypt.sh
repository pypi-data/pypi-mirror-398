#!/bin/bash
# Decrypt conversation files

set -e

if [ $# -eq 0 ]; then
    echo "Usage: ./decrypt.sh <encrypted-file> [output-file]"
    echo ""
    echo "Examples:"
    echo "  ./decrypt.sh conversation.txt.enc                    # Decrypt to conversation.txt"
    echo "  ./decrypt.sh conversation.txt.enc output.txt         # Decrypt to output.txt"
    echo "  ./decrypt.sh conversation.txt.enc - | less           # View without saving"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="${2:-${INPUT_FILE%.enc}}"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File '$INPUT_FILE' not found"
    exit 1
fi

if [ "$OUTPUT_FILE" = "-" ]; then
    # Output to stdout
    openssl enc -aes-256-cbc -d -pbkdf2 -in "$INPUT_FILE"
else
    # Output to file
    echo "Decrypting: $INPUT_FILE -> $OUTPUT_FILE"
    openssl enc -aes-256-cbc -d -pbkdf2 -in "$INPUT_FILE" -out "$OUTPUT_FILE"

    if [ $? -eq 0 ]; then
        echo "✓ Decryption successful"
        echo "✓ Created: $OUTPUT_FILE"
    else
        echo "✗ Decryption failed"
        exit 1
    fi
fi
