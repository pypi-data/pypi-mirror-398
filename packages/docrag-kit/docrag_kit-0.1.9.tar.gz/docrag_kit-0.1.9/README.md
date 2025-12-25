# DocRAG Kit

![Tests](https://github.com/dexiusprime-oss/docrag-kit/workflows/Tests/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Universal RAG (Retrieval-Augmented Generation) system for project documentation. Quickly add AI-powered semantic search to any project.

**Обновление:** Если у вас уже установлен DocRAG Kit, см. [UPDATE.md](UPDATE.md) для быстрого обновления.

## Features

- **Quick Setup** - Initialize RAG system in any project with one command
- **Universal** - Works with any documentation (Markdown, code, configs)
- **MCP Integration** - Seamless integration with Kiro AI via Model Context Protocol
- **Multilingual** - Supports Russian and English questions and answers
- **Project Templates** - Predefined templates for Symfony, iOS, and general projects
- **Secure** - API keys stored safely in .env files

## Installation

> **Обновление существующих проектов:** См. [UPDATE.md](UPDATE.md) для быстрого обновления

### Requirements

- Python >= 3.10 (required for MCP library)
- pip >= 21.0

### From PyPI

```bash
pip install docrag-kit
```

### From Source

```bash
git clone https://github.com/dexiusprime-oss/docrag-kit.git
cd docrag-kit
pip install -e .
```

### Troubleshooting Installation

If you encounter dependency conflicts with `onnxruntime` or `pulsar-client`:

```bash
# Use Python 3.10+
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install docrag-kit
```

For more solutions, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md#dependency-conflict-with-onnxruntime-or-pulsar-client)

## Quick Start

### 1. Initialize RAG System

Navigate to your project directory and run:

```bash
docrag init
```

This will:
- Start an interactive configuration wizard
- Ask for your LLM provider (OpenAI or Gemini)
- Request your API key
- Configure directories and file types to index
- Create `.docrag/` directory with configuration

### 2. Index Your Documentation

```bash
docrag index
```

This will:
- Scan configured directories for documentation
- Split documents into chunks
- Create embeddings using your chosen LLM provider
- Store vectors in local ChromaDB database

### 3. Connect to Kiro AI

```bash
docrag mcp-config
```

This will display the MCP server configuration to add to Kiro.

### 4. Start Searching

Once configured in Kiro, you can ask questions about your project:
- "What is the architecture of this project?"
- "How do I configure the database?"
- "What APIs are available?"

## Configuration

After initialization, your project will have:

```
your-project/
├── .docrag/
│   ├── config.yaml      # Configuration file
│   ├── mcp_server.py    # MCP server for Kiro
│   ├── vectordb/        # Vector database (gitignored)
│   └── .gitignore       # Excludes vectordb and .env
└── .env                 # API keys (gitignored)
```

### Configuration File

`.docrag/config.yaml` contains all settings:

```yaml
project:
  name: "my-project"
  type: "symfony"  # symfony, ios, general, custom

llm:
  provider: "openai"  # openai, gemini
  embedding_model: "text-embedding-3-small"
  llm_model: "gpt-4o-mini"
  temperature: 0.3

indexing:
  directories:
    - "docs/"
    - "src/"
  extensions:
    - ".md"
    - ".txt"
    - ".py"
  exclude_patterns:
    - "node_modules/"
    - ".git/"

chunking:
  chunk_size: 1000
  chunk_overlap: 200

retrieval:
  top_k: 5
```

## Commands

### `docrag init`
Initialize DocRAG in current project with interactive wizard.

### `docrag index`
Index project documents and create vector database.

### `docrag reindex`
Rebuild vector database from scratch (useful after documentation changes).

### `docrag config`
Display current configuration.

### `docrag config --edit`
Open configuration file in default editor.

### `docrag mcp-config`
Display MCP server configuration for Kiro integration.

### `docrag doctor`
Diagnose installation and configuration issues. Checks:
- DocRAG initialization
- Configuration files
- API keys
- Vector database
- Python environment
- Required packages
- MCP configuration

### `docrag fix-prompt`
Fix prompt template to include required placeholders (`{context}` and `{question}`).

Use this command if `answer_question` tool returns only sources without AI-generated answer.

### `docrag --version`
Display version information.

### `docrag update`
Update DocRAG configuration and MCP server for existing projects. Use this after upgrading the package to get new features.

### `docrag fix-database`
Fix database permission and corruption issues. Use this when encountering "readonly database" errors or other database problems.

### `docrag --help`
Display help information.

## Supported File Types

- **Markdown**: `.md`
- **Text**: `.txt`
- **Python**: `.py`
- **PHP**: `.php`
- **Swift**: `.swift`
- **JSON**: `.json`
- **YAML**: `.yaml`, `.yml`
- **Config**: `.conf`, `.config`, `.ini`

## LLM Providers

### OpenAI
- **Embeddings**: `text-embedding-3-small`
- **LLM**: `gpt-4o-mini`
- Get API key: https://platform.openai.com/api-keys

### Google Gemini
- **Embeddings**: `models/embedding-001`
- **LLM**: `gemini-1.5-flash`
- Get API key: https://makersuite.google.com/app/apikey

## Project Templates

### Symfony
Optimized for Symfony PHP framework projects with expert knowledge of:
- Symfony components and bundles
- Doctrine ORM
- Twig templates
- PHP best practices

### iOS
Optimized for iOS development projects with expert knowledge of:
- Swift programming language
- UIKit and SwiftUI
- iOS SDK and frameworks
- Xcode and development tools

### General Documentation
General-purpose template for any project type.

### Custom
Provide your own custom prompt template.

## Security

**CRITICAL WARNING**: Never commit your `.env` file to git!

Your `.env` file contains sensitive API keys that provide access to paid services. If exposed, they can be used by others, potentially costing you money or compromising your accounts.

### Automatic Security Features

DocRAG Kit automatically protects your API keys by:
- Creating `.docrag/.gitignore` to exclude sensitive files (`vectordb/`, `.env`, `*.pyc`)
- Checking if `.env` is in your root `.gitignore`
- Offering to add `.env` to `.gitignore` if missing
- Creating `.env.example` template without real keys
- Displaying security warnings after initialization

### Best Practices

1. **Always keep `.env` in `.gitignore`**
   - DocRAG Kit checks this during initialization
   - Verify with: `grep .env .gitignore`

2. **Use `.env.example` as a template**
   - Share `.env.example` with your team (no real keys)
   - Team members copy it to `.env` and add their own keys

3. **Never share API keys**
   - Don't paste them in public issues or forums
   - Don't commit them to public repositories
   - Don't share them in chat or email

4. **Rotate keys if exposed**
   - If you accidentally commit `.env`, revoke keys immediately
   - Generate new keys from provider dashboard
   - Update your `.env` file

### What to Do If You Accidentally Commit API Keys

If you accidentally commit your `.env` file or API keys to git:

1. **Revoke the exposed keys immediately:**
   - OpenAI: https://platform.openai.com/api-keys
   - Google Gemini: https://makersuite.google.com/app/apikey

2. **Generate new API keys** from the provider dashboard

3. **Update your `.env` file** with the new keys

4. **Remove keys from git history:**
   ```bash
   # Using git filter-branch (for small repos)
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Or use BFG Repo-Cleaner (recommended for large repos)
   # https://rtyley.github.io/bfg-repo-cleaner/
   bfg --delete-files .env
   ```

5. **Force push to remote** (if already pushed):
   ```bash
   git push origin --force --all
   git push origin --force --tags
   ```

6. **Notify team members** to re-clone the repository

### Pre-commit Hook (Recommended)

Add a pre-commit hook to prevent accidentally committing `.env`:

```bash
# Create .git/hooks/pre-commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
if git diff --cached --name-only | grep -q "^\.env$"; then
    echo "ERROR: Attempting to commit .env file!"
    echo "This file contains sensitive API keys."
    echo "Add .env to .gitignore and try again."
    exit 1
fi
EOF

# Make it executable
chmod +x .git/hooks/pre-commit
```

### Security Checklist

Before pushing to git, verify:
- [ ] `.env` is in `.gitignore`
- [ ] `.env` is not staged for commit (`git status`)
- [ ] `.env.example` exists (without real keys)
- [ ] `.docrag/.gitignore` excludes `vectordb/` and `.env`
- [ ] No API keys in configuration files
- [ ] Pre-commit hook is installed (optional but recommended)

## MCP Integration

DocRAG Kit provides four MCP tools for Kiro AI:

### `search_docs` - Fast Fragment Search
Returns relevant document fragments with source files. Best for quick lookups.

**Parameters:**
- `question` (string, required): Search query or topic
- `max_results` (integer, optional): Number of results (1-10, default: 3)

**Performance:** ~1 second, no LLM tokens used

**Example:**
```
Question: "database configuration"
Response: 
🔍 Found 2 relevant document(s):

--- Result 1 ---
📄 Source: docs/config.md
Database settings in .env:
DB_HOST=localhost
DB_PORT=5432
...
```

### `answer_question` - AI-Generated Answer
Returns comprehensive AI-generated answer synthesized from documentation. Best for complex questions.

**Parameters:**
- `question` (string, required): Question to answer
- `include_sources` (boolean, optional): Include source files (default: true)

**Performance:** ~3-5 seconds, uses LLM tokens

**Example:**
```
Question: "How do I configure the database?"
Response: "To configure the database, edit the .env file and set DB_HOST, DB_PORT, and DB_NAME..."

Sources:
  • docs/config.md
  • README.md
```

### `list_indexed_docs`
List all indexed documents in the project.

**Returns:** List of all source files in the vector database.

### `reindex_docs` - Smart Reindexing
Automatically detects document changes and performs intelligent reindexing. Best for keeping documentation up-to-date.

**Parameters:**
- `force` (boolean, optional): Force full reindexing even if no changes detected (default: false)
- `check_only` (boolean, optional): Only check if reindexing is needed without performing it (default: false)

**Performance:** Variable - fast check (~1s), full reindex depends on document count

**Example:**
```
# Check if reindexing is needed
reindex_docs(check_only=True)
Response: "Changes detected in 3 file(s): docs/api.md, README.md, src/config.py"

# Perform smart reindexing
reindex_docs()
Response: "Reindexing completed! Files processed: 15, Chunks created: 127"

# Force full reindexing
reindex_docs(force=True)
Response: "Force reindexing completed! Reason: Force reindexing requested"
```

**Tool Selection Guide:**
- Use `search_docs` for quick lookups (faster, free)
- Use `answer_question` for complex questions (slower, uses tokens)
- Use `reindex_docs` when documents have been updated
- Use `list_indexed_docs` to see what's currently indexed
- See [docs/AGENT_QUICK_START.md](docs/AGENT_QUICK_START.md) for detailed guide

## Documentation

### Quick Links

- **[docs/AGENT_QUICK_START.md](docs/AGENT_QUICK_START.md)** - Quick start guide for AI agents
- **[docs/SECURITY.md](docs/SECURITY.md)** - Complete security guide (read this first!)
- **[docs/EXAMPLES.md](docs/EXAMPLES.md)** - Detailed usage examples for different project types
- **[docs/MCP_INTEGRATION.md](docs/MCP_INTEGRATION.md)** - Complete guide for Kiro AI integration
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Solutions for common issues
- **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)** - Complete CLI and configuration reference

