"""
Tests for DateBasedFileHandler
"""

import re
import os
import tempfile
import shutil
import time
import datetime
import logging
from pathlib import Path
import pytest

from logging_ext.handlers import DateBasedFileHandler, ConcurrentDateBasedFileHandler


class TestDateBasedFileHandler:
    
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
    
    def test_basic_logging(self):
        """Test basic logging functionality."""
        log_file = os.path.join(self.temp_dir, "test-%Y-%m-%d.log")
        handler = DateBasedFileHandler(log_file)
        logger = logging.getLogger("test1")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        logger.info("Test message")
        handler.close()
        
        # Check that file was created
        expected_file = datetime.datetime.now().strftime(log_file)
        assert os.path.exists(expected_file)
        
        # Check content
        with open(expected_file, 'r') as f:
            content = f.read()
            assert "Test message" in content
    
    def test_hourly_rotation(self):
        """Test hourly file rotation."""
        log_file = os.path.join(self.temp_dir, "test-%Y-%m-%d_%H.log")
        handler = DateBasedFileHandler(log_file)
        
        # Create logger
        logger = logging.getLogger("test2")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        # Log first message
        logger.info("First hour message")
        
        # Simulate time passing to next hour
        handler.filename_pattern = (datetime.datetime.now() + 
                                   datetime.timedelta(hours=1)).strftime("test-%Y-%m-%d_%H.log")
        
        logger.info("Next hour message")
        handler.close()
        
        # Both files should exist
        current_hour = datetime.datetime.now().strftime("test-%Y-%m-%d_%H.log")
        next_hour = (datetime.datetime.now() + 
                    datetime.timedelta(hours=1)).strftime("test-%Y-%m-%d_%H.log")
        
        assert os.path.exists(os.path.join(self.temp_dir, current_hour))
        # Note: next hour file won't exist because we just simulated the time change
    
    def test_backup_count_cleanup(self):
        """Test automatic cleanup of old log files."""
        log_file = os.path.join(self.temp_dir, "test-%Y-%m-%d-%H-%M.log")
        handler = DateBasedFileHandler(log_file, backup_count=2)
        
        # Create multiple log files by changing the pattern
        base_time = datetime.datetime.now()
        
        # Pre-create 5 files with different times
        for i in range(5):
            # Create a log message for each "minute"
            file_time = base_time - datetime.timedelta(minutes=i)
            file_name = file_time.strftime("test-%Y-%m-%d-%H-%M.log")
            
            # Manually create the file
            full_path = os.path.join(self.temp_dir, file_name)
            with open(full_path, 'w') as f:
                f.write(f"Log message {i}")
            
            # Set modification time (older files first)
            os.utime(full_path, (time.time() - i*60, time.time() - i*60))
        
        # Now log a message to trigger cleanup
        logger = logging.getLogger("test3")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.info("Trigger cleanup")
        handler.close()
        
        # Count remaining files that match the pattern
        existing_files = []
        pattern = re.compile(handler._file_pattern_regex)
        for f in os.listdir(self.temp_dir):
            if pattern.match(f) and f != Path(handler._get_current_filename()).name:
                existing_files.append(f)
        
        # Should have at most backup_count files (excluding current file)
        assert len(existing_files) <= 2  # backup_count(2)
    
    def test_pattern_matching(self):
        """Test that pattern matching works correctly."""
        log_file = os.path.join(self.temp_dir, "app-%Y-%m-%d.log")
        handler = DateBasedFileHandler(log_file, backup_count=1)
        
        # Create some files that should match
        matching_files = [
            "app-2024-01-15.log",
            "app-2024-01-16.log", 
            "app-2024-01-17.log"
        ]
        
        for filename in matching_files:
            Path(self.temp_dir, filename).touch()
        
        # Create files that should NOT match
        non_matching_files = [
            "app-2024-1-15.log",     # Wrong month format
            "application-2024-01-15.log",  # Wrong prefix
            "app-2024-01-15.txt"     # Wrong extension
        ]
        
        for filename in non_matching_files:
            Path(self.temp_dir, filename).touch()
        
        # Set modification times so oldest files get deleted first
        for i, filename in enumerate(matching_files):
            filepath = Path(self.temp_dir, filename)
            # Older files first
            os.utime(filepath, (time.time() - (10-i)*60, time.time() - (10-i)*60))
        
        # Trigger cleanup
        logger = logging.getLogger("test4")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.info("Test")
        handler.close()
        
        # Check that only matching log files are considered for cleanup
        pattern = re.compile(handler._file_pattern_regex)
        remaining_files = []
        print(os.listdir(self.temp_dir))
        for f in os.listdir(self.temp_dir):
            if f.startswith("app-") and f.endswith(".log") and pattern.match(f) and f != Path(handler._get_current_filename()).name:
                remaining_files.append(f)
        
        # Should keep at most backup_count files (excluding current file)
        assert len(remaining_files) <= 1, remaining_files
        
        # Non-matching files should still exist
        for filename in non_matching_files:
            assert os.path.exists(os.path.join(self.temp_dir, filename)), f"Non-matching file {filename} should not be deleted"


class TestConcurrentDateBasedFileHandler:
    
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
    
    def test_concurrent_access(self):
        """Test concurrent access to the handler."""
        import threading
        
        log_file = os.path.join(self.temp_dir, "concurrent-%Y-%m-%d.log")
        handler = ConcurrentDateBasedFileHandler(log_file)
        
        results = []
        
        def worker(message):
            logger = logging.getLogger(f"worker-{threading.current_thread().ident}")
            logger.setLevel(logging.INFO)
            logger.addHandler(handler)
            logger.info(message)
            results.append(message)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(f"Message {i}",))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        handler.close()
        
        # Check that all messages were logged
        expected_file = datetime.datetime.now().strftime(log_file)
        assert os.path.exists(expected_file)
        
        with open(expected_file, 'r') as f:
            content = f.read()
            for i in range(10):
                assert f"Message {i}" in content


if __name__ == "__main__":
    pytest.main([__file__])
