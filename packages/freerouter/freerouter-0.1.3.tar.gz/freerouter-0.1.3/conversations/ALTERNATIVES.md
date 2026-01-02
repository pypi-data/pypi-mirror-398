# Alternative Solutions for Conversation Storage

## Current Solution: OpenSSL AES-256-CBC ✅

**Pros**:
- Simple, no extra dependencies
- Password-based (symmetric encryption)
- Works everywhere OpenSSL is installed
- Full control

**Cons**:
- Manual encryption/decryption
- Need to remember to encrypt before commit

## Alternative 1: transcrypt (Recommended!)

**What**: Transparent encryption for Git repos using OpenSSL
**Type**: Password-based (like our current solution)
**Magic**: Automatic encryption on commit, decryption on checkout!

### Installation

```bash
# Clone transcrypt
git clone https://github.com/elasticdog/transcrypt.git
cd transcrypt
sudo make install

# Or on Arch Linux
yay -S transcrypt
```

### Setup

```bash
cd freerouter  # Your cloned repo directory

# Initialize transcrypt with a password
transcrypt -c aes-256-cbc -p 'YOUR_PASSWORD_HERE'

# Configure which files to encrypt
echo 'conversations/*.txt filter=crypt diff=crypt merge=crypt' >> .gitattributes

# Commit .gitattributes
git add .gitattributes
git commit -m "chore: enable transcrypt for conversations"
```

### On New Machine

```bash
git clone https://github.com/mmdsnb/freerouter.git
cd freerouter

# Enter the same password
transcrypt -c aes-256-cbc -p 'YOUR_PASSWORD_HERE'

# Files are automatically decrypted!
```

### Usage

```bash
# Just use git normally!
echo "My conversation" > conversations/secret.txt
git add conversations/secret.txt
git commit -m "Add conversation"  # Auto-encrypted!
git push                           # Encrypted version pushed

# On pull
git pull  # Auto-decrypted!
```

**Pros**:
- ✅ Password-based (no key files!)
- ✅ Completely transparent
- ✅ Built on OpenSSL (same as our current solution)
- ✅ Works on any machine with the password
- ✅ No manual encrypt/decrypt steps

**Cons**:
- Requires installing transcrypt

## Alternative 2: Git-secret

**What**: GPG-based encryption for Git
**Type**: GPG keys (public/private)

```bash
# Installation
yay -S git-secret  # Arch Linux

# Setup
git secret init
git secret tell your@email.com
git secret add conversations/*.txt
git secret hide  # Encrypt

# On new machine
git secret reveal  # Decrypt (needs your GPG key)
```

**Pros**:
- GPG integration
- Can share with multiple users

**Cons**:
- ❌ Requires GPG keys (you wanted password-based)
- More complex setup

## Alternative 3: GitHub Encrypted Secrets (Actions)

Store conversations as GitHub Actions secrets and decrypt via workflow.

**Pros**:
- Native GitHub integration

**Cons**:
- ❌ Only accessible via Actions
- ❌ Not practical for regular access

## Alternative 4: Private Submodule

Create a separate private repo for conversations.

```bash
git submodule add https://github.com/mmdsnb/freerouter-conversations.git conversations
```

**Pros**:
- Separation of concerns
- Private repo = encrypted

**Cons**:
- ❌ Still not encrypted (just private)
- More repos to manage

## Recommendation: transcrypt

**Why**: It's exactly what you want!
- Password-based ✅
- Automatic ✅
- Built on OpenSSL ✅
- Transparent workflow ✅

### Migration Path

1. Install transcrypt
2. Initialize with password
3. Configure .gitattributes
4. Keep existing encrypted files (or re-encrypt them transparently)
5. From now on, just use `git add/commit/push` normally!

### Example Workflow with transcrypt

```bash
# Export conversation from Claude
/export conversations/2025-12-26-discussion.txt

# Just commit - transcrypt handles encryption!
git add conversations/2025-12-26-discussion.txt
git commit -m "docs: add discussion about X"
git push

# On another machine (after transcrypt setup with password)
git pull  # File is automatically decrypted and ready to read!
cat conversations/2025-12-26-discussion.txt  # Plain text!
```

No more manual encrypt.sh/decrypt.sh needed!
