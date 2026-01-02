__all__ = ["Image", "ImageInvalidError"]

from collections.abc import Mapping
from ctypes import c_uint8
from datetime import timedelta
from typing import BinaryIO
from typing import Final

from emath import FVector4
from emath import UVector2
from PIL import Image as PilImage
from PIL import ImageMath as PilImageMath
from PIL import UnidentifiedImageError as PilUnidentifiedImageError

from ._texture import MipmapSelection
from ._texture import TextureComponents
from ._texture import TextureFilter
from ._texture import TextureWrap
from ._texture_2d import Texture2d

_PIL_MODE_TO_TEXTURE_COMPONENTS: Final[Mapping[str, TextureComponents]] = {
    "L": TextureComponents.R,
    "RGB": TextureComponents.RGB,
    "RGBA": TextureComponents.RGBA,
}


_PIL_MODE_TO_COMPONENTS: Final[Mapping[str, int]] = {"L": 1, "RGB": 3, "RGBA": 4}


_PIL_CONVERT: Final[Mapping[str, str]] = {
    "1": "L",
    "LA": "RGBA",
    "CMYK": "RGBA",
    "YCbCr": "RGB",
    "LAB": "RGB",
    "HSV": "RGB",
}


class ImageInvalidError(RuntimeError):
    pass


class Image:
    def __init__(self, file: BinaryIO):
        try:
            self._pil = PilImage.open(file)
        except PilUnidentifiedImageError as ex:
            raise ImageInvalidError(str(ex))

        # we "normalize" the image to an R, RGB, or RGBA mode so that the
        # bytes representation is predictable
        convert_mode = self._pil.mode
        if convert_mode[0] in ["I", "F"]:
            # I and F should convert to L, but pillow has some isues with this,
            # so we must to it manually
            # https://github.com/python-pillow/Pillow/issues/3011
            self._pil = PilImageMath.eval(  # type: ignore
                "image >> 8", image=self._pil.convert("I")
            ).convert("L")
            convert_mode = "L"
        # P/PA are palette modes, so use whatever the mode is of the palette
        if convert_mode in ["P", "PA"]:
            assert self._pil.palette is not None
            convert_mode = self._pil.palette.mode
        if convert_mode not in _PIL_MODE_TO_TEXTURE_COMPONENTS:
            try:
                convert_mode = _PIL_CONVERT[convert_mode]
            except KeyError:
                raise ImageInvalidError("unable to normalize image")
        if convert_mode != self._pil.mode:
            self._pil = self._pil.convert(mode=convert_mode)

        self._components = _PIL_MODE_TO_COMPONENTS[self._pil.mode]

        self._pil.load()

    def __len__(self) -> int:
        try:
            return self._pil.n_frames  # type: ignore
        except AttributeError:
            return 1

    def get_frame_duration(self, index: int) -> timedelta:
        self._pil.seek(index)
        try:
            duration = self._pil.info["duration"]
        except KeyError:
            return timedelta(seconds=0)
        return timedelta(milliseconds=duration)

    def read(self, index: int) -> memoryview:
        self._pil.seek(index)
        return memoryview(self._pil.tobytes())

    def to_texture(
        self,
        *,
        frame: int = 0,
        mipmap_selection: MipmapSelection = MipmapSelection.NONE,
        minify_filter: TextureFilter = TextureFilter.NEAREST,
        magnify_filter: TextureFilter = TextureFilter.NEAREST,
        wrap: tuple[TextureWrap, TextureWrap] = (TextureWrap.REPEAT, TextureWrap.REPEAT),
        wrap_color: FVector4 = FVector4(0),
    ) -> Texture2d:
        return Texture2d(
            self.size,
            _PIL_MODE_TO_TEXTURE_COMPONENTS[self._pil.mode],
            c_uint8,
            self.read(frame),
            mipmap_selection=mipmap_selection,
            minify_filter=minify_filter,
            magnify_filter=magnify_filter,
            wrap=wrap,
            wrap_color=wrap_color,
        )

    @property
    def components(self) -> int:
        return self._components

    @property
    def size(self) -> UVector2:
        size: tuple[int, int] = self._pil.size
        assert isinstance(size, tuple)
        assert len(size) == 2
        return UVector2(*size)
