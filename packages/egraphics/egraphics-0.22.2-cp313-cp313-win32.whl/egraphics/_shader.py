from __future__ import annotations

__all__ = [
    "BlendFactor",
    "BlendFunction",
    "DepthTest",
    "FaceCull",
    "FaceRasterization",
    "PrimitiveMode",
    "Shader",
    "ShaderAttribute",
    "ShaderUniform",
    "UniformMap",
]


import ctypes
from collections.abc import Buffer
from collections.abc import Mapping
from collections.abc import Set
from contextlib import ExitStack
from ctypes import addressof
from ctypes import c_int32
from enum import Enum
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import Final
from typing import Generic
from typing import Mapping
from typing import Sequence
from typing import TypeVar
from weakref import ref

import emath
from egeometry import IBoundingBox2d
from emath import FVector4
from emath import I32Array
from emath import IVector2

from ._egraphics import GL_ALWAYS
from ._egraphics import GL_BACK
from ._egraphics import GL_BOOL
from ._egraphics import GL_CONSTANT_ALPHA
from ._egraphics import GL_CONSTANT_COLOR
from ._egraphics import GL_DOUBLE
from ._egraphics import GL_DOUBLE_MAT2
from ._egraphics import GL_DOUBLE_MAT3
from ._egraphics import GL_DOUBLE_MAT4
from ._egraphics import GL_DOUBLE_VEC2
from ._egraphics import GL_DOUBLE_VEC3
from ._egraphics import GL_DOUBLE_VEC4
from ._egraphics import GL_DST_ALPHA
from ._egraphics import GL_DST_COLOR
from ._egraphics import GL_EQUAL
from ._egraphics import GL_FILL
from ._egraphics import GL_FLOAT
from ._egraphics import GL_FLOAT_MAT2
from ._egraphics import GL_FLOAT_MAT3
from ._egraphics import GL_FLOAT_MAT4
from ._egraphics import GL_FLOAT_VEC2
from ._egraphics import GL_FLOAT_VEC3
from ._egraphics import GL_FLOAT_VEC4
from ._egraphics import GL_FRONT
from ._egraphics import GL_FUNC_ADD
from ._egraphics import GL_FUNC_REVERSE_SUBTRACT
from ._egraphics import GL_FUNC_SUBTRACT
from ._egraphics import GL_GEQUAL
from ._egraphics import GL_GREATER
from ._egraphics import GL_INT
from ._egraphics import GL_INT_SAMPLER_1D
from ._egraphics import GL_INT_SAMPLER_1D_ARRAY
from ._egraphics import GL_INT_SAMPLER_2D
from ._egraphics import GL_INT_SAMPLER_2D_ARRAY
from ._egraphics import GL_INT_SAMPLER_2D_MULTISAMPLE
from ._egraphics import GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY
from ._egraphics import GL_INT_SAMPLER_2D_RECT
from ._egraphics import GL_INT_SAMPLER_3D
from ._egraphics import GL_INT_SAMPLER_BUFFER
from ._egraphics import GL_INT_SAMPLER_CUBE
from ._egraphics import GL_INT_SAMPLER_CUBE_MAP_ARRAY
from ._egraphics import GL_INT_VEC2
from ._egraphics import GL_INT_VEC3
from ._egraphics import GL_INT_VEC4
from ._egraphics import GL_LEQUAL
from ._egraphics import GL_LESS
from ._egraphics import GL_LINE
from ._egraphics import GL_LINE_LOOP
from ._egraphics import GL_LINE_STRIP
from ._egraphics import GL_LINE_STRIP_ADJACENCY
from ._egraphics import GL_LINES
from ._egraphics import GL_LINES_ADJACENCY
from ._egraphics import GL_MAX
from ._egraphics import GL_MIN
from ._egraphics import GL_NEVER
from ._egraphics import GL_NOTEQUAL
from ._egraphics import GL_ONE
from ._egraphics import GL_ONE_MINUS_CONSTANT_ALPHA
from ._egraphics import GL_ONE_MINUS_CONSTANT_COLOR
from ._egraphics import GL_ONE_MINUS_DST_ALPHA
from ._egraphics import GL_ONE_MINUS_DST_COLOR
from ._egraphics import GL_ONE_MINUS_SRC_ALPHA
from ._egraphics import GL_ONE_MINUS_SRC_COLOR
from ._egraphics import GL_POINT
from ._egraphics import GL_POINTS
from ._egraphics import GL_SAMPLER_1D
from ._egraphics import GL_SAMPLER_1D_ARRAY
from ._egraphics import GL_SAMPLER_1D_ARRAY_SHADOW
from ._egraphics import GL_SAMPLER_1D_SHADOW
from ._egraphics import GL_SAMPLER_2D
from ._egraphics import GL_SAMPLER_2D_ARRAY
from ._egraphics import GL_SAMPLER_2D_ARRAY_SHADOW
from ._egraphics import GL_SAMPLER_2D_MULTISAMPLE
from ._egraphics import GL_SAMPLER_2D_MULTISAMPLE_ARRAY
from ._egraphics import GL_SAMPLER_2D_RECT
from ._egraphics import GL_SAMPLER_2D_RECT_SHADOW
from ._egraphics import GL_SAMPLER_2D_SHADOW
from ._egraphics import GL_SAMPLER_3D
from ._egraphics import GL_SAMPLER_BUFFER
from ._egraphics import GL_SAMPLER_CUBE
from ._egraphics import GL_SAMPLER_CUBE_MAP_ARRAY
from ._egraphics import GL_SAMPLER_CUBE_SHADOW
from ._egraphics import GL_SRC_ALPHA
from ._egraphics import GL_SRC_COLOR
from ._egraphics import GL_TRIANGLE_FAN
from ._egraphics import GL_TRIANGLE_STRIP
from ._egraphics import GL_TRIANGLE_STRIP_ADJACENCY
from ._egraphics import GL_TRIANGLES
from ._egraphics import GL_TRIANGLES_ADJACENCY
from ._egraphics import GL_UNSIGNED_BYTE
from ._egraphics import GL_UNSIGNED_INT
from ._egraphics import GL_UNSIGNED_INT_SAMPLER_1D
from ._egraphics import GL_UNSIGNED_INT_SAMPLER_1D_ARRAY
from ._egraphics import GL_UNSIGNED_INT_SAMPLER_2D
from ._egraphics import GL_UNSIGNED_INT_SAMPLER_2D_ARRAY
from ._egraphics import GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE
from ._egraphics import GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY
from ._egraphics import GL_UNSIGNED_INT_SAMPLER_2D_RECT
from ._egraphics import GL_UNSIGNED_INT_SAMPLER_3D
from ._egraphics import GL_UNSIGNED_INT_SAMPLER_BUFFER
from ._egraphics import GL_UNSIGNED_INT_SAMPLER_CUBE
from ._egraphics import GL_UNSIGNED_INT_SAMPLER_CUBE_MAP_ARRAY
from ._egraphics import GL_UNSIGNED_INT_VEC2
from ._egraphics import GL_UNSIGNED_INT_VEC3
from ._egraphics import GL_UNSIGNED_INT_VEC4
from ._egraphics import GL_UNSIGNED_SHORT
from ._egraphics import GL_ZERO
from ._egraphics import GL_DOUBLE_MAT2x3
from ._egraphics import GL_DOUBLE_MAT2x4
from ._egraphics import GL_DOUBLE_MAT3x2
from ._egraphics import GL_DOUBLE_MAT3x4
from ._egraphics import GL_DOUBLE_MAT4x2
from ._egraphics import GL_DOUBLE_MAT4x3
from ._egraphics import GL_FLOAT_MAT2x3
from ._egraphics import GL_FLOAT_MAT2x4
from ._egraphics import GL_FLOAT_MAT3x2
from ._egraphics import GL_FLOAT_MAT3x4
from ._egraphics import GL_FLOAT_MAT4x2
from ._egraphics import GL_FLOAT_MAT4x3
from ._egraphics import GlType
from ._egraphics import create_gl_program
from ._egraphics import delete_gl_program
from ._egraphics import execute_gl_program_index_buffer
from ._egraphics import execute_gl_program_indices
from ._egraphics import get_gl_program_attributes
from ._egraphics import get_gl_program_uniforms
from ._egraphics import set_active_gl_program_uniform_double
from ._egraphics import set_active_gl_program_uniform_double_2
from ._egraphics import set_active_gl_program_uniform_double_2x2
from ._egraphics import set_active_gl_program_uniform_double_2x3
from ._egraphics import set_active_gl_program_uniform_double_2x4
from ._egraphics import set_active_gl_program_uniform_double_3
from ._egraphics import set_active_gl_program_uniform_double_3x2
from ._egraphics import set_active_gl_program_uniform_double_3x3
from ._egraphics import set_active_gl_program_uniform_double_3x4
from ._egraphics import set_active_gl_program_uniform_double_4
from ._egraphics import set_active_gl_program_uniform_double_4x2
from ._egraphics import set_active_gl_program_uniform_double_4x3
from ._egraphics import set_active_gl_program_uniform_double_4x4
from ._egraphics import set_active_gl_program_uniform_float
from ._egraphics import set_active_gl_program_uniform_float_2
from ._egraphics import set_active_gl_program_uniform_float_2x2
from ._egraphics import set_active_gl_program_uniform_float_2x3
from ._egraphics import set_active_gl_program_uniform_float_2x4
from ._egraphics import set_active_gl_program_uniform_float_3
from ._egraphics import set_active_gl_program_uniform_float_3x2
from ._egraphics import set_active_gl_program_uniform_float_3x3
from ._egraphics import set_active_gl_program_uniform_float_3x4
from ._egraphics import set_active_gl_program_uniform_float_4
from ._egraphics import set_active_gl_program_uniform_float_4x2
from ._egraphics import set_active_gl_program_uniform_float_4x3
from ._egraphics import set_active_gl_program_uniform_float_4x4
from ._egraphics import set_active_gl_program_uniform_int
from ._egraphics import set_active_gl_program_uniform_int_2
from ._egraphics import set_active_gl_program_uniform_int_3
from ._egraphics import set_active_gl_program_uniform_int_4
from ._egraphics import set_active_gl_program_uniform_unsigned_int
from ._egraphics import set_active_gl_program_uniform_unsigned_int_2
from ._egraphics import set_active_gl_program_uniform_unsigned_int_3
from ._egraphics import set_active_gl_program_uniform_unsigned_int_4
from ._egraphics import set_gl_execution_state
from ._egraphics import use_gl_program
from ._g_buffer_view import GBufferView
from ._render_target import RenderTarget
from ._render_target import set_draw_render_target
from ._state import register_reset_state_callback
from ._texture import Texture
from ._texture import bind_texture_unit

