#!/usr/bin/env python3
"""
MCP Reindexing Worker - Isolated process for safe database operations.

This module provides process-isolated reindexing to avoid ChromaDB/SQLite
file locking conflicts in MCP context.
"""

import sys
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional


def perform_isolated_reindex(project_root: str, config_dict: Dict[str, Any], reason: str = "MCP reindex") -> Dict[str, Any]:
    """
    Perform reindexing in completely isolated process context.
    
    Args:
        project_root: Path to project root directory
        config_dict: Configuration dictionary
        reason: Reason for reindexing
    
    Returns:
        Dictionary with success status and results
    """
    try:
        # Import here to avoid conflicts
        from .document_processor import DocumentProcessor
        from .vector_db import VectorDBManager
        
        project_path = Path(project_root)
        
        # Step 1: Force cleanup of any existing connections
        import gc
        gc.collect()
        
        # Step 2: Initialize managers in clean context
        doc_processor = DocumentProcessor(config_dict)
        vector_db = VectorDBManager(config_dict, project_path)
        
        # Step 3: Aggressive database cleanup
        db_path = project_path / ".docrag" / "vectordb"
        if db_path.exists():
            # Use the most aggressive cleanup strategy
            vector_db._force_delete_database()
        
        # Step 4: Process documents
        chunks, stats = doc_processor.process(project_path)
        
        if stats['files_found'] == 0:
            return {
                "success": False,
                "error": "No files found to index",
                "stats": stats
            }
        
        # Step 5: Create new database in isolated context
        # Redirect stdout temporarily to avoid polluting JSON output
        import io
        import contextlib
        
        stdout_buffer = io.StringIO()
        with contextlib.redirect_stdout(stdout_buffer):
            vector_db.create_database(chunks, show_progress=False)
        
        # Step 6: Verify database creation
        if not db_path.exists():
            return {
                "success": False,
                "error": "Database verification failed",
                "stats": stats
            }
        
        return {
            "success": True,
            "reason": reason,
            "stats": stats,
            "message": f"Reindexing completed successfully! Files: {stats['files_processed']}, Chunks: {stats['chunks_created']}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "stats": {}
        }


def main():
    """Main entry point for isolated reindexing worker."""
    if len(sys.argv) != 4:
        print(json.dumps({
            "success": False,
            "error": "Usage: python -m docrag.mcp_reindex_worker <project_root> <config_json> <reason>"
        }))
        sys.exit(1)
    
    try:
        project_root = sys.argv[1]
        config_json = sys.argv[2]
        reason = sys.argv[3]
        
        # Parse configuration
        config_dict = json.loads(config_json)
        
        # Perform reindexing
        result = perform_isolated_reindex(project_root, config_dict, reason)
        
        # Output result as JSON
        print(json.dumps(result))
        
        # Exit with appropriate code
        sys.exit(0 if result["success"] else 1)
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"Worker process failed: {str(e)}"
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()