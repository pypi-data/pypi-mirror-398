"""
Common key sequences and escape codes for terminal interaction.

This module provides constants for commonly used key sequences when driving
interactive terminal applications. Includes support for vim, fzf, tmux,
readline, and other popular CLI tools.

Key sequence reference: https://invisible-island.net/xterm/ctlseqs/ctlseqs.html
"""


class Keys:
    """
    Common key sequences for terminal interaction.

    This class provides constants for control characters, special keys,
    arrow keys, function keys, and navigation keys commonly used in
    terminal applications.

    Modifier encoding in escape sequences:
    - 2 = Shift
    - 3 = Alt
    - 4 = Shift+Alt
    - 5 = Ctrl
    - 6 = Shift+Ctrl
    - 7 = Alt+Ctrl
    - 8 = Shift+Alt+Ctrl
    """

    # ==========================================================================
    # Control Characters (Ctrl+A through Ctrl+Z)
    # ==========================================================================
    CTRL_A = "\x01"  # Beginning of line (readline)
    CTRL_B = "\x02"  # Back one character / tmux prefix
    CTRL_C = "\x03"  # Interrupt (SIGINT)
    CTRL_D = "\x04"  # EOF / Delete char / Exit
    CTRL_E = "\x05"  # End of line (readline)
    CTRL_F = "\x06"  # Forward one character
    CTRL_G = "\x07"  # Bell / Abort
    CTRL_H = "\x08"  # Backspace (legacy)
    CTRL_I = "\x09"  # Tab (same as \t)
    CTRL_J = "\x0a"  # Newline (same as \n)
    CTRL_K = "\x0b"  # Kill to end of line
    CTRL_L = "\x0c"  # Clear screen / Redraw
    CTRL_M = "\x0d"  # Carriage return (Enter)
    CTRL_N = "\x0e"  # Next history / Down
    CTRL_O = "\x0f"  # Execute and fetch next
    CTRL_P = "\x10"  # Previous history / Up
    CTRL_Q = "\x11"  # Resume output (XON)
    CTRL_R = "\x12"  # Reverse search
    CTRL_S = "\x13"  # Forward search / Stop output (XOFF)
    CTRL_T = "\x14"  # Transpose characters
    CTRL_U = "\x15"  # Kill line (to beginning)
    CTRL_V = "\x16"  # Literal next / Verbatim insert
    CTRL_W = "\x17"  # Kill word backward
    CTRL_X = "\x18"  # Prefix for extended commands
    CTRL_Y = "\x19"  # Yank (paste killed text)
    CTRL_Z = "\x1a"  # Suspend (SIGTSTP)

    # Additional control characters
    CTRL_BACKSLASH = "\x1c"  # Quit (SIGQUIT)
    CTRL_CLOSE_BRACKET = "\x1d"  # GS (Group Separator)
    CTRL_CARET = "\x1e"  # RS (Record Separator)
    CTRL_UNDERSCORE = "\x1f"  # Undo (some apps)

    # ==========================================================================
    # Special Keys
    # ==========================================================================
    ESCAPE = "\x1b"
    ESC = ESCAPE  # Alias
    ENTER = "\r"
    RETURN = ENTER  # Alias
    NEWLINE = "\n"
    TAB = "\t"
    BACKSPACE = "\x7f"  # Modern backspace (DEL)
    BACKSPACE_LEGACY = "\x08"  # Legacy backspace (BS)
    DELETE = "\x1b[3~"
    INSERT = "\x1b[2~"

    # ==========================================================================
    # Arrow Keys (ANSI/CSI mode - most common)
    # ==========================================================================
    UP = "\x1b[A"
    DOWN = "\x1b[B"
    RIGHT = "\x1b[C"
    LEFT = "\x1b[D"

    # Arrow keys (Application/SS3 mode - used by some apps like vim)
    UP_APP = "\x1bOA"
    DOWN_APP = "\x1bOB"
    RIGHT_APP = "\x1bOC"
    LEFT_APP = "\x1bOD"

    # ==========================================================================
    # Modified Arrow Keys
    # ==========================================================================
    # Shift + Arrow
    SHIFT_UP = "\x1b[1;2A"
    SHIFT_DOWN = "\x1b[1;2B"
    SHIFT_RIGHT = "\x1b[1;2C"
    SHIFT_LEFT = "\x1b[1;2D"

    # Alt + Arrow
    ALT_UP = "\x1b[1;3A"
    ALT_DOWN = "\x1b[1;3B"
    ALT_RIGHT = "\x1b[1;3C"
    ALT_LEFT = "\x1b[1;3D"

    # Ctrl + Arrow
    CTRL_UP = "\x1b[1;5A"
    CTRL_DOWN = "\x1b[1;5B"
    CTRL_RIGHT = "\x1b[1;5C"
    CTRL_LEFT = "\x1b[1;5D"

    # ==========================================================================
    # Function Keys (F1-F12)
    # ==========================================================================
    F1 = "\x1bOP"
    F2 = "\x1bOQ"
    F3 = "\x1bOR"
    F4 = "\x1bOS"
    F5 = "\x1b[15~"
    F6 = "\x1b[17~"
    F7 = "\x1b[18~"
    F8 = "\x1b[19~"
    F9 = "\x1b[20~"
    F10 = "\x1b[21~"
    F11 = "\x1b[23~"
    F12 = "\x1b[24~"

    # ==========================================================================
    # Navigation Keys
    # ==========================================================================
    HOME = "\x1b[H"
    END = "\x1b[F"
    PAGE_UP = "\x1b[5~"
    PAGE_DOWN = "\x1b[6~"

    # Alternative sequences (some terminals)
    HOME_ALT = "\x1b[1~"
    END_ALT = "\x1b[4~"

    # Application mode navigation
    HOME_APP = "\x1bOH"
    END_APP = "\x1bOF"

    # ==========================================================================
    # Tab Variations
    # ==========================================================================
    SHIFT_TAB = "\x1b[Z"  # Backtab

    # ==========================================================================
    # Common Characters (for readability)
    # ==========================================================================
    SPACE = " "

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    @staticmethod
    def meta(key: str) -> str:
        """
        Create a Meta/Alt key combination (ESC + key).

        Args:
            key: The key to combine with Meta/Alt

        Returns:
            The escape sequence for Meta + key

        Example:
            Keys.meta('d')  # Alt+D -> '\\x1bd'
            Keys.meta('f')  # Alt+F (forward word in readline)
        """
        return f"\x1b{key}"

    @staticmethod
    def ctrl(key: str) -> str:
        """
        Create a Ctrl key combination.

        Args:
            key: The character to combine with Ctrl.
                 Can be a letter (a-z) or symbol ([, \\, ], etc.)

        Returns:
            The control character

        Example:
            Keys.ctrl('c')  # Ctrl+C -> '\\x03'
            Keys.ctrl('[')  # Ctrl+[ -> '\\x1b' (ESC)
        """
        if len(key) != 1:
            raise ValueError("Key must be a single character")

        # Standard ASCII control character generation
        # Takes the character code and masks bits 6 and 7 (0x1f = 00011111)
        # This works for a-z, A-Z, [, \, ], ^, _, @
        return chr(ord(key.upper()) & 0x1F)

    @staticmethod
    def alt(key: str) -> str:
        """
        Alias for meta() - Create an Alt key combination.

        Args:
            key: The key to combine with Alt

        Returns:
            The escape sequence for Alt + key
        """
        return Keys.meta(key)

    @staticmethod
    def repeat(key: str, count: int) -> str:
        """
        Repeat a key sequence multiple times.

        Args:
            key: The key sequence to repeat
            count: Number of times to repeat

        Returns:
            The repeated key sequence
        """
        return key * count

    @staticmethod
    def sequence(*keys: str) -> str:
        """
        Combine multiple key sequences into one.

        Args:
            keys: Variable number of key sequences

        Returns:
            Combined key sequence
        """
        return "".join(keys)


