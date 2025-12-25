# Troubleshooting Guide

This guide helps you diagnose and fix common issues with DocRAG Kit.

## Table of Contents

- [Installation Issues](#installation-issues)
- [API Key Problems](#api-key-problems)
- [Indexing Errors](#indexing-errors)
- [MCP Connection Issues](#mcp-connection-issues)
- [Performance Optimization](#performance-optimization)
- [Common Error Messages](#common-error-messages)

## Installation Issues

### Python Version Error

**Problem**: Installation fails with Python version error

**Symptoms**:
```
ERROR: Package 'docrag-kit' requires a different Python: 3.9.6 not in '>=3.10'
```

**Root Cause**: DocRAG Kit requires Python 3.10+ due to the MCP (Model Context Protocol) library dependency.

**Solutions**:

1. **Install Python 3.10 or newer**:
   ```bash
   # Using pyenv (recommended)
   pyenv install 3.11.0
   pyenv local 3.11.0
   
   # Or download from python.org
   # https://www.python.org/downloads/
   ```

2. **Check your Python version**:
   ```bash
   python --version
   # Should show 3.10.x or higher
   ```

3. **Use the correct Python executable**:
   ```bash
   # If you have multiple Python versions
   python3.10 -m pip install docrag-kit
   # or
   python3.11 -m pip install docrag-kit
   ```

### Dependency Conflict with onnxruntime or pulsar-client

**Problem**: Installation fails with dependency resolution errors

**Symptoms**:
```
ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
Additionally, some packages in these conflicts have no matching distributions available for your environment:
onnxruntime
pulsar-client
```

**Root Cause**: DocRAG Kit requires Python 3.10+ due to the MCP library dependency. ChromaDB also requires `onnxruntime` and `pulsar-client` which may not be available for all platforms (especially ARM-based systems like Apple Silicon M1/M2).

**Solutions**:

1. **Use Python 3.10 or 3.11** (required):
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install docrag-kit
   ```

2. **Install with --no-deps and manually install core dependencies**:
   ```bash
   pip install --no-deps docrag-kit
   pip install click pyyaml python-dotenv chardet tiktoken mcp
   pip install langchain langchain-openai langchain-google-genai
   pip install chromadb --no-deps
   pip install chromadb-client  # Lighter alternative
   ```

3. **Use conda (for problematic platforms)**:
   ```bash
   conda create -n docrag python=3.11
   conda activate docrag
   conda install -c conda-forge onnxruntime
   pip install docrag-kit
   ```

4. **Install from source with specific ChromaDB version**:
   ```bash
   git clone https://github.com/dexiusprime-oss/docrag-kit.git
   cd docrag-kit
   pip install chromadb==0.4.22
   pip install -e .
   ```

5. **For Apple Silicon (M1/M2/M3)**:
   ```bash
   # Use Rosetta or native ARM build
   arch -arm64 pip install docrag-kit
   # Or use miniforge/mambaforge
   ```

### pip install fails

**Problem**: `pip install docrag-kit` fails with errors

**Symptoms**:
```
ERROR: Could not find a version that satisfies the requirement docrag-kit
```

**Solutions**:

1. **Update pip**:
   ```bash
   pip install --upgrade pip
   ```

2. **Check Python version**:
   ```bash
   python --version
   # Should be 3.10 or higher
   ```

3. **Install from source**:
   ```bash
   git clone https://github.com/dexiusprime-oss/docrag-kit.git
   cd docrag-kit
   pip install -e .
   ```

4. **Use virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install docrag-kit
   ```

### Missing dependencies

**Problem**: Import errors after installation

**Symptoms**:
```
ModuleNotFoundError: No module named 'langchain'
```

**Solutions**:

1. **Reinstall with dependencies**:
   ```bash
   pip install --force-reinstall docrag-kit
   ```

2. **Install dependencies manually**:
   ```bash
   pip install langchain langchain-openai langchain-google-genai chromadb click pyyaml python-dotenv mcp
   ```

3. **Check installation**:
   ```bash
   pip show docrag-kit
   pip list | grep langchain
   ```

### Command not found

**Problem**: `docrag` command not available after installation

**Symptoms**:
```bash
docrag --version
# bash: docrag: command not found
```

**Solutions**:

1. **Check pip installation location**:
   ```bash
   pip show docrag-kit
   # Note the Location path
   ```

2. **Add to PATH** (if needed):
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="$PATH:$HOME/.local/bin"
   ```

3. **Use python -m**:
   ```bash
   python -m docrag --version
   ```

4. **Reinstall in user space**:
   ```bash
   pip install --user docrag-kit
   ```

## API Key Problems

### Missing API key

**Problem**: Error about missing API key

**Symptoms**:
```
Error: API key not found
   Please add your API key to .env file
```

**Solutions**:

1. **Create .env file**:
   ```bash
   cd /path/to/your/project
   touch .env
   ```

2. **Add API key**:
   ```bash
   # For OpenAI
   echo "OPENAI_API_KEY=sk-your-key-here" >> .env
   
   # For Gemini
   echo "GOOGLE_API_KEY=your-key-here" >> .env
   ```

3. **Verify .env file**:
   ```bash
   cat .env
   # Should show your API key
   ```

4. **Check file location**:
   ```bash
   # .env should be in project root, same directory as .docrag/
   ls -la | grep .env
   ```

### Invalid API key

**Problem**: API key is rejected by provider

**Symptoms**:
```
Error: Invalid API key
   Authentication failed with OpenAI
```

**Solutions**:

1. **Verify key format**:
   - OpenAI keys start with `sk-`
   - Gemini keys are alphanumeric strings

2. **Check for extra spaces**:
   ```bash
   # Remove any whitespace
   OPENAI_API_KEY=sk-abc123  # Good
   OPENAI_API_KEY= sk-abc123 # Bad (space before key)
   ```

3. **Generate new key**:
   - OpenAI: https://platform.openai.com/api-keys
   - Gemini: https://makersuite.google.com/app/apikey

4. **Test key directly**:
   ```bash
   # For OpenAI
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer sk-your-key-here"
   ```

### Rate limit exceeded

**Problem**: Too many API requests

**Symptoms**:
```
Error: Rate limit exceeded
   You have exceeded your API quota
```

**Solutions**:

1. **Wait and retry**:
   - Free tier: Wait 1 minute
   - Paid tier: Wait a few seconds

2. **Check usage**:
   - OpenAI: https://platform.openai.com/usage
   - Gemini: https://console.cloud.google.com/

3. **Upgrade plan**:
   - Consider paid tier for higher limits

4. **Reduce indexing frequency**:
   - Index less frequently
   - Reduce number of files

5. **Adjust chunk size**:
   ```yaml
   # In .docrag/config.yaml
   chunking:
     chunk_size: 2000  # Larger chunks = fewer API calls
   ```

## Indexing Errors

### No files found

**Problem**: Indexing finds 0 files

**Symptoms**:
```
Indexing documents...
✓ Found 0 files to index
```

**Solutions**:

1. **Check directories**:
   ```bash
   docrag config
   # Verify directories exist and contain files
   ```

2. **Verify file extensions**:
   ```yaml
   # In .docrag/config.yaml
   indexing:
     extensions:
       - ".md"
       - ".txt"
       # Add extensions for your files
   ```

3. **Check exclusion patterns**:
   ```yaml
   # Make sure patterns aren't too broad
   indexing:
     exclude_patterns:
       - "node_modules/"  # Specific
       - "*/"             # Too broad
   ```

4. **List files manually**:
   ```bash
   find docs/ -name "*.md"
   # Should show your documentation files
   ```

### Encoding errors

**Problem**: Files fail to load due to encoding issues

**Symptoms**:
```
Warning: Failed to read file: docs/legacy.txt
   UnicodeDecodeError: 'utf-8' codec can't decode byte
```

**Solutions**:

1. **Convert to UTF-8**:
   ```bash
   iconv -f ISO-8859-1 -t UTF-8 legacy.txt > legacy_utf8.txt
   ```

2. **Check file encoding**:
   ```bash
   file -I filename.txt
   # Shows: text/plain; charset=utf-8
   ```

3. **Exclude problematic files**:
   ```yaml
   # In .docrag/config.yaml
   indexing:
     exclude_patterns:
       - "legacy/"
       - "*.old"
   ```

4. **Let DocRAG handle it**:
   - DocRAG Kit automatically detects encoding
   - Failed files are logged but don't stop indexing

### Disk space errors

**Problem**: Not enough disk space for vector database

**Symptoms**:
```
Error: No space left on device
   Failed to create vector database
```

**Solutions**:

1. **Check available space**:
   ```bash
   df -h .
   # Need at least 100MB free
   ```

2. **Clean old databases**:
   ```bash
   rm -rf .docrag/vectordb/
   docrag index
   ```

3. **Reduce chunk size**:
   ```yaml
   # Smaller chunks = smaller database
   chunking:
     chunk_size: 500
   ```

4. **Index fewer files**:
   ```yaml
   indexing:
     directories:
       - "docs/"  # Only essential docs
   ```

### Memory errors

**Problem**: Out of memory during indexing

**Symptoms**:
```
MemoryError: Unable to allocate array
```

**Solutions**:

1. **Index in batches**:
   ```yaml
   # Index one directory at a time
   indexing:
     directories:
       - "docs/"
   # Then add more directories later
   ```

2. **Reduce chunk size**:
   ```yaml
   chunking:
     chunk_size: 800
   ```

3. **Close other applications**:
   - Free up RAM before indexing

4. **Increase swap space** (Linux):
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

## MCP Connection Issues

### Server not found

**Problem**: MCP server doesn't appear in Kiro

**Symptoms**:
- Server not listed in MCP Servers panel
- Tools not available in chat

**Solutions**:

1. **Verify mcp.json syntax**:
   ```bash
   # Check for JSON errors
   python -m json.tool ~/.kiro/settings/mcp.json
   ```

2. **Check file paths**:
   ```bash
   # Verify mcp_server.py exists
   ls -la /path/to/project/.docrag/mcp_server.py
   ```

3. **Use absolute paths**:
   ```json
   {
     "mcpServers": {
       "my-docs": {
         "command": "python",
         "args": [
           "/Users/username/project/.docrag/mcp_server.py"  // Absolute
         ]
       }
     }
   }
   ```

4. **Reload servers**:
   - In Kiro: Cmd+Shift+P → "MCP: Reload Servers"
   - Or restart Kiro

### Connection refused

**Problem**: MCP server fails to connect

**Symptoms**:
```
Error: Connection refused
MCP server failed to start
```

**Solutions**:

1. **Test server manually**:
   ```bash
   cd /path/to/project
   python .docrag/mcp_server.py
   # Should start without errors
   ```

2. **Check Python path**:
   ```bash
   which python
   # Use this path in mcp.json
   ```

3. **Verify dependencies**:
   ```bash
   pip show mcp langchain chromadb
   ```

4. **Check PYTHONPATH**:
   ```json
   {
     "mcpServers": {
       "my-docs": {
         "env": {
           "PYTHONPATH": "/path/to/project"  // Must be project root
         }
       }
     }
   }
   ```

### Database not found

**Problem**: MCP server can't find vector database

**Symptoms**:
```
Error: Vector database not found
   Please run 'docrag index' first
```

**Solutions**:

1. **Index documentation**:
   ```bash
   cd /path/to/project
   docrag index
   ```

2. **Verify database exists**:
   ```bash
   ls -la .docrag/vectordb/
   # Should show chroma.sqlite3 and other files
   ```

3. **Check working directory**:
   ```json
   {
     "mcpServers": {
       "my-docs": {
         "env": {
           "PYTHONPATH": "/path/to/project"  // Project root
         }
       }
     }
   }
   ```

4. **Reindex if needed**:
   ```bash
   docrag reindex
   ```

### Slow responses

**Problem**: MCP queries take too long

**Symptoms**:
- Queries timeout
- Kiro shows "thinking" for extended time

**Solutions**:

1. **Reduce top_k**:
   ```yaml
   # In .docrag/config.yaml
   retrieval:
     top_k: 3  # Fewer results = faster
   ```

2. **Use faster model**:
   ```yaml
   llm:
     llm_model: "gpt-3.5-turbo"  # Faster than gpt-4
   ```

3. **Check internet connection**:
   ```bash
   ping api.openai.com
   ```

4. **Monitor API status**:
   - OpenAI: https://status.openai.com/
   - Gemini: https://status.cloud.google.com/

5. **Optimize chunk size**:
   ```yaml
   chunking:
     chunk_size: 800  # Smaller = faster retrieval
   ```

## Performance Optimization

### Improve answer quality

**Problem**: Answers are not accurate or relevant

**Solutions**:

1. **Increase top_k**:
   ```yaml
   retrieval:
     top_k: 7  # More context
   ```

2. **Adjust chunk size**:
   ```yaml
   chunking:
     chunk_size: 1500  # Larger chunks for more context
     chunk_overlap: 300  # More overlap for continuity
   ```

3. **Reindex after doc changes**:
   ```bash
   docrag reindex
   ```

4. **Use better model**:
   ```yaml
   llm:
     llm_model: "gpt-4"  # Higher quality
   ```

5. **Improve documentation**:
   - Add more detail to docs
   - Use clear headings
   - Include examples

### Reduce costs

**Problem**: API costs are too high

**Solutions**:

1. **Use cheaper models**:
   ```yaml
   llm:
     provider: "gemini"  # Generally cheaper
     llm_model: "gemini-1.5-flash"
   ```

2. **Reduce top_k**:
   ```yaml
   retrieval:
     top_k: 3  # Fewer tokens per query
   ```

3. **Optimize chunk size**:
   ```yaml
   chunking:
     chunk_size: 1000  # Balance quality and cost
   ```

4. **Index selectively**:
   ```yaml
   indexing:
     directories:
       - "docs/"  # Only essential docs
   ```

5. **Monitor usage**:
   - Check provider dashboard regularly
   - Set up billing alerts

### Speed up indexing

**Problem**: Indexing takes too long

**Solutions**:

1. **Exclude unnecessary files**:
   ```yaml
   indexing:
     exclude_patterns:
       - "vendor/"
       - "node_modules/"
       - "*.log"
       - "*.tmp"
   ```

2. **Index fewer directories**:
   ```yaml
   indexing:
     directories:
       - "docs/"  # Start with just docs
   ```

3. **Use larger chunks**:
   ```yaml
   chunking:
     chunk_size: 2000  # Fewer chunks = faster
   ```

4. **Check internet speed**:
   - Slow connection affects API calls
   - Consider indexing on faster network

## Common Error Messages

### "Configuration file not found"

**Error**:
```
Error: Configuration file not found: .docrag/config.yaml
   Run 'docrag init' to create configuration
```

**Solution**:
```bash
docrag init
```

### "Chunk size must be between 100 and 5000"

**Error**:
```
Warning: Chunk size 50 is too small
   Recommended range: 100-5000
```

**Solution**:
```yaml
# Edit .docrag/config.yaml
chunking:
  chunk_size: 1000  # Within valid range
```

### "Provider must be 'openai' or 'gemini'"

**Error**:
```
Error: Invalid provider: anthropic
   Supported providers: openai, gemini
```

**Solution**:
```yaml
# Edit .docrag/config.yaml
llm:
  provider: "openai"  # or "gemini"
```

### "Top K must be at least 1"

**Error**:
```
Error: top_k must be >= 1
   Current value: 0
```

**Solution**:
```yaml
# Edit .docrag/config.yaml
retrieval:
  top_k: 5
```

### "Failed to create embeddings"

**Error**:
```
Error: Failed to create embeddings
   OpenAI API error: Incorrect API key provided
```

**Solution**:
1. Check API key in `.env`
2. Verify key is valid
3. Check API quota/billing

### "ChromaDB error"

**Error**:
```
Error: ChromaDB initialization failed
   sqlite3.OperationalError: database is locked
```

**Solution**:
1. Close other processes using database
2. Delete and recreate:
   ```bash
   rm -rf .docrag/vectordb/
   docrag index
   ```

## Getting Help

If your issue isn't covered here:

### 1. Check Documentation
- [README.md](README.md) - Main documentation
- [EXAMPLES.md](EXAMPLES.md) - Usage examples
- [MCP_INTEGRATION.md](MCP_INTEGRATION.md) - MCP setup

### 2. Search Issues
- [GitHub Issues](https://github.com/yourusername/docrag-kit/issues)
- Search for similar problems

### 3. Enable Debug Mode
```bash
# Set debug environment variable
export DEBUG=true
docrag index
```

### 4. Collect Information
Before reporting an issue, gather:
- DocRAG Kit version: `docrag --version`
- Python version: `python --version`
- Operating system: `uname -a` (Linux/Mac) or `ver` (Windows)
- Error messages (full output)
- Configuration file (`.docrag/config.yaml`)
- Steps to reproduce

### 5. Open an Issue
Create a new issue with:
- Clear title describing the problem
- All information from step 4
- What you've tried already
- Expected vs actual behavior

## Preventive Measures

### Regular Maintenance

1. **Update DocRAG Kit**:
   ```bash
   pip install --upgrade docrag-kit
   ```

2. **Reindex periodically**:
   ```bash
   # After major doc changes
   docrag reindex
   ```

3. **Monitor API usage**:
   - Check provider dashboard weekly
   - Set up billing alerts

4. **Backup configuration**:
   ```bash
   cp .docrag/config.yaml .docrag/config.yaml.backup
   ```

5. **Keep .env secure**:
   ```bash
   # Verify it's gitignored
   git check-ignore .env
   # Should output: .env
   ```

### Best Practices

1. Use version control for config.yaml
2. Keep .env gitignored
3. Document your setup in README
4. Test after configuration changes
5. Monitor costs and usage
6. Update documentation regularly
7. Reindex after major changes
8. Use descriptive server names
9. Keep dependencies updated
10. Backup important configurations
