# DocRAG Kit - Quick Start Guide

This guide helps you get DocRAG Kit up and running quickly and troubleshoot common issues.

## Installation

```bash
pip install docrag-kit
```

## Quick Setup (3 steps)

### 1. Initialize DocRAG in your project

```bash
cd your-project
docrag init
```

Follow the interactive wizard or use non-interactive mode:

```bash
docrag init --non-interactive --template general
```

### 2. Index your documentation

```bash
docrag index
```

This will scan your documentation and create a vector database.

### 3. Configure MCP for Kiro AI

```bash
docrag mcp-config
```

This will add DocRAG to your Kiro workspace configuration.

## Troubleshooting

### Run Health Check

If something isn't working, run the diagnostic tool:

```bash
docrag doctor
```

This will check:
- DocRAG initialization
- Configuration files
- API keys
- Vector database
- Python environment
- Required packages
- MCP configuration

### Common Issues

#### 1. Import Errors with MCP Server

**Problem:**
```
ModuleNotFoundError: No module named 'docrag.config_manager'
```

**Solution:**
The MCP server must be run through the installed package, not as a script.

**Correct MCP Configuration:**
```json
{
  "mcpServers": {
    "docrag": {
      "command": "/path/to/python",
      "args": ["-m", "docrag.mcp_server"],
      "cwd": "/path/to/your/project",
      "env": {}
    }
  }
}
```

**Incorrect (don't use):**
```json
{
  "command": "python",
  "args": [".docrag/mcp_server.py"]  // Relative imports won't work
}
```

#### 2. Missing Configuration

**Problem:**
```
Error: Configuration not found
```

**Solution:**
```bash
# Re-initialize DocRAG
docrag init
```

#### 3. Missing Vector Database

**Problem:**
```
Vector database not found
```

**Solution:**
```bash
# Index your documentation
docrag index
```

#### 4. API Key Not Set

**Problem:**
```
OpenAI API key not found
```

**Solution:**
1. Create or edit `.env` file in your project root:
```bash
OPENAI_API_KEY=sk-your-key-here
```

2. Get your API key from: https://platform.openai.com/api-keys

#### 5. Python Version Too Old

**Problem:**
```
Python 3.9 is too old (need 3.10+)
```

**Solution:**
Install Python 3.10 or higher:

```bash
# Using pyenv (recommended)
pyenv install 3.10.14
pyenv local 3.10.14

# Or download from python.org
```

#### 6. MCP Package Not Installed

**Problem:**
```
Required package 'mcp' not installed
```

**Solution:**
```bash
pip install mcp>=0.9.0
```

## Best Practices

### 1. Use Virtual Environments

```bash
# Create virtual environment
python -m venv .venv-docrag

# Activate it
source .venv-docrag/bin/activate  # Linux/Mac
.venv-docrag\Scripts\activate     # Windows

# Install DocRAG Kit
pip install docrag-kit
```

### 2. Keep API Keys Secure

- Store in `.env` file
- Add `.env` to `.gitignore`
- Never commit API keys to git
- Never share `.env` file

### 3. Regular Reindexing

When your documentation changes significantly:

```bash
docrag reindex
```

### 4. Check Configuration

View your current configuration:

```bash
docrag config
```

Edit configuration:

```bash
docrag config --edit
```

## MCP Configuration Details

### Workspace vs User Config

DocRAG adds MCP configuration to **workspace config** by default:
- Location: `.kiro/settings/mcp.json`
- Scope: Only this project
- Benefit: Easy to share with team via git

To use globally, manually add to user config:
- Location: `~/.kiro/settings/mcp.json`
- Scope: All projects

### Correct MCP Configuration Structure

```json
{
  "mcpServers": {
    "docrag": {
      "command": "/full/path/to/python",
      "args": ["-m", "docrag.mcp_server"],
      "cwd": "/full/path/to/project",
      "env": {
        "OPENAI_API_KEY": "sk-..."  // Optional: can use .env instead
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Key points:**
- Use `-m docrag.mcp_server` to run as module
- Set `cwd` to your project directory
- Use full paths (not relative)
- API key can be in `.env` or `env` section

## Getting Help

1. Run `docrag doctor` to diagnose issues
2. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions
3. Open an issue on GitHub: https://github.com/dexiusprime-oss/docrag-kit/issues

## Next Steps

- Read [EXAMPLES.md](EXAMPLES.md) for usage examples
- Check [API_REFERENCE.md](API_REFERENCE.md) for detailed API docs
- See [MCP_INTEGRATION.md](MCP_INTEGRATION.md) for MCP details