if TYPE_CHECKING:
    # egraphics
    from ._g_buffer_view_map import GBufferViewMap

_T = TypeVar("_T")


class DepthTest(Enum):
    NEVER = GL_NEVER
    ALWAYS = GL_ALWAYS
    LESS = GL_LESS
    LESS_EQUAL = GL_LEQUAL
    GREATER = GL_GREATER
    GREATER_EQUAL = GL_GEQUAL
    EQUAL = GL_EQUAL
    NOT_EQUAL = GL_NOTEQUAL


class BlendFactor(Enum):
    ZERO = GL_ZERO
    ONE = GL_ONE
    SOURCE_COLOR = GL_SRC_COLOR
    ONE_MINUS_SOURCE_COLOR = GL_ONE_MINUS_SRC_COLOR
    DESTINATION_COLOR = GL_DST_COLOR
    ONE_MINUS_DESTINATION_COLOR = GL_ONE_MINUS_DST_COLOR
    SOURCE_ALPHA = GL_SRC_ALPHA
    ONE_MINUS_SOURCE_ALPHA = GL_ONE_MINUS_SRC_ALPHA
    DESTINATION_ALPHA = GL_DST_ALPHA
    ONE_MINUS_DESTINATION_ALPHA = GL_ONE_MINUS_DST_ALPHA
    BLEND_COLOR = GL_CONSTANT_COLOR
    ONE_MINUS_BLEND_COLOR = GL_ONE_MINUS_CONSTANT_COLOR
    BLEND_ALPHA = GL_CONSTANT_ALPHA
    ONE_MINUS_BLEND_ALPHA = GL_ONE_MINUS_CONSTANT_ALPHA


