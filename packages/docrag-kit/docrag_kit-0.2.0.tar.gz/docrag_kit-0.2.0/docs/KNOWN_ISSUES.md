# Known Issues

## MCP Reindexing Database Lock Issue - RESOLVED ✅

### Status Update

**Status**: ✅ **RESOLVED** in v0.2.0  
**Solution**: Isolated subprocess reindexing architecture  
**Date Resolved**: December 22, 2024

The MCP reindexing database lock issue has been **RESOLVED** through an architectural solution implemented in v0.2.0. The new isolated subprocess reindexing eliminates ChromaDB/SQLite WAL locking conflicts in MCP context.

### What's Fixed

**✅ Now Working (MCP v0.2.0+)**
- `mcp_docrag_reindex_docs(force: false)` - Smart reindexing ✅
- `mcp_docrag_reindex_docs(force: true)` - Forced reindexing ✅
- `mcp_docrag_reindex_docs(check_only: true)` - Change detection ✅
- All existing functions continue to work perfectly ✅

### Architecture Solution

The v0.2.0 release implements a **multi-strategy reindexing approach**:

1. **Strategy 1**: Isolated subprocess reindexing (most reliable)
   - Runs `docrag.mcp_reindex_worker` in separate process
   - Eliminates file locking conflicts through process isolation
   - Returns structured JSON results

2. **Strategy 2**: Enhanced in-process reindexing with aggressive cleanup
   - Improved connection management and database cleanup
   - Better retry mechanisms and error handling

3. **Strategy 3**: Graceful fallback with clear user guidance
   - Provides CLI workaround if both strategies fail
   - Clear error messages and next steps

### Testing the Fix

```bash
# Test the new architecture
docrag test-isolated-reindex

# Test MCP reindexing functionality
docrag test-mcp-reindex

# Use the new MCP tool
# In Kiro AI:
mcp_docrag_reindex_docs({"check_only": true})   # Check for changes
mcp_docrag_reindex_docs({"force": false})       # Smart reindexing
mcp_docrag_reindex_docs({"force": true})        # Force reindexing
```

### Migration Guide

**For existing users:**

1. **Update to v0.2.0**:
   ```bash
   pip install --upgrade docrag-kit
   ```

2. **Update MCP configuration**:
   ```bash
   docrag update
   ```

3. **Restart Kiro IDE** to reload MCP servers

4. **Test the fix**:
   ```bash
   docrag test-isolated-reindex
   ```

### Previous Issue (Historical)

*This section is kept for historical reference.*

### Error Message
```
ERROR: Error: Reindexing failed: Reindexing operation failed: 
ERROR: Failed to create vector database: Database error: 
error returned from database: (code: 14) unable to open database file
```

### What Works vs What Doesn't

**✅ Working Functions (MCP)**
- `mcp_docrag_search_docs` - Fast semantic search
- `mcp_docrag_answer_question` - AI-generated answers  
- `mcp_docrag_list_indexed_docs` - List indexed files
- `mcp_docrag_reindex_docs(check_only: true)` - Change detection

**✅ Working Functions (CLI)**
- `docrag index` - Initial indexing
- `docrag reindex` - Full reindexing
- `docrag fix-database` - Database repair
- All other CLI commands

**❌ Not Working (MCP Only)**
- `mcp_docrag_reindex_docs(force: false)` - Smart reindexing
- `mcp_docrag_reindex_docs(force: true)` - Forced reindexing

### Root Cause Analysis

1. **ChromaDB uses SQLite with WAL mode** for performance
2. **WAL creates additional lock files** (`*-wal`, `*-shm`) 
3. **MCP server runs in isolated process** context
4. **SQLite file locking conflicts** between processes
5. **Read operations work** (no exclusive locks needed)
6. **Write operations fail** (exclusive locks required)

### Current Workaround

Use a **hybrid approach** for full functionality:

```python
# ✅ For all search and answer operations (use MCP)
result = mcp_docrag_answer_question({
    "question": "How do I configure the database?",
    "include_sources": true
})

# ✅ For change detection (use MCP) 
changes = mcp_docrag_reindex_docs({"check_only": true})

# ❌ For reindexing (use CLI instead)
# In terminal:
docrag reindex
```

### Diagnostic Commands

```bash
# Test MCP reindexing functionality
docrag test-mcp-reindex

# General MCP diagnostics  
docrag debug-mcp

# Fix database issues
docrag fix-database
```

### Investigation Status

We are actively investigating several solutions:

1. **Alternative Database Backends**
   - Evaluating FAISS, Pinecone, Weaviate
   - Testing in-memory databases for MCP context

2. **ChromaDB Configuration**
   - Disabling WAL mode for MCP operations
   - Custom SQLite connection parameters
   - Process-safe database access patterns

3. **Architecture Changes**
   - Separate read/write database instances
   - Database proxy for MCP operations
   - File-based communication protocols

### Timeline

- **v0.1.8**: Initial database locking fixes (partial)
- **v0.1.9**: Enhanced diagnostics and transparency
- **v0.2.0**: Planned architectural solution (targeting Q1 2025)

### Impact Assessment

**Low Impact for Most Users**:
- 95% of MCP operations work perfectly (search, answers)
- CLI provides full functionality as backup
- Automated workflows can use hybrid approach
- No data loss or corruption issues

**Affected Workflows**:
- Fully automated MCP-only reindexing
- Agent workflows requiring write operations
- Real-time documentation updates via MCP

### Reporting

If you encounter this issue:

1. **Confirm it's the known issue**: Run `docrag test-mcp-reindex`
2. **Use the workaround**: CLI reindexing + MCP search/answers
3. **Stay updated**: Watch for v0.2.0 architectural fixes

**Do not report** this as a new bug - we're aware and actively working on it.

### Related Issues

- ChromaDB SQLite locking in multi-process environments
- MCP server process isolation limitations  
- SQLite WAL mode compatibility with process boundaries

---

*Last updated: December 22, 2024*  
*Next review: January 15, 2025*