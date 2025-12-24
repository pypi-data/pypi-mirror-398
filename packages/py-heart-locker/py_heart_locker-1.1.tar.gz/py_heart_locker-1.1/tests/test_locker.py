#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test cases for the locker module.

Tests cover:
- Basic lock/unlock functionality
- Process lock detection
- Stale lock cleanup
- Concurrent access scenarios
- File operations edge cases
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lock import locker


class TestLockerBasicFunctionality(unittest.TestCase):
    """Test basic lock and unlock operations."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for lock files
        self.test_dir = tempfile.mkdtemp()
        self.original_lock_file = locker.LOCK_FILE
        locker.LOCK_FILE = Path(self.test_dir) / "test_locker.dat"

    def tearDown(self):
        """Clean up after tests."""
        # Restore original lock file path
        locker.LOCK_FILE = self.original_lock_file
        
        # Clean up test lock file if it exists
        try:
            if locker.LOCK_FILE.exists():
                locker.LOCK_FILE.unlink()
        except OSError:
            pass
        
        # Remove test directory
        try:
            Path(self.test_dir).rmdir()
        except OSError:
            pass

    def test_lock_creates_file(self):
        """Test that lock() creates a lock file."""
        self.assertFalse(locker.LOCK_FILE.exists())
        result = locker.lock()
        self.assertTrue(result)
        self.assertTrue(locker.LOCK_FILE.exists())

    def test_unlock_removes_file(self):
        """Test that unlock() removes the lock file."""
        locker.lock()
        self.assertTrue(locker.LOCK_FILE.exists())
        locker.unlock()
        self.assertFalse(locker.LOCK_FILE.exists())

    def test_islocked_true_when_locked(self):
        """Test that islocked() returns True when process is locked."""
        self.assertFalse(locker.islocked())
        locker.lock()
        self.assertTrue(locker.islocked())

    def test_islocked_false_after_unlock(self):
        """Test that islocked() returns False after unlock."""
        locker.lock()
        locker.unlock()
        self.assertFalse(locker.islocked())

    def test_unlock_only_removes_own_lock(self):
        """Test that unlock() only removes lock if owned by current process."""
        locker.lock()
        current_pid = os.getpid()
        
        # Mock the PID to simulate a different process
        with mock.patch('os.getpid', return_value=current_pid + 1):
            locker.unlock()
            # Lock file should still exist since we didn't own it
            self.assertTrue(locker.LOCK_FILE.exists())
        
        # Now unlock with correct PID
        locker.unlock()
        self.assertFalse(locker.LOCK_FILE.exists())


class TestLockerLockFileContent(unittest.TestCase):
    """Test lock file content and parsing."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_lock_file = locker.LOCK_FILE
        locker.LOCK_FILE = Path(self.test_dir) / "test_locker.dat"

    def tearDown(self):
        """Clean up after tests."""
        locker.LOCK_FILE = self.original_lock_file
        try:
            if locker.LOCK_FILE.exists():
                locker.LOCK_FILE.unlink()
        except OSError:
            pass
        try:
            Path(self.test_dir).rmdir()
        except OSError:
            pass

    def test_lock_file_format(self):
        """Test that lock file contains PID and creation time."""
        locker.lock()
        content = locker.LOCK_FILE.read_text(encoding=locker.CHATSET).strip()
        parts = content.split(",")
        
        self.assertEqual(len(parts), 2)
        self.assertEqual(int(parts[0]), os.getpid())
        self.assertGreater(float(parts[1]), 0)

    def test_read_lock_valid_format(self):
        """Test _read_lock() with valid lock file."""
        locker.lock()
        info = locker._read_lock()
        
        self.assertIsNotNone(info)
        pid, ctime = info
        self.assertEqual(pid, os.getpid())
        self.assertGreater(ctime, 0)

    def test_read_lock_invalid_format(self):
        """Test _read_lock() with invalid lock file content."""
        locker.LOCK_FILE.write_text("invalid content", encoding=locker.CHATSET)
        info = locker._read_lock()
        self.assertIsNone(info)

    def test_read_lock_empty_file(self):
        """Test _read_lock() with empty lock file."""
        locker.LOCK_FILE.write_text("", encoding=locker.CHATSET)
        info = locker._read_lock()
        self.assertIsNone(info)

    def test_read_lock_nonexistent_file(self):
        """Test _read_lock() when file doesn't exist."""
        info = locker._read_lock()
        self.assertIsNone(info)


