import hashlib
from pathlib import Path

def find_project_root():
    path = Path.cwd()

    for parent in [path] + list(path.parents):
        if (parent / ".git").exists():
            return parent
        if (parent / "pyproject.toml").exists():
            return parent
        if (parent / "setup.py").exists():
            return parent

    return path

def project_id():
    root = find_project_root()
    h = hashlib.sha256(str(root).encode()).hexdigest()
    return h[:16]
