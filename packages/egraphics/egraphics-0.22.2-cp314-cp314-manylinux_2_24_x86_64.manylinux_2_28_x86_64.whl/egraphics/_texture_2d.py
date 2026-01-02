from __future__ import annotations

__all__ = ["Texture2d"]

from collections.abc import Buffer

from emath import FVector4
from emath import UVector2

from ._texture import MipmapSelection
from ._texture import Texture
from ._texture import TextureComponents
from ._texture import TextureDataType
from ._texture import TextureFilter
from ._texture import TextureType
from ._texture import TextureWrap


class Texture2d(Texture):
    def __init__(
        self,
        size: UVector2,
        components: TextureComponents,
        data_type: type[TextureDataType],
        buffer: Buffer,
        *,
        anisotropy: float | None = None,
        mipmap_selection: MipmapSelection | None = None,
        minify_filter: TextureFilter | None = None,
        magnify_filter: TextureFilter | None = None,
        wrap: tuple[TextureWrap, TextureWrap] | None = None,
        wrap_color: FVector4 | None = None,
    ):
        super().__init__(
            TextureType.TWO_DIMENSIONS,
            size=size,
            components=components,
            data_type=data_type,
            buffer=buffer,
            anisotropy=anisotropy,
            mipmap_selection=mipmap_selection,
            minify_filter=minify_filter,
            magnify_filter=magnify_filter,
            wrap=wrap,
            wrap_color=wrap_color,
        )
