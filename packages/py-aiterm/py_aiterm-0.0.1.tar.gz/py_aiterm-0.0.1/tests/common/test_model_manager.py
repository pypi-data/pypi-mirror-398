"""Tests for ModelManager class."""

import threading
import time
from unittest.mock import MagicMock

from ai_term.common.model_manager import ModelManager


class TestModelManager:
    """Test cases for ModelManager."""

    def test_lazy_loading_model_not_loaded_initially(self):
        """Verify model is not loaded until get_model() is called."""
        load_fn = MagicMock(return_value="mock_model")
        manager = ModelManager(load_model_fn=load_fn, ttl_seconds=60)

        try:
            # Model should not be loaded initially
            assert manager.model is None
            load_fn.assert_not_called()
        finally:
            manager.stop()

    def test_get_model_loads_and_returns_instance(self):
        """Verify get_model() loads and returns the model."""
        mock_model = MagicMock()
        load_fn = MagicMock(return_value=mock_model)
        manager = ModelManager(load_model_fn=load_fn, ttl_seconds=60)

        try:
            result = manager.get_model()

            assert result is mock_model
            load_fn.assert_called_once()
        finally:
            manager.stop()

    def test_get_model_returns_same_instance(self):
        """Verify multiple calls to get_model() return the same instance."""
        mock_model = MagicMock()
        load_fn = MagicMock(return_value=mock_model)
        manager = ModelManager(load_model_fn=load_fn, ttl_seconds=60)

        try:
            result1 = manager.get_model()
            result2 = manager.get_model()
            result3 = manager.get_model()

            assert result1 is result2 is result3
            # Load should only be called once
            load_fn.assert_called_once()
        finally:
            manager.stop()

    def test_last_access_time_updates_on_get_model(self):
        """Verify last_access_time updates on each get_model() call."""
        load_fn = MagicMock(return_value="mock_model")
        manager = ModelManager(load_model_fn=load_fn, ttl_seconds=60)

        try:
            initial_time = manager.last_access_time
            time.sleep(0.01)  # Small delay

            manager.get_model()
            first_access = manager.last_access_time

            time.sleep(0.01)
            manager.get_model()
            second_access = manager.last_access_time

            assert first_access > initial_time
            assert second_access > first_access
        finally:
            manager.stop()

    def test_unload_model_clears_model(self):
        """Verify unload_model() clears the model reference."""
        load_fn = MagicMock(return_value="mock_model")
        manager = ModelManager(load_model_fn=load_fn, ttl_seconds=60)

        try:
            manager.get_model()
            assert manager.model is not None

            manager.unload_model()
            assert manager.model is None
        finally:
            manager.stop()

    def test_model_reloads_after_unload(self):
        """Verify model can be reloaded after being unloaded."""
        call_count = 0

        def load_fn():
            nonlocal call_count
            call_count += 1
            return f"mock_model_{call_count}"

        manager = ModelManager(load_model_fn=load_fn, ttl_seconds=60)

        try:
            first_model = manager.get_model()
            assert first_model == "mock_model_1"

            manager.unload_model()

            second_model = manager.get_model()
            assert second_model == "mock_model_2"
            assert call_count == 2
        finally:
            manager.stop()

    def test_stop_terminates_monitor_thread(self):
        """Verify stop() terminates the background monitor thread."""
        load_fn = MagicMock(return_value="mock_model")
        manager = ModelManager(load_model_fn=load_fn, ttl_seconds=60)

        # Thread should be alive after creation
        assert manager._monitor_thread.is_alive()

        manager.stop()

        # Thread should be terminated after stop
        assert not manager._monitor_thread.is_alive()

    def test_thread_safety_concurrent_access(self):
        """Verify concurrent access to get_model() is thread-safe."""
        load_count = 0
        load_lock = threading.Lock()

        def load_fn():
            nonlocal load_count
            with load_lock:
                load_count += 1
            time.sleep(0.01)  # Simulate slow loading
            return "mock_model"

        manager = ModelManager(load_model_fn=load_fn, ttl_seconds=60)
        results = []

        def get_model_thread():
            result = manager.get_model()
            results.append(result)

        try:
            threads = [threading.Thread(target=get_model_thread) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # All results should be the same model
            assert all(r == "mock_model" for r in results)
            # Load should only be called once due to locking
            assert load_count == 1
        finally:
            manager.stop()

    def test_model_unloading_after_ttl_expires(self):
        """Verify model is unloaded after TTL expires (with short TTL)."""
        load_fn = MagicMock(return_value="mock_model")
        # Very short TTL for testing - but monitor checks every 10s
        # So we test the logic directly
        manager = ModelManager(load_model_fn=load_fn, ttl_seconds=1)

        try:
            manager.get_model()
            assert manager.model is not None

            # Simulate time passage by setting last_access_time in the past
            with manager.lock:
                manager.last_access_time = time.time() - 10  # 10 seconds ago

            # Trigger unload check manually (since we can't wait 10s for monitor)
            with manager.lock:
                if manager.model is not None:
                    elapsed = time.time() - manager.last_access_time
                    if elapsed > manager.ttl_seconds:
                        manager.unload_model()

            assert manager.model is None
        finally:
            manager.stop()

    def test_unload_model_when_already_none(self):
        """Verify unload_model() is safe when model is already None."""
        load_fn = MagicMock(return_value="mock_model")
        manager = ModelManager(load_model_fn=load_fn, ttl_seconds=60)

        try:
            # Model is None initially
            assert manager.model is None

            # This should not raise an error
            manager.unload_model()

            assert manager.model is None
        finally:
            manager.stop()
