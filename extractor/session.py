import json
import logging
from pathlib import Path
from typing import Optional
from config.settings import SESSION_FILE

logger = logging.getLogger(__name__)


def is_session_available(session_path: Optional[Path] = None) -> bool:
    """Checks whether a saved session file exists and contains valid cookies."""
    path = session_path or SESSION_FILE
    if not path.exists():
        return False

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            cookies = data.get("cookies", [])
            has_auth = any(c.get("name") in ("auth_token", "ct0") for c in cookies)
            return has_auth
    except Exception as e:
        logger.warning(f"Error inspecting session file at {path}: {e}")
        return False


def get_session_path() -> Path:
    """Returns the resolved session path."""
    return SESSION_FILE
