# DocRAG Kit Upgrade Guide

This guide helps you update existing DocRAG Kit installations to get new features and improvements.

## Quick Update (Recommended)

For existing projects with DocRAG Kit already configured:

```bash
# 1. Update the package
pip install --upgrade docrag-kit

# 2. Update project configuration
docrag update

# 3. Restart Kiro IDE or reload MCP servers
```

## Manual Update Steps

If the quick update doesn't work, follow these manual steps:

### 1. Update Package

```bash
pip install --upgrade docrag-kit
```

### 2. Update MCP Configuration

```bash
# Update MCP server configuration with new tools
docrag mcp-config --update --non-interactive
```

### 3. Restart MCP Server

In Kiro IDE:
- Open Command Palette (Cmd/Ctrl + Shift + P)
- Search for "MCP: Reload Servers"
- Or restart Kiro IDE completely

### 4. Test New Features

Try the new `reindex_docs` tool:

```python
# Check if reindexing is needed
reindex_docs(check_only=True)

# Perform smart reindexing if changes detected
reindex_docs()

# Force full reindexing
reindex_docs(force=True)
```

## New Features in Latest Version

### Smart Reindexing (`reindex_docs` tool)

- **Automatic change detection** - Only reindexes when files have been modified
- **Check mode** - See what would be reindexed without doing it
- **Force mode** - Full reindexing regardless of changes
- **Performance optimized** - Fast checks for large documentation sets

### Enhanced Search Tools

- **Staleness warnings** - Automatic notifications when indexed content might be outdated
- **Better performance** - Optimized for agent workflows
- **Improved error handling** - Clearer messages for troubleshooting

## Troubleshooting Updates

### MCP Server Not Updating

If you don't see new tools after update:

1. **Check package version**:
   ```bash
   pip show docrag-kit
   ```

2. **Verify MCP configuration**:
   ```bash
   docrag mcp-config --update
   ```

3. **Restart Kiro completely** (not just reload MCP)

4. **Check MCP server logs** in Kiro's MCP panel

### Configuration Issues

If configuration seems corrupted:

1. **Backup current config**:
   ```bash
   cp .docrag/config.yaml .docrag/config.yaml.backup
   ```

2. **Run doctor command**:
   ```bash
   docrag doctor
   ```

3. **Reinitialize if needed** (preserves vector database):
   ```bash
   # Only if config is completely broken
   rm .docrag/config.yaml
   docrag init --non-interactive
   ```

### Database Issues

If vector database seems corrupted after update:

```bash
# Rebuild database from scratch
docrag reindex
```

## Version Compatibility

- **DocRAG Kit 1.x** - All versions are backward compatible
- **Kiro IDE** - Requires MCP support (most recent versions)
- **Python** - Requires 3.10+ (unchanged)

## Migration Notes

### From Pre-1.0 Versions

If upgrading from very early versions:

1. **Backup your project**:
   ```bash
   cp -r .docrag .docrag.backup
   ```

2. **Run full update**:
   ```bash
   docrag update
   ```

3. **Verify configuration**:
   ```bash
   docrag doctor
   ```

### Configuration Changes

Recent versions may have updated configuration schemas. The `docrag update` command handles this automatically, but you can also:

1. **Check current config**:
   ```bash
   docrag config
   ```

2. **Fix any issues**:
   ```bash
   docrag fix-prompt  # If prompt template needs updating
   ```

## Getting Help

If you encounter issues during upgrade:

1. **Run diagnostics**:
   ```bash
   docrag doctor
   ```

2. **Check logs** in Kiro's MCP panel

3. **Report issues** at: https://github.com/docrag-kit/docrag-kit/issues

## Rollback

If you need to rollback to a previous version:

```bash
# Install specific version
pip install docrag-kit==<previous_version>

# Restore configuration if needed
cp .docrag/config.yaml.backup .docrag/config.yaml

# Update MCP config
docrag mcp-config --non-interactive
```