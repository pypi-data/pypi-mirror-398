"""Test package installation and configuration.

This test validates that the package is properly configured for distribution.
"""

import sys
from pathlib import Path
import subprocess


def test_package_metadata():
    """Test that package metadata is properly configured."""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    
    with open('pyproject.toml', 'rb') as f:
        config = tomllib.load(f)
    
    project = config.get('project', {})
    
    # Verify required metadata
    assert project.get('name') == 'docrag-kit', "Package name should be 'docrag-kit'"
    assert project.get('version'), "Version should be specified"
    assert project.get('description'), "Description should be specified"
    assert project.get('readme') == 'README.md', "README should be specified"
    requires_python = project.get('requires-python', '')
    assert requires_python.startswith('>=3.10'), "Python version should be >=3.10"
    assert project.get('license'), "License should be specified"
    
    # Verify dependencies
    dependencies = project.get('dependencies', [])
    assert len(dependencies) > 0, "Dependencies should be specified"
    
    required_deps = [
        'click',
        'langchain',
        'chromadb',
        'pyyaml',
        'python-dotenv',
        'mcp'
    ]
    
    dep_names = [dep.split('>=')[0].split('==')[0] for dep in dependencies]
    for req_dep in required_deps:
        assert any(req_dep in dep for dep in dep_names), f"Required dependency '{req_dep}' not found"
    
    # Verify entry points
    scripts = project.get('scripts', {})
    assert 'docrag' in scripts, "CLI entry point 'docrag' should be defined"
    assert scripts['docrag'] == 'docrag.cli:cli', "Entry point should point to docrag.cli:cli"


def test_package_structure():
    """Test that package structure is correct."""
    src_dir = Path('src/docrag')
    assert src_dir.exists(), "src/docrag directory should exist"
    
    required_files = [
        '__init__.py',
        'cli.py',
        'config_manager.py',
        'document_processor.py',
        'vector_db.py',
        'mcp_server.py',
        'prompt_templates.py',
        'security.py',
        'errors.py',
        'py.typed'
    ]
    
    for file in required_files:
        file_path = src_dir / file
        assert file_path.exists(), f"Required file '{file}' should exist"


def test_cli_entry_point():
    """Test that CLI entry point is properly configured."""
    sys.path.insert(0, 'src')
    
    from docrag.cli import cli
    import click
    
    assert callable(cli), "CLI should be callable"
    assert isinstance(cli, (click.Group, click.Command)), "CLI should be a Click command/group"


def test_manifest_includes():
    """Test that MANIFEST.in includes required files."""
    manifest_path = Path('MANIFEST.in')
    assert manifest_path.exists(), "MANIFEST.in should exist"
    
    with open(manifest_path, 'r') as f:
        content = f.read()
    
    required_includes = [
        'README.md',
        'LICENSE',
        'pyproject.toml',
    ]
    
    for item in required_includes:
        assert item in content, f"MANIFEST.in should include '{item}'"
    
    assert 'recursive-include' in content, "MANIFEST.in should recursively include source files"
    assert 'src/docrag' in content, "MANIFEST.in should include src/docrag"


def test_gitignore_configuration():
    """Test that .gitignore is properly configured."""
    gitignore_path = Path('.gitignore')
    assert gitignore_path.exists(), ".gitignore should exist"
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    # Check for required exclusions (some may use patterns)
    required_checks = [
        ('__pycache__', '__pycache__'),
        ('*.pyc or *.py[cod]', lambda c: '*.pyc' in c or '*.py[cod]' in c),
        ('.env', '.env'),
        ('dist/', 'dist/'),
        ('build/', 'build/'),
        ('*.egg-info', '*.egg-info'),
    ]
    
    for name, check in required_checks:
        if callable(check):
            assert check(content), f".gitignore should exclude '{name}'"
        else:
            assert check in content, f".gitignore should exclude '{name}'"


def test_setup_py_exists():
    """Test that setup.py exists for backward compatibility."""
    setup_path = Path('setup.py')
    assert setup_path.exists(), "setup.py should exist for backward compatibility"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
