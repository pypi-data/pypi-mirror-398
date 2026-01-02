import logging
import threading
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages a single model with lazy loading and automatic unloading after inactivity.
    """

    def __init__(self, load_model_fn: Callable[[], Any], ttl_seconds: int = 300):
        self.load_model_fn = load_model_fn
        self.ttl_seconds = ttl_seconds
        self.model = None
        self.last_access_time = 0
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def get_model(self) -> Any:
        """
        Returns the model instance. Loads it if not already loaded.
        Updates the last access time.
        """
        with self.lock:
            self.last_access_time = time.time()
            if self.model is None:
                logger.info("> Loading model...")
                self.model = self.load_model_fn()
                logger.info("> Model loaded.")
            return self.model

    def _monitor_loop(self):
        """
        Background loop to check for inactivity and unload the model.
        """
        while not self._stop_event.is_set():
            time.sleep(10)  # Check every 10 seconds
            with self.lock:
                if self.model is not None:
                    elapsed = time.time() - self.last_access_time
                    if elapsed > self.ttl_seconds:
                        logger.info(
                            f"> Model inactive for {elapsed:.1f}s. Unloading..."
                        )
                        self.unload_model()

    def unload_model(self):
        """
        Unloads the model to free memory.
        """
        # This method is called within a lock (from _monitor_loop)
        # or can be called monitoring logic logic needs to be careful about lock
        # re-entrancy if called externally. But here _monitor_loop has the lock.
        if self.model is not None:
            # If the model has specific cleanup, we might need a cleanup_fn.
            # For now, just setting to None allows GC to reclaim it.
            # PyTorch models might need explicit empty_cache() or similar if strictly
            # managing GPU, but standard GC usually works for CPU or if we just drop
            # references. For MPS/CUDA, explicit gc.collect() and
            # torch.cuda.empty_cache() might be good.
            del self.model
            self.model = None
            logger.info("> Model unloaded.")

    def stop(self):
        self._stop_event.set()
        self._monitor_thread.join()
