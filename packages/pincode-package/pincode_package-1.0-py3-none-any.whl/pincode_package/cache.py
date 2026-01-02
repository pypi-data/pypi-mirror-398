import json
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

APP_NAME = "pincode_package"
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days


def _cache_file() -> Path:
    base = Path.home() / ".cache" / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base / "cache.json"


def load_cache() -> dict:
    path = _cache_file()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def get_cached_pincode(pincode: str):
    cache = load_cache()
    entry = cache.get(str(pincode))

    if not entry:
        return None

    age = time.time() - entry["timestamp"]
    if age > CACHE_TTL_SECONDS:
        logger.info("Cache expired for pincode %s", pincode)
        return None

    logger.info("Cache hit for pincode %s", pincode)
    return entry["data"]


def save_cached_pincode(pincode: str, data):
    cache = load_cache()
    cache[str(pincode)] = {
        "timestamp": time.time(),
        "data": data
    }
    _cache_file().write_text(json.dumps(cache, indent=2), encoding="utf-8")
