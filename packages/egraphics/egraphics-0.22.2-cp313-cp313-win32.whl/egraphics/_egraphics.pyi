__all__ = [
    "GlBlendFactor",
    "GlBlendFunction",
    "GlBuffer",
    "GlBufferTarget",
    "GlBufferUsage",
    "GlCull",
    "GlDepthMode",
    "GlFunc",
    "GlFramebuffer",
    "GlOrigin",
    "GlPrimitive",
    "GlProgram",
    "GlRenderbuffer",
    "GlType",
    "GlTexture",
    "GlTextureComponents",
    "GlTextureFilter",
    "GlTextureTarget",
    "GlTextureWrap",
    "GlVertexArray",
    "GL_ARRAY_BUFFER",
    "GL_COPY_READ_BUFFER",
    "GL_ELEMENT_ARRAY_BUFFER",
    "GL_STREAM_DRAW",
    "GL_STREAM_READ",
    "GL_STREAM_COPY",
    "GL_STATIC_DRAW",
    "GL_STATIC_READ",
    "GL_STATIC_COPY",
    "GL_DYNAMIC_DRAW",
    "GL_DYNAMIC_READ",
    "GL_DYNAMIC_COPY",
    "GL_RED",
    "GL_RG",
    "GL_RGB",
    "GL_RGBA",
    "GL_DEPTH_COMPONENT",
    "GL_RED_INTEGER",
    "GL_RG_INTEGER",
    "GL_RGB_INTEGER",
    "GL_RGBA_INTEGER",
    "GL_R8UI",
    "GL_R8I",
    "GL_R16UI",
    "GL_R16I",
    "GL_R32UI",
    "GL_R32I",
    "GL_R32F",
    "GL_RG8UI",
    "GL_RG8I",
    "GL_RG16UI",
    "GL_RG16I",
    "GL_RG32UI",
    "GL_RG32I",
    "GL_RG32F",
    "GL_RGB8UI",
    "GL_RGB8I",
    "GL_RGB16UI",
    "GL_RGB16I",
    "GL_RGB32UI",
    "GL_RGB32I",
    "GL_RGB32F",
    "GL_RGBA8UI",
    "GL_RGBA8I",
    "GL_RGBA16UI",
    "GL_RGBA16I",
    "GL_RGBA32UI",
    "GL_RGBA32I",
    "GL_RGBA32F",
    "GL_CLAMP_TO_EDGE",
    "GL_CLAMP_TO_BORDER",
    "GL_REPEAT",
    "GL_MIRRORED_REPEAT",
    "GL_NEAREST",
    "GL_LINEAR",
    "GL_NEAREST_MIPMAP_NEAREST",
    "GL_NEAREST_MIPMAP_LINEAR",
    "GL_LINEAR_MIPMAP_NEAREST",
    "GL_LINEAR_MIPMAP_LINEAR",
    "GL_TEXTURE_2D",
    "GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS_VALUE",
    "GL_MAX_CLIP_DISTANCES_VALUE",
    "GL_NEVER",
    "GL_ALWAYS",
    "GL_LESS",
    "GL_LEQUAL",
    "GL_GREATER",
    "GL_GEQUAL",
    "GL_EQUAL",
    "GL_NOTEQUAL",
    "GL_ZERO",
    "GL_ONE",
    "GL_SRC_COLOR",
    "GL_ONE_MINUS_SRC_COLOR",
    "GL_DST_COLOR",
    "GL_ONE_MINUS_DST_COLOR",
    "GL_SRC_ALPHA",
    "GL_ONE_MINUS_SRC_ALPHA",
    "GL_DST_ALPHA",
    "GL_ONE_MINUS_DST_ALPHA",
    "GL_CONSTANT_COLOR",
    "GL_ONE_MINUS_CONSTANT_COLOR",
    "GL_CONSTANT_ALPHA",
    "GL_ONE_MINUS_CONSTANT_ALPHA",
    "GL_FUNC_ADD",
    "GL_FUNC_SUBTRACT",
    "GL_FUNC_REVERSE_SUBTRACT",
    "GL_MIN",
    "GL_MAX",
    "GL_FRONT",
    "GL_BACK",
    "GL_BOOL",
    "GL_FLOAT_VEC2",
    "GL_FLOAT_VEC3",
    "GL_FLOAT_VEC4",
    "GL_DOUBLE_VEC2",
    "GL_DOUBLE_VEC3",
    "GL_DOUBLE_VEC4",
    "GL_INT_VEC2",
    "GL_INT_VEC3",
    "GL_INT_VEC4",
    "GL_UNSIGNED_INT_VEC2",
    "GL_UNSIGNED_INT_VEC3",
    "GL_UNSIGNED_INT_VEC4",
    "GL_FLOAT_MAT2",
    "GL_FLOAT_MAT3",
    "GL_FLOAT_MAT4",
    "GL_FLOAT_MAT2x3",
    "GL_FLOAT_MAT2x4",
    "GL_FLOAT_MAT3x2",
    "GL_FLOAT_MAT3x4",
    "GL_FLOAT_MAT4x2",
    "GL_FLOAT_MAT4x3",
    "GL_DOUBLE_MAT2",
    "GL_DOUBLE_MAT3",
    "GL_DOUBLE_MAT4",
    "GL_DOUBLE_MAT2x3",
    "GL_DOUBLE_MAT2x4",
    "GL_DOUBLE_MAT3x2",
    "GL_DOUBLE_MAT3x4",
    "GL_DOUBLE_MAT4x2",
    "GL_DOUBLE_MAT4x3",
    "GL_SAMPLER_1D",
    "GL_INT_SAMPLER_1D",
    "GL_UNSIGNED_INT_SAMPLER_1D",
    "GL_SAMPLER_2D",
    "GL_INT_SAMPLER_2D",
    "GL_UNSIGNED_INT_SAMPLER_2D",
    "GL_SAMPLER_3D",
    "GL_INT_SAMPLER_3D",
    "GL_UNSIGNED_INT_SAMPLER_3D",
    "GL_SAMPLER_CUBE",
    "GL_INT_SAMPLER_CUBE",
    "GL_UNSIGNED_INT_SAMPLER_CUBE",
    "GL_SAMPLER_2D_RECT",
    "GL_INT_SAMPLER_2D_RECT",
    "GL_UNSIGNED_INT_SAMPLER_2D_RECT",
    "GL_SAMPLER_1D_ARRAY",
    "GL_INT_SAMPLER_1D_ARRAY",
    "GL_UNSIGNED_INT_SAMPLER_1D_ARRAY",
    "GL_SAMPLER_2D_ARRAY",
    "GL_INT_SAMPLER_2D_ARRAY",
    "GL_UNSIGNED_INT_SAMPLER_2D_ARRAY",
    "GL_SAMPLER_CUBE_MAP_ARRAY",
    "GL_INT_SAMPLER_CUBE_MAP_ARRAY",
    "GL_UNSIGNED_INT_SAMPLER_CUBE_MAP_ARRAY",
    "GL_SAMPLER_BUFFER",
    "GL_INT_SAMPLER_BUFFER",
    "GL_UNSIGNED_INT_SAMPLER_BUFFER",
    "GL_SAMPLER_2D_MULTISAMPLE",
    "GL_INT_SAMPLER_2D_MULTISAMPLE",
    "GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE",
    "GL_SAMPLER_2D_MULTISAMPLE_ARRAY",
    "GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY",
    "GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY",
    "GL_SAMPLER_1D_SHADOW",
    "GL_SAMPLER_2D_SHADOW",
    "GL_SAMPLER_CUBE_SHADOW",
    "GL_SAMPLER_2D_RECT_SHADOW",
    "GL_SAMPLER_1D_ARRAY_SHADOW",
    "GL_SAMPLER_2D_ARRAY_SHADOW",
    "GL_POINTS",
    "GL_LINES",
    "GL_LINE_STRIP",
    "GL_LINE_LOOP",
    "GL_TRIANGLES",
    "GL_TRIANGLE_STRIP",
    "GL_TRIANGLE_FAN",
    "GL_LINE_STRIP_ADJACENCY",
    "GL_LINES_ADJACENCY",
    "GL_TRIANGLE_STRIP_ADJACENCY",
    "GL_TRIANGLES_ADJACENCY",
    "GL_POINT",
    "GL_LINE",
    "GL_FILL",
    "GL_LOWER_LEFT",
    "GL_UPPER_LEFT",
    "GL_NEGATIVE_ONE_TO_ONE",
    "GL_ZERO_TO_ONE",
    "debug_gl",
    "activate_gl_vertex_array",
    "set_gl_buffer_target",
    "create_gl_buffer",
    "create_gl_vertex_array",
    "create_gl_texture",
    "create_gl_framebuffer",
    "delete_gl_buffer",
    "delete_gl_vertex_array",
    "delete_gl_texture",
    "delete_gl_framebuffer",
    "delete_gl_renderbuffer",
    "set_gl_buffer_target_data",
    "write_gl_buffer_target_data",
    "create_gl_buffer_memory_view",
    "release_gl_buffer_memory_view",
    "configure_gl_vertex_array_location",
    "set_draw_framebuffer",
    "set_read_framebuffer",
    "read_color_from_framebuffer",
    "read_depth_from_framebuffer",
    "clear_framebuffer",
    "attach_color_texture_to_gl_read_framebuffer",
    "attach_depth_texture_to_gl_read_framebuffer",
    "attach_depth_renderbuffer_to_gl_read_framebuffer",
    "set_active_gl_texture_unit",
    "set_gl_texture_target",
    "set_gl_texture_target_2d_data",
    "generate_gl_texture_target_mipmaps",
    "set_gl_texture_target_parameters",
    "get_gl_program_uniforms",
    "get_gl_program_attributes",
    "create_gl_program",
    "delete_gl_program",
    "use_gl_program",
    "set_active_gl_program_uniform_float",
    "set_active_gl_program_uniform_double",
    "set_active_gl_program_uniform_int",
    "set_active_gl_program_uniform_unsigned_int",
    "set_active_gl_program_uniform_float_2",
    "set_active_gl_program_uniform_double_2",
    "set_active_gl_program_uniform_int_2",
    "set_active_gl_program_uniform_unsigned_int_2",
    "set_active_gl_program_uniform_float_3",
    "set_active_gl_program_uniform_double_3",
    "set_active_gl_program_uniform_int_3",
    "set_active_gl_program_uniform_unsigned_int_3",
    "set_active_gl_program_uniform_float_4",
    "set_active_gl_program_uniform_double_4",
    "set_active_gl_program_uniform_int_4",
    "set_active_gl_program_uniform_unsigned_int_4",
    "set_active_gl_program_uniform_float_2x2",
    "set_active_gl_program_uniform_float_2x3",
    "set_active_gl_program_uniform_float_2x4",
    "set_active_gl_program_uniform_float_3x2",
    "set_active_gl_program_uniform_float_3x3",
    "set_active_gl_program_uniform_float_3x4",
    "set_active_gl_program_uniform_float_4x2",
    "set_active_gl_program_uniform_float_4x3",
    "set_active_gl_program_uniform_float_4x4",
    "set_active_gl_program_uniform_double_2x2",
    "set_active_gl_program_uniform_double_2x3",
    "set_active_gl_program_uniform_double_2x4",
    "set_active_gl_program_uniform_double_3x2",
    "set_active_gl_program_uniform_double_3x3",
    "set_active_gl_program_uniform_double_3x4",
    "set_active_gl_program_uniform_double_4x2",
    "set_active_gl_program_uniform_double_4x3",
    "set_active_gl_program_uniform_double_4x4",
    "execute_gl_program_index_buffer",
    "execute_gl_program_indices",
    "set_gl_execution_state",
    "get_gl_version",
    "set_gl_clip",
    "get_gl_clip",
]

