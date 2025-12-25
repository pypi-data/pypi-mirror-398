# API Reference

Complete reference for DocRAG Kit CLI commands, configuration options, and MCP tools.

## Table of Contents

- [CLI Commands](#cli-commands)
- [Configuration Options](#configuration-options)
- [MCP Tools](#mcp-tools)
- [Environment Variables](#environment-variables)
- [Exit Codes](#exit-codes)

## CLI Commands

### `docrag init`

Initialize DocRAG system in the current project.

**Usage**:
```bash
docrag init
```

**Description**:
Starts an interactive configuration wizard that:
1. Prompts for LLM provider (OpenAI or Gemini)
2. Requests API key
3. Configures directories to index
4. Sets file extensions to include
5. Defines exclusion patterns
6. Selects project type template
7. Optionally adds GitHub token
8. Creates `.docrag/` directory structure
9. Generates configuration files
10. Creates/updates `.env` file

**Creates**:
- `.docrag/` directory
- `.docrag/config.yaml` - Configuration file
- `.docrag/mcp_server.py` - MCP server script
- `.docrag/.gitignore` - Git exclusions
- `.env` - API keys (if doesn't exist)
- `.env.example` - Template without keys

**Options**:
None (interactive mode only)

**Examples**:
```bash
# Initialize in current directory
cd my-project
docrag init

# Follow prompts to configure
```

**Exit Codes**:
- `0` - Success
- `1` - Already initialized (`.docrag/` exists)
- `2` - User cancelled
- `3` - Configuration error

---

### `docrag index`

Index project documents and create vector database.

**Usage**:
```bash
docrag index
```

**Description**:
Performs the following operations:
1. Loads configuration from `.docrag/config.yaml`
2. Verifies API key in `.env`
3. Scans configured directories for matching files
4. Applies exclusion patterns
5. Loads and processes documents
6. Splits documents into chunks
7. Creates embeddings using configured LLM provider
8. Stores vectors in ChromaDB database
9. Displays statistics

**Requires**:
- `.docrag/config.yaml` - Configuration file
- `.env` - API key for chosen provider

**Creates/Updates**:
- `.docrag/vectordb/` - Vector database directory
- `.docrag/vectordb/chroma.sqlite3` - ChromaDB database

**Options**:
None

**Examples**:
```bash
# Index documentation
cd my-project
docrag index

# Output:
# Indexing documents...
# ✓ Found 45 files to index
# ✓ Processing documents...
# ✓ Creating embeddings...
# ✓ Storing in vector database...
# 
# Statistics:
# - Files processed: 45
# - Chunks created: 234
# - Total characters: 89,432
# 
# Indexing complete!
```

**Exit Codes**:
- `0` - Success
- `1` - Configuration not found
- `2` - API key missing
- `3` - No files found
- `4` - Indexing failed

---

### `docrag reindex`

Rebuild vector database from scratch.

**Usage**:
```bash
docrag reindex
```

**Description**:
Performs the same operations as `docrag index`, but:
1. Displays warning about overwriting existing database
2. Prompts for confirmation
3. Deletes old database if confirmed
4. Creates new database from scratch
5. Displays updated statistics

**Requires**:
- `.docrag/config.yaml` - Configuration file
- `.env` - API key for chosen provider

**Options**:
None

**Examples**:
```bash
# Reindex after documentation changes
docrag reindex

# Output:
# Warning: This will delete the existing vector database
# ? Continue? [y/N] y
# 
# Deleting old database...
# Indexing documents...
# ...
```

**Exit Codes**:
- `0` - Success
- `1` - Configuration not found
- `2` - User cancelled
- `3` - Reindexing failed

---

### `docrag config`

Display current configuration.

**Usage**:
```bash
docrag config [--edit]
```

**Description**:
Displays the current configuration from `.docrag/config.yaml` in a formatted, readable way.

**Options**:
- `--edit` - Open configuration file in default editor

**Examples**:
```bash
# Display configuration
docrag config

# Output:
# 📋 Current Configuration
# 
# Project:
#   Name: my-project
#   Type: symfony
# 
# LLM:
#   Provider: openai
#   Embedding Model: text-embedding-3-small
#   LLM Model: gpt-4o-mini
#   Temperature: 0.3
# ...

# Edit configuration
docrag config --edit
# Opens .docrag/config.yaml in default editor
```

**Exit Codes**:
- `0` - Success
- `1` - Configuration not found
- `2` - Editor failed to open

---

### `docrag mcp-config`

Display MCP server configuration for Kiro integration.

**Usage**:
```bash
docrag mcp-config
```

**Description**:
Generates and displays the MCP server configuration that should be added to Kiro's `mcp.json` file. On macOS, offers to automatically add the configuration.

**Displays**:
1. JSON configuration snippet
2. Path to `mcp.json` file
3. Instructions for manual addition
4. (macOS only) Option for automatic addition

**Examples**:
```bash
# Get MCP configuration
docrag mcp-config

# Output:
# MCP Server Configuration for Kiro
# 
# Add the following to your Kiro MCP configuration file:
# ~/.kiro/settings/mcp.json
# 
# {
#   "mcpServers": {
#     "my-project-docs": {
#       "command": "python",
#       "args": [
#         "/absolute/path/to/my-project/.docrag/mcp_server.py"
#       ],
#       "env": {
#         "PYTHONPATH": "/absolute/path/to/my-project"
#       }
#     }
#   }
# }
# 
# ? Kiro installation detected. Add MCP server automatically? [y/N]
```

**Exit Codes**:
- `0` - Success
- `1` - Configuration not found
- `2` - Automatic addition failed

---

### `docrag --version`

Display version information.

**Usage**:
```bash
docrag --version
```

**Description**:
Displays the installed version of DocRAG Kit.

**Examples**:
```bash
docrag --version
# Output: docrag-kit version 0.1.0
```

**Exit Codes**:
- `0` - Success

---

### `docrag --help`

Display help information.

**Usage**:
```bash
docrag --help
docrag <command> --help
```

**Description**:
Displays help information for DocRAG Kit or a specific command.

**Examples**:
```bash
# General help
docrag --help

# Command-specific help
docrag init --help
docrag index --help
```

**Exit Codes**:
- `0` - Success

---

## Configuration Options

Configuration is stored in `.docrag/config.yaml` using YAML format.

### Project Configuration

```yaml
project:
  name: string          # Project name (required)
  type: string          # Project type (required)
```

**Fields**:

- **`name`** (string, required)
  - Project name for identification
  - Used in MCP server name
  - Example: `"my-symfony-app"`

- **`type`** (string, required)
  - Project type for prompt template selection
  - Valid values: `"symfony"`, `"ios"`, `"general"`, `"custom"`
  - Default: `"general"`

---

### LLM Configuration

```yaml
llm:
  provider: string           # LLM provider (required)
  embedding_model: string    # Embedding model name (required)
  llm_model: string          # LLM model name (required)
  temperature: float         # Temperature for generation (optional)
```

**Fields**:

- **`provider`** (string, required)
  - LLM provider to use
  - Valid values: `"openai"`, `"gemini"`
  - Example: `"openai"`

- **`embedding_model`** (string, required)
  - Model for creating embeddings
  - OpenAI default: `"text-embedding-3-small"`
  - Gemini default: `"models/embedding-001"`

- **`llm_model`** (string, required)
  - Model for answer generation
  - OpenAI default: `"gpt-4o-mini"`
  - Gemini default: `"gemini-1.5-flash"`

- **`temperature`** (float, optional)
  - Controls randomness in generation
  - Range: 0.0 to 1.0
  - Default: `0.3`
  - Lower = more focused, Higher = more creative

---

### Indexing Configuration

```yaml
indexing:
  directories: list[string]      # Directories to scan (required)
  extensions: list[string]       # File extensions to include (required)
  exclude_patterns: list[string] # Patterns to exclude (optional)
```

**Fields**:

- **`directories`** (list of strings, required)
  - Directories to scan for documents
  - Can be relative or absolute paths
  - Example: `["docs/", "src/", "README.md"]`

- **`extensions`** (list of strings, required)
  - File extensions to include
  - Must start with dot
  - Example: `[".md", ".txt", ".py", ".php"]`

- **`exclude_patterns`** (list of strings, optional)
  - Glob patterns for files/directories to exclude
  - Example: `["node_modules/", ".git/", "*.log"]`

---

### Chunking Configuration

```yaml
chunking:
  chunk_size: int      # Maximum chunk size in characters (required)
  chunk_overlap: int   # Overlap between chunks in characters (required)
```

**Fields**:

- **`chunk_size`** (integer, required)
  - Maximum size of each chunk in characters
  - Range: 100 to 5000 (recommended)
  - Default: `1000`
  - Larger = more context, fewer chunks
  - Smaller = more precise, more chunks

- **`chunk_overlap`** (integer, required)
  - Number of characters to overlap between consecutive chunks
  - Range: 0 to chunk_size/2 (recommended)
  - Default: `200`
  - Higher = better context continuity
  - Lower = less redundancy

---

### Retrieval Configuration

```yaml
retrieval:
  top_k: int          # Number of chunks to retrieve (required)
```

**Fields**:

- **`top_k`** (integer, required)
  - Number of most relevant chunks to retrieve for each query
  - Range: 1 to 20 (recommended)
  - Default: `5`
  - Higher = more context, slower, more expensive
  - Lower = faster, cheaper, less context

---

### Prompt Configuration

```yaml
prompt:
  template: string    # Custom prompt template (optional)
```

**Fields**:

- **`template`** (string, optional)
  - Custom prompt template for answer generation
  - Only used when `project.type` is `"custom"`
  - Must include `{context}` and `{question}` placeholders
  - Example:
    ```yaml
    prompt:
      template: |
        You are an expert assistant.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:
    ```

---

### Complete Configuration Example

```yaml
project:
  name: "my-symfony-app"
  type: "symfony"

llm:
  provider: "openai"
  embedding_model: "text-embedding-3-small"
  llm_model: "gpt-4o-mini"
  temperature: 0.3

indexing:
  directories:
    - "docs/"
    - "src/"
    - "config/"
  extensions:
    - ".md"
    - ".txt"
    - ".php"
    - ".yaml"
  exclude_patterns:
    - "vendor/"
    - "var/"
    - "node_modules/"
    - ".git/"

chunking:
  chunk_size: 1000
  chunk_overlap: 200

retrieval:
  top_k: 5
```

---

## MCP Tools

DocRAG Kit provides two MCP tools for integration with Kiro AI.

### `search_docs`

Search project documentation using semantic search.

**Description**:
Performs semantic search over indexed documentation and generates an answer using the configured LLM.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "question": {
      "type": "string",
      "description": "Question to search for in the documentation"
    },
    "include_sources": {
      "type": "boolean",
      "description": "Whether to include source file names in the response",
      "default": false
    }
  },
  "required": ["question"]
}
```

**Parameters**:

- **`question`** (string, required)
  - The question to search for
  - Can be in Russian or English
  - Natural language format
  - Example: `"How do I configure the database?"`

- **`include_sources`** (boolean, optional)
  - Whether to append source file names to the response
  - Default: `false`
  - When `true`, adds "Sources: file1.md, file2.py" to response

**Returns**:
- String containing the generated answer
- Optionally includes source file names if `include_sources` is `true`

**Examples**:

```json
// Simple query
{
  "question": "What is the project architecture?"
}

// Query with sources
{
  "question": "How do I deploy to production?",
  "include_sources": true
}
```

**Response Examples**:

```
Without sources:
"The project uses a layered architecture with Controllers, Services, and Repositories..."

With sources:
"The project uses a layered architecture with Controllers, Services, and Repositories...

Sources: docs/architecture.md, README.md"
```

**Error Responses**:
- `"Error: Vector database not found. Please run 'docrag index' first."`
- `"Error: API key not found. Please add your API key to .env file."`
- `"Error: Failed to generate answer: [error details]"`

---

### `list_indexed_docs`

List all indexed documents in the project.

**Description**:
Returns a list of all unique source files that have been indexed in the vector database.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Parameters**:
None

**Returns**:
- String containing a formatted list of indexed files
- Files are sorted alphabetically
- One file per line

**Examples**:

```json
// No parameters needed
{}
```

**Response Example**:

```
Indexed documents (45 files):

- README.md
- docs/architecture.md
- docs/configuration.md
- docs/deployment.md
- src/config.py
- src/main.py
...
```

**Error Responses**:
- `"Error: Vector database not found. Please run 'docrag index' first."`
- `"Error: No documents indexed yet."`

---

## Environment Variables

Environment variables are stored in `.env` file in the project root.

### Required Variables

**`OPENAI_API_KEY`** (required if using OpenAI)
- OpenAI API key for embeddings and LLM
- Format: `sk-...` (starts with `sk-`)
- Get from: https://platform.openai.com/api-keys
- Example: `OPENAI_API_KEY=sk-abc123def456...`

**`GOOGLE_API_KEY`** (required if using Gemini)
- Google Gemini API key for embeddings and LLM
- Format: Alphanumeric string
- Get from: https://makersuite.google.com/app/apikey
- Example: `GOOGLE_API_KEY=AIzaSyD...`

### Optional Variables

**`GITHUB_TOKEN`** (optional)
- GitHub Personal Access Token for future integrations
- Format: `ghp_...` (starts with `ghp_`)
- Get from: https://github.com/settings/tokens
- Example: `GITHUB_TOKEN=ghp_abc123...`

### Example `.env` File

```bash
# OpenAI API Key
OPENAI_API_KEY=sk-proj-abc123def456...

# Google Gemini API Key (alternative to OpenAI)
# GOOGLE_API_KEY=AIzaSyD...

# GitHub Token (optional)
# GITHUB_TOKEN=ghp_abc123...
```

### Security Notes

- Never commit `.env` to version control
- Always keep `.env` in `.gitignore`
- Use `.env.example` as a template for team members
- Rotate API keys regularly
- Monitor API usage to detect unauthorized access

---

## Exit Codes

All DocRAG Kit commands use standard exit codes:

| Code | Meaning | Description |
|------|---------|-------------|
| `0` | Success | Command completed successfully |
| `1` | General Error | Command failed with an error |
| `2` | User Cancelled | User cancelled the operation |
| `3` | Configuration Error | Invalid or missing configuration |
| `4` | API Error | API key or provider error |
| `5` | File System Error | File or directory error |

**Usage in Scripts**:

```bash
#!/bin/bash

# Check if indexing succeeded
docrag index
if [ $? -eq 0 ]; then
    echo "Indexing successful"
else
    echo "Indexing failed"
    exit 1
fi
```

---

## Python API (Advanced)

For advanced users, DocRAG Kit components can be imported and used programmatically.

### ConfigManager

```python
from docrag.config_manager import ConfigManager
from pathlib import Path

# Load configuration
config_manager = ConfigManager(Path.cwd())
config = config_manager.load_config()

# Access configuration
print(config.project.name)
print(config.llm.provider)
```

### DocumentProcessor

```python
from docrag.document_processor import DocumentProcessor

# Initialize processor
processor = DocumentProcessor(config)

# Scan files
files = processor.scan_files()

# Load and chunk documents
documents = processor.load_documents(files)
chunks = processor.chunk_documents(documents)
```

### VectorDBManager

```python
from docrag.vector_db import VectorDBManager

# Initialize database manager
db_manager = VectorDBManager(config)

# Create database
db_manager.create_database(chunks)

# Get retriever
retriever = db_manager.get_retriever(top_k=5)

# List documents
docs = db_manager.list_documents()
```

**Note**: The Python API is not officially supported and may change between versions. Use at your own risk.

---

## Version History

### 0.1.0 (Initial Release)
- Initial release with core functionality
- CLI commands: init, index, reindex, config, mcp-config
- Support for OpenAI and Gemini providers
- MCP integration for Kiro AI
- Interactive setup wizard
- Project templates (Symfony, iOS, General)

---

## See Also

- [README.md](README.md) - Main documentation
- [EXAMPLES.md](EXAMPLES.md) - Usage examples
- [MCP_INTEGRATION.md](MCP_INTEGRATION.md) - MCP setup guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Troubleshooting guide