class TestLockerStaleProcessDetection(unittest.TestCase):
    """Test detection and cleanup of stale locks."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_lock_file = locker.LOCK_FILE
        locker.LOCK_FILE = Path(self.test_dir) / "test_locker.dat"

    def tearDown(self):
        """Clean up after tests."""
        locker.LOCK_FILE = self.original_lock_file
        try:
            if locker.LOCK_FILE.exists():
                locker.LOCK_FILE.unlink()
        except OSError:
            pass
        try:
            Path(self.test_dir).rmdir()
        except OSError:
            pass

    def test_stale_lock_cleanup_on_islocked(self):
        """Test that stale locks are cleaned up when checking islocked()."""
        # Create a lock file with a non-existent PID
        fake_pid = 999999999
        fake_ctime = 1234567890.0
        locker.LOCK_FILE.write_text(
            f"{fake_pid},{fake_ctime}",
            encoding=locker.CHATSET
        )
        
        self.assertTrue(locker.LOCK_FILE.exists())
        result = locker.islocked()
        self.assertFalse(result)
        # Stale lock should be cleaned up
        self.assertFalse(locker.LOCK_FILE.exists())

    def test_stale_lock_cleanup_on_lock(self):
        """Test that lock() cleans up stale locks before creating new ones."""
        # Create a stale lock file
        fake_pid = 999999999
        fake_ctime = 1234567890.0
        locker.LOCK_FILE.write_text(
            f"{fake_pid},{fake_ctime}",
            encoding=locker.CHATSET
        )
        
        # Try to acquire lock - should clean up stale lock first
        result = locker.lock()
        self.assertTrue(result)
        
        # Verify the lock file has the correct PID
        content = locker.LOCK_FILE.read_text(encoding=locker.CHATSET).strip()
        pid = int(content.split(",")[0])
        self.assertEqual(pid, os.getpid())


class TestLockerEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_lock_file = locker.LOCK_FILE
        locker.LOCK_FILE = Path(self.test_dir) / "test_locker.dat"

    def tearDown(self):
        """Clean up after tests."""
        locker.LOCK_FILE = self.original_lock_file
        try:
            if locker.LOCK_FILE.exists():
                locker.LOCK_FILE.unlink()
        except OSError:
            pass
        try:
            Path(self.test_dir).rmdir()
        except OSError:
            pass

    def test_lock_already_locked_returns_false(self):
        """Test that lock() returns False if already locked by current process."""
        first_lock = locker.lock()
        self.assertTrue(first_lock)
        
        second_lock = locker.lock()
        self.assertFalse(second_lock)

    def test_unlock_no_lock_file(self):
        """Test that unlock() handles missing lock file gracefully."""
        # Should not raise an exception
        locker.unlock()

    def test_unlock_without_owning_lock(self):
        """Test that unlock() doesn't remove lock owned by another process."""
        locker.lock()
        
        # Manually change the PID in the lock file
        content = locker.LOCK_FILE.read_text(encoding=locker.CHATSET)
        parts = content.split(",")
        fake_pid = 999999
        new_content = f"{fake_pid},{parts[1]}"
        locker.LOCK_FILE.write_text(new_content, encoding=locker.CHATSET)
        
        # Try to unlock
        locker.unlock()
        
        # Lock file should still exist
        self.assertTrue(locker.LOCK_FILE.exists())

    def test_read_lock_with_whitespace(self):
        """Test _read_lock() handles whitespace in lock file."""
        locker.LOCK_FILE.write_text(
            f"  {os.getpid()}  ,  123.456  ",
            encoding=locker.CHATSET
        )
        info = locker._read_lock()
        
        self.assertIsNotNone(info)
        pid, ctime = info
        self.assertEqual(pid, os.getpid())
        self.assertEqual(ctime, 123.456)

    def test_read_lock_only_pid_no_ctime(self):
        """Test _read_lock() handles lock file with only PID (legacy format)."""
        locker.LOCK_FILE.write_text(
            str(os.getpid()),
            encoding=locker.CHATSET
        )
        info = locker._read_lock()
        
        self.assertIsNotNone(info)
        pid, ctime = info
        self.assertEqual(pid, os.getpid())
        self.assertIsNone(ctime)


class TestLockerPermissionErrors(unittest.TestCase):
    """Test handling of permission-related errors."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_lock_file = locker.LOCK_FILE
        locker.LOCK_FILE = Path(self.test_dir) / "test_locker.dat"

    def tearDown(self):
        """Clean up after tests."""
        locker.LOCK_FILE = self.original_lock_file
        try:
            if locker.LOCK_FILE.exists():
                locker.LOCK_FILE.unlink()
        except OSError:
            pass
        try:
            Path(self.test_dir).rmdir()
        except OSError:
            pass

    @mock.patch('psutil.Process')
    def test_islocked_access_denied(self, mock_process_class):
        """Test islocked() handles AccessDenied exception."""
        locker.lock()
        
        # Mock psutil.Process to raise AccessDenied
        mock_process_class.side_effect = Exception("AccessDenied")
        
        # Should handle the exception
        result = locker.islocked()
        # The actual behavior depends on error type, but should not crash
        self.assertIsInstance(result, bool)

    def test_lock_file_directory_not_writable(self):
        """Test lock() when directory is not writable."""
        # Mock open() to raise PermissionError when trying to create lock file
        with mock.patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = locker.lock()
            # Should return False since we can't write
            self.assertFalse(result)


class TestLockerIntegration(unittest.TestCase):
    """Integration tests for the locker module."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_lock_file = locker.LOCK_FILE
        locker.LOCK_FILE = Path(self.test_dir) / "test_locker.dat"

    def tearDown(self):
        """Clean up after tests."""
        locker.LOCK_FILE = self.original_lock_file
        try:
            if locker.LOCK_FILE.exists():
                locker.LOCK_FILE.unlink()
        except OSError:
            pass
        try:
            Path(self.test_dir).rmdir()
        except OSError:
            pass

    def test_typical_usage_pattern(self):
        """Test the typical lock/check/unlock usage pattern."""
        # Check if locked (should be false initially)
        self.assertFalse(locker.islocked())
        
        # Acquire lock
        self.assertTrue(locker.lock())
        
        # Check if locked (should be true now)
        self.assertTrue(locker.islocked())
        
        # Attempt to lock again (should fail)
        self.assertFalse(locker.lock())
        
        # Release lock
        locker.unlock()
        
        # Check if locked (should be false again)
        self.assertFalse(locker.islocked())

    def test_multiple_lock_cycles(self):
        """Test multiple lock/unlock cycles."""
        for i in range(3):
            self.assertFalse(locker.islocked())
            self.assertTrue(locker.lock())
            self.assertTrue(locker.islocked())
            locker.unlock()
            self.assertFalse(locker.islocked())


if __name__ == '__main__':
    unittest.main()
