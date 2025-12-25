"""Security and data protection utilities for DocRAG Kit."""

from pathlib import Path
from typing import Tuple, Optional
import click


def check_root_gitignore_exists(project_root: Path) -> bool:
    """Check if root .gitignore exists.
    
    Args:
        project_root: Path to project root directory
        
    Returns:
        True if .gitignore exists, False otherwise
    """
    gitignore_path = project_root / ".gitignore"
    return gitignore_path.exists()


def is_env_gitignored(project_root: Path) -> bool:
    """Verify .env is in root .gitignore.
    
    Args:
        project_root: Path to project root directory
        
    Returns:
        True if .env is gitignored, False otherwise
    """
    gitignore_path = project_root / ".gitignore"
    
    if not gitignore_path.exists():
        return False
    
    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for .env in gitignore (as exact match or pattern)
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Check if line matches .env
            if line == '.env' or line == '/.env' or line == '*.env':
                return True
        
        return False
    
    except Exception:
        return False


def add_env_to_gitignore(project_root: Path) -> bool:
    """Add .env to root .gitignore.
    
    Args:
        project_root: Path to project root directory
        
    Returns:
        True if successfully added, False otherwise
    """
    gitignore_path = project_root / ".gitignore"
    
    try:
        # If .gitignore doesn't exist, create it
        if not gitignore_path.exists():
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write("# DocRAG Kit - API keys\n.env\n")
            return True
        
        # Append to existing .gitignore
        with open(gitignore_path, 'a', encoding='utf-8') as f:
            f.write("\n# DocRAG Kit - API keys\n.env\n")
        
        return True
    
    except Exception:
        return False


def validate_gitignore_security(project_root: Path) -> Tuple[bool, Optional[str]]:
    """Validate .gitignore security setup.
    
    Checks if root .gitignore exists and if .env is excluded.
    
    Args:
        project_root: Path to project root directory
        
    Returns:
        Tuple of (is_secure, warning_message)
        - is_secure: True if .env is properly gitignored
        - warning_message: Warning message if not secure, None otherwise
    """
    # Check if root .gitignore exists
    if not check_root_gitignore_exists(project_root):
        return False, "No .gitignore found in project root"
    
    # Check if .env is gitignored
    if not is_env_gitignored(project_root):
        return False, ".env is not in your root .gitignore"
    
    return True, None


def display_gitignore_warning(project_root: Path, offer_fix: bool = True) -> None:
    """Display warning if .env is not gitignored and optionally offer to fix.
    
    Args:
        project_root: Path to project root directory
        offer_fix: Whether to offer automatic fix
    """
    is_secure, warning = validate_gitignore_security(project_root)
    
    if is_secure:
        return
    
    # Display warning
    click.echo(f"\nWARNING:  WARNING: {warning}")
    click.echo("   Your API keys could be committed to git!")
    
    if offer_fix:
        if not check_root_gitignore_exists(project_root):
            if click.confirm("   Create .gitignore and add .env?", default=True):
                if add_env_to_gitignore(project_root):
                    click.echo("   SUCCESS: Created .gitignore with .env excluded")
                else:
                    click.echo("   ERROR: Failed to create .gitignore")
                    click.echo("   Please create .gitignore manually and add: .env")
        else:
            if click.confirm("   Add .env to root .gitignore?", default=True):
                if add_env_to_gitignore(project_root):
                    click.echo("   SUCCESS: Added .env to root .gitignore")
                else:
                    click.echo("   ERROR: Failed to update .gitignore")
                    click.echo("   Please add .env to .gitignore manually")


def create_docrag_gitignore(docrag_dir: Path) -> bool:
    """Create .docrag/.gitignore with proper exclusions.
    
    Args:
        docrag_dir: Path to .docrag directory
        
    Returns:
        True if successfully created, False otherwise
    """
    gitignore_path = docrag_dir / ".gitignore"
    
    gitignore_content = """# Vector database (can be regenerated)
vectordb/

# Python cache
*.pyc
__pycache__/

# Environment variables (contains API keys)
.env
"""
    
    try:
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        return True
    except Exception:
        return False


def create_env_example(project_root: Path) -> bool:
    """Create .env.example template with placeholder keys.
    
    Args:
        project_root: Path to project root directory
        
    Returns:
        True if successfully created, False otherwise
    """
    env_example_path = project_root / ".env.example"
    
    env_example_content = """# DocRAG Kit - API Keys Configuration
# Copy this file to .env and add your actual API keys
# NEVER commit .env to git!

# OpenAI API Key
# Get your key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_key_here

# Google Gemini API Key
# Get your key from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_gemini_key_here
"""
    
    try:
        with open(env_example_path, 'w', encoding='utf-8') as f:
            f.write(env_example_content)
        return True
    except Exception:
        return False


def display_security_reminder() -> None:
    """Display security reminder after initialization.
    
    Shows warnings about not committing .env and instructions for .env.example pattern.
    """
    click.echo("\n🔒 SECURITY REMINDER:")
    click.echo("   • Your API keys are stored in .env")
    click.echo("   • This file is gitignored and will NOT be committed")
    click.echo("   • Never share your .env file or commit it to git")
    click.echo("   • Use .env.example as a template for other users")
    click.echo("\nTIP: Best Practices:")
    click.echo("   • Keep .env in your .gitignore")
    click.echo("   • Share .env.example (without real keys) with your team")
    click.echo("   • Rotate API keys if accidentally exposed")
    click.echo("   • Consider using a pre-commit hook to prevent .env commits")
