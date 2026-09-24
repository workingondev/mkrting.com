"""One shared lock for the timer and local editorial actions."""

import fcntl
from contextlib import contextmanager

from engine import LOCAL


@contextmanager
def editorial_lock():
    LOCAL.mkdir(exist_ok=True)
    with (LOCAL / "editorial.lock").open("a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another collection, research or draft job is running") from None
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