from collections.abc import Buffer
from typing import Callable
from typing import NewType

from egeometry import IRectangle
from emath import FArray
from emath import FVector4
from emath import FVector4Array
from emath import IVector2
from emath import UVector2

GlBlendFactor = NewType("GlBlendFactor", int)
GlBlendFunction = NewType("GlBlendFunction", int)
GlBuffer = NewType("GlBuffer", int)
GlBufferTarget = NewType("GlBufferTarget", int)
GlBufferUsage = NewType("GlBufferUsage", int)
GlCull = NewType("GlCull", int)
GlDepthMode = NewType("GlDepthMode", int)
GlFunc = NewType("GlFunc", int)
GlFramebuffer = NewType("GlFramebuffer", int)
GlOrigin = NewType("GlOrigin", int)
GlPolygonRasterizationMode = NewType("GlPolygonRasterizationMode", int)
GlPrimitive = NewType("GlPrimitive", int)
GlProgram = NewType("GlProgram", int)
GlRenderbuffer = NewType("GlRenderbuffer", int)
GlType = NewType("GlType", int)
GlTexture = NewType("GlTexture", int)
GlTextureComponents = NewType("GlTextureComponents", int)
GlTextureFilter = NewType("GlTextureFilter", int)
GlTextureTarget = NewType("GlTextureTarget", int)
GlTextureWrap = NewType("GlTextureWrap", int)
GlVertexArray = NewType("GlVertexArray", int)

