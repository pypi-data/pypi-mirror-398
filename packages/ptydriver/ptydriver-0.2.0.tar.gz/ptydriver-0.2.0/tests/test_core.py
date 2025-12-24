"""
Core functionality tests for PtyProcess.
"""

import re
import time

import pytest

from ptydriver import Keys, PtyProcess


class TestPtyProcessCore:
    """Core lifecycle and IO tests."""

    def test_lifecycle_context_manager(self):
        """PtyProcess works as a context manager and cleans up."""
        # Use sleep to ensure process stays alive during the check
        with PtyProcess(["sleep", "1"]) as proc:
            assert proc.is_alive()
        assert not proc.is_alive()

    def test_custom_env(self):
        """Can pass custom environment variables."""
        import os

        env = os.environ.copy()
        env["MY_CUSTOM_VAR"] = "my_custom_value"

        with PtyProcess(["bash", "--norc"], env=env) as proc:
            # We don't use the fixture here because we need custom env
            proc.wait_for(re.compile(r"[\$#]"), timeout=2.0)
            proc.send("echo $MY_CUSTOM_VAR")
            proc.wait_for("my_custom_value")

    def test_lifecycle_manual_cleanup(self):
        """Manual cleanup works and is idempotent."""
        proc = PtyProcess(["sleep", "10"])
        assert proc.is_alive()
        proc.cleanup()
        assert not proc.is_alive()
        # Should not raise error
        proc.cleanup()

    def test_send_and_receive(self, bash_proc):
        """Can send commands and read output."""
        bash_proc.send("echo 'CORE_TEST'")
        bash_proc.wait_for("CORE_TEST")
        assert "CORE_TEST" in bash_proc.get_content()

    def test_send_raw(self, bash_proc):
        """Can send raw key sequences (e.g. Ctrl-C)."""
        bash_proc.send("echo 'partial'", press_enter=False)
        bash_proc.send_raw(Keys.CTRL_C)
        bash_proc.send("echo 'after_cancel'")
        bash_proc.wait_for("after_cancel")

    def test_get_screen_structure(self, bash_proc):
        """get_screen returns correct structure."""
        lines = bash_proc.get_screen()
        assert isinstance(lines, list)
        assert len(lines) == bash_proc.height
        assert len(lines[0]) == bash_proc.width

    def test_cursor_position(self, bash_proc):
        """Cursor position updates."""
        # Initial prompt position
        x1, y1 = bash_proc.get_cursor_position()
        bash_proc.send("test")
        time.sleep(0.1)
        x2, y2 = bash_proc.get_cursor_position()

        assert x2 != x1 or y2 != y1

    def test_resize(self, bash_proc):
        """Terminal resizing updates internal state and process."""
        # Check initial size (default 120x40 from init, but fixture might use default)
        assert bash_proc.width == 120
        assert bash_proc.height == 40

        # Resize
        bash_proc.set_size(80, 24)
        assert bash_proc.width == 80
        assert bash_proc.height == 24

        # Verify with tput that the process sees the change
        bash_proc.send("tput cols; tput lines")
        bash_proc.wait_for("80")
        bash_proc.wait_for("24")

    @pytest.mark.slow
    def test_large_output_stress(self):
        """
        Stress test for chunked feeding.
        Dumps a large amount of data and ensures main thread remains responsive.
        """
        # Create a large payload (simulating ~100KB of text)
        large_payload = "X" * 100000

        with PtyProcess(["python3", "-c", f"print('{large_payload}')"], timeout=10) as proc:
            # We should be able to read the screen content while it's processing
            # without hanging forever.
            start = time.time()
            found = False
            while time.time() - start < 5:
                content = proc.get_content()
                if "XXX" in content:
                    found = True
                    break
                time.sleep(0.01)

            assert found, "Failed to read content during massive output dump"
            # Eventually it should finish
            proc.wait_for("XXX", timeout=5)