class BlendFunction(Enum):
    ADD = GL_FUNC_ADD
    SUBTRACT = GL_FUNC_SUBTRACT
    SUBTRACT_REVERSED = GL_FUNC_REVERSE_SUBTRACT
    MIN = GL_MIN
    MAX = GL_MAX


class FaceCull(Enum):
    NONE = None
    FRONT = GL_FRONT
    BACK = GL_BACK


class FaceRasterization(Enum):
    POINT = GL_POINT
    LINE = GL_LINE
    FILL = GL_FILL


class Shader:
    _active: ClassVar[ref[Shader] | None] = None

    def __init__(
        self,
        *,
        vertex: Buffer | None = None,
        geometry: Buffer | None = None,
        fragment: Buffer | None = None,
    ):
        if vertex is None and geometry is None and fragment is None:
            raise TypeError("vertex, geometry or fragment must be provided")

        if geometry is not None and vertex is None:
            raise TypeError("geometry shader requires vertex shader")

        self._gl_program = create_gl_program(vertex, geometry, fragment)

        self._attributes = tuple(
            ShaderAttribute(name.removesuffix("[0]"), _GL_TYPE_TO_PY[type], size, location)
            for name, size, type, location in get_gl_program_attributes(self._gl_program)
            if not name.startswith("gl_")
        )

        self._uniforms = tuple(
            ShaderUniform(name.removesuffix("[0]"), _GL_TYPE_TO_PY[type], size, location)
            for name, size, type, location in get_gl_program_uniforms(self._gl_program)
            if not name.startswith("gl_")
        )

        self._inputs: dict[str, ShaderAttribute | ShaderUniform] = {
            **{attribute.name: attribute for attribute in self._attributes},
            **{uniform.name: uniform for uniform in self._uniforms},
        }

    def __del__(self) -> None:
        if self._active and self._active() is self:
            use_gl_program(None)
            Shader._active = None
        if hasattr(self, "_gl_program") and self._gl_program is not None:
            delete_gl_program(self._gl_program)
            del self._gl_program

    def __getitem__(self, name: str) -> ShaderAttribute | ShaderUniform:
        return self._inputs[name]

    def _set_uniform(
        self, uniform: ShaderUniform, value: UniformValue, exit_stack: ExitStack
    ) -> None:
        assert uniform in self._uniforms
        input_value: Any = None
        cache_key: Any = value
        set_size: int
        if uniform.data_type is Texture:
            if isinstance(value, Texture):
                set_size = 1
                input_value = c_int32(exit_stack.enter_context(bind_texture_unit(value)))
            else:
                try:
                    set_size = min(uniform.size, len(value))  # type: ignore
                except TypeError:
                    raise ValueError(
                        f"expected {Texture} or sequence of {Texture} for {uniform.name} "
                        f"(got {type(value)})"
                    )
                try:
                    value = I32Array(
                        *(
                            exit_stack.enter_context(bind_texture_unit(v))  # type: ignore
                            for v in value  # type: ignore
                        )
                    )
                except Exception as ex:
                    if not all(isinstance(v, Texture) for v in value):  # type: ignore
                        raise ValueError(
                            f"expected {Texture} or sequence of {Texture} for {uniform.name} "
                            f"(got {value})"
                        )
                    raise
                input_value = value.address
        else:
            if isinstance(value, uniform._set_type):
                set_size = 1
                if uniform._set_type in _POD_UNIFORM_TYPES:
                    input_value = value
                    cache_key = value.value  # type: ignore
                else:
                    input_value = value.address  # type: ignore
            else:
                array_type = _PY_TYPE_TO_ARRAY[uniform.data_type]
                if not isinstance(value, array_type):
                    raise ValueError(
                        f"expected {uniform._set_type} or {array_type} for {uniform.name} "
                        f"(got {type(value)})"
                    )
                input_value = value.address  # type: ignore
                set_size = min(uniform.size, len(value))  # type: ignore
        if set_size != 0:
            uniform._set(uniform.location, set_size, input_value, cache_key)

    @property
    def attributes(self) -> tuple[ShaderAttribute, ...]:
        return self._attributes

    @property
    def uniforms(self) -> tuple[ShaderUniform, ...]:
        return self._uniforms

    def _activate(self) -> None:
        if self._active and self._active() is self:
            return
        use_gl_program(self._gl_program)
        Shader._active = ref(self)

    def execute(
        self,
        render_target: RenderTarget,
        primitive_mode: PrimitiveMode,
        buffer_view_map: GBufferViewMap,
        uniforms: UniformMap,
        *,
        blend_source: BlendFactor = BlendFactor.ONE,
        blend_destination: BlendFactor = BlendFactor.ZERO,
        blend_source_alpha: BlendFactor | None = None,
        blend_destination_alpha: BlendFactor | None = None,
        blend_function: BlendFunction = BlendFunction.ADD,
        blend_color: FVector4 | None = None,
        color_write: tuple[bool, bool, bool, bool] = (True, True, True, True),
        depth_test: DepthTest = DepthTest.ALWAYS,
        depth_write: bool = False,
        depth_clamp: bool = False,
        face_cull: FaceCull = FaceCull.NONE,
        instances: int = 1,
        scissor: IBoundingBox2d | None = None,
        face_rasterization: FaceRasterization = FaceRasterization.FILL,
        point_size: float = 1.0,
        clip_distances: int = 0,
    ) -> None:
        uniform_values: list[tuple[ShaderUniform, Any]] = []
        for uniform in self.uniforms:
            try:
                value = uniforms[uniform.name]
            except KeyError:
                continue
            uniform_values.append((uniform, value))
        if instances < 0:
            raise ValueError("instances must be 0 or more")
        elif instances == 0:
            return

        set_gl_execution_state(
            depth_write,
            depth_test.value,
            *color_write,
            blend_source.value,
            blend_destination.value,
            None if blend_source_alpha is None else blend_source_alpha.value,
            None if blend_destination_alpha is None else blend_destination_alpha.value,
            blend_function.value,
            blend_color,
            face_cull.value,
            None
            if scissor is None
            else IVector2(
                scissor.position.x, render_target.size.y - scissor.position.y - scissor.size.y
            ),
            None if scissor is None else scissor.size,
            depth_clamp,
            face_rasterization.value,
            point_size,
            clip_distances,
        )

        set_draw_render_target(render_target)
        self._activate()

        with ExitStack() as exit_stack:
            for uniform, value in uniform_values:
                self._set_uniform(uniform, value, exit_stack)
            buffer_view_map.activate_for_shader(self)

            if isinstance(buffer_view_map.indices, GBufferView):
                index_gl_type = _INDEX_BUFFER_VIEW_TYPE_TO_VERTEX_ATTRIB_POINTER[
                    buffer_view_map.indices.data_type
                ]
                execute_gl_program_index_buffer(
                    primitive_mode.value,
                    len(buffer_view_map.indices),
                    buffer_view_map.indices.offset,
                    index_gl_type,
                    instances,
                )
            else:
                index_range = buffer_view_map.indices
                execute_gl_program_indices(
                    primitive_mode.value, index_range[0], index_range[1], instances
                )


