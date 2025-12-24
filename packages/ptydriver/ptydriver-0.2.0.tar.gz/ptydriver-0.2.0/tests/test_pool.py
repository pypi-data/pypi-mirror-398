"""
Tests for ProcessPool.
"""

import re

from ptydriver import ProcessPool


class TestProcessPool:
    """Tests for managing multiple processes."""

    def test_pool_lifecycle(self):
        """Add, get, and cleanup."""
        pool = ProcessPool()
        proc = pool.add(["echo", "hi"])
        assert len(pool) == 1
        assert pool.get("proc-0") == proc
        pool.cleanup()
        assert not proc.is_alive()

    def test_named_processes(self):
        """Can retrieve processes by custom name."""
        with ProcessPool() as pool:
            p1 = pool.add(["bash", "--norc"], name="worker-1")
            p2 = pool.add(["bash", "--norc"], name="worker-2")
            assert pool.get("worker-1") == p1
            assert pool.get("worker-2") == p2

    def test_broadcast(self):
        """Broadcast sends to all processes."""
        with ProcessPool() as pool:
            pool.add(["bash", "--norc"], name="a")
            pool.add(["bash", "--norc"], name="b")

            # Wait for readiness
            prompt = re.compile(r"[\$#]")
            for proc in pool:
                proc.wait_for(prompt)

            pool.broadcast("echo 'ALL_HEAR_THIS'")

            # Verify
            for proc in pool:
                proc.wait_for("ALL_HEAR_THIS")

    def test_any_all_contains(self):
        """Test aggregation checks."""
        with ProcessPool() as pool:
            p1 = pool.add(["bash", "--norc"], name="a")
            p2 = pool.add(["bash", "--norc"], name="b")

            prompt = re.compile(r"[\$#]")
            for proc in pool:
                proc.wait_for(prompt)

            p1.send("echo 'ONE'")
            p1.wait_for("ONE")

            assert pool.any_contains("ONE")
            assert not pool.all_contain("ONE")

            p2.send("echo 'ONE'")
            p2.wait_for("ONE")

            assert pool.all_contain("ONE")
