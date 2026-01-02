# Conversations Archive

This directory contains encrypted conversation logs between the developer and AI assistant.

## Encryption

All conversation files are encrypted using AES-256-CBC via OpenSSL.

## Usage

### Encrypt a conversation

```bash
# Encrypt a file
./encrypt.sh conversation.txt

# This will create: conversation.txt.enc
```

### Decrypt a conversation

```bash
# Decrypt a file
./decrypt.sh conversation.txt.enc

# This will create: conversation.txt
```

### View encrypted conversation

```bash
# Quick view without saving
./decrypt.sh conversation.txt.enc | less
```

## File Naming Convention

```
YYYY-MM-DD-topic.txt.enc
```

Example:
- `2025-12-26-pypi-release.txt.enc`
- `2025-12-26-provider-refactoring.txt.enc`

## Security Notes

- ⚠️ **Never commit unencrypted `.txt` files**
- ✅ Only commit `.enc` files
- 🔑 Keep your encryption password safe
- 📝 All `.txt` files are in `.gitignore`

## Current Conversations

- `2025-12-26-initial-pypi-release.txt.enc` - First release to PyPI, provider system design