### Examples

See [docs/EXAMPLES.md](docs/EXAMPLES.md) for detailed usage examples including:
- Symfony project setup
- iOS project setup
- General documentation project
- Example questions and answers
- Configuration examples

### MCP Integration

See [docs/MCP_INTEGRATION.md](docs/MCP_INTEGRATION.md) for complete integration guide:
- Getting MCP configuration
- Manual and automatic setup
- Testing MCP server
- Troubleshooting connection issues

### Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed solutions to:
- Installation issues
- API key problems
- Indexing errors
- MCP connection issues
- Performance optimization

For database-specific issues, see [docs/DATABASE_TROUBLESHOOTING.md](docs/DATABASE_TROUBLESHOOTING.md):
- "Readonly database" errors
- Database corruption
- Permission issues
- Lock file problems

Quick fixes:

**Database Issues (Readonly Database, Corruption)**
```bash
# Automatic fix for most database problems
docrag fix-database

# Manual fix if needed
rm -rf .docrag/vectordb && docrag index
```

**Database Not Found**
```bash
docrag index
```

**API Key Errors**
```bash
# Check .env file
cat .env
# Should show: OPENAI_API_KEY=sk-... or GOOGLE_API_KEY=...
```

**MCP Connection Issues**
```bash
# Verify MCP server exists
ls .docrag/mcp_server.py

# Test manually
python .docrag/mcp_server.py
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/yourusername/docrag-kit.git
cd docrag-kit
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Run Property-Based Tests

```bash
pytest tests/property/
```

### Code Formatting

```bash
black src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Requirements

