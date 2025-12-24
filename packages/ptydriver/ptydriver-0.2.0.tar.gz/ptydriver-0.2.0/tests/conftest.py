"""
Pytest configuration for ptydriver tests.
"""

import re
import shutil

import pytest

from ptydriver import PtyProcess


def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")


@pytest.fixture
def bash_proc():
    """
    Yields a ready-to-use PtyProcess running bash.
    Waits for the initial prompt before yielding.
    """
    # Check if bash is available, fallback to sh if not (e.g. some alpines)
    cmd = ["bash", "--norc"] if shutil.which("bash") else ["sh"]

    with PtyProcess(cmd) as proc:
        # Wait for a prompt (simplified for sh/bash)
        # Bash usually ends in $ or #. Relaxed regex to match even if no trailing space.
        # MUST compile regex because wait_for treats strings as literal text.
        proc.wait_for(re.compile(r"[\$#]"), timeout=2.0)
        yield proc


@pytest.fixture
def python_proc():
    """
    Yields a ready-to-use PtyProcess running a Python REPL.
    """
    with PtyProcess(["python3", "-q"], timeout=5) as proc:
        proc.wait_for(">>>")
        yield proc
