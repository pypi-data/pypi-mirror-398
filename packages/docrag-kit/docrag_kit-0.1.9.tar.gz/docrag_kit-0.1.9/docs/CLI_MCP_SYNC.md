# CLI vs MCP Synchronization Issues

This guide addresses the critical issue where CLI and MCP interfaces show different data.

## Problem Description

**Symptoms:**
- CLI shows many documents (e.g., 27 files, 300 chunks)
- MCP shows only few documents (e.g., 1 file - README.md)
- MCP cannot reindex due to "readonly database" error
- Search through MCP is limited to subset of documents

**Root Cause:**
MCP server runs from different working directory than the project, causing it to access wrong database.

## Quick Diagnosis

```bash
# Check if you have this problem
docrag debug-mcp
```

This command will show:
- Current project directory
- CLI database status (number of documents)
- MCP configuration and working directory
- Path mismatch detection

## Quick Fix

```bash
# 1. Reconfigure MCP with correct paths
docrag mcp-config --update --non-interactive

# 2. Restart Kiro IDE completely
# (not just reload MCP servers)

# 3. Verify fix
docrag debug-mcp
```

## Manual Fix

If automatic fix doesn't work:

### 1. Check MCP Configuration

**Workspace config:** `.kiro/settings/mcp.json`
**User config:** `~/.kiro/settings/mcp.json`

### 2. Verify Working Directory

The MCP configuration should have:
```json
{
  "mcpServers": {
    "docrag": {
      "command": "python",
      "args": ["-m", "docrag.mcp_server"],
      "cwd": "/path/to/your/project",  // <- This must match your project
      "env": {},
      "disabled": false
    }
  }
}
```

### 3. Update Configuration

```bash
# Generate correct configuration
docrag mcp-config --non-interactive

# Copy the "cwd" path and update your MCP config manually
```

## Detailed Diagnosis

### Check CLI Status
```bash
# From your project directory
docrag doctor
docrag config
ls -la .docrag/vectordb/
```

### Check MCP Status
```bash
# Debug MCP paths and database access
docrag debug-mcp

# Test MCP server manually
python -m docrag.mcp_server
```

### Compare Results
- CLI should show all your project documents
- MCP should show the same documents after fix
- Both should access same `.docrag/vectordb/` directory

## Common Scenarios

### Scenario 1: Global MCP Configuration
**Problem:** MCP configured globally, points to wrong project
**Solution:** Use workspace-specific configuration

```bash
# Create workspace config
docrag mcp-config --non-interactive
# This creates .kiro/settings/mcp.json in current project
```

### Scenario 2: Wrong Working Directory
**Problem:** MCP `cwd` points to different directory
**Solution:** Update working directory in MCP config

```json
{
  "mcpServers": {
    "docrag": {
      "cwd": "/correct/path/to/your/project"
    }
  }
}
```

### Scenario 3: Multiple DocRAG Projects
**Problem:** MCP points to different DocRAG project
**Solution:** Each project needs its own MCP configuration

```bash
# In each project directory
cd /path/to/project1
docrag mcp-config --non-interactive

cd /path/to/project2  
docrag mcp-config --non-interactive
```

## Prevention

### Best Practices
1. **Always run `docrag mcp-config` from project directory**
2. **Use workspace-specific MCP configuration**
3. **Verify paths after configuration**
4. **Test with `docrag debug-mcp` after setup**

### Project Setup Checklist
```bash
# 1. Initialize in project directory
cd /path/to/your/project
docrag init

# 2. Index documents
docrag index

# 3. Configure MCP from same directory
docrag mcp-config --non-interactive

# 4. Verify synchronization
docrag debug-mcp

# 5. Restart Kiro IDE
```

## Troubleshooting

### Still Not Working?

1. **Complete restart of Kiro IDE** (not just MCP reload)
2. **Check file permissions** on `.docrag/vectordb/`
3. **Verify API keys** in `.env` file
4. **Clear MCP cache** by restarting Kiro

### Multiple Issues?

```bash
# Comprehensive fix
docrag fix-database
docrag mcp-config --update --non-interactive
# Restart Kiro IDE
docrag debug-mcp
```

### Nuclear Option

If nothing works, reset everything:

```bash
# Backup configuration
cp .docrag/config.yaml config.backup

# Remove MCP configs
rm -f .kiro/settings/mcp.json
rm -f ~/.kiro/settings/mcp.json

# Reconfigure from scratch
docrag mcp-config --non-interactive

# Restart Kiro IDE
# Test with: docrag debug-mcp
```

## Verification

After fixing, you should see:
- **Same document count** in CLI and MCP
- **Same search results** from both interfaces
- **Successful reindexing** through MCP tools
- **No "readonly database" errors**

Use `docrag debug-mcp` to verify all paths are correct.