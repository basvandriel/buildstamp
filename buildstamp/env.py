from __future__ import annotations

import os
from pathlib import Path


def envvar_to_bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() not in ("", "0", "false", "no")


def load_dotenv(root: Path) -> None:
    dotenv_path = root / ".env"
    if not dotenv_path.exists():
        return

    try:
        import dotenv

        dotenv.load_dotenv(dotenv_path, override=False)
    except ImportError:
        return