- Python >= 3.8
- OpenAI API key or Google Gemini API key
- 100MB+ disk space for vector database

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

### Documentation
- [README.md](README.md) - Main documentation
- [docs/](docs/) - Complete documentation
- [docs/SECURITY.md](docs/SECURITY.md) - Security best practices
- [docs/EXAMPLES.md](docs/EXAMPLES.md) - Usage examples
- [docs/MCP_INTEGRATION.md](docs/MCP_INTEGRATION.md) - MCP setup guide
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Troubleshooting guide
- [docs/API_REFERENCE.md](docs/API_REFERENCE.md) - Complete API reference

### Community
- Issues: [GitHub Issues](https://github.com/yourusername/docrag-kit/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/docrag-kit/discussions)

## Changelog

### 0.1.9 (2024-12-22) - Hotfix for MCP Reindexing
- **INVESTIGATION**: Added comprehensive diagnostics for persistent MCP reindexing issues
- **NEW**: Added `docrag test-mcp-reindex` command for detailed MCP reindexing diagnostics
- **IMPROVEMENT**: Enhanced database deletion with 5 different strategies and aggressive cleanup
- **IMPROVEMENT**: Better error messages acknowledging the ChromaDB/SQLite WAL locking issue
- **TRANSPARENCY**: Clear documentation that this is a known ChromaDB limitation in MCP context
- **WORKAROUND**: Documented hybrid workflow (MCP for search/answers, CLI for reindexing)
- **NOTE**: Read operations (search_docs, answer_question) work perfectly in MCP
- **NOTE**: Write operations (reindex_docs) require CLI workaround due to SQLite WAL locking

### 0.1.8 (2024-12-22)
- **NEW**: Enhanced `reindex_docs` MCP tool with improved database lock handling
- **NEW**: Added comprehensive database repair mechanisms for MCP compatibility
- **NEW**: Added `docrag fix-database` command with automatic lock file removal and permission fixes
- **NEW**: Added `docrag debug-mcp` command with detailed CLI/MCP synchronization diagnostics
- **FIX**: **CRITICAL**: Fixed MCP reindexing database lock errors that prevented automated reindexing
- **FIX**: Enhanced database deletion with retry mechanisms and connection cleanup
- **FIX**: Improved MCP server error handling with helpful user guidance
- **IMPROVEMENT**: Added automatic staleness warnings when documents may be outdated
- **IMPROVEMENT**: Enhanced database operations with MCP-safe file handling
- **IMPROVEMENT**: Added comprehensive upgrade documentation and troubleshooting guides
- This resolves the critical issue where MCP reindexing failed with "unable to open database file" errors

### 0.1.7 (2024-12-22)
- Internal development version with database improvements

### 0.1.6 (2024-12-14)
- **NEW**: Added `reindex_docs` MCP tool for smart reindexing with automatic change detection
- **NEW**: Added `docrag debug-mcp` command to diagnose CLI vs MCP synchronization issues
- **NEW**: Added `docrag fix-database` command for database permission and corruption issues
- **NEW**: Added `docrag update` command for upgrading existing projects
- **FIX**: Fixed critical CLI/MCP synchronization issue where different databases were accessed
- **IMPROVEMENT**: Enhanced MCP configuration with correct working directory paths
- **IMPROVEMENT**: Added comprehensive documentation for troubleshooting
- **IMPROVEMENT**: Added debug logging to MCP server for path diagnostics
- This resolves issues where CLI shows many documents but MCP shows only few

### 0.1.5 (2024-12-09)
- **FIX**: Added `docrag fix-prompt` command to fix prompt templates missing required placeholders
- **FIX**: Added validation for prompt template placeholders (`{context}` and `{question}`)
- **IMPROVEMENT**: Better error messages when prompt template is invalid
- This fixes the issue where `answer_question` tool returns only sources without AI-generated answer

### 0.1.4 (2024-12-09)
- **NEW**: Added `answer_question` MCP tool for AI-generated comprehensive answers
- Split `search_docs` into two distinct tools:
  - `search_docs`: Fast semantic search returning document fragments (no LLM, ~1s)
  - `answer_question`: AI-generated comprehensive answers (uses LLM, ~3-5s)
- All three MCP tools now available: `search_docs`, `answer_question`, `list_indexed_docs`
- Improved tool descriptions and parameter schemas

### 0.1.3 (2024-12-09)
- Skipped due to packaging issue

### 0.1.2 (2024-12-09)
- Skipped due to packaging issue

### 0.1.1 (2024-12-09)
- Fixed GitHub Actions permissions for automated releases
- Updated artifact actions to v4
- Improved CI/CD pipeline

### 0.1.0 (2024-12-09)
- Initial release with core functionality
- Support for OpenAI and Gemini providers
- MCP integration for Kiro AI
- Interactive setup wizard
- Project templates (Symfony, iOS, General)
- Doctor command for diagnostics
- Automatic project structure detection
