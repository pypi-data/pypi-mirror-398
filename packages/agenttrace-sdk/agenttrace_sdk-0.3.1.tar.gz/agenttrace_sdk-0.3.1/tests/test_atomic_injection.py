"""
Improved unit tests for What-If Event Injection (atomic pattern)

Key improvements:
- Uses TemporaryDirectory for isolation and automatic cleanup
- Polls for events.jsonl with timeout (avoids flaky timing issues)
- Ensures tracer flushes events to disk before assertions
- Adds barrier timeouts for thread tests
"""

import pytest
import threading
import os
import json
import time

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agenttrace.core.tracer import Tracer, Mode


POLL_TIMEOUT = 3.0
POLL_INTERVAL = 0.05


def wait_for_file(path: str, timeout: float = POLL_TIMEOUT):
    """Wait until path exists or timeout; returns True if exists."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(path):
            return True
        time.sleep(POLL_INTERVAL)
    return False


def read_events(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class TestAtomicInjection:
    """Tests for try_consume_injected_result() atomic behavior"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Reset tracer singleton before each test and point storage to temp dir"""
        Tracer._instance = None
        self.tracer = Tracer.get_instance()
        self.temp_dir = str(tmp_path)
        self.tracer.storage_root = self.temp_dir
        yield
        Tracer._instance = None

    def test_basic_injection_returns_correct_value(self):
        """Verify injection returns the overridden result value"""
        self.tracer.start_recording(
            trace_id="test-123",
            fork_step=2,
            event_override={
                "type": "tool_end",
                "payload": {"tool": "get_market_data", "result": {"price": 100, "trend": "bearish"}}
            },
            skip_instrumentation=True
        )

        injected, result = self.tracer.try_consume_injected_result("get_market_data")

        assert injected is True
        assert result == {"price": 100, "trend": "bearish"}

    def test_non_matching_tool_not_injected(self):
        """Verify injection only applies to the correct tool"""
        self.tracer.start_recording(
            trace_id="test-123",
            fork_step=2,
            event_override={
                "type": "tool_end",
                "payload": {"tool": "get_market_data", "result": {"trend": "bearish"}}
            },
            skip_instrumentation=True
        )

        injected, result = self.tracer.try_consume_injected_result("different_tool")

        assert injected is False
        assert result is None
        assert self.tracer.event_override is not None

    def test_one_time_consumption(self):
        """Verify override is cleared after first use"""
        self.tracer.start_recording(
            trace_id="test-123",
            fork_step=2,
            event_override={
                "type": "tool_end",
                "payload": {"tool": "get_market_data", "result": {"trend": "bearish"}}
            },
            skip_instrumentation=True
        )

        injected1, result1 = self.tracer.try_consume_injected_result("get_market_data")
        injected2, result2 = self.tracer.try_consume_injected_result("get_market_data")

        assert injected1 is True
        assert result1 == {"trend": "bearish"}
        assert injected2 is False
        assert result2 is None

    def test_no_override_returns_false(self):
        """Verify returns (False, None) when no override is set"""
        self.tracer.start_recording(trace_id="test-123", skip_instrumentation=True)

        injected, result = self.tracer.try_consume_injected_result("any_tool")

        assert injected is False
        assert result is None

    def test_string_result_parsing(self):
        """Verify string representation of dict is parsed correctly"""
        self.tracer.start_recording(
            trace_id="test-123",
            fork_step=2,
            event_override={
                "type": "tool_end",
                "payload": {"tool": "get_market_data", "result": "{'price': 100, 'trend': 'bearish'}"}
            },
            skip_instrumentation=True
        )

        injected, result = self.tracer.try_consume_injected_result("get_market_data")

        assert injected is True
        assert result == {'price': 100, 'trend': 'bearish'}


class TestThreadSafety:
    """Tests for thread-safety of atomic injection"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        Tracer._instance = None
        self.tracer = Tracer.get_instance()
        self.temp_dir = str(tmp_path)
        self.tracer.storage_root = self.temp_dir
        yield
        Tracer._instance = None

    def test_only_one_thread_gets_injected_value(self):
        """Verify only one thread successfully consumes the override"""
        self.tracer.start_recording(
            trace_id="test-concurrent",
            fork_step=2,
            event_override={
                "type": "tool_end",
                "payload": {"tool": "get_market_data", "result": {"trend": "bearish"}}
            },
            skip_instrumentation=True
        )

        results = []
        barrier = threading.Barrier(10, timeout=5)

        def try_inject():
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                pass
            injected, result = self.tracer.try_consume_injected_result("get_market_data")
            results.append((injected, result))

        threads = [threading.Thread(target=try_inject) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        injected_count = sum(1 for inj, _ in results if inj)
        assert injected_count == 1, f"Expected 1 injection, got {injected_count}"

        successful = [r for inj, r in results if inj]
        assert len(successful) == 1
        assert successful[0] == {"trend": "bearish"}


class TestCrashResilience:
    """Tests for crash resilience - event persisted before clearing override"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        Tracer._instance = None
        self.tracer = Tracer.get_instance()
        self.temp_dir = str(tmp_path)
        self.tracer.storage_root = self.temp_dir
        yield
        Tracer._instance = None

    def test_event_persisted_to_file(self):
        """Verify injected tool_end event is written to events.jsonl"""
        trace_id = "test-persist"
        self.tracer.start_recording(
            trace_id=trace_id,
            fork_step=2,
            event_override={
                "type": "tool_end",
                "payload": {"tool": "get_market_data", "result": {"trend": "bearish"}}
            },
            skip_instrumentation=True
        )

        injected, result = self.tracer.try_consume_injected_result("get_market_data")
        
        # Flush if available
        if hasattr(self.tracer, "_flush_events_to_disk"):
            self.tracer._flush_events_to_disk()

        events_path = os.path.join(self.temp_dir, trace_id, "events.jsonl")
        assert wait_for_file(events_path), f"Events file not found at {events_path}"

        events = read_events(events_path)

        injected_events = [e for e in events if e.get("type") == "tool_end" and e.get("payload", {}).get("injected")]
        assert len(injected_events) == 1, f"Expected 1 injected event, found {len(injected_events)}"
        assert injected_events[0]["payload"]["tool"] == "get_market_data"
        assert injected_events[0]["payload"]["result"].get("trend") == "bearish"


