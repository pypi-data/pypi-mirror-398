"""Configuration management for DocRAG Kit."""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
import os


@dataclass
class ProjectConfig:
    """Project configuration."""
    name: str
    type: str  # symfony, ios, general, custom


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str  # openai, gemini
    embedding_model: str
    llm_model: str
    temperature: float = 0.3


@dataclass
class IndexingConfig:
    """Document indexing configuration."""
    directories: List[str]
    extensions: List[str]
    exclude_patterns: List[str]


@dataclass
class ChunkingConfig:
    """Document chunking configuration."""
    chunk_size: int = 800  # Optimized for faster processing
    chunk_overlap: int = 150  # Optimized overlap


@dataclass
class RetrievalConfig:
    """Retrieval configuration."""
    top_k: int = 3  # Reduced from 5 for faster response


@dataclass
class PromptConfig:
    """Prompt template configuration."""
    template: str


@dataclass
class DocRAGConfig:
    """Complete DocRAG configuration container."""
    project: ProjectConfig
    llm: LLMConfig
    indexing: IndexingConfig
    chunking: ChunkingConfig
    retrieval: RetrievalConfig
    prompt: PromptConfig

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'project': asdict(self.project),
            'llm': asdict(self.llm),
            'indexing': asdict(self.indexing),
            'chunking': asdict(self.chunking),
            'retrieval': asdict(self.retrieval),
            'prompt': asdict(self.prompt)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocRAGConfig':
        """Create configuration from dictionary."""
        return cls(
            project=ProjectConfig(**data['project']),
            llm=LLMConfig(**data['llm']),
            indexing=IndexingConfig(**data['indexing']),
            chunking=ChunkingConfig(**data['chunking']),
            retrieval=RetrievalConfig(**data['retrieval']),
            prompt=PromptConfig(**data['prompt'])
        )
    
    @classmethod
    def from_template(cls, template: str = 'general') -> 'DocRAGConfig':
        """
        Create configuration from template.
        
        Args:
            template: Template name (general, symfony, ios)
        
        Returns:
            DocRAGConfig with default values for the template
        """
        from .prompt_templates import get_template_for_project_type
        
        # Default project name
        project_name = "My Project"
        
        # Template-specific defaults
        if template == 'symfony':
            directories = ['docs/', 'src/', 'config/']
            extensions = ['.md', '.php', '.yaml', '.yml', '.twig']
        elif template == 'ios':
            directories = ['docs/', 'Sources/', 'README.md']
            extensions = ['.md', '.swift', '.h', '.m']
        else:  # general
            directories = ['docs/', 'README.md']
            extensions = ['.md', '.txt', '.rst']
        
        return cls(
            project=ProjectConfig(
                name=project_name,
                type=template
            ),
            llm=LLMConfig(
                provider='openai',
                embedding_model='text-embedding-3-small',
                llm_model='gpt-4o-mini',
                temperature=0.3
            ),
            indexing=IndexingConfig(
                directories=directories,
                extensions=extensions,
                exclude_patterns=[
                    'node_modules/', '.git/', '__pycache__/', 
                    'venv/', '.venv/', 'vendor/', 'build/', 'dist/'
                ]
            ),
            chunking=ChunkingConfig(
                chunk_size=800,
                chunk_overlap=150
            ),
            retrieval=RetrievalConfig(
                top_k=3
            ),
            prompt=PromptConfig(
                template=get_template_for_project_type(template)
            )
        )


