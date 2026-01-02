from __future__ import annotations

__all__ = [
    "get_gl_version",
    "register_reset_state_callback",
    "reset_state",
    "ClipOrigin",
    "ClipDepth",
    "clip_space",
]

from contextlib import contextmanager
from enum import Enum
from typing import Callable
from typing import Generator

from ._egraphics import GL_LOWER_LEFT
from ._egraphics import GL_NEGATIVE_ONE_TO_ONE
from ._egraphics import GL_UPPER_LEFT
from ._egraphics import GL_ZERO_TO_ONE
from ._egraphics import get_gl_clip
from ._egraphics import get_gl_version as get_gl_version_string
from ._egraphics import set_gl_clip

_reset_state_callbacks: list[Callable[[], None]] = []
_gl_version: tuple[int, int] | None = None


def register_reset_state_callback(callback: Callable[[], None]) -> Callable[[], None]:
    _reset_state_callbacks.append(callback)
    return callback


def reset_state() -> None:
    global _gl_version
    for callback in _reset_state_callbacks:
        callback()
    _gl_version = None


def get_gl_version() -> tuple[int, int]:
    global _gl_version
    if _gl_version is None:
        gl_version = get_gl_version_string()
        _gl_version = tuple(  # type: ignore
            int(v) for v in gl_version.split(" ")[0].split(".")[:2]
        )
    assert _gl_version is not None
    return _gl_version


class ClipOrigin(Enum):
    BOTTOM_LEFT = GL_LOWER_LEFT
    TOP_LEFT = GL_UPPER_LEFT


class ClipDepth(Enum):
    NEGATIVE_ONE_TO_ONE = GL_NEGATIVE_ONE_TO_ONE
    ZERO_TO_ONE = GL_ZERO_TO_ONE


@contextmanager
def clip_space(origin: ClipOrigin, depth: ClipDepth) -> Generator[None, None, None]:
    original_origin, original_depth = get_gl_clip()
    set_gl_clip(ClipOrigin(origin).value, ClipDepth(depth).value)
    try:
        yield
    finally:
        set_gl_clip(original_origin, original_depth)