class TestEventSequencing:
    """Tests for correct event sequence numbering"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        Tracer._instance = None
        self.tracer = Tracer.get_instance()
        self.temp_dir = str(tmp_path)
        self.tracer.storage_root = self.temp_dir
        yield
        Tracer._instance = None

    def test_seq_increments_after_injection(self):
        """Verify _event_seq is incremented after injection"""
        self.tracer.start_recording(
            trace_id="test-seq",
            fork_step=2,
            event_override={
                "type": "tool_end",
                "payload": {"tool": "get_market_data", "result": {"trend": "bearish"}}
            },
            skip_instrumentation=True
        )

        seq_before = int(self.tracer._event_seq)
        injected, result = self.tracer.try_consume_injected_result("get_market_data")
        seq_after = int(self.tracer._event_seq)

        assert injected is True
        assert seq_after == seq_before + 1


class TestMultiToolOverrides:
    """Tests for multi-tool event_overrides dict functionality"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        Tracer._instance = None
        self.tracer = Tracer.get_instance()
        self.temp_dir = str(tmp_path)
        self.tracer.storage_root = self.temp_dir
        yield
        Tracer._instance = None

    def test_multi_tool_basic_injection(self):
        """Verify multi-tool overrides work for basic injection"""
        self.tracer.start_recording(
            trace_id="test-multi",
            fork_step=1,
            event_overrides={
                "get_market_data": {"result": {"price": 100, "trend": "bearish"}},
                "get_weather": {"result": {"temp": 72, "condition": "sunny"}}
            },
            skip_instrumentation=True
        )

        # First tool injection
        injected1, result1 = self.tracer.try_consume_injected_result("get_market_data")
        assert injected1 is True
        assert result1 == {"price": 100, "trend": "bearish"}

        # Second tool injection
        injected2, result2 = self.tracer.try_consume_injected_result("get_weather")
        assert injected2 is True
        assert result2 == {"temp": 72, "condition": "sunny"}

    def test_multi_tool_independent_consumption(self):
        """Verify each tool override is consumed independently"""
        self.tracer.start_recording(
            trace_id="test-multi-consume",
            fork_step=1,
            event_overrides={
                "tool_a": {"result": "value_a"},
                "tool_b": {"result": "value_b"}
            },
            skip_instrumentation=True
        )

        # Consume tool_a
        injected_a, _ = self.tracer.try_consume_injected_result("tool_a")
        assert injected_a is True
        
        # tool_b should still be available
        assert "tool_b" in self.tracer.event_overrides
        
        # Consume tool_b
        injected_b, _ = self.tracer.try_consume_injected_result("tool_b")
        assert injected_b is True
        
        # Both should be consumed now
        assert len(self.tracer.event_overrides) == 0

    def test_multi_tool_non_matching_returns_false(self):
        """Verify non-matching tool returns False but doesn't affect other overrides"""
        self.tracer.start_recording(
            trace_id="test-multi-nomatch",
            fork_step=1,
            event_overrides={
                "tool_a": {"result": "value_a"}
            },
            skip_instrumentation=True
        )

        # Non-matching tool
        injected, result = self.tracer.try_consume_injected_result("tool_b")
        assert injected is False
        assert result is None
        
        # tool_a should still be available
        assert "tool_a" in self.tracer.event_overrides

    def test_multi_tool_takes_priority_over_legacy(self):
        """Verify multi-tool dict takes priority over legacy single override"""
        self.tracer.start_recording(
            trace_id="test-multi-priority",
            fork_step=1,
            event_override={
                "type": "tool_end",
                "payload": {"tool": "shared_tool", "result": "legacy_value"}
            },
            event_overrides={
                "shared_tool": {"result": "multi_value"}
            },
            skip_instrumentation=True
        )

        # Multi-tool should win
        injected, result = self.tracer.try_consume_injected_result("shared_tool")
        assert injected is True
        assert result == "multi_value"
        
        # Legacy should still exist (wasn't consumed)
        assert self.tracer.event_override is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