GL_ARRAY_BUFFER: GlBufferTarget
GL_COPY_READ_BUFFER: GlBufferTarget
GL_ELEMENT_ARRAY_BUFFER: GlBufferTarget

GL_STREAM_DRAW: GlBufferUsage
GL_STREAM_READ: GlBufferUsage
GL_STREAM_COPY: GlBufferUsage
GL_STATIC_DRAW: GlBufferUsage
GL_STATIC_READ: GlBufferUsage
GL_STATIC_COPY: GlBufferUsage
GL_DYNAMIC_DRAW: GlBufferUsage
GL_DYNAMIC_READ: GlBufferUsage
GL_DYNAMIC_COPY: GlBufferUsage

GL_FLOAT: GlType
GL_DOUBLE: GlType
GL_BYTE: GlType
GL_UNSIGNED_BYTE: GlType
GL_SHORT: GlType
GL_UNSIGNED_SHORT: GlType
GL_INT: GlType
GL_UNSIGNED_INT: GlType
GL_BOOL: GlType
GL_FLOAT_VEC2: GlType
GL_FLOAT_VEC3: GlType
GL_FLOAT_VEC4: GlType
GL_DOUBLE_VEC2: GlType
GL_DOUBLE_VEC3: GlType
GL_DOUBLE_VEC4: GlType
GL_INT_VEC2: GlType
GL_INT_VEC3: GlType
GL_INT_VEC4: GlType
GL_UNSIGNED_INT_VEC2: GlType
GL_UNSIGNED_INT_VEC3: GlType
GL_UNSIGNED_INT_VEC4: GlType
GL_FLOAT_MAT2: GlType
GL_FLOAT_MAT3: GlType
GL_FLOAT_MAT4: GlType
GL_FLOAT_MAT2x3: GlType
GL_FLOAT_MAT2x4: GlType
GL_FLOAT_MAT3x2: GlType
GL_FLOAT_MAT3x4: GlType
GL_FLOAT_MAT4x2: GlType
GL_FLOAT_MAT4x3: GlType
GL_DOUBLE_MAT2: GlType
GL_DOUBLE_MAT3: GlType
GL_DOUBLE_MAT4: GlType
GL_DOUBLE_MAT2x3: GlType
GL_DOUBLE_MAT2x4: GlType
GL_DOUBLE_MAT3x2: GlType
GL_DOUBLE_MAT3x4: GlType
GL_DOUBLE_MAT4x2: GlType
GL_DOUBLE_MAT4x3: GlType
GL_SAMPLER_1D: GlType
GL_INT_SAMPLER_1D: GlType
GL_UNSIGNED_INT_SAMPLER_1D: GlType
GL_SAMPLER_2D: GlType
GL_INT_SAMPLER_2D: GlType
GL_UNSIGNED_INT_SAMPLER_2D: GlType
GL_SAMPLER_3D: GlType
GL_INT_SAMPLER_3D: GlType
GL_UNSIGNED_INT_SAMPLER_3D: GlType
GL_SAMPLER_CUBE: GlType
GL_INT_SAMPLER_CUBE: GlType
GL_UNSIGNED_INT_SAMPLER_CUBE: GlType
GL_SAMPLER_2D_RECT: GlType
GL_INT_SAMPLER_2D_RECT: GlType
GL_UNSIGNED_INT_SAMPLER_2D_RECT: GlType
GL_SAMPLER_1D_ARRAY: GlType
GL_INT_SAMPLER_1D_ARRAY: GlType
GL_UNSIGNED_INT_SAMPLER_1D_ARRAY: GlType
GL_SAMPLER_2D_ARRAY: GlType
GL_INT_SAMPLER_2D_ARRAY: GlType
GL_UNSIGNED_INT_SAMPLER_2D_ARRAY: GlType
GL_SAMPLER_CUBE_MAP_ARRAY: GlType
GL_INT_SAMPLER_CUBE_MAP_ARRAY: GlType
GL_UNSIGNED_INT_SAMPLER_CUBE_MAP_ARRAY: GlType
GL_SAMPLER_BUFFER: GlType
GL_INT_SAMPLER_BUFFER: GlType
GL_UNSIGNED_INT_SAMPLER_BUFFER: GlType
GL_SAMPLER_2D_MULTISAMPLE: GlType
GL_INT_SAMPLER_2D_MULTISAMPLE: GlType
GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE: GlType
GL_SAMPLER_2D_MULTISAMPLE_ARRAY: GlType
GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY: GlType
GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY: GlType
GL_SAMPLER_1D_SHADOW: GlType
GL_SAMPLER_2D_SHADOW: GlType
GL_SAMPLER_CUBE_SHADOW: GlType
GL_SAMPLER_2D_RECT_SHADOW: GlType
GL_SAMPLER_1D_ARRAY_SHADOW: GlType
GL_SAMPLER_2D_ARRAY_SHADOW: GlType

