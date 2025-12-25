import time
from .config import ENABLED
from .utils import resolve_name
from .storage import store_sample
from .analyzer import analyze

class TimeBudget:
    def __init__(self, name, max_ms, warn_only=False, tags=None):
        self.enabled = ENABLED
        if not self.enabled:
            return

        self.name = name or resolve_name()
        self.max_ms = max_ms
        self.warn_only = warn_only
        self.start = time.perf_counter()

    def stop(self):
        if not self.enabled:
            return None

        elapsed_ms = (time.perf_counter() - self.start) * 1000

        record = {
            "name": self.name,
            "elapsed_ms": elapsed_ms,
            "max_ms": self.max_ms,
            "timestamp": time.time(),
        }

        try:
            store_sample(record)
            analyze(record, self.warn_only)
        except Exception:
            pass

        return elapsed_ms

    # sync context
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()

    # async context
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.stop()
