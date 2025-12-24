"""
ptydriver - Programmatically drive interactive terminal applications via PTY.

This library provides a simple, reliable way to control interactive CLI
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

from .keys import Keys, MacKeys, ReadlineKeys
from .process import ProcessPool, PtyProcess

__all__ = [
    "PtyProcess",
    "ProcessPool",
    "Keys",
    "MacKeys",
    "ReadlineKeys",
]

__version__ = "0.2.0"
