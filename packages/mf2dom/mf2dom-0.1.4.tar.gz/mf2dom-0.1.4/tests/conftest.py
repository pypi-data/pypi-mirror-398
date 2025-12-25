from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
projects_root = repo_root.parent

sys.path.insert(0, str(repo_root / "src"))
try:
    import justhtml  # noqa: F401
except ImportError:
    sys.path.insert(0, str(projects_root / "justhtml" / "src"))
