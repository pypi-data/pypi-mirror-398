"""Vector database management for DocRAG Kit."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import os
import shutil
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv


class VectorDBManager:
    """Manages ChromaDB vector database operations."""

    def __init__(self, config: Dict[str, Any], project_root: Optional[Path] = None):
        """
        Initialize vector database manager.
        
        Args:
            config: Configuration dictionary containing LLM and retrieval settings.
            project_root: Root directory of the project. Defaults to current directory.
        """
        self.config = config
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.db_path = self.project_root / ".docrag" / "vectordb"
        
        # Load environment variables
        load_dotenv(self.project_root / ".env")
        
        # Initialize embeddings
        self.embeddings = self._init_embeddings()
        
        # Store previous provider for change detection
        self._previous_provider = None

    def _init_embeddings(self):
        """
        Initialize embeddings based on configured provider.
        
        Returns:
            Embeddings instance (OpenAIEmbeddings or GoogleGenerativeAIEmbeddings).
        
        Raises:
            ValueError: If provider is not supported or API key is missing.
        """
        llm_config = self.config.get('llm', {})
        provider = llm_config.get('provider', 'openai')
        embedding_model = llm_config.get('embedding_model')
        
        if provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError(
                    "ERROR: OpenAI API key not found.\n"
                    "   Add OPENAI_API_KEY to your .env file.\n"
                    "   Get your API key from: https://platform.openai.com/api-keys"
                )
            
            return OpenAIEmbeddings(
                model=embedding_model or 'text-embedding-3-small',
                openai_api_key=api_key
            )
        
        elif provider == 'gemini':
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError(
                    "ERROR: Google API key not found.\n"
                    "   Add GOOGLE_API_KEY to your .env file.\n"
                    "   Get your API key from: https://makersuite.google.com/app/apikey"
                )
            
            return GoogleGenerativeAIEmbeddings(
                model=embedding_model or 'models/embedding-001',
                google_api_key=api_key
            )
        
        else:
            raise ValueError(
                f"ERROR: Unsupported provider: {provider}\n"
                f"   Supported providers: openai, gemini"
            )

    def create_database(self, chunks: List[Document], show_progress: bool = True) -> None:
        """
        Create new vector database from chunks.
        
        Args:
            chunks: List of Document chunks to index.
            show_progress: Whether to display progress information.
        
        Raises:
            Exception: If database creation fails.
        """
        if not chunks:
            raise ValueError("ERROR: No chunks provided for indexing")
        
        # Ensure .docrag directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Delete existing database if it exists (with MCP-safe deletion)
        if self.db_path.exists():
            self.delete_database()
        
        if show_progress:
            print(f"Creating embeddings for {len(chunks)} chunks...")
        
        try:
            # Create ChromaDB vector store with MCP-safe settings
            vectorstore = self._create_vectorstore_safe(chunks)
            
            if show_progress:
                print(f"SUCCESS: Vector database created successfully at {self.db_path}")
        
        except Exception as e:
            raise Exception(f"Database error: {e}")

    def _create_vectorstore_safe(self, chunks: List[Document]):
        """
        Create ChromaDB vectorstore with MCP-safe configuration.
        
        Args:
            chunks: Document chunks to index.
            
        Returns:
            Chroma vectorstore instance.
        """
        import time
        
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Ensure clean state
                self._close_existing_connections()
                
                # Create ChromaDB vector store
                vectorstore = Chroma.from_documents(
                    documents=chunks,
                    embedding=self.embeddings,
                    persist_directory=str(self.db_path)
                )
                
                # Store reference for cleanup
                self._vectorstore = vectorstore
                return vectorstore
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"   Retry {attempt + 1}/{max_retries}: Database creation failed, retrying...")
                    time.sleep(retry_delay * (attempt + 1))
                    
                    # Clean up any partial creation
                    if self.db_path.exists():
                        try:
                            shutil.rmtree(self.db_path)
                        except:
                            pass
                else:
                    raise Exception(f"unable to open database file: {e}")

    def delete_database(self) -> None:
        """
        Delete existing vector database.
        
        This removes the .docrag/vectordb/ directory and all its contents.
        Uses safe deletion with retry mechanism for MCP compatibility.
        """
        if self.db_path.exists():
            try:
                # Try graceful deletion first
                self._safe_delete_database()
            except Exception as e:
                print(f"WARNING: Warning: Failed to delete database: {e}")

    def _safe_delete_database(self) -> None:
        """
        Safely delete database with aggressive retry mechanism for MCP compatibility.
        
        This handles potential file locking issues when MCP server
        and CLI access the database simultaneously.
        """
        import time
        import platform
        import os
        
        max_retries = 5  # Increased from 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                # On Windows, ensure no processes are holding file handles
                if platform.system() == "Windows":
                    import gc
                    gc.collect()
                
                # Force close any existing ChromaDB connections
                self._close_existing_connections()
                
                # Wait progressively longer for file handles to be released
                wait_time = retry_delay * (attempt + 1)
                time.sleep(wait_time)
                
                # Try different deletion strategies based on attempt
                if attempt == 0:
                    # Strategy 1: Normal deletion
                    shutil.rmtree(self.db_path)
                    return
                
                elif attempt == 1:
                    # Strategy 2: Force deletion with ignore_errors
                    shutil.rmtree(self.db_path, ignore_errors=True)
                    if not self.db_path.exists():
                        return
                
                elif attempt == 2:
                    # Strategy 3: Delete individual files first
                    for file_path in self.db_path.rglob("*"):
                        if file_path.is_file():
                            try:
                                # Remove read-only flag if present
                                if platform.system() == "Windows":
                                    os.chmod(file_path, 0o777)
                                file_path.unlink()
                            except:
                                pass
                    
                    # Then remove directories
                    shutil.rmtree(self.db_path, ignore_errors=True)
                    if not self.db_path.exists():
                        return
                
                elif attempt == 3:
                    # Strategy 4: Try to rename first, then delete
                    backup_path = self.db_path.parent / f"vectordb_backup_{int(time.time())}"
                    try:
                        self.db_path.rename(backup_path)
                        shutil.rmtree(backup_path, ignore_errors=True)
                        return
                    except:
                        pass
                
                else:
                    # Strategy 5: Last resort - just try to remove what we can
                    try:
                        shutil.rmtree(self.db_path, ignore_errors=True)
                        return
                    except:
                        pass
                
            except (OSError, PermissionError) as e:
                if attempt < max_retries - 1:
                    continue
                else:
                    # If all strategies failed, provide detailed error
                    raise Exception(f"Database deletion failed after {max_retries} attempts. "
                                  f"This may be due to ChromaDB file locking in MCP context. "
                                  f"Last error: {e}")

    def _close_existing_connections(self) -> None:
        """
        Aggressively close any existing ChromaDB connections to prevent file locking.
        """
        try:
            # Force garbage collection to close any lingering connections
            import gc
            gc.collect()
            
            # Clear any cached vectorstore references
            if hasattr(self, '_vectorstore'):
                try:
                    # Try to close ChromaDB client if it has a close method
                    if hasattr(self._vectorstore, '_client'):
                        client = self._vectorstore._client
                        if hasattr(client, 'reset'):
                            client.reset()
                        if hasattr(client, 'close'):
                            client.close()
                except:
                    pass
                
                delattr(self, '_vectorstore')
            
            # Clear any other potential references
            for attr_name in ['_client', '_collection', '_embeddings_cache']:
                if hasattr(self, attr_name):
                    try:
                        delattr(self, attr_name)
                    except:
                        pass
            
            # Additional garbage collection
            gc.collect()
            
            # Small delay to ensure cleanup
            import time
            time.sleep(0.1)
                
        except Exception:
            # Ignore errors during cleanup - this is best effort
            pass

    def get_retriever(self, top_k: Optional[int] = None):
        """
        Get retriever for querying the vector database.
        
        Args:
            top_k: Number of top results to retrieve. If None, uses config value.
        
        Returns:
            VectorStoreRetriever instance.
        
        Raises:
            ValueError: If database doesn't exist.
        """
        if not self.db_path.exists():
            raise ValueError(
                "ERROR: Vector database not found.\n"
                "   Run 'docrag index' to create the database first."
            )
        
        # Use provided top_k or fall back to config
        if top_k is None:
            retrieval_config = self.config.get('retrieval', {})
            top_k = retrieval_config.get('top_k', 5)
        
        # Load existing vector store
        vectorstore = Chroma(
            persist_directory=str(self.db_path),
            embedding_function=self.embeddings
        )
        
        # Create and return retriever
        return vectorstore.as_retriever(
            search_kwargs={"k": top_k}
        )

    def list_documents(self) -> List[str]:
        """
        List all unique source files in the database.
        
        Returns:
            Sorted list of unique source file names.
        
        Raises:
            ValueError: If database doesn't exist.
        """
        if not self.db_path.exists():
            raise ValueError(
                "ERROR: Vector database not found.\n"
                "   Run 'docrag index' to create the database first."
            )
        
        # Load existing vector store
        vectorstore = Chroma(
            persist_directory=str(self.db_path),
            embedding_function=self.embeddings
        )
        
        # Get all documents
        # We need to query with a dummy search to get all documents
        # ChromaDB doesn't have a direct "get all" method, so we use get()
        collection = vectorstore._collection
        results = collection.get()
        
        # Extract unique source files from metadata
        source_files = set()
        if results and 'metadatas' in results:
            for metadata in results['metadatas']:
                if metadata and 'source_file' in metadata:
                    source_files.add(metadata['source_file'])
                elif metadata and 'source' in metadata:
                    # Fallback to extracting filename from full path
                    source_path = Path(metadata['source'])
                    source_files.add(source_path.name)
        
        # Return sorted list
        return sorted(list(source_files))

    def detect_provider_change(self, previous_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Detect if LLM provider has changed from previous configuration.
        
        Args:
            previous_config: Previous configuration dictionary. If None, loads from file.
        
        Returns:
            True if provider has changed, False otherwise.
        """
        if previous_config is None:
            # Try to load previous config from a stored file
            config_path = self.project_root / ".docrag" / "config.yaml"
            if not config_path.exists():
                return False
            
            import yaml
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    previous_config = yaml.safe_load(f)
            except Exception:
                return False
        
        # Get current and previous providers
        current_provider = self.config.get('llm', {}).get('provider')
        previous_provider = previous_config.get('llm', {}).get('provider')
        
        # Check if provider changed
        if previous_provider and current_provider != previous_provider:
            return True
        
        return False
    
    def check_reindex_required(self) -> Optional[str]:
        """
        Check if reindexing is required due to configuration changes.
        
        Returns:
            Warning message if reindexing is required, None otherwise.
        """
        if self.detect_provider_change():
            return (
                "WARNING:  WARNING: LLM provider has changed!\n"
                "   Different providers use different embedding dimensions.\n"
                "   You must run 'docrag reindex' to rebuild the vector database."
            )
        
        return None
