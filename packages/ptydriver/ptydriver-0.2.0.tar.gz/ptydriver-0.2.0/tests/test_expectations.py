"""
Tests for new expectation methods: expect_any, expect_sequence.
"""

import re

import pytest

from ptydriver import PtyProcess


class TestExpectationMethods:
    def test_send_bytes(self, bash_proc):
        """Test sending raw bytes."""
        # Send Ctrl-D (EOF) as bytes
        bash_proc.send_bytes(b"\x04")
        # Bash should exit, or if in middle of input, cancel
        # We can't easily assert on process exit for bash_proc fixture
        # so let's try a simpler use case.

        with PtyProcess(["cat"]) as proc:
            proc.send_bytes(b"hello\n")
            proc.wait_for("hello")
            proc.send_bytes(b"\x04")  # EOF
            # Cat should exit
            assert not proc.is_alive()

    def test_expect_any_string(self, python_proc):
        """Test expect_any with multiple string patterns."""
        python_proc.send("import time")
        python_proc.send("print('apple')")
        python_proc.send("time.sleep(0.1)")
        python_proc.send("print('banana')")

        index, content = python_proc.expect_any(["banana", "cherry"])
        assert index == 0
        assert "banana" in content

    def test_expect_any_regex(self, python_proc):
        """Test expect_any with multiple regex patterns."""
        python_proc.send("import time")
        python_proc.send("print('ID: 123')")
        python_proc.send("time.sleep(0.1)")
        python_proc.send("print('Code: ABC')")

        index, content = python_proc.expect_any(
            [re.compile(r"Code: [A-Z]{3}"), re.compile(r"Error: \d+")]
        )
        assert index == 0
        assert "Code: ABC" in content

    def test_expect_any_timeout(self, python_proc):
        """Test expect_any raises TimeoutError."""
        with pytest.raises(TimeoutError):
            python_proc.expect_any(["never_appear_1", "never_appear_2"], timeout=0.5)

    def test_expect_sequence_string(self, python_proc):
        """Test expect_sequence with string patterns."""
        python_proc.send("print('step 1')")
        python_proc.send("print('step 2')")
        python_proc.send("print('step 3')")

        matches = python_proc.expect_sequence(["step 1", "step 2", "step 3"])
        assert len(matches) == 3
        assert "step 1" in matches[0]
        assert "step 2" in matches[1]
        assert "step 3" in matches[2]

    def test_expect_sequence_regex(self, python_proc):
        """Test expect_sequence with regex patterns."""
        python_proc.send("print('Task A started')")
        python_proc.send("print('Processing data ID: 100')")
        python_proc.send("print('Task A finished')")

        matches = python_proc.expect_sequence(
            [
                re.compile(r"Task A (started|completed)"),
                re.compile(r"data ID: (\d+)"),
                "Task A finished",
            ]
        )
        assert len(matches) == 3
        assert "Task A started" in matches[0]
        assert "data ID: 100" in matches[1]
        assert "Task A finished" in matches[2]

    def test_expect_sequence_timeout(self, python_proc):
        """Test expect_sequence raises TimeoutError on intermediate step."""
        python_proc.send("print('first step')")

        with pytest.raises(TimeoutError):
            python_proc.expect_sequence(
                ["first step", "second step that won't appear"], timeout=0.5
            )
