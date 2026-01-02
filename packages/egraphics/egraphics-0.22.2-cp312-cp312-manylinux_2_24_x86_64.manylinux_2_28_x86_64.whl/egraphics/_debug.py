__all__ = ["debug_callback"]

from contextlib import contextmanager
from typing import Callable
from typing import Generator

from ._egraphics import debug_gl


@contextmanager
def debug_callback(f: Callable) -> Generator[None, None, None]:
    debug_gl(f)
    yield