@register_reset_state_callback
def _reset_shader_state() -> None:
    Shader._active = None


class ShaderAttribute(Generic[_T]):
    def __init__(self, name: str, data_type: type[_T], size: int, location: int) -> None:
        self._name = name
        self._data_type: type[_T] = data_type
        self._size = size
        self._location = location

    def __repr__(self) -> str:
        return f"<ShaderAttribute {self.name!r}>"

    @property
    def name(self) -> str:
        return self._name

    @property
    def data_type(self) -> type[_T]:
        return self._data_type

    @property
    def size(self) -> int:
        return self._size

    @property
    def location(self) -> int:
        return self._location


class ShaderUniform(Generic[_T]):
    def __init__(self, name: str, data_type: type[_T], size: int, location: int) -> None:
        self._name = name
        self._data_type: type[_T] = data_type
        self._size = size
        self._location = location
        self._setter = _TYPE_TO_UNIFORM_SETTER[data_type]
        self._set_type: Any = c_int32 if data_type is Texture else data_type
        self._cache: Any = None

    def __repr__(self) -> str:
        return f"<ShaderUniform {self.name!r}>"

    def _set(self, location: int, size: int, gl_value: Any, cache_key: Any) -> None:
        if self._cache == cache_key:
            return
        if isinstance(gl_value, int):
            value_ptr = gl_value
        else:
            try:
                value_ptr = addressof(gl_value.contents)
            except AttributeError:
                value_ptr = addressof(gl_value)
        self._setter(location, size, value_ptr)
        self._cache = cache_key

    @property
    def name(self) -> str:
        return self._name

    @property
    def data_type(self) -> type[_T]:
        return self._data_type

    @property
    def size(self) -> int:
        return self._size

    @property
    def location(self) -> int:
        return self._location


