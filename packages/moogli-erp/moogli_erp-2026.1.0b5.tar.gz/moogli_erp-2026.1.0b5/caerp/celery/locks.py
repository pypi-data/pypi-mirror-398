import time
from pathlib import Path
from typing import Optional

from .conf import get_setting


def _get_lock_path(lockname: str) -> Path:
    cache_dir = get_setting("caerp.static_tmp", default="/tmp")
    directory = Path(cache_dir)
    return directory.joinpath(f"{lockname}.lock")


def _get_file_age(path: Path) -> int:
    return int(time.time() - path.stat().st_mtime)


def is_locked(lockname, max_age: Optional[int] = 3600):
    """
    lockname: the name of the lock
    max_age: the maximum age of the lock file in seconds
    """
    p = _get_lock_path(lockname)
    result = p.exists()
    if result and max_age is not None and _get_file_age(p) > max_age:
        p.unlink(missing_ok=True)
        result = False
    return result


def acquire_lock(lockname):
    p = _get_lock_path(lockname)
    p.touch()


def release_lock(lockname):
    p = _get_lock_path(lockname)
    p.unlink(missing_ok=True)
