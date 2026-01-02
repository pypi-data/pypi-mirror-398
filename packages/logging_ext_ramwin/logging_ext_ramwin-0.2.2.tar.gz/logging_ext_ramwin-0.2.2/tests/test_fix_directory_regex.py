"""
Test to verify the directory path bug in DateBasedFileHandler cleanup logic.

BUG DESCRIPTION:
When filename_pattern contains directory paths (e.g., "logs/debug-%Y-%m-%d.log"),
the cleanup logic fails to match and delete old log files because:
1. _convert_pattern_to_regex() generates regex for the full path
2. _get_matching_files() uses file.name (filename only) for matching
3. This causes the regex pattern to never match the filename-only pattern

This test should FAIL before the bug fix and PASS after the fix.
"""

import os
import re
import tempfile
import shutil
import time
import datetime
import logging
from pathlib import Path
import pytest

from logging_ext.handlers import DateBasedFileHandler


class TestDirectoryPathBug:
    """Test case to verify the directory path matching bug."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
    
    def addCleanup(self, func, *args, **kwargs):
        """Simple cleanup registration."""
        self._cleanups = getattr(self, '_cleanups', [])
        self._cleanups.append((func, args, kwargs))
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if hasattr(self, '_cleanups'):
            for func, args, kwargs in reversed(self._cleanups):
                func(*args, **kwargs)
    
    def test_directory_path_cleanup_bug(self):
        """
        Test that demonstrates the bug with directory paths in filename_pattern.
        
        This test should:
        1. Create old log files in a subdirectory
        2. Use a filename_pattern with directory path
        3. After writing one log message, old files should be cleaned up
        4. BEFORE FIX: cleanup will not happen (test FAILS)
        5. AFTER FIX: cleanup will happen correctly (test PASSES)
        """
        # Create subdirectory structure
        log_dir = Path(self.temp_dir) / "logs" / "debug"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create old log files that should be deleted
        # These are "old" files with different dates
        old_files = [
            "debug-2024-01-01_00.log",
            "debug-2024-01-02_00.log",
            "debug-2024-01-03_00.log",
            "debug-2024-01-04_00.log",
            "debug-2024-01-05_00.log",
        ]
        
        for filename in old_files:
            file_path = log_dir / filename
            file_path.write_text(f"Old log content for {filename}")
            # Set old modification time to simulate old files
            old_time = time.time() - (old_files.index(filename) + 1) * 86400  # days ago
            os.utime(file_path, (old_time, old_time))
        
        # Count initial files
        initial_file_count = len(list(log_dir.glob("*.log")))
        print(f"\n[DEBUG] Initial file count: {initial_file_count}")
        
        # Use filename_pattern WITH directory path
        # This is the problematic case
        pattern = str(log_dir / "debug-%Y-%m-%d_%H.log")
        handler = DateBasedFileHandler(
            filename_pattern=pattern,
            backup_count=2  # Keep only 2 old files
        )
        
        # Create logger and write one message
        logger = logging.getLogger("test_directory_bug")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        # This should trigger cleanup of old files
        logger.info("New log message that should trigger cleanup")
        handler.close()
        
        # Count remaining files after cleanup
        remaining_files = list(log_dir.glob("*.log"))
        remaining_count = len(remaining_files)
        print(f"[DEBUG] Remaining file count: {remaining_count}")
        print(f"[DEBUG] Remaining files: {[f.name for f in remaining_files]}")
        
        # VERIFY THE BUG:
        # With backup_count=2, we should have at most 3 files:
        # - 1 current file
        # - 2 old files (backup_count)
        expected_max_files = 3
        
        # BEFORE FIX: All 5 old files + 1 new file = 6 files (test FAILS)
        # AFTER FIX: Only 2 old files + 1 new file = 3 files (test PASSES)
        assert remaining_count <= expected_max_files, (
            f"Bug detected: Expected at most {expected_max_files} files "
            f"(current + {handler.backup_count} backups), but found {remaining_count} files. "
            f"Files: {[f.name for f in remaining_files]}"
        )
    
    def test_regex_pattern_generation(self):
        """
        Test that demonstrates the regex pattern generation issue.
        
        This test shows that the regex pattern includes the directory path
        but matching is done against filename only.
        """
        # Setup
        log_dir = Path(self.temp_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test files
        test_file = log_dir / "app-2024-01-15.log"
        test_file.write_text("test")
        
        # Create handler with directory path
        pattern = str(log_dir / "app-%Y-%m-%d.log")
        handler = DateBasedFileHandler(filename_pattern=pattern, backup_count=1)
        
        # The regex pattern should match the filename, not the full path
        filename_only = test_file.name  # "app-2024-01-15.log"
        
        print(f"\n[DEBUG] Full pattern: {pattern}")
        print(f"[DEBUG] Filename only: {filename_only}")
        print(f"[DEBUG] Regex pattern: {handler._file_pattern_regex}")
        
        # BEFORE FIX: This will be False (regex expects full path, but we match filename)
        # AFTER FIX: This should be True
        matches = re.match(handler._file_pattern_regex, filename_only) is not None
        
        assert matches, (
            f"Regex pattern does not match filename-only pattern. "
            f"This causes cleanup to fail. "
            f"Pattern: {handler._file_pattern_regex}, "
            f"Test filename: {filename_only}"
        )
        
        handler.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