_GL_TYPE_TO_PY: Final[Mapping[GlType, Any]] = {
    GL_FLOAT: ctypes.c_float,
    GL_FLOAT_VEC2: emath.FVector2,
    GL_FLOAT_VEC3: emath.FVector3,
    GL_FLOAT_VEC4: emath.FVector4,
    GL_DOUBLE: ctypes.c_double,
    GL_DOUBLE_VEC2: emath.DVector2,
    GL_DOUBLE_VEC3: emath.DVector3,
    GL_DOUBLE_VEC4: emath.DVector4,
    GL_INT: ctypes.c_int32,
    GL_INT_VEC2: emath.I32Vector2,
    GL_INT_VEC3: emath.I32Vector3,
    GL_INT_VEC4: emath.I32Vector4,
    GL_UNSIGNED_INT: ctypes.c_uint32,
    GL_UNSIGNED_INT_VEC2: emath.U32Vector2,
    GL_UNSIGNED_INT_VEC3: emath.U32Vector3,
    GL_UNSIGNED_INT_VEC4: emath.U32Vector4,
    GL_BOOL: ctypes.c_bool,
    GL_FLOAT_MAT2: emath.FMatrix2x2,
    GL_FLOAT_MAT3: emath.FMatrix3x3,
    GL_FLOAT_MAT4: emath.FMatrix4x4,
    GL_FLOAT_MAT2x3: emath.FMatrix2x3,
    GL_FLOAT_MAT2x4: emath.FMatrix2x4,
    GL_FLOAT_MAT3x2: emath.FMatrix3x2,
    GL_FLOAT_MAT3x4: emath.FMatrix3x4,
    GL_FLOAT_MAT4x2: emath.FMatrix4x2,
    GL_FLOAT_MAT4x3: emath.FMatrix4x3,
    GL_DOUBLE_MAT2: emath.DMatrix2x2,
    GL_DOUBLE_MAT3: emath.DMatrix3x3,
    GL_DOUBLE_MAT4: emath.DMatrix4x4,
    GL_DOUBLE_MAT2x3: emath.DMatrix2x3,
    GL_DOUBLE_MAT2x4: emath.DMatrix2x4,
    GL_DOUBLE_MAT3x2: emath.DMatrix3x2,
    GL_DOUBLE_MAT3x4: emath.DMatrix3x4,
    GL_DOUBLE_MAT4x2: emath.DMatrix4x2,
    GL_DOUBLE_MAT4x3: emath.DMatrix4x3,
    GL_SAMPLER_1D: Texture,
    GL_INT_SAMPLER_1D: Texture,
    GL_UNSIGNED_INT_SAMPLER_1D: Texture,
    GL_SAMPLER_2D: Texture,
    GL_INT_SAMPLER_2D: Texture,
    GL_UNSIGNED_INT_SAMPLER_2D: Texture,
    GL_SAMPLER_3D: Texture,
    GL_INT_SAMPLER_3D: Texture,
    GL_UNSIGNED_INT_SAMPLER_3D: Texture,
    GL_SAMPLER_CUBE: Texture,
    GL_INT_SAMPLER_CUBE: Texture,
    GL_UNSIGNED_INT_SAMPLER_CUBE: Texture,
    GL_SAMPLER_2D_RECT: Texture,
    GL_INT_SAMPLER_2D_RECT: Texture,
    GL_UNSIGNED_INT_SAMPLER_2D_RECT: Texture,
    GL_SAMPLER_1D_ARRAY: Texture,
    GL_INT_SAMPLER_1D_ARRAY: Texture,
    GL_UNSIGNED_INT_SAMPLER_1D_ARRAY: Texture,
    GL_SAMPLER_2D_ARRAY: Texture,
    GL_INT_SAMPLER_2D_ARRAY: Texture,
    GL_UNSIGNED_INT_SAMPLER_2D_ARRAY: Texture,
    GL_SAMPLER_CUBE_MAP_ARRAY: Texture,
    GL_INT_SAMPLER_CUBE_MAP_ARRAY: Texture,
    GL_UNSIGNED_INT_SAMPLER_CUBE_MAP_ARRAY: Texture,
    GL_SAMPLER_BUFFER: Texture,
    GL_INT_SAMPLER_BUFFER: Texture,
    GL_UNSIGNED_INT_SAMPLER_BUFFER: Texture,
    GL_SAMPLER_2D_MULTISAMPLE: Texture,
    GL_INT_SAMPLER_2D_MULTISAMPLE: Texture,
    GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE: Texture,
    GL_SAMPLER_2D_MULTISAMPLE_ARRAY: Texture,
    GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY: Texture,
    GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY: Texture,
    GL_SAMPLER_1D_SHADOW: Texture,
    GL_SAMPLER_2D_SHADOW: Texture,
    GL_SAMPLER_CUBE_SHADOW: Texture,
    GL_SAMPLER_2D_RECT_SHADOW: Texture,
    GL_SAMPLER_1D_ARRAY_SHADOW: Texture,
    GL_SAMPLER_2D_ARRAY_SHADOW: Texture,
}