GL_RED: GlTextureComponents
GL_RG: GlTextureComponents
GL_RGB: GlTextureComponents
GL_RGBA: GlTextureComponents
GL_DEPTH_COMPONENT: GlTextureComponents
GL_RED_INTEGER: GlTextureComponents
GL_RG_INTEGER: GlTextureComponents
GL_RGB_INTEGER: GlTextureComponents
GL_RGBA_INTEGER: GlTextureComponents

GL_R8UI: GlTextureComponents
GL_R8I: GlTextureComponents
GL_R16UI: GlTextureComponents
GL_R16I: GlTextureComponents
GL_R32UI: GlTextureComponents
GL_R32I: GlTextureComponents
GL_R32F: GlTextureComponents

GL_RG8UI: GlTextureComponents
GL_RG8I: GlTextureComponents
GL_RG16UI: GlTextureComponents
GL_RG16I: GlTextureComponents
GL_RG32UI: GlTextureComponents
GL_RG32I: GlTextureComponents
GL_RG32F: GlTextureComponents

GL_RGB8UI: GlTextureComponents
GL_RGB8I: GlTextureComponents
GL_RGB16UI: GlTextureComponents
GL_RGB16I: GlTextureComponents
GL_RGB32UI: GlTextureComponents
GL_RGB32I: GlTextureComponents
GL_RGB32F: GlTextureComponents

