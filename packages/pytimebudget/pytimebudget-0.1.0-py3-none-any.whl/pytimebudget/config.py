import os
from pathlib import Path

ENABLED = os.getenv("PYTIMEBUDGET", "1") == "1"

DATA_DIR = Path(
    os.getenv("PYTIMEBUDGET_DIR", Path.home() / ".pytimebudget")
)
