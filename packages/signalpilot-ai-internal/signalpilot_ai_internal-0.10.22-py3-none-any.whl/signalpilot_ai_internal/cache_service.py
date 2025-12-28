"""
Persistent caching service for SignalPilot AI.
Handles OS-specific cache directory management and robust file operations.
"""

import hashlib
import json
import os
import platform
import shutil
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


class CacheDirectoryManager:
    """OS-specific cache directory management with fallbacks"""
    
    @staticmethod
    def get_cache_directories() -> list[Path]:
        """Get ordered list of cache directories from most to least preferred"""
        system = platform.system().lower()
        directories = []
        
        try:
            if system == "windows":
                # Primary: AppData\Local
                appdata_local = os.environ.get('LOCALAPPDATA')
                if appdata_local:
                    directories.append(Path(appdata_local) / "SignalPilotAI" / "Cache")
                
                # Secondary: AppData\Roaming
                appdata_roaming = os.environ.get('APPDATA')
                if appdata_roaming:
                    directories.append(Path(appdata_roaming) / "SignalPilotAI" / "Cache")
                
                # Tertiary: User profile
                userprofile = os.environ.get('USERPROFILE')
                if userprofile:
                    directories.append(Path(userprofile) / ".signalpilot-cache")
                    
            elif system == "darwin":  # macOS
                # Primary: ~/Library/Caches
                home = Path.home()
                directories.append(home / "Library" / "Caches" / "SignalPilotAI")
                
                # Secondary: ~/Library/Application Support
                directories.append(home / "Library" / "Application Support" / "SignalPilotAI")
                
                # Tertiary: ~/.signalpilot-cache
                directories.append(home / ".signalpilot-cache")
                
            else:  # Linux and other Unix-like
                # Primary: XDG_CACHE_HOME or ~/.cache
                cache_home = os.environ.get('XDG_CACHE_HOME')
                if cache_home:
                    directories.append(Path(cache_home) / "signalpilot-ai-internal")
                else:
                    directories.append(Path.home() / ".cache" / "signalpilot-ai-internal")
                
                # Secondary: XDG_DATA_HOME or ~/.local/share
                data_home = os.environ.get('XDG_DATA_HOME')
                if data_home:
                    directories.append(Path(data_home) / "signalpilot-ai-internal")
                else:
                    directories.append(Path.home() / ".local" / "share" / "signalpilot-ai-internal")
                
                # Tertiary: ~/.signalpilot-cache
                directories.append(Path.home() / ".signalpilot-cache")
            
            # Final fallback: temp directory
            directories.append(Path(tempfile.gettempdir()) / f"signalpilot-ai-internal-{os.getuid() if hasattr(os, 'getuid') else 'user'}")
            
        except Exception as e:
            print(f"Error determining cache directories: {e}")
            # Emergency fallback
            directories.append(Path(tempfile.gettempdir()) / "signalpilot-ai-internal-emergency")
        
        return directories
    
    @staticmethod
    def find_usable_cache_directory() -> Optional[Path]:
        """Find the first usable cache directory with write permissions"""
        for cache_dir in CacheDirectoryManager.get_cache_directories():
            try:
                # Create directory if it doesn't exist
                cache_dir.mkdir(parents=True, exist_ok=True)
                
                # Test write permissions
                test_file = cache_dir / f"test_write_{uuid.uuid4().hex[:8]}.tmp"
                test_file.write_text("test")
                test_file.unlink()
                
                print(f"Using cache directory: {cache_dir}")
                return cache_dir
                
            except Exception as e:
                print(f"Cannot use cache directory {cache_dir}: {e}")
                continue
        
        print("ERROR: No usable cache directory found!")
        return None


