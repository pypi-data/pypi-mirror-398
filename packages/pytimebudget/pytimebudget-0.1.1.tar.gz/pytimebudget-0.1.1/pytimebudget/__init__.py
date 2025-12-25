from .core import TimeBudget

def pytimebudget(name=None, max_ms=None, warn_only=False, tags=None):
    return TimeBudget(
        name=name,
        max_ms=max_ms,
        warn_only=warn_only,
        tags=tags,
    )

__all__ = ["pytimebudget", "TimeBudget"]
