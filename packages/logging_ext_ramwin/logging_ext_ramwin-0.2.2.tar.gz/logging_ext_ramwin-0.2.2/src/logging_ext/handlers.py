"""
Date-based logging handler with automatic file rotation and cleanup
"""

import os
import time
import datetime
import logging
import glob
import re
from typing import Optional, List
from pathlib import Path


class DateBasedFileHandler(logging.FileHandler):
    """
    A logging handler that writes to different files based on date patterns.
    
    This handler automatically creates log files with names based on the current
    date/time according to the specified format pattern. It also supports
    automatic cleanup of old log files.
    
    Args:
        filename_pattern: Pattern for log filenames using strftime format codes.
                         Examples: "%Y-%m-%d.log" -> "2024-01-15.log"
                                  "%Y-%m-%d_%H.log" -> "2024-01-15_14.log"
        backup_count: Number of old log files to keep. If > 0, old files matching
                     the pattern will be automatically deleted. Default: 0 (no cleanup)
        encoding: File encoding. Default: "utf-8"
        delay: If True, file opening is deferred until the first log message. Default: False
        mode: File opening mode. Default: "a" (append)
    
    Example:
        handler = DateBasedFileHandler(
            filename_pattern="logs/app-%Y-%m-%d.log",
            backup_count=7  # Keep last 7 days
        )
    """
    
    def __init__(
        self,
        filename_pattern: str,
        backup_count: int = 0,
        encoding: str = "utf-8",
        delay: bool = False,
        mode: str = "a"
    ):
        self.filename_pattern = filename_pattern
        self.backup_count = max(0, backup_count)
        self.current_filename: Optional[str] = None
        self._file_pattern_regex = self._convert_pattern_to_regex(filename_pattern)
        
        # Initialize with a placeholder - actual file will be opened in emit()
        super().__init__(
            filename=self._get_current_filename(),
            mode=mode,
            encoding=encoding,
            delay=delay
        )
    
    def _convert_pattern_to_regex(self, pattern: str) -> str:
        """
        Convert strftime pattern to regex pattern for matching existing files.
        """
        # Escape special regex characters first
        regex_pattern = re.escape(Path(pattern).name)
        
        # Replace common strftime format codes with regex patterns
        replacements = {
            r'%Y': r'\d{4}',           # Year with century
            r'%y': r'\d{2}',           # Year without century
            r'%m': r'(0[1-9]|1[0-2])', # Month as zero-padded decimal (01-12)
            r'%d': r'(0[1-9]|[12][0-9]|3[01])',  # Day of month as zero-padded decimal (01-31)
            r'%H': r'([01][0-9]|2[0-3])',  # Hour (24-hour clock) as zero-padded decimal (00-23)
            r'%I': r'(0[1-9]|1[0-2])',  # Hour (12-hour clock) as zero-padded decimal (01-12)
            r'%M': r'[0-5][0-9]',      # Minute as zero-padded decimal (00-59)
            r'%S': r'[0-5][0-9]',      # Second as zero-padded decimal (00-59)
            r'%j': r'(00[1-9]|0[1-9][0-9]|[12][0-9][0-9]|3[0-5][0-9]|36[0-6])',  # Day of year (001-366)
            r'%U': r'[0-5][0-9]',      # Week number of year (00-53)
            r'%W': r'[0-5][0-9]',      # Week number of year (00-53)
            r'%a': r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)',  # Weekday abbreviated name
            r'%A': r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',  # Weekday full name
            r'%b': r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',  # Month abbreviated name
            r'%B': r'(January|February|March|April|May|June|July|August|September|October|November|December)',  # Month full name
            r'%p': r'(AM|PM)',         # AM or PM
        }
        
        for strftime_code, regex_replacement in replacements.items():
            regex_pattern = regex_pattern.replace(
                re.escape(strftime_code), regex_replacement
            )
        
        return f'^{regex_pattern}$'
    
    def _get_current_filename(self) -> str:
        """Get the current filename based on the pattern and current time."""
        now = datetime.datetime.now()
        return now.strftime(self.filename_pattern)
    
    def _should_rollover(self) -> bool:
        """Check if we should roll over to a new file."""
        current_file = self._get_current_filename()
        return current_file != self.current_filename
    
    def _close_stream(self):
        """Close the current file stream safely."""
        if self.stream and hasattr(self.stream, 'close'):
            try:
                self.stream.close()
            except Exception:
                pass  # Ignore errors during close
            finally:
                self.stream = None
    
    def _open_current_file(self):
        """Open the current log file, creating directories if needed."""
        current_file = self._get_current_filename()
        
        # Create directories if they don't exist
        file_path = Path(current_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Close current stream if open
        self._close_stream()
        
        # Open new file
        self.baseFilename = current_file
        self.current_filename = current_file
        
        try:
            self.stream = open(current_file, self.mode, encoding=self.encoding)
        except Exception as e:
            # If we can't open the file, fall back to stderr
            self.handleError(logging.LogRecord(
                name="DateBasedFileHandler",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg=f"Failed to open log file {current_file}: {e}",
                args=(),
                exc_info=None
            ))
    
    def _get_matching_files(self) -> List[Path]:
        """Get all files matching the pattern, sorted by modification time."""
        try:
            # Get directory from pattern
            file_path = Path(self.filename_pattern)
            directory = file_path.parent
            if not directory or str(directory) == '.':
                directory = Path(".")
            
            # Find all files in directory that match the pattern
            matching_files = []
            current_filename = self._get_current_filename()
            
            for file in directory.iterdir():
                if file.is_file() and file.name != Path(current_filename).name:
                    if re.match(self._file_pattern_regex, file.name):
                        matching_files.append(file)
            
            # Sort by modification time (newest first)
            matching_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            return matching_files
            
        except Exception:
            return []
    
    def _cleanup_old_files(self):
        """Remove old log files if backup_count is specified."""
        if self.backup_count <= 0:
            return
        
        try:
            # Get matching files sorted by modification time (excluding current file)
            matching_files = self._get_matching_files()
            
            # Keep only the most recent files (backup_count)
            files_to_delete = matching_files[self.backup_count:]
            
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                except (OSError, IOError):
                    # File might have been deleted by another process
                    pass
                    
        except Exception as e:
            # Log cleanup errors but don't fail the logging operation
            self.handleError(logging.LogRecord(
                name="DateBasedFileHandler",
                level=logging.WARNING,
                pathname="",
                lineno=0,
                msg=f"Error during log cleanup: {e}",
                args=(),
                exc_info=None
            ))
    
    def emit(self, record: logging.LogRecord):
        """
        Emit a log record to the appropriate file.
        
        This method checks if we need to roll over to a new file based on the
        current time and filename pattern.
        """
        try:
            # Check if we need to roll over
            if self._should_rollover():
                self._open_current_file()
            
            # Always run cleanup if backup_count is set, regardless of rollover
            if self.backup_count > 0:
                self._cleanup_old_files()
            
            # Write the log record
            if self.stream is None:
                self._open_current_file()
            
            if self.stream:
                super().emit(record)
                
        except Exception as error:
            print(error)
            self.handleError(record)
    
    def close(self):
        """Close the handler and underlying stream."""
        self._close_stream()
        super().close()


class ConcurrentDateBasedFileHandler(DateBasedFileHandler):
    """
    A thread-safe version of DateBasedFileHandler using file locking.
    
    This handler provides basic concurrency protection for multi-process scenarios
    by using file locking mechanisms.
    """
    
    def __init__(self, *args, **kwargs):
        self._lock_file = None
        self._lock_filename = None
        super().__init__(*args, **kwargs)
    
    def _acquire_lock(self):
        """Acquire an exclusive lock on the lock file."""
        if self._lock_filename is None:
            base_name = Path(self.filename_pattern).stem
            self._lock_filename = f"{base_name}.lock"
        
        try:
            self._lock_file = open(self._lock_filename, 'w')
            # Simple file locking - may not work on all systems
            # For production use, consider portalocker or similar
            if hasattr(self._lock_file, 'fileno'):
                try:
                    import fcntl
                    fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (ImportError, IOError, OSError):
                    # Fallback for Windows or if flock is not available
                    pass
        except Exception:
            self._lock_file = None
    
    def _release_lock(self):
        """Release the file lock."""
        if self._lock_file:
            try:
                if hasattr(self._lock_file, 'fileno'):
                    try:
                        import fcntl
                        fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
                    except (ImportError, IOError, OSError):
                        pass
                self._lock_file.close()
            except Exception:
                pass
            finally:
                self._lock_file = None
    
    def emit(self, record: logging.LogRecord):
        """Emit a record with file locking for concurrency safety."""
        self._acquire_lock()
        try:
            super().emit(record)
        finally:
            self._release_lock()
    
    def close(self):
        """Close the handler and release any locks."""
        self._release_lock()
        super().close()