_TYPE_TO_UNIFORM_SETTER: Final[Mapping] = {
    ctypes.c_float: set_active_gl_program_uniform_float,
    emath.FVector2: set_active_gl_program_uniform_float_2,
    emath.FVector3: set_active_gl_program_uniform_float_3,
    emath.FVector4: set_active_gl_program_uniform_float_4,
    ctypes.c_double: set_active_gl_program_uniform_double,
    emath.DVector2: set_active_gl_program_uniform_double_2,
    emath.DVector3: set_active_gl_program_uniform_double_3,
    emath.DVector4: set_active_gl_program_uniform_double_4,
    ctypes.c_int32: set_active_gl_program_uniform_int,
    emath.I32Vector2: set_active_gl_program_uniform_int_2,
    emath.I32Vector3: set_active_gl_program_uniform_int_3,
    emath.I32Vector4: set_active_gl_program_uniform_int_4,
    ctypes.c_uint32: set_active_gl_program_uniform_unsigned_int,
    emath.U32Vector2: set_active_gl_program_uniform_unsigned_int_2,
    emath.U32Vector3: set_active_gl_program_uniform_unsigned_int_3,
    emath.U32Vector4: set_active_gl_program_uniform_unsigned_int_4,
    ctypes.c_bool: set_active_gl_program_uniform_int,
    emath.FMatrix2x2: set_active_gl_program_uniform_float_2x2,
    emath.FMatrix2x3: set_active_gl_program_uniform_float_2x3,
    emath.FMatrix2x4: set_active_gl_program_uniform_float_2x4,
    emath.FMatrix3x2: set_active_gl_program_uniform_float_3x2,
    emath.FMatrix3x3: set_active_gl_program_uniform_float_3x3,
    emath.FMatrix3x4: set_active_gl_program_uniform_float_3x4,
    emath.FMatrix4x2: set_active_gl_program_uniform_float_4x2,
    emath.FMatrix4x3: set_active_gl_program_uniform_float_4x3,
    emath.FMatrix4x4: set_active_gl_program_uniform_float_4x4,
    emath.DMatrix2x2: set_active_gl_program_uniform_double_2x2,
    emath.DMatrix2x3: set_active_gl_program_uniform_double_2x3,
    emath.DMatrix2x4: set_active_gl_program_uniform_double_2x4,
    emath.DMatrix3x2: set_active_gl_program_uniform_double_3x2,
    emath.DMatrix3x3: set_active_gl_program_uniform_double_3x3,
    emath.DMatrix3x4: set_active_gl_program_uniform_double_3x4,
    emath.DMatrix4x2: set_active_gl_program_uniform_double_4x2,
    emath.DMatrix4x3: set_active_gl_program_uniform_double_4x3,
    emath.DMatrix4x4: set_active_gl_program_uniform_double_4x4,
    Texture: set_active_gl_program_uniform_int,
}