class ConfigManager:
    """Manages DocRAG configuration."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            project_root: Root directory of the project. Defaults to current directory.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.docrag_dir = self.project_root / ".docrag"
        self.config_path = self.docrag_dir / "config.yaml"
        self.env_path = self.project_root / ".env"

    def load_config(self) -> Optional[DocRAGConfig]:
        """
        Load configuration from YAML file.
        
        Returns:
            DocRAGConfig object if file exists, None otherwise.
        
        Raises:
            yaml.YAMLError: If YAML parsing fails.
            KeyError: If required configuration fields are missing.
        """
        if not self.config_path.exists():
            return None
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return None
            
            return DocRAGConfig.from_dict(data)
        
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse config.yaml: {e}")
        except KeyError as e:
            raise KeyError(f"Missing required configuration field: {e}")

    def save_config(self, config: DocRAGConfig) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config: DocRAGConfig object to save.
        
        Raises:
            OSError: If file cannot be written.
        """
        # Ensure .docrag directory exists
        self.docrag_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert config to dictionary
        config_dict = config.to_dict()
        
        # Write to YAML file
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        except OSError as e:
            raise OSError(f"Failed to write config.yaml: {e}")

    def validate_config(self, config: DocRAGConfig) -> List[str]:
        """
        Validate configuration parameters.
        
        Args:
            config: DocRAGConfig object to validate.
        
        Returns:
            List of validation error messages. Empty list if valid.
        """
        errors = []
        
        # Validate chunk_size range
        if config.chunking.chunk_size < 100:
            errors.append("chunk_size must be at least 100 characters")
        if config.chunking.chunk_size > 5000:
            errors.append("chunk_size must not exceed 5000 characters")
        
        # Validate top_k
        if config.retrieval.top_k < 1:
            errors.append("top_k must be at least 1")
        
        # Validate provider
        valid_providers = ['openai', 'gemini']
        if config.llm.provider not in valid_providers:
            errors.append(f"provider must be one of: {', '.join(valid_providers)}")
        
        # Validate required fields are present
        if not config.project.name:
            errors.append("project.name is required")
        if not config.project.type:
            errors.append("project.type is required")
        if not config.llm.embedding_model:
            errors.append("llm.embedding_model is required")
        if not config.llm.llm_model:
            errors.append("llm.llm_model is required")
        if not config.indexing.directories:
            errors.append("indexing.directories must contain at least one directory")
        if not config.indexing.extensions:
            errors.append("indexing.extensions must contain at least one extension")
        if not config.prompt.template:
            errors.append("prompt.template is required")
        
        # Validate prompt template has required placeholders
        if config.prompt.template:
            if '{context}' not in config.prompt.template:
                errors.append("prompt.template must contain {context} placeholder")
            if '{question}' not in config.prompt.template:
                errors.append("prompt.template must contain {question} placeholder")
        
        return errors

    def _detect_project_structure(self) -> Dict[str, Any]:
        """
        Detect project structure and suggest relevant directories and file types.
        
        Returns:
            Dictionary with suggested directories, extensions, and exclusions.
        """
        from pathlib import Path
        
        suggested_dirs = []
        suggested_extensions = set(['.md', '.txt'])  # Always include these
        
        # Common documentation directories
        doc_dirs = ['docs', 'doc', 'documentation', 'wiki']
        for dir_name in doc_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                suggested_dirs.append(f"{dir_name}/")
        
        # Check for README files
        readme_files = list(self.project_root.glob("README*"))
        if readme_files:
            suggested_dirs.append("README.md")
        
        # Detect project type by files and add relevant extensions
        project_files = list(self.project_root.glob("*"))
        
        # Python project
        if any(f.name in ['setup.py', 'pyproject.toml', 'requirements.txt'] for f in project_files):
            suggested_extensions.update(['.py', '.rst'])
        
        # JavaScript/TypeScript project
        if any(f.name in ['package.json', 'tsconfig.json'] for f in project_files):
            suggested_extensions.update(['.js', '.ts', '.jsx', '.tsx'])
        
        # PHP/Symfony project
        if any(f.name in ['composer.json', 'symfony.lock'] for f in project_files):
            suggested_extensions.update(['.php'])
        
        # iOS/Swift project
        if any(f.suffix == '.xcodeproj' for f in project_files) or \
           any(f.suffix == '.xcworkspace' for f in project_files):
            suggested_extensions.update(['.swift', '.m', '.h'])
        
        # Configuration files
        if any(f.suffix in ['.yaml', '.yml', '.json', '.toml'] for f in project_files):
            suggested_extensions.update(['.yaml', '.yml', '.json', '.toml'])
        
        # If no specific directories found, suggest current directory
        if not suggested_dirs:
            suggested_dirs = ['.']
        
        # Standard exclusions
        suggested_exclusions = ['node_modules/', '.git/', '__pycache__/', 'vendor/', 'venv/', '.venv/']
        
        return {
            'directories': suggested_dirs,
            'extensions': sorted(list(suggested_extensions)),
            'exclusions': suggested_exclusions
        }
    
    def interactive_setup(self) -> DocRAGConfig:
        """
        Run interactive configuration wizard.
        
        Returns:
            DocRAGConfig object with user-provided values.
        """
        print("SETUP: DocRAG Kit - Interactive Setup\n")
        
        # Detect project structure
        detected = self._detect_project_structure()
        
        # Project configuration
        print("PROJECT: Project Configuration")
        project_name = input("Project name: ").strip() or self.project_root.name
        
        print("\nProject type:")
        print("  1. Symfony (PHP framework)")
        print("  2. iOS (Swift/UIKit/SwiftUI)")
        print("  3. General Documentation")
        print("  4. Custom")
        project_type_choice = input("Choose [1-4]: ").strip()
        project_type_map = {
            '1': 'symfony',
            '2': 'ios',
            '3': 'general',
            '4': 'custom'
        }
        project_type = project_type_map.get(project_type_choice, 'general')
        
        # LLM configuration
        print("\n🤖 LLM Provider Configuration")
        print("  1. OpenAI (GPT-4)")
        print("  2. Google Gemini")
        provider_choice = input("Choose provider [1-2]: ").strip()
        provider = 'openai' if provider_choice == '1' else 'gemini'
        
        api_key = input(f"Enter {provider.upper()} API key: ").strip()
        
        # Set default models based on provider
        if provider == 'openai':
            embedding_model = 'text-embedding-3-small'
            llm_model = 'gpt-4o-mini'
        else:
            embedding_model = 'models/embedding-001'
            llm_model = 'gemini-1.5-flash'
        
        # Indexing configuration
        print("\n📁 Indexing Configuration")
        
        # Directories
        default_dirs = ','.join(detected['directories'])
        print(f"Detected directories: {', '.join(detected['directories'])}")
        dirs_input = input(f"Directories to index (comma-separated) [{default_dirs}]: ").strip()
        directories = [d.strip() for d in dirs_input.split(',')] if dirs_input else detected['directories']
        
        # Extensions
        default_exts = ','.join(detected['extensions'])
        print(f"\nDetected file types: {', '.join(detected['extensions'])}")
        exts_input = input(f"File extensions (comma-separated) [{default_exts}]: ").strip()
        extensions = [e.strip() for e in exts_input.split(',')] if exts_input else detected['extensions']
        
        # Exclusions
        default_excl = ','.join(detected['exclusions'])
        print(f"\nSuggested exclusions: {', '.join(detected['exclusions'])}")
        excl_input = input(f"Exclusion patterns (comma-separated) [{default_excl}]: ").strip()
        exclude_patterns = [p.strip() for p in excl_input.split(',')] if excl_input else detected['exclusions']
        
        # Get prompt template based on project type
        from .prompt_templates import PromptTemplateManager
        prompt_template = PromptTemplateManager.get_template(project_type)
        
        # Create configuration
        config = DocRAGConfig(
            project=ProjectConfig(name=project_name, type=project_type),
            llm=LLMConfig(
                provider=provider,
                embedding_model=embedding_model,
                llm_model=llm_model,
                temperature=0.3
            ),
            indexing=IndexingConfig(
                directories=directories,
                extensions=extensions,
                exclude_patterns=exclude_patterns
            ),
            chunking=ChunkingConfig(chunk_size=800, chunk_overlap=150),  # Smaller chunks for faster processing
            retrieval=RetrievalConfig(top_k=3),  # Fewer docs for faster response
            prompt=PromptConfig(template=prompt_template)
        )
        
        # Save API key to .env
        self._save_env_vars(provider, api_key)
        
        return config

    def _save_env_vars(self, provider: str, api_key: str) -> None:
        """
        Save API key to .env file.
        
        Args:
            provider: LLM provider name (openai or gemini).
            api_key: API key for the provider.
        """
        # Read existing .env content if it exists
        existing_content = ""
        if self.env_path.exists():
            with open(self.env_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # Prepare new content to append
        new_lines = []
        
        # Add API key
        if provider == 'openai':
            key_name = 'OPENAI_API_KEY'
        else:
            key_name = 'GOOGLE_API_KEY'
        
        # Check if key already exists
        if key_name not in existing_content:
            new_lines.append(f"{key_name}={api_key}")
        
        # Append new content if there's anything to add
        if new_lines:
            with open(self.env_path, 'a', encoding='utf-8') as f:
                if existing_content and not existing_content.endswith('\n'):
                    f.write('\n')
                f.write('\n'.join(new_lines) + '\n')