class RobustFileOperations:
    """Extremely safe file operations with atomic writes and recovery"""
    
    @staticmethod
    def safe_write_json(file_path: Path, data: Any, max_retries: int = 3) -> bool:
        """Safely write JSON data with atomic operations and backups"""
        # print(f"Attempting to write JSON to: {file_path}")
        
        if not file_path.parent.exists():
            try:
                print(f"Creating parent directory: {file_path.parent}")
                file_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Failed to create directory {file_path.parent}: {e}")
                return False
        
        # Create backup if file exists and is valid, but only if last backup is older than 1 hour
        backup_path = None
        if file_path.exists():
            try:
                # Verify current file is valid JSON before backing up
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                
                # Check if we need a new backup (only if last backup is > 1 hour old)
                should_create_backup = RobustFileOperations._should_create_backup(file_path)
                
                if should_create_backup:
                    backup_path = file_path.with_suffix(f".backup.{int(time.time())}")
                    shutil.copy2(file_path, backup_path)
                    print(f"Created backup: {backup_path}")
                    
                    # Keep only the most recent backup that's at least 1 hour old
                    RobustFileOperations._cleanup_backups(file_path)
                
            except Exception as e:
                print(f"Warning: Could not create backup for {file_path}: {e}")
        
        # Attempt atomic write with retries
        for attempt in range(max_retries):
            temp_path = file_path.with_suffix(f".tmp.{uuid.uuid4().hex[:8]}")
            
            try:
                # Write to temporary file first
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Verify the written data
                with open(temp_path, 'r', encoding='utf-8') as f:
                    verification_data = json.load(f)
                
                # Atomic move to final location
                if platform.system().lower() == "windows":
                    # Windows requires removing target first
                    if file_path.exists():
                        file_path.unlink()
                
                shutil.move(str(temp_path), str(file_path))
                
                return True
                
            except Exception as e:
                print(f"Write attempt {attempt + 1} failed for {file_path}: {e}")
                
                # Clean up temp file
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except:
                    pass
                
                if attempt == max_retries - 1:
                    # Restore from backup if all attempts failed
                    if backup_path and backup_path.exists():
                        try:
                            shutil.copy2(backup_path, file_path)
                            print(f"Restored {file_path} from backup")
                        except Exception as restore_error:
                            print(f"Failed to restore backup: {restore_error}")
                    
                    return False
                
                # Wait before retry
                time.sleep(0.1 * (attempt + 1))
        
        return False
    
    @staticmethod
    def safe_read_json(file_path: Path, default: Any = None) -> Any:
        """Safely read JSON data with corruption recovery"""
        if not file_path.exists():
            return default
        
        # Try reading main file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")
            
            # Try to recover from backup
            backup_files = sorted(
                file_path.parent.glob(f"{file_path.stem}.backup.*"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            for backup_path in backup_files:
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    print(f"Recovered data from backup: {backup_path}")
                    
                    # Try to restore the main file
                    try:
                        shutil.copy2(backup_path, file_path)
                        print(f"Restored {file_path} from {backup_path}")
                    except Exception as restore_error:
                        print(f"Could not restore main file: {restore_error}")
                    
                    return data
                    
                except Exception as backup_error:
                    print(f"Backup {backup_path} also corrupted: {backup_error}")
                    continue
            
            print(f"All recovery attempts failed for {file_path}, using default")
            return default
    
    @staticmethod
    def _should_create_backup(file_path: Path) -> bool:
        """Check if we should create a new backup (only if last backup is > 1 hour old)"""
        try:
            backup_files = sorted(
                file_path.parent.glob(f"{file_path.stem}.backup.*"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            if not backup_files:
                return True  # No backups exist, create first one
            
            # Check if the most recent backup is older than 1 hour
            most_recent_backup = backup_files[0]
            backup_age = time.time() - most_recent_backup.stat().st_mtime
            return backup_age > 3600  # 3600 seconds = 1 hour
            
        except Exception as e:
            print(f"Error checking backup age: {e}")
            return True  # If we can't check, err on the side of creating a backup
    
    @staticmethod
    def _cleanup_backups(file_path: Path, keep_count: int = 1):
        """Keep only the most recent backup file (limit to 1 backup)"""
        try:
            backup_files = sorted(
                file_path.parent.glob(f"{file_path.stem}.backup.*"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Keep only the most recent backup, delete all others
            for old_backup in backup_files[keep_count:]:
                try:
                    old_backup.unlink()
                    print(f"Cleaned up old backup: {old_backup}")
                except Exception as cleanup_error:
                    print(f"Failed to cleanup backup {old_backup}: {cleanup_error}")
                    
        except Exception as e:
            print(f"Error cleaning up backups: {e}")


class PersistentCacheService:
    """Extremely robust persistent caching service for SignalPilot AI"""
    
    def __init__(self):
        self.cache_dir = CacheDirectoryManager.find_usable_cache_directory()
        self.chat_histories_file = None
        self.app_values_file = None
        self._lock = threading.RLock()
        
        if self.cache_dir:
            print(f"Cache service initialized with directory: {self.cache_dir}")
            self.chat_histories_file = self.cache_dir / "chat_histories.json"
            self.app_values_file = self.cache_dir / "app_values.json"
            
            print(f"Chat histories file: {self.chat_histories_file}")
            print(f"App values file: {self.app_values_file}")
            
            # Initialize files if they don't exist
            try:
                self._initialize_cache_files()
                print("Cache files initialized successfully")
            except Exception as e:
                print(f"ERROR: Failed to initialize cache files: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("WARNING: Cache service running without persistent storage!")
    
    def _initialize_cache_files(self):
        """Initialize cache files with empty structures if they don't exist"""
        try:
            if not self.chat_histories_file.exists():
                print(f"Creating new chat histories file: {self.chat_histories_file}")
                success = RobustFileOperations.safe_write_json(self.chat_histories_file, {})
                if not success:
                    print(f"ERROR: Failed to create chat histories file: {self.chat_histories_file}")
                else:
                    print(f"Successfully created chat histories file")
            else:
                print(f"Chat histories file already exists: {self.chat_histories_file}")
            
            if not self.app_values_file.exists():
                print(f"Creating new app values file: {self.app_values_file}")
                success = RobustFileOperations.safe_write_json(self.app_values_file, {})
                if not success:
                    print(f"ERROR: Failed to create app values file: {self.app_values_file}")
                else:
                    print(f"Successfully created app values file")
            else:
                print(f"App values file already exists: {self.app_values_file}")
                
        except Exception as e:
            print(f"ERROR: Exception in _initialize_cache_files: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if cache service is available"""
        return self.cache_dir is not None and self.cache_dir.exists()
    
    def _is_notebook_chat_history_key(self, chat_id: str) -> bool:
        """Check if this is a notebook-specific chat history key"""
        return chat_id.startswith('chat-history-notebook-')
    
    def _get_notebook_chat_history_file(self, chat_id: str) -> Path:
        """Get the file path for a notebook-specific chat history"""
        if not self.cache_dir:
            raise ValueError("Cache directory not available")
        
        # Extract notebook ID from the chat_id
        notebook_id = chat_id.replace('chat-history-notebook-', '')
        filename = f"notebook_chat_{notebook_id}.json"
        return self.cache_dir / filename
    
    # Chat Histories Management
    def get_chat_histories(self) -> Dict[str, Any]:
        """Get all chat histories"""
        with self._lock:
            if not self.chat_histories_file:
                return {}
            return RobustFileOperations.safe_read_json(self.chat_histories_file, {})
    
    def get_chat_history(self, chat_id: str) -> Optional[Any]:
        """Get specific chat history"""
        # Handle notebook-specific chat histories
        if self._is_notebook_chat_history_key(chat_id):
            try:
                notebook_file = self._get_notebook_chat_history_file(chat_id)
                if notebook_file.exists():
                    print(f"Loading notebook chat history from: {notebook_file}")
                    return RobustFileOperations.safe_read_json(notebook_file, None)
                else:
                    print(f"Notebook chat history file does not exist: {notebook_file}")
                    return None
            except Exception as e:
                print(f"ERROR: Failed to get notebook chat history for {chat_id}: {e}")
                return None
        
        # Handle regular chat histories
        histories = self.get_chat_histories()
        return histories.get(chat_id)
    
    def set_chat_history(self, chat_id: str, history: Any) -> bool:
        """Set specific chat history"""
        with self._lock:
            # Handle notebook-specific chat histories
            if self._is_notebook_chat_history_key(chat_id):
                try:
                    notebook_file = self._get_notebook_chat_history_file(chat_id)
                    print(f"Saving notebook chat history to: {notebook_file}")
                    success = RobustFileOperations.safe_write_json(notebook_file, history)
                    if success:
                        print(f"Successfully saved notebook chat history for {chat_id}")
                    else:
                        print(f"ERROR: Failed to write notebook chat history for {chat_id}")
                    return success
                except Exception as e:
                    print(f"ERROR: Exception while saving notebook chat history for {chat_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            
            # Handle regular chat histories
            if not self.chat_histories_file:
                print(f"ERROR: Cannot save chat history for {chat_id} - no chat histories file configured")
                return False
            
            try:
                print(f"Attempting to save chat history for chat_id: {chat_id}")
                histories = self.get_chat_histories()
                print(f"Current histories count: {len(histories)}")
                
                histories[chat_id] = history
                print(f"Updated histories count: {len(histories)}")
                
                success = RobustFileOperations.safe_write_json(self.chat_histories_file, histories)
                if success:
                    print(f"Successfully saved chat history for {chat_id}")
                else:
                    print(f"ERROR: Failed to write chat history file for {chat_id}")
                
                return success
                
            except Exception as e:
                print(f"ERROR: Exception while saving chat history for {chat_id}: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    def delete_chat_history(self, chat_id: str) -> bool:
        """Delete specific chat history"""
        with self._lock:
            # Handle notebook-specific chat histories
            if self._is_notebook_chat_history_key(chat_id):
                try:
                    notebook_file = self._get_notebook_chat_history_file(chat_id)
                    if notebook_file.exists():
                        notebook_file.unlink()
                        print(f"Deleted notebook chat history file: {notebook_file}")
                    return True
                except Exception as e:
                    print(f"ERROR: Failed to delete notebook chat history for {chat_id}: {e}")
                    return False
            
            # Handle regular chat histories
            if not self.chat_histories_file:
                return False
            
            histories = self.get_chat_histories()
            if chat_id in histories:
                del histories[chat_id]
                return RobustFileOperations.safe_write_json(self.chat_histories_file, histories)
            return True
    
    def clear_chat_histories(self) -> bool:
        """Clear all chat histories"""
        with self._lock:
            if not self.chat_histories_file:
                return False
            return RobustFileOperations.safe_write_json(self.chat_histories_file, {})
    
    # App Values Management
    def get_app_values(self) -> Dict[str, Any]:
        """Get all app values"""
        with self._lock:
            if not self.app_values_file:
                return {}
            return RobustFileOperations.safe_read_json(self.app_values_file, {})
    
    def get_app_value(self, key: str, default: Any = None) -> Any:
        """Get specific app value"""
        values = self.get_app_values()
        return values.get(key, default)
    
    def set_app_value(self, key: str, value: Any) -> bool:
        """Set specific app value"""
        with self._lock:
            if not self.app_values_file:
                return False
            
            values = self.get_app_values()
            values[key] = value
            return RobustFileOperations.safe_write_json(self.app_values_file, values)
    
    def delete_app_value(self, key: str) -> bool:
        """Delete specific app value"""
        with self._lock:
            if not self.app_values_file:
                return False
            
            values = self.get_app_values()
            if key in values:
                del values[key]
                return RobustFileOperations.safe_write_json(self.app_values_file, values)
            return True
    
    def clear_app_values(self) -> bool:
        """Clear all app values"""
        with self._lock:
            if not self.app_values_file:
                return False
            return RobustFileOperations.safe_write_json(self.app_values_file, {})
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache service information"""
        info = {
            "available": self.is_available(),
            "cache_directory": str(self.cache_dir) if self.cache_dir else None,
            "platform": platform.system(),
            "chat_histories_size": 0,
            "app_values_size": 0,
            "total_chat_histories": 0,
            "total_app_values": 0,
            "notebook_chat_files": 0,
            "notebook_chat_files_size": 0
        }
        
        if self.is_available():
            try:
                if self.chat_histories_file.exists():
                    info["chat_histories_size"] = self.chat_histories_file.stat().st_size
                    histories = self.get_chat_histories()
                    info["total_chat_histories"] = len(histories)
                
                if self.app_values_file.exists():
                    info["app_values_size"] = self.app_values_file.stat().st_size
                    values = self.get_app_values()
                    info["total_app_values"] = len(values)
                
                # Count notebook chat history files
                notebook_files = list(self.cache_dir.glob("notebook_chat_*.json"))
                info["notebook_chat_files"] = len(notebook_files)
                info["notebook_chat_files_size"] = sum(f.stat().st_size for f in notebook_files if f.exists())
                
            except Exception as e:
                info["error"] = str(e)
        
        return info


class FileScanCacheManager:
    """Dedicated cache manager for file scanning operations with individual file caching"""
    
    def __init__(self):
        self.cache_dir = CacheDirectoryManager.find_usable_cache_directory()
        self.file_scans_dir = None
        self.scanned_directories_file = None
        self._lock = threading.RLock()
        
        if self.cache_dir:
            self.file_scans_dir = self.cache_dir / "file_scans"
            self.scanned_directories_file = self.file_scans_dir / "scanned_directories.json"
            
            # Initialize file scans directory
            try:
                self.file_scans_dir.mkdir(parents=True, exist_ok=True)
                print(f"File scan cache directory initialized: {self.file_scans_dir}")
            except Exception as e:
                print(f"ERROR: Failed to create file scans directory: {e}")
                self.file_scans_dir = None
                self.scanned_directories_file = None
        else:
            print("WARNING: File scan cache manager running without persistent storage!")
    
    def _get_file_cache_path(self, file_path: str) -> Path:
        """Generate cache file path using MD5 hash of absolute file path"""
        if not self.file_scans_dir:
            raise ValueError("File scans directory not available")
        
        # Create hash from absolute file path
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        return self.file_scans_dir / f"{file_hash}.json"
    
    def is_available(self) -> bool:
        """Check if file scan cache is available"""
        return self.file_scans_dir is not None and self.file_scans_dir.exists()
    
    def get_file_entry(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read individual file cache entry"""
        if not self.is_available():
            return None
        
        try:
            cache_path = self._get_file_cache_path(file_path)
            return RobustFileOperations.safe_read_json(cache_path, None)
        except Exception as e:
            print(f"Error reading file cache for {file_path}: {e}")
            return None
    
    def set_file_entry(self, file_path: str, entry: Dict[str, Any]) -> bool:
        """Write individual file cache entry"""
        if not self.is_available():
            return False
        
        try:
            cache_path = self._get_file_cache_path(file_path)
            return RobustFileOperations.safe_write_json(cache_path, entry)
        except Exception as e:
            print(f"Error writing file cache for {file_path}: {e}")
            return False
    
    def delete_file_entry(self, file_path: str) -> bool:
        """Delete individual file cache entry"""
        if not self.is_available():
            return False
        
        try:
            cache_path = self._get_file_cache_path(file_path)
            if cache_path.exists():
                cache_path.unlink()
                return True
            return True  # File doesn't exist, consider it deleted
        except Exception as e:
            print(f"Error deleting file cache for {file_path}: {e}")
            return False
    
    def get_scanned_directories(self) -> List[Dict[str, Any]]:
        """Read scanned directories list"""
        if not self.scanned_directories_file:
            return []
        
        try:
            return RobustFileOperations.safe_read_json(self.scanned_directories_file, [])
        except Exception as e:
            print(f"Error reading scanned directories: {e}")
            return []
    
    def set_scanned_directories(self, directories: List[Dict[str, Any]]) -> bool:
        """Write scanned directories list"""
        if not self.scanned_directories_file:
            return False
        
        try:
            return RobustFileOperations.safe_write_json(self.scanned_directories_file, directories)
        except Exception as e:
            print(f"Error writing scanned directories: {e}")
            return False
    
    def clear_all_file_entries(self) -> bool:
        """Clear all cached file entries"""
        if not self.is_available():
            return False
        
        try:
            # Remove all .json files except scanned_directories.json
            for cache_file in self.file_scans_dir.glob("*.json"):
                if cache_file.name != "scanned_directories.json":
                    cache_file.unlink()
            return True
        except Exception as e:
            print(f"Error clearing file entries: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Return cache statistics"""
        stats = {
            "available": self.is_available(),
            "file_scans_directory": str(self.file_scans_dir) if self.file_scans_dir else None,
            "total_file_entries": 0,
            "total_cache_size": 0,
            "scanned_directories_count": 0
        }
        
        if self.is_available():
            try:
                # Count file entries (excluding scanned_directories.json)
                file_entries = list(self.file_scans_dir.glob("*.json"))
                file_entries = [f for f in file_entries if f.name != "scanned_directories.json"]
                stats["total_file_entries"] = len(file_entries)
                stats["total_cache_size"] = sum(f.stat().st_size for f in file_entries if f.exists())
                
                # Count scanned directories
                directories = self.get_scanned_directories()
                stats["scanned_directories_count"] = len(directories)
                
            except Exception as e:
                stats["error"] = str(e)
        
        return stats


# Global cache service instance
_cache_service = None
_file_scan_cache_manager = None


def get_cache_service() -> PersistentCacheService:
    """Get the global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = PersistentCacheService()
    return _cache_service


def get_file_scan_cache_manager() -> FileScanCacheManager:
    """Get the global file scan cache manager instance"""
    global _file_scan_cache_manager
    if _file_scan_cache_manager is None:
        _file_scan_cache_manager = FileScanCacheManager()
    return _file_scan_cache_manager
