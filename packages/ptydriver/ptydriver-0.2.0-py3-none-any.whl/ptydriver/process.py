"""
PtyProcess - Core class for driving interactive terminal applications.

This module provides a simple, reliable way to control interactive CLI
applications (TUI apps, REPLs, shells, etc.) by spawning them in a PTY
and maintaining a virtual terminal screen.

Example:
    from ptydriver import PtyProcess, Keys

    # Drive any interactive CLI
    with PtyProcess(["python3"]) as proc:
        proc.send("print('hello')")
        proc.wait_for("hello")

    # Drive multiple instances
    procs = [PtyProcess(["claude"]) for _ in range(3)]
    for proc in procs:
        proc.send("What is 2+2?")
"""

import re
import select
import time
from threading import Condition, RLock, Thread
from typing import Any, Dict, Iterator, List, Literal, Optional, Pattern, Tuple, Union

import pyte
from ptyprocess import PtyProcess as PtyProcessNative


class PtyProcess:
    """
    Drives an interactive terminal application via PTY.

    This class spawns CLI processes directly via ptyprocess and maintains a
    virtual terminal screen using pyte. Designed for programmatic control
    of interactive applications like shells, REPLs, TUI apps, and AI agents.

    Example:
        with PtyProcess(["bash", "--norc"]) as proc:
            proc.send("echo hello")
            proc.wait_for("hello")

        # Test fzf
        with PtyProcess(["fzf"]) as proc:
            proc.send_raw("test")
            proc.wait_for("test")

    Attributes:
        command: Command and arguments being executed
        width: Terminal width in characters
        height: Terminal height in characters
        timeout: Default timeout for operations
    """

    def __init__(
        self,
        command: List[str],
        width: int = 120,
        height: int = 40,
        timeout: int = 5,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ):
        """
        Create a PTY process for driving an interactive application.

        Args:
            command: Command and arguments to execute (e.g., ["bash", "--norc"])
            width: Terminal width in characters
            height: Terminal height in characters
            timeout: Default timeout for operations in seconds
            env: Environment variables (None = inherit from parent)
            cwd: Working directory (None = current directory)
        """
        self.command = command
        self.width = width
        self.height = height
        self.timeout = timeout
        self.env = env
        self.cwd = cwd

        # Track cleanup state
        self._is_cleaned_up = False

        # Initialize attributes that cleanup() depends on
        self.process: Optional[PtyProcessNative] = None
        self._stop_thread = False
        self._update_thread: Optional[Thread] = None

        # Virtual terminal screen (using pyte)
        self.screen = pyte.Screen(width, height)
        self.stream = pyte.Stream(self.screen)

        # Concurrency primitives
        # RLock allows the same thread (main) to acquire lock recursively,
        # which is needed if we call get_content() inside a with screen_updated block.
        self.screen_lock = RLock()
        self.screen_updated = Condition(self.screen_lock)

        # Spawn process using ptyprocess
        # ptyprocess.spawn takes list of arguments
        self.process = PtyProcessNative.spawn(command, cwd=cwd, env=env, dimensions=(height, width))

        # Start background thread to update screen
        self._update_thread = Thread(target=self._update_screen_loop, daemon=True)
        self._update_thread.start()

        # Give process time to start
        time.sleep(0.1)

    def _update_screen_loop(self) -> None:
        """
        Background thread to continuously feed process output to virtual screen.

        This keeps the pyte screen in sync with the actual process output.
        """
        while not self._stop_thread:
            try:
                # Check if process is alive or has data
                if self.process and self.process.isalive():
                    # Use select to wait for data (non-blocking check)
                    # We wait up to 0.05s
                    r, _, _ = select.select([self.process.fd], [], [], 0.05)

                    if r:
                        try:
                            # Read bytes directly
                            data_bytes = self.process.read(4096)
                            if data_bytes:
                                # Decode bytes to string for pyte.Stream
                                data_str = data_bytes.decode("utf-8", errors="ignore")
                                # Feed to pyte screen in chunks to avoid holding lock too long
                                chunk_size = 1024
                                for i in range(0, len(data_str), chunk_size):
                                    chunk = data_str[i : i + chunk_size]
                                    with self.screen_lock:
                                        self.stream.feed(chunk)
                                        self.screen_updated.notify_all()
                                    # Yield to allow readers to acquire lock
                                    time.sleep(0)
                        except EOFError:
                            # Process ended
                            break
                        except OSError:
                            # File descriptor issue
                            break
                else:
                    break
            except Exception:
                # Process might be dead
                break

            # If no data was read, sleep briefly to prevent tight loop
            time.sleep(0.01)

    def send(self, text: str, delay: float = 0.15, press_enter: bool = True) -> None:
        """
        Send text to the process.

        Args:
            text: Text to send
            delay: Delay after sending (seconds)
            press_enter: If True (default), append Enter key after text.
                        If False, send text as-is.
        """
        if not self.process or not self.process.isalive():
            raise RuntimeError("Process not running")

        # ptyprocess.write takes bytes
        self.process.write(text.encode("utf-8"))
        if press_enter:
            self.process.write(b"\r")
        time.sleep(delay)

    def send_raw(self, sequence: str, delay: float = 0.15) -> None:
        """
        Send raw string sequences or escape codes to the process.

        Use this for special keys, control characters, and escape sequences.
        The sequence string will be encoded to UTF-8 bytes before sending.

        Args:
            sequence: Raw string to send (can include escape sequences)
            delay: Delay after sending for processing (seconds)
        """
        if not self.process or not self.process.isalive():
            raise RuntimeError("Process not running")

        self.process.write(sequence.encode("utf-8"))
        time.sleep(delay)

    def send_bytes(self, data: bytes, delay: float = 0.15) -> None:
        """
        Send raw bytes directly to the process.

        This is useful for binary data or specific low-level control sequences
        that are not suitable for string encoding.

        Args:
            data: Raw bytes to send
            delay: Delay after sending for processing (seconds)
        """
        if not self.process or not self.process.isalive():
            raise RuntimeError("Process not running")

        self.process.write(data)
        time.sleep(delay)

    def get_content(self) -> str:
        """
        Get visible terminal content from virtual screen.

        Returns:
            Text content of the current screen as a single string
        """
        with self.screen_lock:
            lines = []
            for line in self.screen.display:
                lines.append(line)
            return "\n".join(lines)

    def get_screen(self) -> List[str]:
        """
        Get the current screen as a list of lines.

        Returns:
            List of lines (strings) representing the screen
        """
        with self.screen_lock:
            return list(self.screen.display)

    def get_cursor_position(self) -> tuple[int, int]:
        """
        Get current cursor position.

        Returns:
            Tuple of (x, y) where x is column and y is row
        """
        with self.screen_lock:
            return (self.screen.cursor.x, self.screen.cursor.y)

    def set_size(self, width: int, height: int) -> None:
        """
        Resize the terminal window.

        Args:
            width: New width in columns
            height: New height in rows
        """
        with self.screen_lock:
            self.width = width
            self.height = height
            self.screen.resize(height, width)
            if self.process and self.process.isalive():
                self.process.setwinsize(height, width)

    def wait_for(
        self,
        pattern: Union[str, Pattern[str]],
        timeout: Optional[float] = None,
    ) -> bool:
        """
        Wait for text or regex pattern to appear in terminal content.

        Args:
            pattern: Text string or compiled regex pattern to wait for
            timeout: Max seconds to wait (None = use default)

        Returns:
            True if pattern matches within timeout

        Raises:
            TimeoutError: If pattern doesn't match within timeout
        """
        timeout = timeout if timeout is not None else self.timeout
        end_time = time.time() + timeout

        with self.screen_updated:
            while True:
                # Check content directly (we hold the lock)
                lines = []
                for line in self.screen.display:
                    lines.append(line)
                content = "\n".join(lines)

                if isinstance(pattern, str):
                    if pattern in content:
                        return True
                elif isinstance(pattern, re.Pattern):
                    if pattern.search(content):
                        return True

                remaining = end_time - time.time()
                if remaining <= 0:
                    # Truncate content for error message to prevent huge log spam
                    display_content = (
                        content if len(content) < 1000 else content[:1000] + "\n... (truncated)"
                    )
                    pattern_desc = pattern if isinstance(pattern, str) else pattern.pattern
                    raise TimeoutError(
                        f"Pattern '{pattern_desc}' did not match within {timeout}s.\n"
                        f"Current content:\n{display_content}"
                    )

                self.screen_updated.wait(remaining)

    def contains(self, pattern: Union[str, Pattern[str]]) -> bool:
        """
        Check if text or regex pattern is currently visible on screen.

        Args:
            pattern: Text string or compiled regex pattern to search for

        Returns:
            True if pattern is found on screen, False otherwise
        """
        content = self.get_content()
        if isinstance(pattern, str):
            return pattern in content
        elif isinstance(pattern, re.Pattern):
            return bool(pattern.search(content))
        return False

    def expect_any(
        self,
        patterns: List[Union[str, Pattern[str]]],
        timeout: Optional[float] = None,
    ) -> Tuple[int, str]:
        """
        Wait for any of the provided patterns to appear in terminal content.

        Args:
            patterns: A list of string or compiled regex patterns to wait for.
            timeout: Max seconds to wait (None = use default).

        Returns:
            A tuple (index, matched_string) where index is the 0-based index
            of the first pattern that matched, and matched_string is the
            content of the screen at the time of the match.

        Raises:
            TimeoutError: If none of the patterns appear within timeout.
        """
        timeout = timeout if timeout is not None else self.timeout
        end_time = time.time() + timeout

        with self.screen_updated:
            while True:
                content = "\n".join(line for line in self.screen.display)

                for i, pattern in enumerate(patterns):
                    if isinstance(pattern, str):
                        if pattern in content:
                            return (i, content)
                    elif isinstance(pattern, re.Pattern):
                        if pattern.search(content):
                            return (i, content)

                remaining = end_time - time.time()
                if remaining <= 0:
                    pattern_descs = [p if isinstance(p, str) else p.pattern for p in patterns]
                    display_content = (
                        content if len(content) < 1000 else content[:1000] + "\n... (truncated)"
                    )
                    raise TimeoutError(
                        f"None of patterns '{pattern_descs}' matched within {timeout}s.\n"
                        f"Current content:\n{display_content}"
                    )

                self.screen_updated.wait(remaining)

    def expect_sequence(
        self,
        patterns: List[Union[str, Pattern[str]]],
        timeout: Optional[float] = None,
    ) -> List[str]:
        """
        Wait for a sequence of patterns to appear in terminal content, one after another.

        Each pattern must appear after the previous one.

        Args:
            patterns: A list of string or compiled regex patterns to wait for.
            timeout: Max seconds to wait for each pattern (None = use default).

        Returns:
            A list of matched strings for each pattern in the sequence.

        Raises:
            TimeoutError: If any pattern in the sequence does not appear within timeout.
        """
        matched_contents: List[str] = []
        current_timeout = timeout if timeout is not None else self.timeout

        for i, pattern in enumerate(patterns):
            end_time = time.time() + current_timeout
            found_match = False

            with self.screen_updated:
                while True:
                    content = "\n".join(line for line in self.screen.display)

                    if isinstance(pattern, str):
                        if pattern in content:
                            matched_contents.append(content)
                            found_match = True
                            break
                    elif isinstance(pattern, re.Pattern):
                        if pattern.search(content):
                            matched_contents.append(content)
                            found_match = True
                            break

                    remaining = end_time - time.time()
                    if remaining <= 0:
                        pattern_desc = pattern if isinstance(pattern, str) else pattern.pattern
                        display_content = (
                            content if len(content) < 1000 else content[:1000] + "\n... (truncated)"
                        )
                        raise TimeoutError(
                            f"Pattern '{pattern_desc}' (step {i + 1} in sequence) did not match within {current_timeout}s.\n"
                            f"Current content:\n{display_content}"
                        )

                    self.screen_updated.wait(remaining)

            if not found_match:
                # This should ideally be caught by TimeoutError, but as a safeguard
                raise RuntimeError(f"Unexpected error: Pattern '{pattern}' not found in sequence.")

        return matched_contents

    def is_alive(self) -> bool:
        """
        Check if the process is still running.

        Returns:
            True if process is running, False otherwise
        """
        return self.process is not None and self.process.isalive()

    def terminate(self, force: bool = False) -> None:
        """
        Terminate the process.

        Args:
            force: If True, forcefully kill the process
        """
        if self.process and self.process.isalive():
            self.process.terminate(force=force)

    def cleanup(self) -> None:
        """
        Clean up the process and resources.

        MUST be called to prevent orphaned processes.
        Automatically called when using context manager.
        """
        if self._is_cleaned_up:
            return

        self._is_cleaned_up = True

        # Stop update thread
        self._stop_thread = True
        if self._update_thread and self._update_thread.is_alive():
            self._update_thread.join(timeout=1.0)

        # Kill process
        if self.process:
            try:
                if self.process.isalive():
                    self.process.terminate(force=True)
                self.process.close()
            except (OSError, Exception):
                pass

    def __enter__(self) -> "PtyProcess":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> Literal[False]:
        """Context manager exit - ensure cleanup."""
        self.cleanup()
        return False