_POD_UNIFORM_TYPES: Final[Set] = {
    ctypes.c_float,
    ctypes.c_double,
    ctypes.c_int32,
    ctypes.c_uint32,
    ctypes.c_bool,
}

_PY_TYPE_TO_ARRAY: Final[Mapping] = {
    ctypes.c_float: emath.FArray,
    emath.FVector2: emath.FVector2Array,
    emath.FVector3: emath.FVector3Array,
    emath.FVector4: emath.FVector4Array,
    ctypes.c_double: emath.DArray,
    emath.DVector2: emath.DVector2Array,
    emath.DVector3: emath.DVector3Array,
    emath.DVector4: emath.DVector4Array,
    ctypes.c_int32: emath.I32Array,
    emath.I32Vector2: emath.I32Vector2Array,
    emath.I32Vector3: emath.I32Vector3Array,
    emath.I32Vector4: emath.I32Vector4Array,
    ctypes.c_uint32: emath.U32Array,
    emath.U32Vector2: emath.U32Vector2Array,
    emath.U32Vector3: emath.U32Vector3Array,
    emath.U32Vector4: emath.U32Vector4Array,
    ctypes.c_bool: emath.I32Array,
    emath.FMatrix2x2: emath.FMatrix2x2Array,
    emath.FMatrix3x3: emath.FMatrix3x3Array,
    emath.FMatrix4x4: emath.FMatrix4x4Array,
    emath.FMatrix2x3: emath.FMatrix2x3Array,
    emath.FMatrix2x4: emath.FMatrix2x4Array,
    emath.FMatrix3x2: emath.FMatrix3x2Array,
    emath.FMatrix3x4: emath.FMatrix3x4Array,
    emath.FMatrix4x2: emath.FMatrix4x2Array,
    emath.FMatrix4x3: emath.FMatrix4x3Array,
    emath.DMatrix2x2: emath.DMatrix2x2Array,
    emath.DMatrix3x3: emath.DMatrix3x3Array,
    emath.DMatrix4x4: emath.DMatrix4x4Array,
    emath.DMatrix2x3: emath.DMatrix2x3Array,
    emath.DMatrix2x4: emath.DMatrix2x4Array,
    emath.DMatrix3x2: emath.DMatrix3x2Array,
    emath.DMatrix3x4: emath.DMatrix3x4Array,
    emath.DMatrix4x2: emath.DMatrix4x2Array,
    emath.DMatrix4x3: emath.DMatrix4x3Array,
}


