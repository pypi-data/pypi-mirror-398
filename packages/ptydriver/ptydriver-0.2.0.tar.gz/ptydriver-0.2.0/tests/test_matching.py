"""
Tests for pattern matching (wait_for, contains).
"""

import re

import pytest


class TestPatternMatching:
    """Tests for wait_for and contains with strings and regex."""

    def test_wait_for_string(self, bash_proc):
        """Standard string matching."""
        bash_proc.send("echo 'simple string'")
        assert bash_proc.wait_for("simple string")

    def test_wait_for_regex(self, bash_proc):
        """Regex matching."""
        bash_proc.send("echo 'ID: 12345'")
        # Match using regex object
        pattern = re.compile(r"ID: \d+")
        assert bash_proc.wait_for(pattern)

    def test_wait_for_timeout(self, bash_proc):
        """Raises TimeoutError correctly."""
        with pytest.raises(TimeoutError) as exc:
            bash_proc.wait_for("NON_EXISTENT_TEXT", timeout=0.2)

        # Check that error message contains truncated content
        msg = str(exc.value)
        assert "NON_EXISTENT_TEXT" in msg
        assert "Current content:" in msg

    def test_wait_for_regex_timeout_msg(self, bash_proc):
        """Error message handles regex patterns correctly."""
        pattern = re.compile(r"MISSING-\d+")
        with pytest.raises(TimeoutError) as exc:
            bash_proc.wait_for(pattern, timeout=0.2)
        assert "MISSING-\\d+" in str(exc.value)

    def test_contains_string(self, bash_proc):
        """Contains check for string."""
        assert not bash_proc.contains("MAGIC_TOKEN")
        bash_proc.send("echo 'MAGIC_TOKEN'")
        bash_proc.wait_for("MAGIC_TOKEN")
        assert bash_proc.contains("MAGIC_TOKEN")

    def test_contains_regex(self, bash_proc):
        """Contains check for regex."""
        bash_proc.send("echo 'Error code: 404'")
        bash_proc.wait_for("404")
        assert bash_proc.contains(re.compile(r"Error code: \d{3}"))
        assert not bash_proc.contains(re.compile(r"Error code: \d{2}$"))
