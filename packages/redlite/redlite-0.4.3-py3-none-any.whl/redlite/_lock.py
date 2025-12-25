import contextlib
import os
import json
import time
from ._util import redlite_data_dir
from collections.abc import Iterator

__all__ = ["incr_run_count"]


@contextlib.contextmanager
def file_lock(fname: str) -> Iterator[None]:
    lockfile = fname + ".lock"
    while True:
        try:
            fd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            with os.fdopen(fd, "a") as f:
                f.write(f"Locked by {os.getpid()}\n")
            yield
            os.unlink(lockfile)
            break
        except FileExistsError:
            time.sleep(0.25)


def incr_run_count() -> int:
    fname = os.path.join(redlite_data_dir(), "count.json")
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    with file_lock(fname):
        if not os.path.isfile(fname):
            count = 0
        else:
            with open(fname, "r", encoding="utf-8") as f:
                count = json.load(f)

        count += 1
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(count, f)
        return count
