# Database Troubleshooting Guide

This guide helps resolve common database issues in DocRAG Kit, particularly the "readonly database" error.

## Quick Fix for "Readonly Database" Error

If you encounter the error `(code: 1032) attempt to write a readonly database`, try this:

```bash
# Automatic fix (recommended)
docrag fix-database

# Manual fix (if automatic doesn't work)
rm -rf .docrag/vectordb
docrag index
```

## Common Database Issues

### 1. Readonly Database Error

**Symptoms:**
- Error: `attempt to write a readonly database`
- Cannot reindex or update documents
- MCP tools fail with database errors

**Causes:**
- File permission issues
- Database created by different user
- Corrupted database files
- File system issues

**Solutions:**
```bash
# Try automatic fix first
docrag fix-database

# If that fails, manual cleanup
chmod -R 755 .docrag/
rm -rf .docrag/vectordb
docrag index
```

### 2. Database Locked Error

**Symptoms:**
- Error: `database is locked`
- Long delays when accessing database
- Multiple processes trying to access database

**Causes:**
- Another DocRAG process is running
- Crashed process left lock files
- System shutdown during database operation

**Solutions:**
```bash
# Remove lock files
docrag fix-database

# Or manually
rm -f .docrag/vectordb/*.db-wal
rm -f .docrag/vectordb/*.db-shm
```

### 3. Database Corruption

**Symptoms:**
- Inconsistent search results
- Random database errors
- Missing documents after indexing

**Causes:**
- System crash during indexing
- Disk full during operation
- Hardware issues

**Solutions:**
```bash
# Rebuild database completely
docrag fix-database
# (choose "yes" when prompted to rebuild)

# Or manually
rm -rf .docrag/vectordb
docrag reindex
```

### 4. Permission Issues

**Symptoms:**
- Cannot create database files
- Permission denied errors
- Database files owned by wrong user

**Causes:**
- DocRAG run with different user permissions
- System permission changes
- Docker/container permission issues

**Solutions:**
```bash
# Fix permissions
sudo chown -R $USER:$USER .docrag/
chmod -R 755 .docrag/

# Or use automatic fix
docrag fix-database
```

## Diagnostic Commands

### Check Database Status
```bash
# Comprehensive health check
docrag doctor

# Database-specific diagnostics
docrag fix-database
```

### Manual Diagnostics
```bash
# Check file permissions
ls -la .docrag/vectordb/

# Check for lock files
find .docrag/vectordb -name "*.db-wal" -o -name "*.db-shm"

# Check disk space
df -h .

# Check database files
file .docrag/vectordb/*.db 2>/dev/null || echo "No database files"
```

## Prevention

### Best Practices
1. **Consistent user**: Always run DocRAG commands as the same user
2. **Sufficient space**: Ensure adequate disk space before indexing
3. **Clean shutdown**: Don't force-kill DocRAG processes
4. **Regular backups**: Backup `.docrag/config.yaml` (not the database)

### Monitoring
```bash
# Regular health checks
docrag doctor

# Check before major operations
docrag fix-database
docrag index
```

## Advanced Troubleshooting

### For Developers

If automatic fixes don't work, you can debug manually:

```bash
# Check SQLite database directly
sqlite3 .docrag/vectordb/chroma.sqlite3 "PRAGMA integrity_check;"

# Check ChromaDB logs
python -c "
import chromadb
client = chromadb.PersistentClient(path='.docrag/vectordb')
print('Collections:', client.list_collections())
"
```

### Environment Issues

**Docker/Container environments:**
```bash
# Ensure proper volume mounting
docker run -v $(pwd)/.docrag:/app/.docrag your-image

# Check container permissions
docker exec container-name ls -la /app/.docrag/
```

**Network file systems (NFS, SMB):**
- Database operations may be slower
- Lock files might not work correctly
- Consider using local storage for `.docrag/vectordb/`

## Recovery Procedures

### Complete Reset
```bash
# Backup configuration
cp .docrag/config.yaml config.yaml.backup

# Remove everything
rm -rf .docrag/

# Reinitialize
docrag init --non-interactive
cp config.yaml.backup .docrag/config.yaml

# Rebuild database
docrag index
```

### Partial Recovery
```bash
# Keep configuration, rebuild database only
rm -rf .docrag/vectordb
docrag index
```

## Getting Help

If these solutions don't work:

1. **Run diagnostics**: `docrag doctor`
2. **Check logs**: Look for error messages in terminal output
3. **File an issue**: Include output from `docrag doctor`
4. **Provide context**: OS, Python version, file system type

## Related Commands

- `docrag doctor` - Comprehensive system diagnostics
- `docrag fix-database` - Automatic database repair
- `docrag index` - Rebuild database from scratch
- `docrag reindex` - Smart database rebuild
- `docrag config` - View current configuration