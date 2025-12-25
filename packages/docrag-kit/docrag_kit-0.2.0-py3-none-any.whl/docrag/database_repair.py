"""Database repair utilities for DocRAG Kit."""

import os
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class DatabaseRepair:
    """Handles database repair and process management for DocRAG Kit."""
    
    def __init__(self, project_root: Path):
        """
        Initialize database repair utility.
        
        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root)
        self.docrag_dir = self.project_root / ".docrag"
        self.vectordb_path = self.docrag_dir / "vectordb"
        self.config_path = self.docrag_dir / "config.yaml"
    
    def diagnose_issues(self) -> Tuple[List[str], List[str]]:
        """
        Diagnose database and process issues.
        
        Returns:
            Tuple of (critical_issues, warnings)
        """
        critical_issues = []
        warnings = []
        
        # Check if DocRAG is initialized
        if not self.docrag_dir.exists():
            critical_issues.append("DocRAG not initialized (.docrag/ directory missing)")
            return critical_issues, warnings
        
        if not self.config_path.exists():
            critical_issues.append("Configuration file missing (.docrag/config.yaml)")
            return critical_issues, warnings
        
        # Check vector database directory
        if not self.vectordb_path.exists():
            warnings.append("Vector database directory doesn't exist")
            return critical_issues, warnings
        
        # Check directory permissions
        if not os.access(self.vectordb_path, os.W_OK):
            critical_issues.append("Vector database directory is not writable")
        
        # Check for database files and their permissions
        db_files = list(self.vectordb_path.rglob("*.sqlite*")) + list(self.vectordb_path.rglob("*.db"))
        
        for db_file in db_files:
            # Check file permissions
            if not os.access(db_file, os.W_OK):
                critical_issues.append(f"Database file {db_file.name} is not writable (readonly database)")
            
            # Check for database corruption
            try:
                conn = sqlite3.connect(str(db_file))
                conn.execute("PRAGMA integrity_check;")
                conn.close()
            except sqlite3.DatabaseError as e:
                if "readonly database" in str(e).lower():
                    critical_issues.append(f"Database {db_file.name} is readonly")
                elif "locked" in str(e).lower():
                    critical_issues.append(f"Database {db_file.name} is locked by another process")
                else:
                    critical_issues.append(f"Database {db_file.name} is corrupted: {e}")
            except Exception as e:
                warnings.append(f"Could not check database {db_file.name}: {e}")
        
        # Check for lock files
        lock_files = (
            list(self.vectordb_path.rglob("*.db-wal")) + 
            list(self.vectordb_path.rglob("*.db-shm")) +
            list(self.vectordb_path.rglob("*.lock"))
        )
        
        if lock_files:
            warnings.append(f"Found {len(lock_files)} database lock files")
        
        # Check for conflicting processes
        conflicting_processes = self.find_conflicting_processes()
        if conflicting_processes:
            critical_issues.append(f"Found {len(conflicting_processes)} conflicting MCP server processes")
        
        # Check disk space
        try:
            statvfs = os.statvfs(str(self.docrag_dir))
            free_bytes = statvfs.f_frsize * statvfs.f_bavail
            free_mb = free_bytes / (1024 * 1024)
            
            if free_mb < 100:  # Less than 100MB
                warnings.append(f"Low disk space ({free_mb:.1f} MB available)")
        except Exception:
            pass
        
        return critical_issues, warnings
    
    def find_conflicting_processes(self) -> List[dict]:
        """
        Find running processes that might conflict with DocRAG.
        
        Returns:
            List of process information dictionaries
        """
        conflicting_processes = []
        
        if not PSUTIL_AVAILABLE:
            # Fallback to subprocess approach
            try:
                result = subprocess.run(['pgrep', '-f', 'docrag.mcp_server'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid:
                            conflicting_processes.append({
                                'pid': int(pid),
                                'name': 'python',
                                'cmdline': f'python -m docrag.mcp_server (PID: {pid})'
                            })
            except Exception:
                pass
            return conflicting_processes
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('docrag.mcp_server' in arg for arg in cmdline):
                        conflicting_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': ' '.join(cmdline)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        
        return conflicting_processes
    
    def kill_conflicting_processes(self) -> bool:
        """
        Kill conflicting MCP server processes.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conflicting_processes = self.find_conflicting_processes()
            
            if not PSUTIL_AVAILABLE:
                # Fallback to subprocess approach
                try:
                    subprocess.run(['pkill', '-f', 'docrag.mcp_server'], 
                                 capture_output=True, timeout=10)
                    return True
                except Exception:
                    return False
            
            for proc_info in conflicting_processes:
                try:
                    proc = psutil.Process(proc_info['pid'])
                    proc.terminate()
                    
                    # Wait for process to terminate
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        # Force kill if it doesn't terminate gracefully
                        proc.kill()
                        proc.wait(timeout=2)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return True
        except Exception:
            return False
    
    def fix_readonly_database(self) -> bool:
        """
        Fix readonly database issues by correcting file permissions.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Fix directory permissions
            if self.vectordb_path.exists():
                os.chmod(self.vectordb_path, 0o755)
                
                # Fix permissions for all files and subdirectories
                for root, dirs, files in os.walk(self.vectordb_path):
                    # Fix directory permissions
                    for d in dirs:
                        dir_path = os.path.join(root, d)
                        os.chmod(dir_path, 0o755)
                    
                    # Fix file permissions
                    for f in files:
                        file_path = os.path.join(root, f)
                        os.chmod(file_path, 0o644)
            
            return True
        except Exception:
            return False
    
    def fix_permissions(self) -> bool:
        """
        Fix directory and file permissions.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Fix .docrag directory permissions
            if self.docrag_dir.exists():
                os.chmod(self.docrag_dir, 0o755)
            
            # Fix vectordb directory permissions
            if self.vectordb_path.exists():
                return self.fix_readonly_database()
            
            return True
        except Exception:
            return False
    
    def remove_lock_files(self) -> bool:
        """
        Remove database lock files.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            lock_patterns = ["*.db-wal", "*.db-shm", "*.lock"]
            
            for pattern in lock_patterns:
                lock_files = list(self.vectordb_path.rglob(pattern))
                for lock_file in lock_files:
                    try:
                        lock_file.unlink()
                    except Exception:
                        continue
            
            return True
        except Exception:
            return False
    
    def rebuild_database(self) -> bool:
        """
        Remove corrupted database to force rebuild.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.vectordb_path.exists():
                shutil.rmtree(self.vectordb_path)
            return True
        except Exception:
            return False
    
    def get_repair_recommendations(self, critical_issues: List[str], warnings: List[str]) -> List[str]:
        """
        Get repair recommendations based on diagnosed issues.
        
        Args:
            critical_issues: List of critical issues
            warnings: List of warnings
        
        Returns:
            List of recommended actions
        """
        recommendations = []
        
        if any("not initialized" in issue.lower() for issue in critical_issues):
            recommendations.append("Run 'docrag init' to initialize DocRAG")
        
        if any("readonly" in issue.lower() for issue in critical_issues):
            recommendations.append("Fix file permissions with 'docrag fix-database'")
        
        if any("locked" in issue.lower() for issue in critical_issues):
            recommendations.append("Kill conflicting processes and remove lock files")
        
        if any("corrupted" in issue.lower() for issue in critical_issues):
            recommendations.append("Rebuild database with 'rm -rf .docrag/vectordb && docrag index'")
        
        if any("conflicting" in issue.lower() for issue in critical_issues):
            recommendations.append("Stop conflicting MCP server processes")
        
        if any("lock files" in warning.lower() for warning in warnings):
            recommendations.append("Remove database lock files")
        
        if any("disk space" in warning.lower() for warning in warnings):
            recommendations.append("Free up disk space")
        
        if not recommendations:
            recommendations.append("Run 'docrag doctor' for detailed diagnosis")
        
        return recommendations
    
    def comprehensive_repair(self) -> Tuple[List[str], List[str]]:
        """
        Perform comprehensive repair of database issues.
        
        Returns:
            Tuple of (fixes_applied, remaining_issues)
        """
        fixes_applied = []
        
        # Step 1: Kill conflicting processes
        conflicting_processes = self.find_conflicting_processes()
        if conflicting_processes:
            if self.kill_conflicting_processes():
                fixes_applied.append(f"Killed {len(conflicting_processes)} conflicting processes")
        
        # Step 2: Remove lock files
        lock_files = (
            list(self.vectordb_path.rglob("*.db-wal")) + 
            list(self.vectordb_path.rglob("*.db-shm")) +
            list(self.vectordb_path.rglob("*.lock"))
        )
        
        if lock_files:
            if self.remove_lock_files():
                fixes_applied.append("Removed database lock files")
        
        # Step 3: Fix permissions
        if self.fix_permissions():
            fixes_applied.append("Fixed file and directory permissions")
        
        # Step 4: Check if database is still problematic
        critical_issues, warnings = self.diagnose_issues()
        
        # Step 5: If database is still corrupted, offer to rebuild
        if any("corrupted" in issue.lower() or "readonly" in issue.lower() for issue in critical_issues):
            # This will be handled by the CLI with user confirmation
            pass
        
        return fixes_applied, critical_issues