GL_RGBA8UI: GlTextureComponents
GL_RGBA8I: GlTextureComponents
GL_RGBA16UI: GlTextureComponents
GL_RGBA16I: GlTextureComponents
GL_RGBA32UI: GlTextureComponents
GL_RGBA32I: GlTextureComponents
GL_RGBA32F: GlTextureComponents

GL_CLAMP_TO_EDGE: GlTextureWrap
GL_CLAMP_TO_BORDER: GlTextureWrap
GL_REPEAT: GlTextureWrap
GL_MIRRORED_REPEAT: GlTextureWrap

GL_NEAREST: GlTextureFilter
GL_LINEAR: GlTextureFilter
GL_NEAREST_MIPMAP_NEAREST: GlTextureFilter
GL_NEAREST_MIPMAP_LINEAR: GlTextureFilter
GL_LINEAR_MIPMAP_NEAREST: GlTextureFilter
GL_LINEAR_MIPMAP_LINEAR: GlTextureFilter

GL_TEXTURE_2D: GlTextureTarget

GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS_VALUE: int
GL_MAX_CLIP_DISTANCES_VALUE: int

GL_NEVER: GlFunc
GL_ALWAYS: GlFunc
GL_LESS: GlFunc
GL_LEQUAL: GlFunc
GL_GREATER: GlFunc
GL_GEQUAL: GlFunc
GL_EQUAL: GlFunc
GL_NOTEQUAL: GlFunc

GL_ZERO: GlBlendFactor
GL_ONE: GlBlendFactor
GL_SRC_COLOR: GlBlendFactor
GL_ONE_MINUS_SRC_COLOR: GlBlendFactor
GL_DST_COLOR: GlBlendFactor
GL_ONE_MINUS_DST_COLOR: GlBlendFactor
GL_SRC_ALPHA: GlBlendFactor
GL_ONE_MINUS_SRC_ALPHA: GlBlendFactor
GL_DST_ALPHA: GlBlendFactor
GL_ONE_MINUS_DST_ALPHA: GlBlendFactor
GL_CONSTANT_COLOR: GlBlendFactor
GL_ONE_MINUS_CONSTANT_COLOR: GlBlendFactor
GL_CONSTANT_ALPHA: GlBlendFactor
GL_ONE_MINUS_CONSTANT_ALPHA: GlBlendFactor

