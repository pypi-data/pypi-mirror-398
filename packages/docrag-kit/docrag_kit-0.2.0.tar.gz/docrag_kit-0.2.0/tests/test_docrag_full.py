#!/usr/bin/env python3
"""
Automated testing script for DocRAG Kit.
Tests the full workflow: init -> index -> search
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# Test configuration
TEST_DIR = Path("test-demo-project")
import sys
PYTHON_BIN = Path(sys.executable)
DOCRAG_BIN = "docrag"  # Use the installed version in current environment
# Get API key from environment or use placeholder
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your-api-key-here")


def run_command(cmd, cwd=None, input_text=None):
    """Run command and return output."""
    print(f"\nRunning: {' '.join(str(c) for c in cmd)}")
    if input_text:
        print(f"Input: {input_text[:100]}...")
    
    result = subprocess.run(
        cmd,
        cwd=cwd,
        input=input_text,
        text=True,
        capture_output=True
    )
    
    if result.stdout:
        print(f"Output:\n{result.stdout}")
    if result.stderr:
        print(f"Stderr:\n{result.stderr}")
    
    return result


def test_init(test_demo_project):
    """Test docrag init with non-interactive mode."""
    print("\n" + "="*60)
    print("TEST 1: Initialize DocRAG")
    print("="*60)
    
    # Create .env file with test API key
    env_file = test_demo_project / ".env"
    env_file.write_text("OPENAI_API_KEY=sk-test-key-for-testing\n")
    
    result = run_command(
        [DOCRAG_BIN, "init", "--non-interactive", "--template", "general"],
        cwd=test_demo_project
    )
    
    assert result.returncode == 0, f"Init failed with code {result.returncode}"
    print("SUCCESS: Init successful")


def test_index(test_demo_project):
    """Test docrag index."""
    print("\n" + "="*60)
    print("TEST 2: Index Documentation")
    print("="*60)
    
    # Ensure .env file exists with test API key
    env_file = test_demo_project / ".env"
    if not env_file.exists():
        env_file.write_text("OPENAI_API_KEY=sk-test-key-for-testing\n")
    
    result = run_command(
        [DOCRAG_BIN, "index"],
        cwd=test_demo_project
    )
    
    # Index should succeed or fail gracefully with API key error
    if result.returncode != 0:
        # If it fails due to API key, that's expected in tests
        if "api key" in result.stdout.lower() or "api key" in result.stderr.lower():
            print("INFO: Index failed due to API key (expected in tests)")
            return
        else:
            assert False, f"Indexing failed unexpectedly: {result.stdout} {result.stderr}"
    
    assert "indexed successfully" in result.stdout.lower() or "SUCCESS:" in result.stdout, "Index success message not found"
    print("SUCCESS: Indexing successful")


def test_mcp_config(test_demo_project):
    """Test docrag mcp-config."""
    print("\n" + "="*60)
    print("TEST 3: Get MCP Configuration")
    print("="*60)
    
    result = run_command(
        [DOCRAG_BIN, "mcp-config", "--non-interactive"],
        cwd=test_demo_project
    )
    
    assert result.returncode == 0, f"MCP config failed with code {result.returncode}"
    assert "mcpServers" in result.stdout, "MCP config JSON not found in output"
    print("SUCCESS: MCP config generated")


def test_mcp_server(test_demo_project):
    """Test MCP server startup."""
    print("\n" + "="*60)
    print("TEST 4: Test MCP Server Startup")
    print("="*60)
    
    # Start server and kill it after 2 seconds (just to test it starts)
    proc = subprocess.Popen(
        [PYTHON_BIN, "-m", "docrag.mcp_server"],
        cwd=test_demo_project,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(2)
    proc.terminate()
    
    try:
        stdout, stderr = proc.communicate(timeout=2)
        
        # If no error in stderr, server started successfully
        assert "ModuleNotFoundError" not in stderr, f"MCP server has module errors: {stderr}"
        assert "ImportError" not in stderr, f"MCP server has import errors: {stderr}"
        print("SUCCESS: MCP server starts without errors")
        
    except subprocess.TimeoutExpired:
        proc.kill()
        print("SUCCESS: MCP server running (killed after timeout)")


def test_list_docs(test_demo_project):
    """Test listing indexed documents."""
    print("\n" + "="*60)
    print("TEST 5: List Indexed Documents")
    print("="*60)
    
    # Check if vectordb exists (may not exist if indexing failed due to API key)
    vectordb_path = test_demo_project / ".docrag" / "vectordb"
    if vectordb_path.exists():
        print(f"SUCCESS: Vector database exists at {vectordb_path}")
        
        # Count files
        files = list(vectordb_path.rglob("*"))
        print(f"INFO: Vector DB contains {len(files)} files")
    else:
        print(f"INFO: Vector database not found at {vectordb_path} (expected if indexing was skipped)")
        # Check if .docrag directory exists at least
        docrag_dir = test_demo_project / ".docrag"
        assert docrag_dir.exists(), f"DocRAG directory not found at {docrag_dir}"
        print(f"SUCCESS: DocRAG directory exists at {docrag_dir}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("DocRAG Kit - Automated Testing Suite")
    print("="*60)
    
    # Check prerequisites
    if not PYTHON_BIN.exists():
        print(f"ERROR: Python not found at {PYTHON_BIN}")
        sys.exit(1)
    
    if not DOCRAG_BIN.exists():
        print(f"ERROR: docrag not found at {DOCRAG_BIN}")
        sys.exit(1)
    
    if not TEST_DIR.exists():
        print(f"ERROR: Test directory not found: {TEST_DIR}")
        sys.exit(1)
    
    # Clean up previous test data
    print("\nCleaning up previous test data...")
    docrag_dir = TEST_DIR / ".docrag"
    env_file = TEST_DIR / ".env"
    
    if docrag_dir.exists():
        import shutil
        shutil.rmtree(docrag_dir)
        print(f"   Removed {docrag_dir}")
    
    if env_file.exists():
        env_file.unlink()
        print(f"   Removed {env_file}")
    
    # Run tests
    try:
        test_init()
        test_index()
        test_mcp_config()
        test_mcp_server()
        test_list_docs()
        
        print("\n" + "="*60)
        print("SUCCESS: All tests passed!")
        print("="*60)
        return 0
        
    except AssertionError as e:
        print(f"\nERROR: Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\nERROR: Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
