import json
from pathlib import Path

APP_NAME = "pincode_package"


def get_cache_path():
    """
    Returns OS-safe cache path and creates it if missing
    """
    base_dir = Path.home() / ".cache" / APP_NAME
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "cache.json"


def load_cache():
    path = get_cache_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(cache):
    path = get_cache_path()
    path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