GL_FUNC_ADD: GlBlendFunction
GL_FUNC_SUBTRACT: GlBlendFunction
GL_FUNC_REVERSE_SUBTRACT: GlBlendFunction
GL_MIN: GlBlendFunction
GL_MAX: GlBlendFunction

GL_FRONT: GlCull
GL_BACK: GlCull

GL_POINTS: GlPrimitive
GL_LINES: GlPrimitive
GL_LINE_STRIP: GlPrimitive
GL_LINE_LOOP: GlPrimitive
GL_TRIANGLES: GlPrimitive
GL_TRIANGLE_STRIP: GlPrimitive
GL_TRIANGLE_FAN: GlPrimitive
GL_LINE_STRIP_ADJACENCY: GlPrimitive
GL_LINES_ADJACENCY: GlPrimitive
GL_TRIANGLE_STRIP_ADJACENCY: GlPrimitive
GL_TRIANGLES_ADJACENCY: GlPrimitive

GL_POINT: GlPolygonRasterizationMode
GL_LINE: GlPolygonRasterizationMode
GL_FILL: GlPolygonRasterizationMode

GL_LOWER_LEFT: GlOrigin
GL_UPPER_LEFT: GlOrigin

GL_NEGATIVE_ONE_TO_ONE: GlDepthMode
GL_ZERO_TO_ONE: GlDepthMode

