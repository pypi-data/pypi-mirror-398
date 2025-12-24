"""
Tests for Key constants and generation.
"""

from ptydriver import Keys, MacKeys, ReadlineKeys


class TestKeys:
    """Test standard Keys."""

    def test_ctrl_ascii(self):
        """Standard control characters."""
        assert Keys.ctrl("c") == "\x03"
        assert Keys.ctrl("C") == "\x03"
        assert Keys.ctrl("z") == "\x1a"

    def test_ctrl_extended(self):
        """Extended control characters (punctuation)."""
        assert Keys.ctrl("[") == "\x1b"  # ESC
        assert Keys.ctrl("\\") == "\x1c"  # FS
        assert Keys.ctrl("]") == "\x1d"  # GS
        assert Keys.ctrl("^") == "\x1e"  # RS
        assert Keys.ctrl("_") == "\x1f"  # US
        assert Keys.ctrl("@") == "\x00"  # NUL

    def test_meta_generation(self):
        """Meta key generation."""
        assert Keys.meta("x") == "\x1bx"
        assert Keys.alt("x") == "\x1bx"

    def test_helpers(self):
        """Helper methods."""
        assert Keys.repeat("a", 3) == "aaa"
        assert Keys.sequence("a", "b", "c") == "abc"


class TestMacKeys:
    """Test Mac/Option key bindings."""

    def test_mac_keys(self):
        """Mac option keys map to Meta sequences."""
        assert MacKeys.OPT_B == "\x1bb"
        assert MacKeys.OPT_F == "\x1bf"
        assert MacKeys.OPT_BACKSPACE == "\x1b\x7f"


class TestReadlineKeys:
    """Test Readline bindings."""

    def test_readline_navigation(self):
        """Common navigation keys."""
        assert ReadlineKeys.BEGINNING_OF_LINE == "\x01"  # Ctrl-A
        assert ReadlineKeys.END_OF_LINE == "\x05"  # Ctrl-E
        assert ReadlineKeys.FORWARD_WORD == "\x1bf"  # Alt-F
        assert ReadlineKeys.BACKWARD_WORD == "\x1bb"  # Alt-B
