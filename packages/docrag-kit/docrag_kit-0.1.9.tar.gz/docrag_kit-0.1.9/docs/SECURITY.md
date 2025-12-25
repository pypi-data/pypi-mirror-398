# Security Best Practices for DocRAG Kit

This document provides comprehensive security guidance for using DocRAG Kit safely and protecting your API keys.

## Table of Contents

- [Overview](#overview)
- [API Key Protection](#api-key-protection)
- [Automatic Security Features](#automatic-security-features)
- [Best Practices](#best-practices)
- [What to Do If Keys Are Exposed](#what-to-do-if-keys-are-exposed)
- [Pre-commit Hook Setup](#pre-commit-hook-setup)
- [Security Checklist](#security-checklist)
- [Team Collaboration](#team-collaboration)

## Overview

DocRAG Kit uses API keys to access LLM services (OpenAI or Google Gemini). These keys:
- Provide access to paid services
- Can incur charges if misused
- Should never be shared or committed to version control
- Must be kept confidential

**Critical Rule**: Never commit your `.env` file to git!

## API Key Protection

### Why API Keys Must Be Protected

1. **Financial Risk**: Exposed keys can be used by others, costing you money
2. **Account Security**: Keys provide access to your account and data
3. **Rate Limits**: Misuse can exhaust your rate limits
4. **Service Disruption**: Compromised keys may need to be revoked, disrupting your workflow

### Where API Keys Are Stored

DocRAG Kit stores API keys in:
- `.env` file in project root (for project-specific keys)
- Environment variables (alternative method)

**Never store API keys in:**
- Configuration files (`.docrag/config.yaml`)
- Source code files
- Git repositories
- Public documentation
- Chat messages or emails

## Automatic Security Features

DocRAG Kit automatically protects your API keys during initialization:

### 1. .docrag/.gitignore Creation

Creates `.docrag/.gitignore` with:
```gitignore
# Vector database (can be regenerated)
vectordb/

# Python cache
*.pyc
__pycache__/

# Environment variables (contains API keys)
.env
```

### 2. Root .gitignore Validation

- Checks if root `.gitignore` exists
- Verifies `.env` is excluded
- Offers to add `.env` if missing
- Displays warnings if not properly configured

### 3. .env.example Template

Creates `.env.example` with:
- Placeholder keys (not real keys)
- Comments with links to get keys
- Instructions for team members

### 4. Security Warnings

Displays security reminders after initialization:
- API key storage location
- Gitignore status
- Best practices
- Pre-commit hook suggestion

## Best Practices

### 1. Always Use .gitignore

Ensure `.env` is in your root `.gitignore`:

```bash
# Check if .env is gitignored
grep .env .gitignore

# If not found, add it
echo ".env" >> .gitignore
```

### 2. Use .env.example Pattern

**For project maintainers:**
1. Create `.env.example` with placeholder keys
2. Commit `.env.example` to git
3. Document setup process in README

**For team members:**
1. Copy `.env.example` to `.env`
2. Add your own API keys
3. Never commit `.env`

Example `.env.example`:
```bash
# OpenAI API Key
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_key_here

# Google Gemini API Key
# Get from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_gemini_key_here
```

### 3. Verify Before Committing

Before every commit:
```bash
# Check what's staged
git status

# Verify .env is not staged
git diff --cached --name-only | grep .env

# If .env appears, unstage it
git reset .env
```

### 4. Use Environment Variables (Alternative)

Instead of `.env` file, use system environment variables:

```bash
# Add to ~/.bashrc or ~/.zshrc
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

### 5. Rotate Keys Regularly

- Rotate API keys every 90 days
- Rotate immediately if exposure suspected
- Keep old keys active briefly during rotation
- Update all environments after rotation

### 6. Use Separate Keys for Different Environments

- Development: Use separate API key
- Production: Use different API key
- Testing: Use yet another API key
- This limits damage if one key is exposed

## What to Do If Keys Are Exposed

If you accidentally commit `.env` or expose API keys:

### Step 1: Revoke Exposed Keys Immediately

**OpenAI:**
1. Go to https://platform.openai.com/api-keys
2. Find the exposed key
3. Click "Revoke" or delete the key
4. Confirm revocation

**Google Gemini:**
1. Go to https://makersuite.google.com/app/apikey
2. Find the exposed key
3. Delete or disable the key
4. Confirm deletion

### Step 2: Generate New Keys

1. Create new API key from provider dashboard
2. Copy the new key
3. Update your `.env` file
4. Test that new key works

### Step 3: Remove Keys from Git History

**Option A: Using git filter-branch (small repos)**
```bash
# Remove .env from all commits
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push to remote
git push origin --force --all
git push origin --force --tags
```

**Option B: Using BFG Repo-Cleaner (recommended for large repos)**
```bash
# Install BFG
# macOS: brew install bfg
# Or download from: https://rtyley.github.io/bfg-repo-cleaner/

# Remove .env from history
bfg --delete-files .env

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
```

### Step 4: Notify Team Members

If working in a team:
1. Notify all team members immediately
2. Ask them to re-clone the repository
3. Provide new API keys securely (not via git)
4. Verify everyone has updated

### Step 5: Monitor for Misuse

After exposure:
- Check API usage dashboard for unusual activity
- Monitor billing for unexpected charges
- Review API logs for suspicious requests
- Consider enabling usage alerts

## Pre-commit Hook Setup

Prevent accidental commits of `.env` with a pre-commit hook:

### Automatic Setup

```bash
# Create and install pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# Check if .env is being committed
if git diff --cached --name-only | grep -q "^\.env$"; then
    echo "ERROR: Attempting to commit .env file!"
    echo ""
    echo "This file contains sensitive API keys and should never be committed."
    echo ""
    echo "To fix this:"
    echo "  1. Unstage .env: git reset .env"
    echo "  2. Add .env to .gitignore"
    echo "  3. Commit again"
    echo ""
    exit 1
fi

# Check if any file contains potential API keys
if git diff --cached | grep -qE "(OPENAI_API_KEY|GOOGLE_API_KEY|sk-[a-zA-Z0-9]{32,})"; then
    echo "WARNING: Potential API key detected in staged changes!"
    echo ""
    echo "Please review your changes carefully."
    echo "API keys should only be in .env file (which should be gitignored)."
    echo ""
    read -p "Continue with commit? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

exit 0
EOF

# Make executable
chmod +x .git/hooks/pre-commit

echo "Pre-commit hook installed successfully!"
```

### Manual Setup

1. Create `.git/hooks/pre-commit` file
2. Add the script above
3. Make it executable: `chmod +x .git/hooks/pre-commit`
4. Test by trying to commit `.env`

### Testing the Hook

```bash
# Try to commit .env (should fail)
git add .env
git commit -m "test"

# Should see error message and commit blocked
```

## Security Checklist

Before pushing code to git, verify:

- [ ] `.env` exists and contains your API keys
- [ ] `.env` is in `.gitignore`
- [ ] `.env` is NOT staged for commit (`git status`)
- [ ] `.env.example` exists (without real keys)
- [ ] `.docrag/.gitignore` excludes `vectordb/` and `.env`
- [ ] No API keys in configuration files
- [ ] No API keys in source code
- [ ] Pre-commit hook is installed (recommended)
- [ ] Team members know not to commit `.env`

## Team Collaboration

### For Project Maintainers

1. **Initial Setup:**
   ```bash
   # Initialize DocRAG
   docrag init
   
   # Verify .env is gitignored
   grep .env .gitignore
   
   # Commit .env.example (not .env!)
   git add .env.example
   git commit -m "Add .env.example template"
   ```

2. **Document Setup Process:**
   Add to your README:
   ```markdown
   ## Setup
   
   1. Clone repository
   2. Copy .env.example to .env
   3. Add your API keys to .env
   4. Run: docrag index
   ```

3. **Provide Keys Securely:**
   - Use password manager (1Password, LastPass)
   - Use secure messaging (Signal, encrypted email)
   - Never commit keys to git
   - Never share keys in public channels

### For Team Members

1. **Initial Setup:**
   ```bash
   # Clone repository
   git clone <repo-url>
   cd <repo>
   
   # Copy template
   cp .env.example .env
   
   # Edit .env and add your keys
   nano .env
   
   # Verify .env is gitignored
   git status  # .env should not appear
   ```

2. **Verify Security:**
   ```bash
   # Check .env is not tracked
   git ls-files | grep .env  # Should be empty
   
   # Check .env is gitignored
   git check-ignore .env  # Should output: .env
   ```

3. **Get API Keys:**
   - OpenAI: https://platform.openai.com/api-keys
   - Google Gemini: https://makersuite.google.com/app/apikey
   - Use your own keys (don't share with team)

## Additional Resources

### API Key Management

- **OpenAI API Keys**: https://platform.openai.com/api-keys
- **Google Gemini API Keys**: https://makersuite.google.com/app/apikey
- **GitHub Tokens**: https://github.com/settings/tokens

### Security Tools

- **BFG Repo-Cleaner**: https://rtyley.github.io/bfg-repo-cleaner/
- **git-secrets**: https://github.com/awslabs/git-secrets
- **truffleHog**: https://github.com/trufflesecurity/trufflehog

### Best Practices

- **OWASP Secrets Management**: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- **GitHub Security Best Practices**: https://docs.github.com/en/code-security/getting-started/best-practices-for-preventing-data-leaks-in-your-organization

## Support

If you have security concerns or questions:

1. Review this document thoroughly
2. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Open a GitHub issue (without exposing keys!)
4. Contact maintainers privately for sensitive issues

---

**Remember**: Security is everyone's responsibility. When in doubt, don't commit!