def debug_gl(callback: Callable[[int, int, int, int, str], None], /) -> None: ...
def activate_gl_vertex_array(gl_vertex_array: GlVertexArray | None, /) -> None: ...
def set_gl_buffer_target(target: GlBufferTarget, gl_buffer: GlBuffer | None, /) -> None: ...
def create_gl_buffer() -> GlBuffer: ...
def create_gl_vertex_array() -> GlVertexArray: ...
def create_gl_texture() -> GlTexture: ...
def create_gl_framebuffer() -> GlFramebuffer: ...
def delete_gl_buffer(gl_buffer: GlBuffer, /) -> None: ...
def delete_gl_vertex_array(gl_vertex_array: GlVertexArray, /) -> None: ...
def delete_gl_texture(gl_texture: GlTexture, /) -> None: ...
def delete_gl_framebuffer(gl_framebuffer: GlFramebuffer, /) -> None: ...
def delete_gl_renderbuffer(gl_renderbuffer: GlRenderbuffer, /) -> None: ...
def set_gl_buffer_target_data(
    target: GlBufferTarget, data: Buffer | int, usage: int, /
) -> int: ...
def write_gl_buffer_target_data(target: GlBufferTarget, data: Buffer, offset: int, /) -> None: ...
def create_gl_buffer_memory_view(target: GlBufferTarget, length: int, /) -> memoryview: ...
def release_gl_buffer_memory_view(target: GlBufferTarget, /) -> None: ...
def configure_gl_vertex_array_location(
    location: int,
    size: int,
    type: GlType,
    stride: int,
    offset: int,
    instancing_divistor: int | None,
    /,
) -> None: ...
def set_draw_framebuffer(gl_framebuffer: GlFramebuffer, size: IVector2) -> None: ...
def set_read_framebuffer(gl_framebuffer: GlFramebuffer) -> None: ...
def read_color_from_framebuffer(rect: IRectangle, index: int, /) -> FVector4Array: ...
def read_depth_from_framebuffer(rect: IRectangle, /) -> FArray: ...
def clear_framebuffer(color: FVector4 | None, depth: float | None, /) -> None: ...
def attach_color_texture_to_gl_read_framebuffer(gl_texture: GlTexture, index: int, /) -> None: ...
def attach_depth_texture_to_gl_read_framebuffer(gl_texture: GlTexture, /) -> None: ...
def attach_depth_renderbuffer_to_gl_read_framebuffer(size: IVector2, /) -> GlRenderbuffer: ...
def set_texture_locations_on_gl_draw_framebuffer(texture_indices: list[None | int], /) -> None: ...
def set_active_gl_texture_unit(unit: int, /) -> None: ...
def set_gl_texture_target(target: GlTextureTarget, gl_texture: GlTexture | None, /) -> None: ...
def set_gl_texture_target_2d_data(
    target: GlTextureTarget,
    internal_format: GlTextureComponents,
    size: UVector2,
    format: GlTextureComponents,
    type: GlType,
    data: Buffer,
    /,
) -> None: ...
def generate_gl_texture_target_mipmaps(target: GlTextureTarget, /) -> None: ...
def set_gl_texture_target_parameters(
    target: GlTextureTarget,
    min_filter: GlTextureFilter,
    mag_filter: GlTextureFilter,
    wrap_s: GlTextureWrap,
    wrap_t: GlTextureWrap | None,
    wrap_r: GlTextureWrap | None,
    wrap_color: FVector4,
    anisotropy: float,
    /,
) -> None: ...
def get_gl_program_uniforms(program: GlProgram, /) -> tuple[tuple[str, int, GlType, int], ...]: ...
def get_gl_program_attributes(
    program: GlProgram, /
) -> tuple[tuple[str, int, GlType, int], ...]: ...
def create_gl_program(
    vertex: Buffer | None, geometry: Buffer | None, fragment: Buffer | None, /
) -> GlProgram: ...
def delete_gl_program(gl_program: GlProgram, /) -> None: ...
def use_gl_program(gl_program: GlProgram | None, /) -> None: ...
def set_active_gl_program_uniform_float(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_double(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_int(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_unsigned_int(
    location: int, count: int, value_ptr: int
) -> None: ...
def set_active_gl_program_uniform_float_2(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_double_2(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_int_2(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_unsigned_int_2(
    location: int, count: int, value_ptr: int
) -> None: ...
def set_active_gl_program_uniform_float_3(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_double_3(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_int_3(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_unsigned_int_3(
    location: int, count: int, value_ptr: int
) -> None: ...
def set_active_gl_program_uniform_float_4(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_double_4(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_int_4(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_unsigned_int_4(
    location: int, count: int, value_ptr: int
) -> None: ...
def set_active_gl_program_uniform_float_2x2(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_float_2x3(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_float_2x4(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_float_3x2(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_float_3x3(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_float_3x4(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_float_4x2(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_float_4x3(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_float_4x4(location: int, count: int, value_ptr: int) -> None: ...
def set_active_gl_program_uniform_double_2x2(
    location: int, count: int, value_ptr: int
) -> None: ...
def set_active_gl_program_uniform_double_2x3(
    location: int, count: int, value_ptr: int
) -> None: ...
def set_active_gl_program_uniform_double_2x4(
    location: int, count: int, value_ptr: int
) -> None: ...
def set_active_gl_program_uniform_double_3x2(
    location: int, count: int, value_ptr: int
) -> None: ...
def set_active_gl_program_uniform_double_3x3(
    location: int, count: int, value_ptr: int
) -> None: ...
def set_active_gl_program_uniform_double_3x4(
    location: int, count: int, value_ptr: int
) -> None: ...
def set_active_gl_program_uniform_double_4x2(
    location: int, count: int, value_ptr: int
) -> None: ...
def set_active_gl_program_uniform_double_4x3(
    location: int, count: int, value_ptr: int
) -> None: ...
def set_active_gl_program_uniform_double_4x4(
    location: int, count: int, value_ptr: int
) -> None: ...
def execute_gl_program_index_buffer(
    mode: GlPrimitive, count: int, offset: int, type: GlType, instances: int
) -> None: ...
def execute_gl_program_indices(
    mode: GlPrimitive, first: int, count: int, instances: int
) -> None: ...
def set_gl_execution_state(
    depth_write: bool,
    depth_func: GlFunc,
    color_mask_r: bool,
    color_mask_g: bool,
    color_mask_b: bool,
    color_mask_a: bool,
    blend_source: GlBlendFactor,
    blend_destination: GlBlendFactor,
    blend_source_alpha: GlBlendFactor | None,
    blend_destination_alpha: GlBlendFactor | None,
    blend_function: GlBlendFunction,
    blend_color: FVector4 | None,
    cull_face: GlCull | None,
    scissor_position: IVector2 | None,
    scissor_size: IVector2 | None,
    depth_clamp: bool,
    polygon_rasterization_mode: GlPolygonRasterizationMode,
    point_size: float,
    clip_distances: int,
    /,
) -> None: ...
def get_gl_version() -> str: ...
def set_gl_clip(origin: GlOrigin, depth: GlDepthMode) -> None: ...
def get_gl_clip() -> tuple[GlOrigin, GlDepthMode]: ...