class MacKeys(Keys):
    """
    macOS-specific key combinations using Option key.

    On macOS, Option (Alt) key combinations are sent as ESC + key,
    same as Meta key on other systems.
    """

    # Common Option + letter combinations
    OPT_B = Keys.meta("b")  # Back word
    OPT_D = Keys.meta("d")  # Delete word forward
    OPT_F = Keys.meta("f")  # Forward word
    OPT_L = Keys.meta("l")  # Lowercase word
    OPT_T = Keys.meta("t")  # Transpose words
    OPT_U = Keys.meta("u")  # Uppercase word

    # Option + Backspace
    OPT_BACKSPACE = Keys.meta("\x7f")  # Delete word backward


class ReadlineKeys:
    """
    Key bindings for readline (bash, zsh, and other shells).

    These are the default Emacs-style bindings. Vi mode uses different bindings.
    """

    # Movement
    BEGINNING_OF_LINE = Keys.CTRL_A
    END_OF_LINE = Keys.CTRL_E
    FORWARD_CHAR = Keys.CTRL_F
    BACKWARD_CHAR = Keys.CTRL_B
    FORWARD_WORD = Keys.meta("f")
    BACKWARD_WORD = Keys.meta("b")
    CLEAR_SCREEN = Keys.CTRL_L

    # History
    PREVIOUS_HISTORY = Keys.CTRL_P
    NEXT_HISTORY = Keys.CTRL_N
    REVERSE_SEARCH = Keys.CTRL_R
    FORWARD_SEARCH = Keys.CTRL_S

    # Editing
    DELETE_CHAR = Keys.CTRL_D
    BACKWARD_DELETE_CHAR = Keys.BACKSPACE
    KILL_LINE = Keys.CTRL_K
    UNIX_LINE_DISCARD = Keys.CTRL_U
    KILL_WORD = Keys.meta("d")
    BACKWARD_KILL_WORD = Keys.CTRL_W
    TRANSPOSE_CHARS = Keys.CTRL_T

    # Yank (paste)
    YANK = Keys.CTRL_Y

    # Completion
    COMPLETE = Keys.TAB

    # Misc
    ACCEPT_LINE = Keys.ENTER
    ABORT = Keys.CTRL_G
    INTERRUPT = Keys.CTRL_C
    SUSPEND = Keys.CTRL_Z