class PrimitiveMode(Enum):
    POINT = GL_POINTS
    LINE = GL_LINES
    LINE_STRIP = GL_LINE_STRIP
    LINE_LOOP = GL_LINE_LOOP
    TRIANGLE = GL_TRIANGLES
    TRIANGLE_STRIP = GL_TRIANGLE_STRIP
    TRIANGLE_FAN = GL_TRIANGLE_FAN
    LINE_STRIP_ADJACENCY = GL_LINE_STRIP_ADJACENCY
    LINE_ADJACENCY = GL_LINES_ADJACENCY
    TRIANGLE_STRIP_ADJACENCY = GL_TRIANGLE_STRIP_ADJACENCY
    TRIANGLE_ADJACENCY = GL_TRIANGLES_ADJACENCY


UniformValue = (
    ctypes.c_float
    | emath.FArray
    | emath.FVector2
    | emath.FVector2Array
    | emath.FVector3
    | emath.FVector3Array
    | emath.FVector4
    | emath.FVector4Array
    | ctypes.c_double
    | emath.DArray
    | emath.DVector2
    | emath.DVector2Array
    | emath.DVector3
    | emath.DVector3Array
    | emath.DVector4
    | emath.DVector4Array
    | ctypes.c_int32
    | emath.I32Array
    | emath.I32Vector2
    | emath.I32Vector2Array
    | emath.I32Vector3
    | emath.I32Vector3Array
    | emath.I32Vector4
    | emath.I32Vector4Array
    | ctypes.c_uint32
    | emath.U32Array
    | emath.U32Vector2
    | emath.U32Vector2Array
    | emath.U32Vector3
    | emath.U32Vector3Array
    | emath.U32Vector4
    | emath.U32Vector4Array
    | ctypes.c_bool
    | emath.FMatrix2x2
    | emath.FMatrix2x2Array
    | emath.FMatrix2x3
    | emath.FMatrix2x3Array
    | emath.FMatrix2x4
    | emath.FMatrix2x4Array
    | emath.FMatrix3x2
    | emath.FMatrix3x2Array
    | emath.FMatrix3x3
    | emath.FMatrix3x3Array
    | emath.FMatrix3x4
    | emath.FMatrix3x4Array
    | emath.FMatrix4x2
    | emath.FMatrix4x2Array
    | emath.FMatrix4x3
    | emath.FMatrix4x3Array
    | emath.FMatrix4x4
    | emath.FMatrix4x4Array
    | emath.DMatrix2x2
    | emath.DMatrix2x2Array
    | emath.DMatrix2x3
    | emath.DMatrix2x3Array
    | emath.DMatrix2x4
    | emath.DMatrix2x4Array
    | emath.DMatrix3x2
    | emath.DMatrix3x2Array
    | emath.DMatrix3x3
    | emath.DMatrix3x3Array
    | emath.DMatrix3x4
    | emath.DMatrix3x4Array
    | emath.DMatrix4x2
    | emath.DMatrix4x2Array
    | emath.DMatrix4x3
    | emath.DMatrix4x3Array
    | emath.DMatrix4x4
    | emath.DMatrix4x4Array
    | Texture
    | Sequence[Texture]
)

UniformMap = Mapping[str, UniformValue]

_INDEX_BUFFER_VIEW_TYPE_TO_VERTEX_ATTRIB_POINTER: Final[Mapping[Any, GlType]] = {
    ctypes.c_uint8: GL_UNSIGNED_BYTE,
    ctypes.c_uint16: GL_UNSIGNED_SHORT,
    ctypes.c_uint32: GL_UNSIGNED_INT,
}
