"""Document processing for DocRAG Kit."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import fnmatch
import chardet
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter
)


class DocumentProcessor:
    """Processes documents for indexing."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize document processor.
        
        Args:
            config: Configuration dictionary containing indexing and chunking settings.
        """
        self.config = config
        self.indexing_config = config.get('indexing', {})
        self.chunking_config = config.get('chunking', {})
        self.project_name = config.get('project', {}).get('name', 'unknown')
        
        # Initialize text splitters
        self.text_splitters = self._init_splitters()

    def _init_splitters(self) -> Dict[str, Any]:
        """
        Initialize text splitters for different file types.
        
        Returns:
            Dictionary mapping file types to text splitters.
        """
        chunk_size = self.chunking_config.get('chunk_size', 1000)
        chunk_overlap = self.chunking_config.get('chunk_overlap', 200)
        
        return {
            'markdown': MarkdownTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            ),
            'code': RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", " ", ""]
            ),
            'text': CharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separator="\n"
            )
        }

    def scan_files(self, project_root: Path) -> List[Path]:
        """
        Scan directories and return list of files to index.
        
        Args:
            project_root: Root directory of the project.
        
        Returns:
            List of Path objects for files to be indexed.
        """
        directories = self.indexing_config.get('directories', [])
        extensions = self.indexing_config.get('extensions', [])
        exclude_patterns = self.indexing_config.get('exclude_patterns', [])
        
        files_to_index = []
        
        for directory in directories:
            dir_path = project_root / directory
            
            # Handle single files (like README.md)
            if dir_path.is_file():
                if self._should_include_file(dir_path, extensions, exclude_patterns):
                    files_to_index.append(dir_path)
                continue
            
            # Handle directories
            if not dir_path.exists() or not dir_path.is_dir():
                continue
            
            # Recursively scan directory
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    if self._should_include_file(file_path, extensions, exclude_patterns):
                        files_to_index.append(file_path)
        
        return sorted(files_to_index)

    def _should_include_file(
        self, 
        file_path: Path, 
        extensions: List[str], 
        exclude_patterns: List[str]
    ) -> bool:
        """
        Check if file should be included based on extension and exclusion patterns.
        
        Args:
            file_path: Path to the file.
            extensions: List of allowed file extensions.
            exclude_patterns: List of exclusion patterns.
        
        Returns:
            True if file should be included, False otherwise.
        """
        # Check extension
        if extensions:
            if not any(str(file_path).endswith(ext) for ext in extensions):
                return False
        
        # Check exclusion patterns
        file_str = str(file_path)
        for pattern in exclude_patterns:
            # Support both glob patterns and simple string matching
            if fnmatch.fnmatch(file_str, f"*{pattern}*"):
                return False
            if pattern in file_str:
                return False
        
        return True

    def load_documents(self, files: List[Path]) -> List[Document]:
        """
        Load documents from files.
        
        Args:
            files: List of file paths to load.
        
        Returns:
            List of LangChain Document objects.
        """
        documents = []
        
        for file_path in files:
            try:
                content = self._load_file_content(file_path)
                
                # Create LangChain Document
                doc = Document(
                    page_content=content,
                    metadata={
                        'source': str(file_path),
                        'source_file': file_path.name,
                        'file_type': file_path.suffix
                    }
                )
                documents.append(doc)
                
            except Exception as e:
                # Log warning and continue with other files
                print(f"WARNING:  Warning: Failed to load {file_path}: {e}")
                continue
        
        return documents

    def _load_file_content(self, file_path: Path) -> str:
        """
        Load file content with encoding detection.
        
        Args:
            file_path: Path to the file.
        
        Returns:
            File content as string.
        
        Raises:
            Exception: If file cannot be read.
        """
        # Try UTF-8 first
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
            
            # Try detected encoding
            if encoding:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except Exception:
                    pass
            
            # Last resort: read as binary and decode with errors='ignore'
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks.
        
        Args:
            documents: List of Document objects to chunk.
        
        Returns:
            List of chunked Document objects.
        """
        chunked_documents = []
        
        for doc in documents:
            # Determine splitter based on file type
            file_type = doc.metadata.get('file_type', '')
            
            if file_type == '.md':
                splitter = self.text_splitters['markdown']
            elif file_type in ['.py', '.php', '.swift', '.js', '.java', '.cpp', '.c', '.go']:
                splitter = self.text_splitters['code']
            else:
                splitter = self.text_splitters['text']
            
            # Split document
            chunks = splitter.split_documents([doc])
            chunked_documents.extend(chunks)
        
        return chunked_documents

    def add_metadata(self, chunks: List[Document]) -> List[Document]:
        """
        Add metadata to chunks.
        
        Args:
            chunks: List of Document chunks.
        
        Returns:
            List of Document chunks with added metadata.
        """
        for i, chunk in enumerate(chunks):
            # Add chunk_id
            chunk.metadata['chunk_id'] = i
            
            # Add project_name
            chunk.metadata['project_name'] = self.project_name
            
            # Ensure source_file is present (should be from load_documents)
            if 'source_file' not in chunk.metadata and 'source' in chunk.metadata:
                source_path = Path(chunk.metadata['source'])
                chunk.metadata['source_file'] = source_path.name
        
        return chunks

    def process(self, project_root: Path) -> tuple[List[Document], Dict[str, Any]]:
        """
        Complete document processing pipeline.
        
        Args:
            project_root: Root directory of the project.
        
        Returns:
            Tuple of (processed documents, statistics dictionary).
        """
        # Scan files
        files = self.scan_files(project_root)
        
        if not files:
            return [], {
                'files_found': 0,
                'files_processed': 0,
                'chunks_created': 0,
                'total_characters': 0
            }
        
        # Load documents
        documents = self.load_documents(files)
        
        # Chunk documents
        chunks = self.chunk_documents(documents)
        
        # Add metadata
        chunks = self.add_metadata(chunks)
        
        # Calculate statistics
        total_chars = sum(len(chunk.page_content) for chunk in chunks)
        
        stats = {
            'files_found': len(files),
            'files_processed': len(documents),
            'chunks_created': len(chunks),
            'total_characters': total_chars
        }
        
        return chunks, stats