class ProcessPool:
    """
    Manages multiple PtyProcess instances for parallel execution.

    Useful for driving multiple instances of interactive applications
    simultaneously, like running multiple AI agents in parallel.

    Example:
        pool = ProcessPool()

        # Add 3 Claude instances
        for i in range(3):
            pool.add(["claude"], name=f"claude-{i}")

        # Send to all
        pool.broadcast("What is 2+2?")

        # Wait for responses
        for name, proc in pool.processes.items():
            proc.wait_for("4")

        pool.cleanup()
    """

    def __init__(self) -> None:
        """Initialize an empty process pool."""
        self.processes: Dict[str, PtyProcess] = {}
        self._counter = 0

    def add(
        self,
        command: List[str],
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> PtyProcess:
        """
        Add a new process to the pool.

        Args:
            command: Command to execute
            name: Optional name for the process (auto-generated if None)
            **kwargs: Additional arguments passed to PtyProcess

        Returns:
            The created PtyProcess instance
        """
        if name is None:
            name = f"proc-{self._counter}"
            self._counter += 1

        proc = PtyProcess(command, **kwargs)
        self.processes[name] = proc
        return proc

    def get(self, name: str) -> Optional[PtyProcess]:
        """
        Get a process by name.

        Args:
            name: Process name

        Returns:
            PtyProcess instance or None if not found
        """
        return self.processes.get(name)

    def broadcast(self, text: str, delay: float = 0.15, press_enter: bool = True) -> None:
        """
        Send text to all processes in the pool.

        Args:
            text: Text to send
            delay: Delay after sending
            press_enter: Whether to press Enter after text
        """
        for proc in self.processes.values():
            if proc.is_alive():
                proc.send(text, delay=delay, press_enter=press_enter)

    def broadcast_raw(self, sequence: str, delay: float = 0.15) -> None:
        """
        Send raw sequence to all processes in the pool.

        Args:
            sequence: Raw sequence to send
            delay: Delay after sending
        """
        for proc in self.processes.values():
            if proc.is_alive():
                proc.send_raw(sequence, delay=delay)

    def all_contain(self, text: str) -> bool:
        """
        Check if all processes contain the given text.

        Args:
            text: Text to search for

        Returns:
            True if all processes contain the text
        """
        return all(proc.contains(text) for proc in self.processes.values())

    def any_contains(self, text: str) -> bool:
        """
        Check if any process contains the given text.

        Args:
            text: Text to search for

        Returns:
            True if any process contains the text
        """
        return any(proc.contains(text) for proc in self.processes.values())

    def cleanup(self) -> None:
        """Clean up all processes in the pool."""
        for proc in self.processes.values():
            proc.cleanup()
        self.processes.clear()

    def __enter__(self) -> "ProcessPool":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> Literal[False]:
        """Context manager exit - ensure cleanup."""
        self.cleanup()
        return False

    def __len__(self) -> int:
        """Return number of processes in pool."""
        return len(self.processes)

    def __iter__(self) -> Iterator[PtyProcess]:
        """Iterate over processes."""
        return iter(self.processes.values())
