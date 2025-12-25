"""
MCP server for DocRAG Kit.

This module implements a Model Context Protocol (MCP) server that provides
semantic search capabilities over project documentation. It integrates with
Kiro AI to enable intelligent question-answering about project documentation.

The server provides three main tools:
1. search_docs: Fast semantic search returning relevant document fragments
   - Best for agents that need to quickly find specific documentation
   - Returns raw document chunks with source files
   - No LLM processing, just vector similarity search
   
2. answer_question: AI-generated comprehensive answers
   - Best for complex questions requiring synthesis and explanation
   - Uses LLM to generate contextual answers from multiple sources
   - Includes source attribution
   
3. list_indexed_docs: List all indexed documentation files

Requirements covered:
- 5.1-5.12: MCP server functionality
- 10.1-10.6: Error handling and user feedback

Usage:
    python -m docrag.mcp_server
    
    Or run via Kiro AI after configuration with `docrag mcp-config`
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from .config_manager import ConfigManager
from .vector_db import VectorDBManager


class MCPServer:
    """MCP server for DocRAG Kit integration with Kiro AI."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize MCP server.
        
        Args:
            config_path: Path to .docrag directory. Defaults to current directory.
        """
        # Determine project root
        if config_path:
            self.project_root = Path(config_path).parent if Path(config_path).name == ".docrag" else Path(config_path)
        else:
            self.project_root = Path.cwd()
        
        # Debug: Log paths for troubleshooting
        import sys
        print(f"DEBUG MCP: Current working directory: {Path.cwd()}", file=sys.stderr)
        print(f"DEBUG MCP: Project root: {self.project_root}", file=sys.stderr)
        print(f"DEBUG MCP: Config path: {self.project_root / '.docrag' / 'config.yaml'}", file=sys.stderr)
        print(f"DEBUG MCP: Vector DB path: {self.project_root / '.docrag' / 'vectordb'}", file=sys.stderr)
        
        # Load environment variables
        load_dotenv(self.project_root / ".env")
        
        # Load configuration
        self.config_manager = ConfigManager(self.project_root)
        config_obj = self.config_manager.load_config()
        
        if not config_obj:
            raise ValueError(
                "ERROR: Configuration not found.\n"
                "   Run 'docrag init' to initialize DocRAG in this project."
            )
        
        self.config = config_obj.to_dict()
        
        # Initialize vector database manager
        self.vector_db = VectorDBManager(self.config, self.project_root)
        
        # QA chain will be lazily loaded
        self._qa_chain = None
        
        # Initialize MCP server
        self.server = Server("docrag-kit")
        
        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register MCP tools."""
        
        @self.server.list_tools()
        async def list_tools() -> list[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="search_docs",
                    description="Fast semantic search returning relevant document fragments. "
                                "Best for agents that need to quickly find and read specific documentation sections. "
                                "Быстрый семантический поиск с фрагментами документов.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Question or topic to search for in the documentation. "
                                              "Вопрос или тема для поиска в документации."
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (1-10). Default: 3",
                                "default": 3,
                                "minimum": 1,
                                "maximum": 10
                            }
                        },
                        "required": ["question"]
                    }
                ),
                types.Tool(
                    name="answer_question",
                    description="Get a comprehensive AI-generated answer based on project documentation. "
                                "Uses LLM to synthesize information from multiple sources. "
                                "Best for complex questions requiring context and explanation. "
                                "Получить полный ответ на основе документации проекта с использованием LLM.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Question to answer using project documentation. "
                                              "Вопрос для ответа на основе документации проекта."
                            },
                            "include_sources": {
                                "type": "boolean",
                                "description": "Include source file names in the response. "
                                              "Включить имена исходных файлов в ответ.",
                                "default": True
                            }
                        },
                        "required": ["question"]
                    }
                ),
                types.Tool(
                    name="list_indexed_docs",
                    description="List all indexed documents in the project. "
                                "Список всех проиндексированных документов в проекте.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="reindex_docs",
                    description="Reindex project documentation when documents have been updated. "
                                "Automatically detects changes and performs smart reindexing. "
                                "Переиндексировать документацию при обновлении файлов с автоматическим обнаружением изменений.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "force": {
                                "type": "boolean",
                                "description": "Force full reindexing even if no changes detected. Default: false",
                                "default": False
                            },
                            "check_only": {
                                "type": "boolean", 
                                "description": "Only check if reindexing is needed without performing it. Default: false",
                                "default": False
                            }
                        },
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
            """Handle tool calls."""
            try:
                if name == "search_docs":
                    result = await self.handle_search_docs(
                        question=arguments.get("question", ""),
                        max_results=arguments.get("max_results", 3)
                    )
                    return [types.TextContent(type="text", text=result)]
                
                elif name == "answer_question":
                    result = await self.handle_answer_question(
                        question=arguments.get("question", ""),
                        include_sources=arguments.get("include_sources", True)
                    )
                    return [types.TextContent(type="text", text=result)]
                
                elif name == "list_indexed_docs":
                    result = await self.handle_list_docs()
                    return [types.TextContent(type="text", text=result)]
                
                elif name == "reindex_docs":
                    result = await self.handle_reindex_docs(
                        force=arguments.get("force", False),
                        check_only=arguments.get("check_only", False)
                    )
                    return [types.TextContent(type="text", text=result)]
                
                else:
                    error_msg = f"ERROR: Unknown tool: {name}"
                    return [types.TextContent(type="text", text=error_msg)]
            
            except Exception as e:
                error_msg = self._format_error(e)
                return [types.TextContent(type="text", text=error_msg)]

    def get_qa_chain(self):
        """
        Lazy load QA chain.
        
        Returns:
            Tuple of (chain, retriever) for executing queries.
        
        Raises:
            ValueError: If database doesn't exist or API key is missing.
        """
        if self._qa_chain is not None:
            return self._qa_chain
        
        # Get retriever
        try:
            retriever = self.vector_db.get_retriever()
        except ValueError as e:
            raise ValueError(str(e))
        
        # Initialize LLM based on provider
        llm_config = self.config.get('llm', {})
        provider = llm_config.get('provider', 'openai')
        llm_model = llm_config.get('llm_model')
        temperature = llm_config.get('temperature', 0.3)
        
        if provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError(
                    "ERROR: OpenAI API key not found.\n"
                    "   Add OPENAI_API_KEY to your .env file.\n"
                    "   Get your API key from: https://platform.openai.com/api-keys"
                )
            
            llm = ChatOpenAI(
                model=llm_model or 'gpt-4o-mini',
                temperature=temperature,
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
            
            llm = ChatGoogleGenerativeAI(
                model=llm_model or 'gemini-1.5-flash',
                temperature=temperature,
                google_api_key=api_key
            )
        
        else:
            raise ValueError(f"ERROR: Unsupported provider: {provider}")
        
        # Get prompt template
        prompt_config = self.config.get('prompt', {})
        prompt_template_str = prompt_config.get('template', '')
        
        # Create prompt template
        prompt = PromptTemplate(
            template=prompt_template_str,
            input_variables=["context", "question"]
        )
        
        # Helper function to format documents
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # Create QA chain using LCEL (LangChain Expression Language)
        # This is the new LangChain 1.x pattern
        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        # Store both chain and retriever for source document retrieval
        self._qa_chain = (chain, retriever)
        
        return self._qa_chain

    async def handle_search_docs(self, question: str, max_results: int = 3) -> str:
        """
        Handle search_docs tool call - returns relevant document fragments.
        
        Args:
            question: Question to search for.
            max_results: Maximum number of results to return (1-10).
        
        Returns:
            Formatted search results with document fragments and metadata.
        
        Raises:
            ValueError: If question is empty or database errors occur.
        """
        if not question or not question.strip():
            raise ValueError("ERROR: Question cannot be empty")
        
        # Validate max_results
        max_results = max(1, min(10, max_results))
        
        # Check if reindexing might be needed (non-blocking)
        staleness_warning = await self._check_database_staleness()
        
        # Get retriever
        try:
            _, retriever = self.get_qa_chain()
        except ValueError as e:
            raise ValueError(str(e))
        
        # Execute search
        try:
            # Get relevant documents with scores
            source_docs = retriever.invoke(question)
            
            if not source_docs:
                return "SEARCH: No relevant documents found for your query."
            
            # Limit results
            source_docs = source_docs[:max_results]
            
            # Format results
            results = []
            results.append(f"SEARCH: Found {len(source_docs)} relevant document(s):\n")
            
            for idx, doc in enumerate(source_docs, 1):
                metadata = doc.metadata
                content = doc.page_content
                
                # Extract source file
                source_file = "Unknown"
                if 'source_file' in metadata:
                    source_file = metadata['source_file']
                elif 'source' in metadata:
                    source_path = Path(metadata['source'])
                    source_file = str(source_path.relative_to(self.project_root))
                
                # Truncate content if too long
                max_content_length = 800
                if len(content) > max_content_length:
                    content = content[:max_content_length] + "..."
                
                # Format result
                results.append(f"--- Result {idx} ---")
                results.append(f"SOURCE: {source_file}")
                results.append(f"\n{content}\n")
            
            # Add staleness warning if needed
            final_result = "\n".join(results)
            if staleness_warning:
                final_result += staleness_warning
            
            return final_result
        
        except Exception as e:
            raise ValueError(f"ERROR: Search failed: {str(e)}")

    async def handle_answer_question(self, question: str, include_sources: bool = True) -> str:
        """
        Handle answer_question tool call - returns AI-generated answer.
        
        Args:
            question: Question to answer.
            include_sources: Whether to include source file names in response.
        
        Returns:
            AI-generated answer, optionally with source files.
        
        Raises:
            ValueError: If question is empty or database/API errors occur.
        """
        if not question or not question.strip():
            raise ValueError("ERROR: Question cannot be empty")
        
        # Check if reindexing might be needed (non-blocking)
        staleness_warning = await self._check_database_staleness()
        
        # Get QA chain and retriever
        chain, retriever = self.get_qa_chain()
        
        # Execute query
        try:
            # Invoke the chain with the question
            answer = chain.invoke(question)
            
            # Append sources if requested
            if include_sources:
                # Get source documents from retriever
                source_docs = retriever.invoke(question)
                if source_docs:
                    # Extract unique source files
                    source_files = set()
                    for doc in source_docs:
                        metadata = doc.metadata
                        if 'source_file' in metadata:
                            source_files.add(metadata['source_file'])
                        elif 'source' in metadata:
                            source_path = Path(metadata['source'])
                            try:
                                rel_path = source_path.relative_to(self.project_root)
                                source_files.add(str(rel_path))
                            except ValueError:
                                source_files.add(source_path.name)
                    
                    if source_files:
                        sources_list = sorted(list(source_files))
                        answer += f"\n\nSOURCES: Sources:\n" + "\n".join(f"  • {s}" for s in sources_list)
            
            # Add staleness warning if needed
            if staleness_warning:
                answer += staleness_warning
            
            return answer
        
        except Exception as e:
            raise ValueError(f"ERROR: Query failed: {str(e)}")

    async def handle_list_docs(self) -> str:
        """
        Handle list_indexed_docs tool call.
        
        Returns:
            Formatted list of indexed documents.
        
        Raises:
            ValueError: If database doesn't exist.
        """
        try:
            documents = self.vector_db.list_documents()
            
            if not documents:
                return "DOCS: No documents indexed yet.\n   Run 'docrag index' to index your documentation."
            
            # Format document list
            doc_list = "\n".join(f"- {doc}" for doc in documents)
            return f"SOURCES: Indexed Documents ({len(documents)}):\n\n{doc_list}"
        
        except ValueError as e:
            raise ValueError(str(e))

    async def handle_reindex_docs(self, force: bool = False, check_only: bool = False) -> str:
        """
        Handle reindex_docs tool call - smart reindexing with change detection.
        
        Args:
            force: Force full reindexing even if no changes detected.
            check_only: Only check if reindexing is needed without performing it.
        
        Returns:
            Status message about reindexing operation.
        
        Raises:
            ValueError: If configuration or database errors occur.
        """
        try:
            from .document_processor import DocumentProcessor
            import time
            import os
            
            # Check if database exists
            db_path = self.project_root / ".docrag" / "vectordb"
            if not db_path.exists():
                if check_only:
                    return "REINDEX: Database not found - full indexing needed.\n   Run with force=false to create initial index."
                
                # No database exists, need initial indexing
                return await self._perform_full_reindex("Initial indexing (no database found)")
            
            # Get database creation time
            try:
                db_created_time = os.path.getctime(db_path)
            except:
                db_created_time = 0
            
            # Scan for document changes
            doc_processor = DocumentProcessor(self.config)
            
            # Get list of files that would be indexed
            files_to_check = []
            for directory in self.config.get('indexing', {}).get('directories', ['.']):
                dir_path = self.project_root / directory
                if dir_path.exists():
                    extensions = self.config.get('indexing', {}).get('extensions', ['.md', '.txt'])
                    for ext in extensions:
                        files_to_check.extend(dir_path.rglob(f"*{ext}"))
            
            # Check for changes
            changes_detected = False
            newer_files = []
            
            for file_path in files_to_check:
                try:
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime > db_created_time:
                        changes_detected = True
                        newer_files.append(str(file_path.relative_to(self.project_root)))
                except:
                    continue
            
            # Check if force reindexing requested
            if force:
                if check_only:
                    return "REINDEX: Force reindexing requested - will rebuild entire database."
                return await self._perform_full_reindex("Force reindexing requested")
            
            # Report findings
            if check_only:
                if changes_detected:
                    files_list = "\n".join(f"  • {f}" for f in newer_files[:10])
                    if len(newer_files) > 10:
                        files_list += f"\n  • ... and {len(newer_files) - 10} more files"
                    
                    return f"REINDEX: Changes detected in {len(newer_files)} file(s):\n{files_list}\n\nReindexing recommended."
                else:
                    return "REINDEX: No changes detected - database is up to date."
            
            # Perform reindexing if changes detected
            if changes_detected:
                files_summary = f"{len(newer_files)} file(s) changed"
                return await self._perform_full_reindex(f"Changes detected: {files_summary}")
            else:
                return "REINDEX: No changes detected - database is already up to date."
        
        except Exception as e:
            raise ValueError(f"Reindexing failed: {str(e)}")

    async def _perform_full_reindex(self, reason: str) -> str:
        """
        Perform full reindexing operation with aggressive MCP-safe database handling.
        
        Args:
            reason: Reason for reindexing (for user feedback).
        
        Returns:
            Status message about completed reindexing.
        """
        try:
            from .document_processor import DocumentProcessor
            import time
            import os
            import shutil
            
            # Step 1: Aggressive cleanup of existing database
            db_path = self.project_root / ".docrag" / "vectordb"
            if db_path.exists():
                # Force close any existing database connections
                self.vector_db._close_existing_connections()
                self._qa_chain = None  # Clear cached chain immediately
                
                # Wait for connections to close
                time.sleep(1.0)
                
                # Try multiple cleanup strategies
                success = False
                for attempt in range(5):  # More aggressive retry count
                    try:
                        # Strategy 1: Normal deletion
                        if attempt == 0:
                            self.vector_db.delete_database()
                            success = True
                            break
                        
                        # Strategy 2: Force remove with longer wait
                        elif attempt == 1:
                            time.sleep(2.0)
                            if db_path.exists():
                                shutil.rmtree(db_path, ignore_errors=True)
                            if not db_path.exists():
                                success = True
                                break
                        
                        # Strategy 3: Remove individual files
                        elif attempt == 2:
                            if db_path.exists():
                                for file_path in db_path.rglob("*"):
                                    if file_path.is_file():
                                        try:
                                            file_path.unlink()
                                        except:
                                            pass
                                # Remove empty directories
                                try:
                                    shutil.rmtree(db_path, ignore_errors=True)
                                except:
                                    pass
                            if not db_path.exists():
                                success = True
                                break
                        
                        # Strategy 4: Create new database in temporary location first
                        elif attempt == 3:
                            temp_db_path = db_path.parent / f"vectordb_temp_{int(time.time())}"
                            break  # Will use temp strategy below
                        
                        # Strategy 5: Last resort - rename old database
                        else:
                            if db_path.exists():
                                backup_path = db_path.parent / f"vectordb_backup_{int(time.time())}"
                                try:
                                    db_path.rename(backup_path)
                                    success = True
                                    break
                                except:
                                    pass
                    
                    except Exception as e:
                        if attempt < 4:
                            time.sleep(1.0 * (attempt + 1))
                        continue
                
                if not success and attempt == 3:
                    # Use temporary database strategy
                    temp_db_path = db_path.parent / f"vectordb_temp_{int(time.time())}"
                    use_temp_strategy = True
                else:
                    use_temp_strategy = False
            else:
                use_temp_strategy = False
            
            # Step 2: Process documents
            doc_processor = DocumentProcessor(self.config)
            chunks, stats = doc_processor.process(self.project_root)
            
            if stats['files_found'] == 0:
                return "REINDEX: No files found to index.\n   Check your configuration directories and extensions."
            
            # Step 3: Create new database with MCP-safe method
            if use_temp_strategy:
                # Create in temporary location first
                original_db_path = self.vector_db.db_path
                self.vector_db.db_path = temp_db_path
                
                try:
                    self.vector_db.create_database(chunks, show_progress=False)
                    
                    # Move temporary database to final location
                    if db_path.exists():
                        shutil.rmtree(db_path, ignore_errors=True)
                    
                    temp_db_path.rename(db_path)
                    self.vector_db.db_path = original_db_path
                    
                except Exception as e:
                    # Cleanup temporary database
                    self.vector_db.db_path = original_db_path
                    if temp_db_path.exists():
                        shutil.rmtree(temp_db_path, ignore_errors=True)
                    raise e
            else:
                # Direct creation
                self.vector_db.create_database(chunks, show_progress=False)
            
            # Step 4: Reset cached QA chain
            self._qa_chain = None
            
            # Step 5: Verify database was created successfully
            if not db_path.exists():
                raise Exception("Database creation verification failed - database directory not found")
            
            # Return success message
            return (f"REINDEX: Reindexing completed successfully!\n"
                   f"   Reason: {reason}\n"
                   f"   Files processed: {stats['files_processed']}\n"
                   f"   Chunks created: {stats['chunks_created']}\n"
                   f"   Total characters: {stats['total_characters']:,}")
        
        except Exception as e:
            error_msg = str(e)
            
            # Provide helpful error message for common database issues
            if "unable to open database file" in error_msg or "database is locked" in error_msg:
                return (f"REINDEX: Database access error persists despite v0.1.8 improvements.\n"
                       f"   This appears to be a deeper ChromaDB/SQLite locking issue in MCP context.\n"
                       f"   WORKAROUND: Use 'docrag reindex' in terminal for now.\n"
                       f"   We're investigating this specific MCP process isolation issue.\n"
                       f"   Technical details: {error_msg}")
            
            raise ValueError(f"Reindexing operation failed: {error_msg}")

    async def _check_database_staleness(self) -> str:
        """
        Check if database might be stale (non-blocking check).
        
        Returns:
            Warning message if database might be stale, empty string otherwise.
        """
        try:
            import os
            
            # Check if database exists
            db_path = self.project_root / ".docrag" / "vectordb"
            if not db_path.exists():
                return ""
            
            # Get database creation time
            try:
                db_created_time = os.path.getctime(db_path)
            except:
                return ""
            
            # Quick check for any recently modified files
            recent_files = 0
            for directory in self.config.get('indexing', {}).get('directories', ['.']):
                dir_path = self.project_root / directory
                if dir_path.exists():
                    extensions = self.config.get('indexing', {}).get('extensions', ['.md', '.txt'])
                    for ext in extensions:
                        for file_path in dir_path.rglob(f"*{ext}"):
                            try:
                                if os.path.getmtime(file_path) > db_created_time:
                                    recent_files += 1
                                    if recent_files >= 3:  # Stop early for performance
                                        break
                            except:
                                continue
                        if recent_files >= 3:
                            break
                if recent_files >= 3:
                    break
            
            if recent_files > 0:
                return f"\nNOTE: {recent_files}+ files may have been updated since last indexing. Consider using 'reindex_docs' tool for latest content."
            
            return ""
        
        except:
            return ""

    def _format_error(self, error: Exception) -> str:
        """
        Format error message for user-friendly display.
        
        Args:
            error: Exception to format.
        
        Returns:
            Formatted error message.
        """
        error_msg = str(error)
        
        # If error already has emoji and formatting, return as-is
        if error_msg.startswith("ERROR:"):
            return error_msg
        
        # Otherwise, format it
        return f"ERROR: Error: {error_msg}"

    async def run(self):
        """Run the MCP server with stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point for MCP server."""
    try:
        # Determine project root from current directory
        server = MCPServer()
        await server.run()
    except Exception as e:
        print(f"ERROR: Failed to start MCP server: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
