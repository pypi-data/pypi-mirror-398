#include "GL/glew.h"

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdio.h>

#include "emath.h"

#define CHECK_UNEXPECTED_ARG_COUNT_ERROR(expected_count)\
    if (expected_count != nargs)\
    {\
        PyErr_Format(PyExc_TypeError, "expected %zi args, got %zi", expected_count, nargs);\
        goto error;\
    }

#define CHECK_UNEXPECTED_PYTHON_ERROR()\
    if (PyErr_Occurred())\
    {\
        goto error;\
    }

#define CHECK_GL_ERROR()\
    {\
        GLenum gl_error = glGetError();\
        if (gl_error != GL_NO_ERROR)\
        {\
            PyErr_Format(\
                PyExc_RuntimeError,\
                "gl error: %s\nfile: %s\nfunction: %s\nline: %i",\
                gluErrorString(gl_error),\
                __FILE__,\
                __func__,\
                __LINE__\
            );\
            goto error;\
        }\
    }

typedef struct ModuleState
{
    bool is_gl_clip_control_supported;

    float clear_color[4];
    float clear_depth;
    int texture_filter_anisotropic_supported;
    bool depth_test;
    bool depth_mask;
    bool depth_clamp;
    GLenum depth_func;
    bool color_mask_r;
    bool color_mask_g;
    bool color_mask_b;
    bool color_mask_a;
    bool blend;
    GLenum blend_source;
    GLenum blend_destination;
    GLenum blend_source_alpha;
    GLenum blend_destination_alpha;
    GLenum blend_equation;
    float blend_color[4];
    bool cull_face_enabled;
    GLenum cull_face;
    bool scissor_enabled;
    int scissor[4];
    GLenum polygon_rasterization_mode;
    float point_size;
    int clip_distances;
    GLenum clip_origin;
    GLenum clip_depth;
} ModuleState;

static PyObject *
reset_module_state(PyObject *module, PyObject *unused)
{
    ModuleState *state = (ModuleState *)PyModule_GetState(module);
    CHECK_UNEXPECTED_PYTHON_ERROR();
    if (!state){ Py_RETURN_NONE; }

    state->is_gl_clip_control_supported = false;

    state->clear_color[0] = -1;
    state->clear_color[1] = -1;
    state->clear_color[2] = -1;
    state->clear_color[3] = -1;
    state->clear_depth = -1;
    state->depth_test = false;
    state->depth_mask = true;
    state->depth_clamp = false;
    state->depth_func = GL_LESS;
    state->color_mask_r = true;
    state->color_mask_g = true;
    state->color_mask_b = true;
    state->color_mask_a = true;
    state->blend = false;
    state->blend_source = GL_ONE;
    state->blend_destination = GL_ZERO;
    state->blend_source_alpha = GL_ONE;
    state->blend_destination_alpha = GL_ZERO;
    state->blend_equation = GL_FUNC_ADD;
    state->blend_color[0] = 0;
    state->blend_color[1] = 1;
    state->blend_color[2] = 2;
    state->blend_color[3] = 3;
    state->cull_face_enabled = false;
    state->cull_face = GL_BACK;
    state->scissor_enabled = false;
    state->scissor[0] = -1;
    state->scissor[1] = -1;
    state->scissor[2] = -1;
    state->scissor[3] = -1;
    state->polygon_rasterization_mode = GL_FILL;
    state->point_size = 1.0f;
    state->clip_distances = 0;
    state->clip_origin = GL_LOWER_LEFT;
    state->clip_depth = GL_NEGATIVE_ONE_TO_ONE;

    state->texture_filter_anisotropic_supported = GLEW_EXT_texture_filter_anisotropic;
    Py_RETURN_NONE;
error:
    return 0;
}

static void GLAPIENTRY
debug_callback_(
    GLenum source,
    GLenum type,
    GLuint id,
    GLenum severity,
    GLsizei length,
    const GLchar *message,
    const void *py_callback
)
{
    PyObject* result = PyObject_CallFunction(
        (PyObject *)py_callback,
        "iiIis",
        source, type, id, severity, message
    );
    if (!result)
    {
        PyObject *py_err = PyErr_GetRaisedException();
        PyErr_WriteUnraisable(py_err);
        Py_DECREF(py_err);
    }
    Py_DECREF(result);
}

static PyObject *
debug_gl(PyObject *module, PyObject *py_callback)
{
    glEnable(GL_DEBUG_OUTPUT);
    if (glGetError() != GL_NO_ERROR)
    {
        Py_RETURN_NONE;
    }

    Py_INCREF(py_callback);
    glEnable(GL_DEBUG_OUTPUT_SYNCHRONOUS);
    CHECK_GL_ERROR();
    glDebugMessageCallback(debug_callback_, py_callback);
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    Py_DECREF(py_callback);
    return 0;
}

static PyObject *
activate_gl_vertex_array(PyObject *module, PyObject *py_gl_vertex_array)
{
    GLuint gl_vertex_array = 0;
    if (py_gl_vertex_array != Py_None)
    {
        gl_vertex_array = PyLong_AsUnsignedLong(py_gl_vertex_array);
        CHECK_UNEXPECTED_PYTHON_ERROR();
    }

    glBindVertexArray(gl_vertex_array);
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
set_gl_buffer_target(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    CHECK_UNEXPECTED_ARG_COUNT_ERROR(2);

    GLenum target = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLuint gl_buffer = 0;
    if (args[1] != Py_None)
    {
        gl_buffer = PyLong_AsUnsignedLong(args[1]);
        CHECK_UNEXPECTED_PYTHON_ERROR();
    }

    glBindBuffer(target, gl_buffer);
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
create_gl_buffer(PyObject *module, PyObject *unused)
{
    GLuint gl_buffer = 0;

    glGenBuffers(1, &gl_buffer);
    CHECK_GL_ERROR();

    return PyLong_FromUnsignedLong(gl_buffer);
error:
    return 0;
}

static PyObject *
create_gl_vertex_array(PyObject *module, PyObject *unused)
{
    GLuint gl_vertex_array = 0;

    glGenVertexArrays(1, &gl_vertex_array);
    CHECK_GL_ERROR();

    return PyLong_FromUnsignedLong(gl_vertex_array);
error:
    return 0;
}

static PyObject *
create_gl_texture(PyObject *module, PyObject *unused)
{
    GLuint gl_texture = 0;

    glGenTextures(1, &gl_texture);
    CHECK_GL_ERROR();

    return PyLong_FromUnsignedLong(gl_texture);
error:
    return 0;
}

static PyObject *
create_gl_framebuffer(PyObject *module, PyObject *unused)
{
    GLuint gl_framebuffer = 0;

    glGenFramebuffers(1, &gl_framebuffer);
    CHECK_GL_ERROR();

    return PyLong_FromUnsignedLong(gl_framebuffer);
error:
    return 0;
}

static PyObject *
delete_gl_buffer(PyObject *module, PyObject *py_gl_buffer)
{
    GLuint gl_buffer = PyLong_AsUnsignedLong(py_gl_buffer);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    glDeleteBuffers(1, &gl_buffer);

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
delete_gl_vertex_array(PyObject *module, PyObject *py_gl_vertex_array)
{
    GLuint gl_vertex_array = PyLong_AsUnsignedLong(py_gl_vertex_array);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    glDeleteVertexArrays(1, &gl_vertex_array);

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
delete_gl_texture(PyObject *module, PyObject *py_gl_texture)
{
    GLuint gl_texture = PyLong_AsUnsignedLong(py_gl_texture);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    glDeleteTextures(1, &gl_texture);

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
delete_gl_framebuffer(PyObject *module, PyObject *py_gl_framebuffer)
{
    GLuint gl_framebuffer = PyLong_AsUnsignedLong(py_gl_framebuffer);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    glDeleteFramebuffers(1, &gl_framebuffer);

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
delete_gl_renderbuffer(PyObject *module, PyObject *gl_gl_render_buffer)
{
    GLuint gl_render_buffer = PyLong_AsUnsignedLong(gl_gl_render_buffer);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    glDeleteRenderbuffers(1, &gl_render_buffer);

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
write_gl_buffer_target_data(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    Py_buffer buffer;
    buffer.obj = 0;

    CHECK_UNEXPECTED_ARG_COUNT_ERROR(3);

    GLenum target = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    if (PyObject_GetBuffer(args[1], &buffer, PyBUF_CONTIG_RO) == -1){ goto error; }

    GLintptr offset = PyLong_AsLong(args[2]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLint buffer_size;
    glGetBufferParameteriv(target, GL_BUFFER_SIZE, &buffer_size);
    CHECK_GL_ERROR();

    if (offset < 0 || offset + buffer.len > buffer_size)
    {
        PyErr_Format(
            PyExc_ValueError,
            "write would overrun buffer (offset: %zi, size: %zi, buffer size: %i)",
            offset,
            buffer.len,
            buffer_size
        );
        goto error;
    }

    glBufferSubData(target, offset, buffer.len, buffer.buf);
    PyBuffer_Release(&buffer);
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    if (buffer.buf != 0)
    {
        PyBuffer_Release(&buffer);
    }
    return 0;
}

static PyObject *
set_gl_buffer_target_data(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    CHECK_UNEXPECTED_ARG_COUNT_ERROR(3);

    GLenum target = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    PyObject *data = args[1];

    GLenum usage = PyLong_AsLong(args[2]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    Py_buffer buffer;
    if (PyLong_Check(data))
    {
        long length = PyLong_AsLong(data);
        CHECK_UNEXPECTED_PYTHON_ERROR();
        if (length < 0)
        {
            PyErr_Format(PyExc_ValueError, "data must be 0 or more");
            goto error;
        }
        buffer.len = length;
        buffer.buf = 0;
    }
    else
    {
        if (PyObject_GetBuffer(data, &buffer, PyBUF_CONTIG_RO) == -1){ goto error; }
    }

    glBufferData(target, buffer.len, buffer.buf, usage);

    if (buffer.buf != 0)
    {
        PyBuffer_Release(&buffer);
    }

    CHECK_GL_ERROR();

    return PyLong_FromSsize_t(buffer.len);
error:
    return 0;
}

static PyObject *
create_gl_buffer_memory_view(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    CHECK_UNEXPECTED_ARG_COUNT_ERROR(2);

    GLenum target = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    Py_ssize_t length = PyLong_AsSsize_t(args[1]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    void *memory = glMapBuffer(target, GL_READ_WRITE);
    CHECK_GL_ERROR();

    PyObject *memory_view = PyMemoryView_FromMemory(memory, length, PyBUF_WRITE);
    if (!memory_view)
    {
        glUnmapBuffer(target);
        CHECK_GL_ERROR();
        goto error;
    }

    return memory_view;
error:
    return 0;
}

static PyObject *
release_gl_buffer_memory_view(PyObject *module, PyObject *py_target)
{
    GLenum target = PyLong_AsLong(py_target);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    glUnmapBuffer(target);
    CHECK_GL_ERROR();
    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
configure_gl_vertex_array_location(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    CHECK_UNEXPECTED_ARG_COUNT_ERROR(6);

    GLuint location = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLint count = PyLong_AsLong(args[1]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLenum type = PyLong_AsLong(args[2]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLsizei stride = PyLong_AsLong(args[3]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    void *offset = (void *)PyLong_AsLong(args[4]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    PyObject *py_instancing_divisor = args[5];

    switch (type)
    {
        case GL_BYTE:
        case GL_UNSIGNED_BYTE:
        case GL_SHORT:
        case GL_UNSIGNED_SHORT:
        case GL_INT:
        case GL_UNSIGNED_INT:
        {
            glVertexAttribIPointer(location, count, type, stride, offset);
            break;
        }
        default:
        {
            glVertexAttribPointer(location, count, type, GL_FALSE, stride, offset);
            break;
        }

    }
    CHECK_GL_ERROR();

    glEnableVertexAttribArray(location);
    CHECK_GL_ERROR();

    if (py_instancing_divisor != Py_None)
    {
        GLuint instancing_divisor = PyLong_AsLong(py_instancing_divisor);
        CHECK_UNEXPECTED_PYTHON_ERROR();
        glVertexAttribDivisor(location, instancing_divisor);
        CHECK_GL_ERROR();
    }

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
set_draw_framebuffer(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    PyObject *ex = 0;
    struct EMathApi *emath_api = 0;

    CHECK_UNEXPECTED_ARG_COUNT_ERROR(2);

    GLuint gl_framebuffer = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    PyObject *py_size = args[1];
    CHECK_UNEXPECTED_PYTHON_ERROR();

    emath_api = EMathApi_Get();
    CHECK_UNEXPECTED_PYTHON_ERROR();

    const int *size = emath_api->IVector2_GetValuePointer(py_size);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    EMathApi_Release();
    emath_api = 0;

    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, gl_framebuffer);
    CHECK_GL_ERROR();

    glViewport(0, 0, size[0], size[1]);
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    ex = PyErr_GetRaisedException();
    if (emath_api){ EMathApi_Release(); }
    PyErr_SetRaisedException(ex);
    return 0;
}

static PyObject *
set_read_framebuffer(PyObject *module, PyObject *py_gl_framebuffer)
{
    GLuint gl_framebuffer = PyLong_AsLong(py_gl_framebuffer);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    glBindFramebuffer(GL_READ_FRAMEBUFFER, gl_framebuffer);
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
read_color_from_framebuffer(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    GLint original_texture_0_name = -1;
    PyObject *ex = 0;
    float *data = 0;
    struct EMathApi *emath_api = 0;

    CHECK_UNEXPECTED_ARG_COUNT_ERROR(2);

    PyObject *py_rect = args[0];
    long index = PyLong_AsLong(args[1]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    PyObject *py_position = PyObject_GetAttrString(py_rect, "position");
    CHECK_UNEXPECTED_PYTHON_ERROR();

    PyObject *py_size = PyObject_GetAttrString(py_rect, "size");
    CHECK_UNEXPECTED_PYTHON_ERROR();

    emath_api = EMathApi_Get();
    CHECK_UNEXPECTED_PYTHON_ERROR();

    const int *position = emath_api->IVector2_GetValuePointer(py_position);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    const int *size = emath_api->IVector2_GetValuePointer(py_size);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    size_t count = (size_t)size[0] * (size_t)size[1];
    data = malloc(sizeof(float) * 4 * count);
    if (!data)
    {
        PyErr_Format(PyExc_MemoryError, "out of memory");
        goto error;
    }

    GLint texture_name;
    if (index != 0)
    {
        glGetFramebufferAttachmentParameteriv(
            GL_READ_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            GL_FRAMEBUFFER_ATTACHMENT_OBJECT_NAME,
            &original_texture_0_name
        );
        CHECK_GL_ERROR();
        glGetFramebufferAttachmentParameteriv(
            GL_READ_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0 + index,
            GL_FRAMEBUFFER_ATTACHMENT_OBJECT_NAME,
            &texture_name
        );
        CHECK_GL_ERROR();
        glFramebufferTexture2D(
            GL_READ_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            GL_TEXTURE_2D,
            texture_name,
            0
        );
        CHECK_GL_ERROR();
    }

    glReadPixels(position[0], position[1], size[0], size[1], GL_RGBA, GL_FLOAT, data);
    CHECK_GL_ERROR();

    if (index != 0)
    {
        glFramebufferTexture2D(
            GL_READ_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            GL_TEXTURE_2D,
            original_texture_0_name,
            0
        );
        CHECK_GL_ERROR();
        original_texture_0_name = -1;
    }

    PyObject *array = emath_api->FVector4Array_Create(count, data);
    free(data);
    data = 0;
    EMathApi_Release();
    return array;
error:
    ex = PyErr_GetRaisedException();
    if (emath_api){ EMathApi_Release(); }
    if (original_texture_0_name != -1)
    {
        glFramebufferTexture2D(
            GL_READ_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            GL_TEXTURE_2D,
            original_texture_0_name,
            0
        );
    }
    if (data){ free(data); }
    PyErr_SetRaisedException(ex);
    return 0;
}

static PyObject *
read_depth_from_framebuffer(PyObject *module, PyObject *rect)
{
    PyObject *ex = 0;
    struct EMathApi *emath_api = 0;
    float *data = 0;

    PyObject *py_position = PyObject_GetAttrString(rect, "position");
    CHECK_UNEXPECTED_PYTHON_ERROR();

    PyObject *py_size = PyObject_GetAttrString(rect, "size");
    CHECK_UNEXPECTED_PYTHON_ERROR();

    emath_api = EMathApi_Get();
    CHECK_UNEXPECTED_PYTHON_ERROR();

    const int *position = emath_api->IVector2_GetValuePointer(py_position);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    const int *size = emath_api->IVector2_GetValuePointer(py_size);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    size_t count = (size_t)size[0] * (size_t)size[1];
    data = malloc(sizeof(float) * count);
    if (!data)
    {
        PyErr_Format(PyExc_MemoryError, "out of memory");
        goto error;
    }

    glReadPixels(position[0], position[1], size[0], size[1], GL_DEPTH_COMPONENT, GL_FLOAT, data);
    CHECK_GL_ERROR();

    PyObject *array = emath_api->FArray_Create(count, data);
    free(data);
    data = 0;
    EMathApi_Release();
    return array;
error:
    ex = PyErr_GetRaisedException();
    if (emath_api){ EMathApi_Release(); }
    if (!data){ free(data); }
    PyErr_SetRaisedException(ex);
    return 0;
}

static PyObject *
clear_framebuffer(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    PyObject *ex = 0;
    struct EMathApi *emath_api = 0;

    CHECK_UNEXPECTED_ARG_COUNT_ERROR(2);

    PyObject *py_color = args[0];
    PyObject *py_depth = args[1];
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLbitfield clear_mask = 0;

    ModuleState *state = (ModuleState *)PyModule_GetState(module);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    if (py_color != Py_None)
    {
        emath_api = EMathApi_Get();
        CHECK_UNEXPECTED_PYTHON_ERROR();

        const float *color = emath_api->FVector4_GetValuePointer(py_color);
        CHECK_UNEXPECTED_PYTHON_ERROR();

        EMathApi_Release();
        emath_api = 0;

        if (memcmp(state->clear_color, color, sizeof(float) * 4) != 0)
        {
            glClearColor(color[0], color[1], color[2], color[3]);
            CHECK_GL_ERROR();
            memcpy(state->clear_color, color, sizeof(float) * 4);
        }
        clear_mask |= GL_COLOR_BUFFER_BIT;
        if (
            state->color_mask_r != true ||
            state->color_mask_g != true ||
            state->color_mask_b != true ||
            state->color_mask_a != true
        )
        {
            glColorMask(true, true, true, true);
            CHECK_GL_ERROR();
            state->color_mask_r = true;
            state->color_mask_g = true;
            state->color_mask_b = true;
            state->color_mask_a = true;
        }
    }

    if (py_depth != Py_None)
    {
        float depth = PyFloat_AsDouble(py_depth);
        CHECK_UNEXPECTED_PYTHON_ERROR();
        if (depth != state->clear_depth)
        {
            glClearDepth(depth);
            CHECK_GL_ERROR();
        }
        clear_mask |= GL_DEPTH_BUFFER_BIT;
        if (state->depth_mask != GL_TRUE)
        {
            glDepthMask(GL_TRUE);
            CHECK_GL_ERROR();
            state->depth_mask = GL_TRUE;
        }
    }

    if (state->scissor_enabled)
    {
        glDisable(GL_SCISSOR_TEST);
        CHECK_GL_ERROR();
        state->scissor_enabled = false;
    }

    if (clear_mask != 0)
    {
        glClear(clear_mask);
        CHECK_GL_ERROR();
    }
    Py_RETURN_NONE;
error:
    ex = PyErr_GetRaisedException();
    if (emath_api){ EMathApi_Release(); }
    PyErr_SetRaisedException(ex);
    return 0;
}

static PyObject *
attach_color_texture_to_gl_read_framebuffer(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    CHECK_UNEXPECTED_ARG_COUNT_ERROR(2);

    GLuint gl_texture = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    long index = PyLong_AsLong(args[1]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    glFramebufferTexture2D(GL_READ_FRAMEBUFFER, GL_COLOR_ATTACHMENT0 + index, GL_TEXTURE_2D, gl_texture, 0);
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
attach_depth_texture_to_gl_read_framebuffer(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    CHECK_UNEXPECTED_ARG_COUNT_ERROR(1);

    GLuint gl_texture = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    glFramebufferTexture2D(GL_READ_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, gl_texture, 0);
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
attach_depth_renderbuffer_to_gl_read_framebuffer(PyObject *module, PyObject *py_size)
{
    PyObject *ex = 0;
    struct EMathApi *emath_api = 0;
    GLuint gl_render_buffer = 0;

    emath_api = EMathApi_Get();
    CHECK_UNEXPECTED_PYTHON_ERROR();

    const int *size = emath_api->IVector2_GetValuePointer(py_size);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    EMathApi_Release();
    emath_api = 0;

    glGenRenderbuffers(1, &gl_render_buffer);
    CHECK_GL_ERROR();

    glBindRenderbuffer(GL_RENDERBUFFER, gl_render_buffer);
    CHECK_GL_ERROR();

    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, size[0], size[1]);
    CHECK_GL_ERROR();

    glFramebufferRenderbuffer(
        GL_READ_FRAMEBUFFER,
        GL_DEPTH_ATTACHMENT,
        GL_RENDERBUFFER,
        gl_render_buffer
    );
    CHECK_GL_ERROR();

    PyObject *py_gl_render_buffer = PyLong_FromUnsignedLong(gl_render_buffer);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    return py_gl_render_buffer;
error:
    if (gl_render_buffer){ glDeleteRenderbuffers(1, &gl_render_buffer); }
    ex = PyErr_GetRaisedException();
    if (emath_api){ EMathApi_Release(); }
    PyErr_SetRaisedException(ex);
    return 0;
}

static PyObject *
set_texture_locations_on_gl_draw_framebuffer(PyObject *module, PyObject *py_texture_indices)
{
    Py_ssize_t n_indices = PyList_GET_SIZE(py_texture_indices);

    GLenum *gl_buffers = malloc(sizeof(GLenum) * n_indices);

    for (Py_ssize_t i = 0; i < n_indices; i++)
    {
        PyObject *index = PyList_GET_ITEM(py_texture_indices, i);
        if (index == Py_None)
        {
            gl_buffers[i] = GL_NONE;
        }
        else
        {
            gl_buffers[i] = GL_COLOR_ATTACHMENT0 + i;
        }
    }

    glDrawBuffers(n_indices, gl_buffers);
    free(gl_buffers);
    gl_buffers = 0;
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    if (gl_buffers != 0){ free(gl_buffers); }
    return 0;
}

static PyObject *
set_active_gl_texture_unit(PyObject *module, PyObject *py_unit)
{
    GLenum unit = PyLong_AsLong(py_unit);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    glActiveTexture(GL_TEXTURE0 + unit);
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
set_gl_texture_target(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    CHECK_UNEXPECTED_ARG_COUNT_ERROR(2);

    GLenum target = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLuint gl_texture = 0;
    if (args[1] != Py_None)
    {
        gl_texture = PyLong_AsUnsignedLong(args[1]);
        CHECK_UNEXPECTED_PYTHON_ERROR();
    }

    glBindTexture(target, gl_texture);
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
set_gl_texture_target_2d_data(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    PyObject *ex = 0;
    struct EMathApi *emath_api = 0;

    CHECK_UNEXPECTED_ARG_COUNT_ERROR(6);

    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    CHECK_GL_ERROR();

    GLenum target = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLint internal_format = PyLong_AsLong(args[1]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLsizei width = 0;
    GLsizei height = 0;
    {
        PyObject *py_size = args[2];

        emath_api = EMathApi_Get();
        CHECK_UNEXPECTED_PYTHON_ERROR();

        const unsigned int *size = emath_api->UVector2_GetValuePointer(py_size);
        CHECK_UNEXPECTED_PYTHON_ERROR();

        EMathApi_Release();
        emath_api = 0;

        width = size[0];
        height = size[1];
    }

    GLint format = PyLong_AsLong(args[3]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLenum type = PyLong_AsLong(args[4]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    Py_buffer buffer;
    {
        PyObject *py_data = args[5];
        if (PyObject_GetBuffer(py_data, &buffer, PyBUF_CONTIG_RO) == -1){ goto error; }
    }

    glTexImage2D(
        target,
        0,
        internal_format,
        width,
        height,
        0,
        format,
        type,
        buffer.buf
    );
    PyBuffer_Release(&buffer);
    CHECK_UNEXPECTED_PYTHON_ERROR();
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    ex = PyErr_GetRaisedException();
    if (emath_api){ EMathApi_Release(); }
    PyErr_SetRaisedException(ex);
    return 0;
}

static PyObject *
generate_gl_texture_target_mipmaps(PyObject *module, PyObject *py_target)
{
    GLenum target = PyLong_AsLong(py_target);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    glGenerateMipmap(target);
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
set_gl_texture_target_parameters(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    PyObject *ex = 0;
    struct EMathApi *emath_api = 0;

    ModuleState *state = (ModuleState *)PyModule_GetState(module);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    CHECK_UNEXPECTED_ARG_COUNT_ERROR(8);

    GLenum target = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLenum min_filter = PyLong_AsLong(args[1]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLenum mag_filter = PyLong_AsLong(args[2]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    glTexParameteri(target, GL_TEXTURE_MIN_FILTER, min_filter);
    CHECK_GL_ERROR();

    glTexParameteri(target, GL_TEXTURE_MAG_FILTER, mag_filter);
    CHECK_GL_ERROR();

    for (size_t i = 0; i < 3; i++)
    {
        static const GLenum wrap_target[] = {
            GL_TEXTURE_WRAP_S,
            GL_TEXTURE_WRAP_T,
            GL_TEXTURE_WRAP_R
        };
        PyObject *py_wrap = args[3 + i];
        if (i > 0 && py_wrap == Py_None){ break; }
        GLenum wrap = PyLong_AsLong(py_wrap);
        CHECK_UNEXPECTED_PYTHON_ERROR();

        glTexParameteri(target, wrap_target[i], wrap);
        CHECK_GL_ERROR();
    }

    {
        PyObject *py_wrap_color = args[6];

        emath_api = EMathApi_Get();
        CHECK_UNEXPECTED_PYTHON_ERROR();

        const float *wrap_color = emath_api->FVector4_GetValuePointer(py_wrap_color);
        CHECK_UNEXPECTED_PYTHON_ERROR();

        EMathApi_Release();
        emath_api = 0;

        glTexParameterfv(target, GL_TEXTURE_BORDER_COLOR, wrap_color);
        CHECK_GL_ERROR();
    }

    GLfloat anisotropy = PyFloat_AsDouble(args[7]);
    CHECK_UNEXPECTED_PYTHON_ERROR();
    if (anisotropy >= 1.0 && state->texture_filter_anisotropic_supported)
    {
        glTexParameterf(target, GL_TEXTURE_MAX_ANISOTROPY_EXT, anisotropy);
        CHECK_GL_ERROR();
    }

    Py_RETURN_NONE;
error:
    ex = PyErr_GetRaisedException();
    if (emath_api){ EMathApi_Release(); }
    PyErr_SetRaisedException(ex);
    return 0;
}

static PyObject *
get_gl_program_uniforms(PyObject *module, PyObject *py_gl_shader)
{
    PyObject *result = 0;
    GLchar *name = 0;

    GLuint gl_shader = PyLong_AsUnsignedLong(py_gl_shader);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLint uniform_count = 0;
    glGetProgramiv(gl_shader, GL_ACTIVE_UNIFORMS, &uniform_count);
    CHECK_GL_ERROR();

    GLint max_name_length = 0;
    glGetProgramiv(gl_shader, GL_ACTIVE_UNIFORM_MAX_LENGTH, &max_name_length);
    CHECK_GL_ERROR();

    name = malloc(sizeof(GLchar) * max_name_length + 1);
    if (!name)
    {
        PyErr_Format(PyExc_MemoryError, "out of memory");
        goto error;
    }
    GLsizei name_length;
    GLint size;
    GLenum type;

    result = PyTuple_New(uniform_count);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    for (GLint i = 0; i < uniform_count; i++)
    {
        glGetActiveUniform(gl_shader, i, max_name_length, &name_length, &size, &type, name);
        CHECK_GL_ERROR();
        name[name_length] = 0;

        GLint location = glGetUniformLocation(gl_shader, name);
        CHECK_GL_ERROR();

        PyObject *uniform = Py_BuildValue("siii", name, size, type, location);
        CHECK_UNEXPECTED_PYTHON_ERROR();

        PyTuple_SET_ITEM(result, i, uniform);
    }

    free(name);

    return result;
error:
    Py_XDECREF(result);
    if (name){ free(name); }
    return 0;
}


static PyObject *
get_gl_program_attributes(PyObject *module, PyObject *py_gl_shader)
{
    PyObject *result = 0;
    GLchar *name = 0;

    GLuint gl_shader = PyLong_AsUnsignedLong(py_gl_shader);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLint attr_count = 0;
    glGetProgramiv(gl_shader, GL_ACTIVE_ATTRIBUTES, &attr_count);
    CHECK_GL_ERROR();

    GLint max_name_length = 0;
    glGetProgramiv(gl_shader, GL_ACTIVE_ATTRIBUTE_MAX_LENGTH, &max_name_length);
    CHECK_GL_ERROR();

    name = malloc(sizeof(GLchar) * max_name_length + 1);
    if (!name)
    {
        PyErr_Format(PyExc_MemoryError, "out of memory");
        goto error;
    }
    GLsizei name_length;
    GLint size;
    GLenum type;

    result = PyTuple_New(attr_count);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    for (GLint i = 0; i < attr_count; i++)
    {
        glGetActiveAttrib(gl_shader, i, max_name_length, &name_length, &size, &type, name);
        CHECK_GL_ERROR();
        name[name_length] = 0;

        GLint location = glGetAttribLocation(gl_shader, name);
        CHECK_GL_ERROR();

        PyObject *attr = Py_BuildValue("siii", name, size, type, location);
        CHECK_UNEXPECTED_PYTHON_ERROR();

        PyTuple_SET_ITEM(result, i, attr);
    }

    free(name);

    return result;
error:
    Py_XDECREF(result);
    if (name){ free(name); }
    return 0;
}


static PyObject *
create_gl_program(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    static const char * SHADER_STAGE_NAME[] = {
        "vertex",
        "geometry",
        "fragment"
    };
    static const GLenum SHADER_STAGES[] = {
        GL_VERTEX_SHADER,
        GL_GEOMETRY_SHADER,
        GL_FRAGMENT_SHADER
    };
    static const size_t SHADER_STAGES_LENGTH = sizeof(SHADER_STAGES) / sizeof(SHADER_STAGES[0]);
    GLuint shaders[] = {0, 0, 0};
    GLchar *log = 0;
    GLuint gl_program = 0;

    CHECK_UNEXPECTED_ARG_COUNT_ERROR(3);

    for(size_t i = 0; i < SHADER_STAGES_LENGTH; i++)
    {
        PyObject *shader_code = args[i];
        if (shader_code == Py_None){ continue; }

        GLuint shader = glCreateShader(SHADER_STAGES[i]);
        shaders[i] = shader;
        CHECK_GL_ERROR();

        {
            Py_buffer buffer;
            if (PyObject_GetBuffer(shader_code, &buffer, PyBUF_CONTIG_RO) == -1){ goto error; }
            GLint length = buffer.len;
            glShaderSource(shader, 1, (const GLchar *const *)&buffer.buf, &length);
            PyBuffer_Release(&buffer);
            CHECK_GL_ERROR();
        }

        glCompileShader(shader);
        CHECK_GL_ERROR();

        {
            GLint compile_status;
            glGetShaderiv(shader, GL_COMPILE_STATUS, &compile_status);
            CHECK_GL_ERROR();
            if (compile_status == GL_FALSE)
            {
                GLint log_length;
                glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &log_length);
                CHECK_GL_ERROR();

                log = malloc(sizeof(GLchar *) * log_length);
                if (!log)
                {
                    PyErr_Format(PyExc_MemoryError, "out of memory");
                    goto error;
                }

                glGetShaderInfoLog(shader, log_length, 0, log);
                CHECK_GL_ERROR();

                PyErr_Format(
                    PyExc_RuntimeError,
                    "%s stage failed to compile:\n%s",
                    SHADER_STAGE_NAME[i],
                    log
                );
                free(log);
                log = 0;

                goto error;
            }
        }
    }

    gl_program = glCreateProgram();
    CHECK_GL_ERROR();

    for(size_t i = 0; i < SHADER_STAGES_LENGTH; i++)
    {
        GLuint shader = shaders[i];
        if (shader == 0){ continue; }
        glAttachShader(gl_program, shader);
        CHECK_GL_ERROR();
    }

    glLinkProgram(gl_program);
    CHECK_GL_ERROR();
    {
        GLint link_status;
        glGetProgramiv(gl_program, GL_LINK_STATUS, &link_status);
        CHECK_GL_ERROR();

        if (link_status == GL_FALSE)
        {
            GLint log_length;
            glGetProgramiv(gl_program, GL_INFO_LOG_LENGTH, &log_length);
            CHECK_GL_ERROR();

            log = malloc(sizeof(GLchar *) * log_length);
            if (!log)
            {
                PyErr_Format(PyExc_MemoryError, "out of memory");
                goto error;
            }

            glGetProgramInfoLog(gl_program, log_length, 0, log);
            CHECK_GL_ERROR();

            PyErr_Format(
                PyExc_RuntimeError,
                "failed to link:\n%s",
                log
            );
            free(log);
            log = 0;

            goto error;
        }
    }

    for(size_t i = 0; i < SHADER_STAGES_LENGTH; i++)
    {
        GLuint shader = shaders[i];
        if (shader == 0){ continue; }
        glDeleteShader(shader);
        CHECK_GL_ERROR();
    }

    return PyLong_FromUnsignedLong(gl_program);
error:
    if (log){ free(log); }
    if (gl_program != 0){ glDeleteProgram(gl_program); }
    for(size_t i = 0; i < SHADER_STAGES_LENGTH; i++)
    {
        GLuint shader = shaders[i];
        if (shader == 0){ continue; }
        glDeleteShader(shader);
        CHECK_GL_ERROR();
    }
    return 0;
}

static PyObject *
delete_gl_program(PyObject *module, PyObject *py_gl_program)
{
    GLuint gl_program = PyLong_AsUnsignedLong(py_gl_program);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    glDeleteProgram(gl_program);

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
use_gl_program(PyObject *module, PyObject *py_gl_program)
{
    GLuint gl_program = 0;

    if (py_gl_program != Py_None)
    {
        gl_program = PyLong_AsUnsignedLong(py_gl_program);
        CHECK_UNEXPECTED_PYTHON_ERROR();
    }

    glUseProgram(gl_program);
    CHECK_GL_ERROR();

    Py_RETURN_NONE;
error:
    return 0;
}

#define SET_ACTIVE_GL_PROGRAM_UNIFORM(name, gl_type, uniform_name)\
    static PyObject *\
    set_active_gl_program_uniform_##name(PyObject *module, PyObject **args, Py_ssize_t nargs)\
    {\
        CHECK_UNEXPECTED_ARG_COUNT_ERROR(3);\
        \
        GLint location = PyLong_AsLong(args[0]);\
        CHECK_UNEXPECTED_PYTHON_ERROR();\
        \
        GLsizei count = (GLsizei)PyLong_AsSize_t(args[1]);\
        CHECK_UNEXPECTED_PYTHON_ERROR();\
        \
        gl_type *value = (gl_type *)PyLong_AsVoidPtr(args[2]);\
        CHECK_UNEXPECTED_PYTHON_ERROR();\
        \
        glUniform##uniform_name##v(location, count, value);\
        CHECK_GL_ERROR();\
        \
        Py_RETURN_NONE;\
    error:\
        return 0;\
    }

#define SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(name, gl_type, uniform_name)\
    static PyObject *\
    set_active_gl_program_uniform_##name(PyObject *module, PyObject **args, Py_ssize_t nargs)\
    {\
        CHECK_UNEXPECTED_ARG_COUNT_ERROR(3);\
        \
        GLint location = PyLong_AsLong(args[0]);\
        CHECK_UNEXPECTED_PYTHON_ERROR();\
        \
        GLsizei count = (GLsizei)PyLong_AsSize_t(args[1]);\
        CHECK_UNEXPECTED_PYTHON_ERROR();\
        \
        gl_type *value = (gl_type *)PyLong_AsVoidPtr(args[2]);\
        CHECK_UNEXPECTED_PYTHON_ERROR();\
        \
        glUniform##uniform_name##v(location, count, GL_FALSE, value);\
        CHECK_GL_ERROR();\
        \
        Py_RETURN_NONE;\
    error:\
        return 0;\
    }

SET_ACTIVE_GL_PROGRAM_UNIFORM(float, GLfloat, 1f);
SET_ACTIVE_GL_PROGRAM_UNIFORM(float_2, GLfloat, 2f);
SET_ACTIVE_GL_PROGRAM_UNIFORM(float_3, GLfloat, 3f);
SET_ACTIVE_GL_PROGRAM_UNIFORM(float_4, GLfloat, 4f);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(float_2x2, GLfloat, Matrix2f);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(float_2x3, GLfloat, Matrix2x3f);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(float_2x4, GLfloat, Matrix2x4f);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(float_3x2, GLfloat, Matrix3x2f);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(float_3x3, GLfloat, Matrix3f);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(float_3x4, GLfloat, Matrix3x4f);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(float_4x2, GLfloat, Matrix4x2f);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(float_4x3, GLfloat, Matrix4x3f);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(float_4x4, GLfloat, Matrix4f);
SET_ACTIVE_GL_PROGRAM_UNIFORM(double, GLdouble, 1d);
SET_ACTIVE_GL_PROGRAM_UNIFORM(double_2, GLdouble, 2d);
SET_ACTIVE_GL_PROGRAM_UNIFORM(double_3, GLdouble, 3d);
SET_ACTIVE_GL_PROGRAM_UNIFORM(double_4, GLdouble, 4d);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(double_2x2, GLdouble, Matrix2d);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(double_2x3, GLdouble, Matrix2x3d);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(double_2x4, GLdouble, Matrix2x4d);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(double_3x2, GLdouble, Matrix3x2d);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(double_3x3, GLdouble, Matrix3d);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(double_3x4, GLdouble, Matrix3x4d);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(double_4x2, GLdouble, Matrix4x2d);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(double_4x3, GLdouble, Matrix4x3d);
SET_ACTIVE_GL_PROGRAM_UNIFORM_MATRIX(double_4x4, GLdouble, Matrix4d);
SET_ACTIVE_GL_PROGRAM_UNIFORM(int, GLint, 1i);
SET_ACTIVE_GL_PROGRAM_UNIFORM(int_2, GLint, 2i);
SET_ACTIVE_GL_PROGRAM_UNIFORM(int_3, GLint, 3i);
SET_ACTIVE_GL_PROGRAM_UNIFORM(int_4, GLint, 4i);
SET_ACTIVE_GL_PROGRAM_UNIFORM(unsigned_int, GLuint, 1ui);
SET_ACTIVE_GL_PROGRAM_UNIFORM(unsigned_int_2, GLuint, 2ui);
SET_ACTIVE_GL_PROGRAM_UNIFORM(unsigned_int_3, GLuint, 3ui);
SET_ACTIVE_GL_PROGRAM_UNIFORM(unsigned_int_4, GLuint, 4ui);


static PyObject *
execute_gl_program_index_buffer(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    CHECK_UNEXPECTED_ARG_COUNT_ERROR(5);

    GLenum mode = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLsizei count = PyLong_AsSize_t(args[1]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLsizei offset = PyLong_AsSize_t(args[2]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLenum type = PyLong_AsLong(args[3]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLsizei instances = PyLong_AsSize_t(args[4]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    if (instances > 1)
    {
        glDrawElementsInstanced(mode, count, type, (void *)offset, instances);
        CHECK_GL_ERROR();
    }
    else
    {
        glDrawElements(mode, count, type, (void *)offset);
        CHECK_GL_ERROR();
    }

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
execute_gl_program_indices(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    CHECK_UNEXPECTED_ARG_COUNT_ERROR(4);

    GLenum mode = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLint first = PyLong_AsLong(args[1]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLenum count = PyLong_AsLong(args[2]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLsizei instances = PyLong_AsSize_t(args[3]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    if (instances > 1)
    {
        glDrawArraysInstanced(mode, first, count, instances);
        CHECK_GL_ERROR();
    }
    else
    {
        glDrawArrays(mode, first, count);
        CHECK_GL_ERROR();
    }

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
set_gl_execution_state(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    PyObject *ex = 0;
    struct EMathApi *emath_api = 0;

    CHECK_UNEXPECTED_ARG_COUNT_ERROR(19);

    bool depth_write = (args[0] == Py_True);

    GLenum depth_func = PyLong_AsLong(args[1]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLboolean color_mask_r = (args[2] == Py_True);
    GLboolean color_mask_g = (args[3] == Py_True);
    GLboolean color_mask_b = (args[4] == Py_True);
    GLboolean color_mask_a = (args[5] == Py_True);

    GLenum blend_source = PyLong_AsLong(args[6]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLenum blend_destination = PyLong_AsLong(args[7]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLenum blend_source_alpha = blend_source;
    if (args[8] != Py_None)
    {
        blend_source_alpha = PyLong_AsLong(args[8]);
        CHECK_UNEXPECTED_PYTHON_ERROR();
    }

    GLenum blend_destination_alpha = blend_destination;
    if (args[9] != Py_None)
    {
        blend_destination_alpha = PyLong_AsLong(args[9]);
        CHECK_UNEXPECTED_PYTHON_ERROR();
    }

    GLenum blend_function = PyLong_AsLong(args[10]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    PyObject *py_blend_color = args[11];

    PyObject *py_cull_face = args[12];

    PyObject *py_scissor_position = args[13];
    PyObject *py_scissor_size = args[14];

    bool depth_clamp = (args[15] == Py_True);

    GLenum polygon_rasterization_mode = PyLong_AsLong(args[16]);

    float point_size = PyFloat_AsDouble(args[17]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    float clip_distances = PyLong_AsLong(args[18]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    ModuleState *state = (ModuleState *)PyModule_GetState(module);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    if (!depth_write && depth_func == GL_ALWAYS)
    {
        if (state->depth_test)
        {
            glDisable(GL_DEPTH_TEST);
            CHECK_GL_ERROR();
            state->depth_test = false;
        }
    }
    else
    {
        if (!state->depth_test)
        {
            glEnable(GL_DEPTH_TEST);
            CHECK_GL_ERROR();
            state->depth_test = true;
        }
        if (state->depth_mask != depth_write)
        {
            glDepthMask(depth_write);
            CHECK_GL_ERROR();
            state->depth_mask = depth_write;
        }
        if (state->depth_func != depth_func)
        {
            glDepthFunc(depth_func);
            CHECK_GL_ERROR();
            state->depth_func = depth_func;
        }
    }

    if (state->depth_clamp != depth_clamp)
    {
        if (depth_clamp)
        {
            glEnable(GL_DEPTH_CLAMP);
        }
        else
        {
            glDisable(GL_DEPTH_CLAMP);
        }
        CHECK_GL_ERROR();
        state->depth_clamp = depth_clamp;
    }

    if (
        state->color_mask_r != color_mask_r ||
        state->color_mask_g != color_mask_g ||
        state->color_mask_b != color_mask_b ||
        state->color_mask_a != color_mask_a
    )
    {
        glColorMask(color_mask_r, color_mask_g, color_mask_b, color_mask_a);
        CHECK_GL_ERROR();
        state->color_mask_r = color_mask_r;
        state->color_mask_g = color_mask_g;
        state->color_mask_b = color_mask_b;
        state->color_mask_a = color_mask_a;
    }

    if (
        blend_source == GL_ONE &&
        blend_source_alpha == GL_ONE &&
        blend_destination == GL_ZERO &&
        blend_destination_alpha == GL_ZERO
    )
    {
        if (state->blend)
        {
            glDisable(GL_BLEND);
            CHECK_GL_ERROR();
            state->blend = false;
        }
    }
    else
    {
        if (!state->blend)
        {
            glEnable(GL_BLEND);
            CHECK_GL_ERROR();
            state->blend = true;
        }
        if (
            state->blend_source != blend_source ||
            state->blend_destination != blend_destination ||
            state->blend_source_alpha != blend_source_alpha ||
            state->blend_destination_alpha != blend_destination_alpha
        )
        {
            glBlendFuncSeparate(
                blend_source,
                blend_destination,
                blend_source_alpha,
                blend_destination_alpha
            );
            CHECK_GL_ERROR();
            state->blend_source = blend_source;
            state->blend_destination = blend_destination;
            state->blend_source_alpha = blend_source_alpha;
            state->blend_destination_alpha = blend_destination_alpha;
        }
        if (state->blend_equation != blend_function)
        {
            glBlendEquation(blend_function);
            CHECK_GL_ERROR();
            state->blend_equation = blend_function;
        }

        static const float default_blend_color[] = {1, 1, 1, 1};
        const float *blend_color = default_blend_color;
        if (py_blend_color != Py_None)
        {
            if (!emath_api)
            {
                emath_api = EMathApi_Get();
                CHECK_UNEXPECTED_PYTHON_ERROR();
            }
            blend_color = emath_api->FVector4_GetValuePointer(py_blend_color);
            CHECK_UNEXPECTED_PYTHON_ERROR();
        }
        if (memcmp(state->blend_color, blend_color, sizeof(float) * 4) != 0)
        {
            glBlendColor(blend_color[0], blend_color[1], blend_color[2], blend_color[3]);
            CHECK_GL_ERROR();
            memcpy(state->blend_color, blend_color, sizeof(float) * 4);
        }
    }

    if (py_cull_face == Py_None)
    {
        if (state->cull_face_enabled)
        {
            glDisable(GL_CULL_FACE);
            CHECK_GL_ERROR();
            state->cull_face_enabled = false;
        }
    }
    else
    {
        if (!state->cull_face_enabled)
        {
            glEnable(GL_CULL_FACE);
            CHECK_GL_ERROR();
            state->cull_face_enabled = true;
        }

        GLenum cull_face = PyLong_AsLong(args[12]);
        CHECK_UNEXPECTED_PYTHON_ERROR();

        if (state->cull_face != cull_face)
        {
            glCullFace(cull_face);
            CHECK_GL_ERROR();
            state->cull_face = cull_face;
        }
    }

    if (py_scissor_position == Py_None || py_scissor_size == Py_None)
    {
        if (state->scissor_enabled)
        {
            glDisable(GL_SCISSOR_TEST);
            CHECK_GL_ERROR();
            state->scissor_enabled = false;
        }
    }
    else
    {
        if (!state->scissor_enabled)
        {
            glEnable(GL_SCISSOR_TEST);
            CHECK_GL_ERROR();
            state->scissor_enabled = true;
        }

        if (!emath_api)
        {
            emath_api = EMathApi_Get();
            CHECK_UNEXPECTED_PYTHON_ERROR();
        }

        const int* scissor_position = emath_api->IVector2_GetValuePointer(py_scissor_position);
        CHECK_UNEXPECTED_PYTHON_ERROR();
        const int* scissor_size = emath_api->IVector2_GetValuePointer(py_scissor_size);
        CHECK_UNEXPECTED_PYTHON_ERROR();

        if (
            scissor_position[0] != state->scissor[0] ||
            scissor_position[1] != state->scissor[1] ||
            scissor_size[0] != state->scissor[2] ||
            scissor_size[1] != state->scissor[3]
        )
        {
            glScissor(scissor_position[0], scissor_position[1], scissor_size[0], scissor_size[1]);
            CHECK_GL_ERROR();
            state->scissor[0] = scissor_position[0];
            state->scissor[1] = scissor_position[1];
            state->scissor[2] = scissor_size[2];
            state->scissor[3] = scissor_size[3];
        }
    }

    if (state->polygon_rasterization_mode != polygon_rasterization_mode)
    {
        glPolygonMode(GL_FRONT_AND_BACK, polygon_rasterization_mode);
        CHECK_GL_ERROR();
        state->polygon_rasterization_mode = polygon_rasterization_mode;
    }

    if (state->point_size != point_size)
    {
        glPointSize(point_size);
        CHECK_GL_ERROR();
        state->point_size = point_size;
    }

    if (state->clip_distances != clip_distances)
    {
        if (state->clip_distances < clip_distances)
        {
            for (int i = state->clip_distances; i < clip_distances; i++)
            {
                glEnable(GL_CLIP_DISTANCE0 + i);
                CHECK_GL_ERROR();
            }
        }
        else
        {
            for (int i = clip_distances; i < state->clip_distances; i++)
            {
                glDisable(GL_CLIP_DISTANCE0 + i);
                CHECK_GL_ERROR();
            }
        }
        state->clip_distances = clip_distances;
    }

    if (emath_api){ EMathApi_Release(); }
    Py_RETURN_NONE;
error:
    ex = PyErr_GetRaisedException();
    if (emath_api){ EMathApi_Release(); }
    PyErr_SetRaisedException(ex);
    return 0;
}

static PyObject *
get_gl_version(PyObject *module, PyObject *unused)
{
    const GLubyte *gl_version = glGetString(GL_VERSION);
    CHECK_GL_ERROR();

    return PyUnicode_FromString(gl_version);
error:
    return 0;
}

static PyObject *
set_gl_clip(PyObject *module, PyObject **args, Py_ssize_t nargs)
{
    CHECK_UNEXPECTED_ARG_COUNT_ERROR(2);

    GLenum origin = PyLong_AsLong(args[0]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    GLenum depth = PyLong_AsLong(args[1]);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    ModuleState *state = (ModuleState *)PyModule_GetState(module);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    if (
        !state->is_gl_clip_control_supported &&
        (
            origin != GL_LOWER_LEFT ||
            depth != GL_NEGATIVE_ONE_TO_ONE
        )
    )
    {
        PyErr_SetString(PyExc_RuntimeError, "glClipControl not supported");
        goto error;
    }

    if (state->clip_origin != origin || state->clip_depth != depth)
    {
        glClipControl(origin, depth);
        CHECK_GL_ERROR();

        state->clip_origin = origin;
        state->clip_depth = depth;
    }

    Py_RETURN_NONE;
error:
    return 0;
}

static PyObject *
get_gl_clip(PyObject *module, PyObject* unused)
{
    ModuleState *state = (ModuleState *)PyModule_GetState(module);
    CHECK_UNEXPECTED_PYTHON_ERROR();

    return Py_BuildValue("(ii)", state->clip_origin, state->clip_depth);
error:
    return 0;
}

static PyMethodDef module_PyMethodDef[] = {
    {"reset_module_state", reset_module_state, METH_NOARGS, 0},
    {"debug_gl", debug_gl, METH_O, 0},
    {"activate_gl_vertex_array", activate_gl_vertex_array, METH_O, 0},
    {"create_gl_buffer", create_gl_buffer, METH_NOARGS, 0},
    {"create_gl_vertex_array", create_gl_vertex_array, METH_NOARGS, 0},
    {"create_gl_texture", create_gl_texture, METH_NOARGS, 0},
    {"create_gl_framebuffer", create_gl_framebuffer, METH_NOARGS, 0},
    {"delete_gl_buffer", delete_gl_buffer, METH_O, 0},
    {"delete_gl_vertex_array", delete_gl_vertex_array, METH_O, 0},
    {"delete_gl_texture", delete_gl_texture, METH_O, 0},
    {"delete_gl_framebuffer", delete_gl_framebuffer, METH_O, 0},
    {"delete_gl_renderbuffer", delete_gl_renderbuffer, METH_O, 0},
    {"set_gl_buffer_target", (PyCFunction)set_gl_buffer_target, METH_FASTCALL, 0},
    {"set_gl_buffer_target_data", (PyCFunction)set_gl_buffer_target_data, METH_FASTCALL, 0},
    {"write_gl_buffer_target_data", (PyCFunction)write_gl_buffer_target_data, METH_FASTCALL, 0},
    {"create_gl_buffer_memory_view", (PyCFunction)create_gl_buffer_memory_view, METH_FASTCALL, 0},
    {"release_gl_buffer_memory_view", release_gl_buffer_memory_view, METH_O, 0},
    {"configure_gl_vertex_array_location", (PyCFunction)configure_gl_vertex_array_location, METH_FASTCALL, 0},
    {"set_draw_framebuffer", (PyCFunction)set_draw_framebuffer, METH_FASTCALL, 0},
    {"set_read_framebuffer", set_read_framebuffer, METH_O, 0},
    {"read_color_from_framebuffer", (PyCFunction)read_color_from_framebuffer, METH_FASTCALL, 0},
    {"read_depth_from_framebuffer", read_depth_from_framebuffer, METH_O, 0},
    {"clear_framebuffer", (PyCFunction)clear_framebuffer, METH_FASTCALL, 0},
    {"attach_color_texture_to_gl_read_framebuffer", (PyCFunction)attach_color_texture_to_gl_read_framebuffer, METH_FASTCALL, 0},
    {"attach_depth_texture_to_gl_read_framebuffer", (PyCFunction)attach_depth_texture_to_gl_read_framebuffer, METH_FASTCALL, 0},
    {"attach_depth_renderbuffer_to_gl_read_framebuffer", attach_depth_renderbuffer_to_gl_read_framebuffer, METH_O, 0},
    {"set_texture_locations_on_gl_draw_framebuffer", (PyCFunction)set_texture_locations_on_gl_draw_framebuffer, METH_O, 0},
    {"set_active_gl_texture_unit", set_active_gl_texture_unit, METH_O, 0},
    {"set_gl_texture_target", (PyCFunction)set_gl_texture_target, METH_FASTCALL, 0},
    {"set_gl_texture_target_2d_data", (PyCFunction)set_gl_texture_target_2d_data, METH_FASTCALL, 0},
    {"generate_gl_texture_target_mipmaps", generate_gl_texture_target_mipmaps, METH_O, 0},
    {"set_gl_texture_target_parameters", (PyCFunction)set_gl_texture_target_parameters, METH_FASTCALL, 0},
    {"get_gl_program_uniforms", get_gl_program_uniforms, METH_O, 0},
    {"get_gl_program_attributes", get_gl_program_attributes, METH_O, 0},
    {"create_gl_program", (PyCFunction)create_gl_program, METH_FASTCALL, 0},
    {"delete_gl_program", delete_gl_program, METH_O, 0},
    {"use_gl_program", use_gl_program, METH_O, 0},
    {"set_active_gl_program_uniform_float", (PyCFunction)set_active_gl_program_uniform_float, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_double", (PyCFunction)set_active_gl_program_uniform_double, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_int", (PyCFunction)set_active_gl_program_uniform_int, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_unsigned_int", (PyCFunction)set_active_gl_program_uniform_unsigned_int, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_float_2", (PyCFunction)set_active_gl_program_uniform_float_2, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_double_2", (PyCFunction)set_active_gl_program_uniform_double_2, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_int_2", (PyCFunction)set_active_gl_program_uniform_int_2, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_unsigned_int_2", (PyCFunction)set_active_gl_program_uniform_unsigned_int_2, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_float_3", (PyCFunction)set_active_gl_program_uniform_float_3, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_double_3", (PyCFunction)set_active_gl_program_uniform_double_3, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_int_3", (PyCFunction)set_active_gl_program_uniform_int_3, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_unsigned_int_3", (PyCFunction)set_active_gl_program_uniform_unsigned_int_3, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_float_4", (PyCFunction)set_active_gl_program_uniform_float_4, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_double_4", (PyCFunction)set_active_gl_program_uniform_double_4, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_int_4", (PyCFunction)set_active_gl_program_uniform_int_4, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_unsigned_int_4", (PyCFunction)set_active_gl_program_uniform_unsigned_int_4, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_float_2x2", (PyCFunction)set_active_gl_program_uniform_float_2x2, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_float_2x3", (PyCFunction)set_active_gl_program_uniform_float_2x3, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_float_2x4", (PyCFunction)set_active_gl_program_uniform_float_2x4, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_float_3x2", (PyCFunction)set_active_gl_program_uniform_float_3x2, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_float_3x3", (PyCFunction)set_active_gl_program_uniform_float_3x3, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_float_3x4", (PyCFunction)set_active_gl_program_uniform_float_3x4, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_float_4x2", (PyCFunction)set_active_gl_program_uniform_float_4x2, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_float_4x3", (PyCFunction)set_active_gl_program_uniform_float_4x3, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_float_4x4", (PyCFunction)set_active_gl_program_uniform_float_4x4, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_double_2x2", (PyCFunction)set_active_gl_program_uniform_double_2x2, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_double_2x3", (PyCFunction)set_active_gl_program_uniform_double_2x3, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_double_2x4", (PyCFunction)set_active_gl_program_uniform_double_2x4, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_double_3x2", (PyCFunction)set_active_gl_program_uniform_double_3x2, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_double_3x3", (PyCFunction)set_active_gl_program_uniform_double_3x3, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_double_3x4", (PyCFunction)set_active_gl_program_uniform_double_3x4, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_double_4x2", (PyCFunction)set_active_gl_program_uniform_double_4x2, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_double_4x3", (PyCFunction)set_active_gl_program_uniform_double_4x3, METH_FASTCALL, 0},
    {"set_active_gl_program_uniform_double_4x4", (PyCFunction)set_active_gl_program_uniform_double_4x4, METH_FASTCALL, 0},
    {"execute_gl_program_index_buffer", (PyCFunction)execute_gl_program_index_buffer, METH_FASTCALL, 0},
    {"execute_gl_program_indices", (PyCFunction)execute_gl_program_indices, METH_FASTCALL, 0},
    {"set_gl_execution_state", (PyCFunction)set_gl_execution_state, METH_FASTCALL, 0},
    {"get_gl_version", (PyCFunction)get_gl_version, METH_NOARGS, 0},
    {"set_gl_clip", (PyCFunction)set_gl_clip, METH_FASTCALL, 0},
    {"get_gl_clip", (PyCFunction)get_gl_clip, METH_NOARGS, 0},
    {0},
};

static struct PyModuleDef module_PyModuleDef = {
    PyModuleDef_HEAD_INIT,
    "egraphics._egraphics",
    0,
    sizeof(ModuleState),
    module_PyMethodDef,
};

PyMODINIT_FUNC
PyInit__egraphics()
{
    GLint GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS_VALUE = 0;
    GLint GL_MAX_CLIP_DISTANCES_VALUE = 0;
    bool is_gl_clip_control_supported = false;
    {
        PyObject *eplatform = PyImport_ImportModule("eplatform");
        if (!eplatform){ return 0; }

        PyObject *platform_cls = PyObject_GetAttrString(eplatform, "Platform");
        Py_DECREF(eplatform);
        if (!platform_cls){ return 0; }

        PyObject *platform = PyObject_CallNoArgs(platform_cls);
        Py_DECREF(platform_cls);
        if (!platform){ return 0; }

        PyObject *context = PyObject_CallMethod(platform, "__enter__", "");
        Py_XDECREF(context);
        if (!context)
        {
            Py_DECREF(platform);
            return 0;
        }

        GLenum err = glewInit();
        if (err != GLEW_OK)
        {
            Py_XDECREF(PyObject_CallMethod(platform, "__exit__", ""));
            Py_DECREF(platform);
            PyErr_SetString(PyExc_RuntimeError, glewGetErrorString(err));
            return 0;
        }

        char *gl_clip_control_env = getenv("EGRAPHICS_GL_CLIP_CONTROL");
        if (gl_clip_control_env && strcmp(gl_clip_control_env, "disabled") == 0)
        {
            assert(is_gl_clip_control_supported == false);
        }
        else
        {
            if (GLEW_VERSION_4_5 || glewGetExtension("GL_ARB_clip_control"))
            {
                is_gl_clip_control_supported = true;
            }
            else
            {
                assert(is_gl_clip_control_supported == false);
            }
        }

        glGetIntegerv(
            GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS,
            &GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS_VALUE
        );

        glGetIntegerv(
            GL_MAX_CLIP_DISTANCES,
            &GL_MAX_CLIP_DISTANCES_VALUE
        );

        context = PyObject_CallMethod(platform, "__exit__", "");
        Py_XDECREF(context);
        Py_DECREF(platform);
        if (!context){ return 0; }
    }

    PyObject *module = PyModule_Create(&module_PyModuleDef);
    if (!module){ return 0; }

    if (PyState_AddModule(module, &module_PyModuleDef) == -1)
    {
        Py_DECREF(module);
        return 0;
    }
    {
        PyObject *r = reset_module_state(module, 0);
        if (!r)
        {
            Py_DECREF(module);
            return 0;
        }
        Py_DECREF(r);
    }

    {
        ModuleState *state = (ModuleState *)PyModule_GetState(module);
        if (!state)
        {
            Py_DECREF(module);
            return 0;
        }
        state->is_gl_clip_control_supported = is_gl_clip_control_supported;
    }

#define ADD_ALIAS(name, type)\
    {\
        if (PyModule_AddObjectRef(module, name, (PyObject *)&type) != 0)\
        {\
            return 0;\
        }\
    }

    ADD_ALIAS("GlBlendFactor", PyLong_Type);
    ADD_ALIAS("GlBlendFunction", PyLong_Type);
    ADD_ALIAS("GlBuffer", PyLong_Type);
    ADD_ALIAS("GlBufferTarget", PyLong_Type);
    ADD_ALIAS("GlBufferUsage", PyLong_Type);
    ADD_ALIAS("GlCull", PyLong_Type);
    ADD_ALIAS("GlDepthMode", PyLong_Type);
    ADD_ALIAS("GlFunc", PyLong_Type);
    ADD_ALIAS("GlFramebuffer", PyLong_Type);
    ADD_ALIAS("GlOrigin", PyLong_Type);
    ADD_ALIAS("GlPrimitive", PyLong_Type);
    ADD_ALIAS("GlProgram", PyLong_Type);
    ADD_ALIAS("GlRenderbuffer", PyLong_Type);
    ADD_ALIAS("GlType", PyLong_Type);
    ADD_ALIAS("GlTexture", PyLong_Type);
    ADD_ALIAS("GlTextureComponents", PyLong_Type);
    ADD_ALIAS("GlTextureFilter", PyLong_Type);
    ADD_ALIAS("GlTextureTarget", PyLong_Type);
    ADD_ALIAS("GlTextureWrap", PyLong_Type);
    ADD_ALIAS("GlVertexArray", PyLong_Type);

#define ADD_CONSTANT(n)\
    {\
        PyObject *constant = PyLong_FromLong(n);\
        if (!constant){ return 0; }\
        if (PyModule_AddObject(module, #n, constant) != 0)\
        {\
            Py_DECREF(constant);\
            return 0;\
        }\
    }

    ADD_CONSTANT(GL_ARRAY_BUFFER);
    ADD_CONSTANT(GL_COPY_READ_BUFFER);
    ADD_CONSTANT(GL_ELEMENT_ARRAY_BUFFER);

    ADD_CONSTANT(GL_STREAM_DRAW);
    ADD_CONSTANT(GL_STREAM_READ);
    ADD_CONSTANT(GL_STREAM_COPY);
    ADD_CONSTANT(GL_STATIC_DRAW);
    ADD_CONSTANT(GL_STATIC_READ);
    ADD_CONSTANT(GL_STATIC_COPY);
    ADD_CONSTANT(GL_DYNAMIC_DRAW);
    ADD_CONSTANT(GL_DYNAMIC_READ);
    ADD_CONSTANT(GL_DYNAMIC_COPY);

    ADD_CONSTANT(GL_FLOAT);
    ADD_CONSTANT(GL_DOUBLE);
    ADD_CONSTANT(GL_BYTE);
    ADD_CONSTANT(GL_UNSIGNED_BYTE);
    ADD_CONSTANT(GL_SHORT);
    ADD_CONSTANT(GL_UNSIGNED_SHORT);
    ADD_CONSTANT(GL_INT);
    ADD_CONSTANT(GL_UNSIGNED_INT);
    ADD_CONSTANT(GL_BOOL);
    ADD_CONSTANT(GL_FLOAT_VEC2);
    ADD_CONSTANT(GL_FLOAT_VEC3);
    ADD_CONSTANT(GL_FLOAT_VEC4);
    ADD_CONSTANT(GL_DOUBLE_VEC2);
    ADD_CONSTANT(GL_DOUBLE_VEC3);
    ADD_CONSTANT(GL_DOUBLE_VEC4);
    ADD_CONSTANT(GL_INT_VEC2);
    ADD_CONSTANT(GL_INT_VEC3);
    ADD_CONSTANT(GL_INT_VEC4);
    ADD_CONSTANT(GL_UNSIGNED_INT_VEC2);
    ADD_CONSTANT(GL_UNSIGNED_INT_VEC3);
    ADD_CONSTANT(GL_UNSIGNED_INT_VEC4);
    ADD_CONSTANT(GL_FLOAT_MAT2);
    ADD_CONSTANT(GL_FLOAT_MAT3);
    ADD_CONSTANT(GL_FLOAT_MAT4);
    ADD_CONSTANT(GL_FLOAT_MAT2x3);
    ADD_CONSTANT(GL_FLOAT_MAT2x4);
    ADD_CONSTANT(GL_FLOAT_MAT3x2);
    ADD_CONSTANT(GL_FLOAT_MAT3x4);
    ADD_CONSTANT(GL_FLOAT_MAT4x2);
    ADD_CONSTANT(GL_FLOAT_MAT4x3);
    ADD_CONSTANT(GL_DOUBLE_MAT2);
    ADD_CONSTANT(GL_DOUBLE_MAT3);
    ADD_CONSTANT(GL_DOUBLE_MAT4);
    ADD_CONSTANT(GL_DOUBLE_MAT2x3);
    ADD_CONSTANT(GL_DOUBLE_MAT2x4);
    ADD_CONSTANT(GL_DOUBLE_MAT3x2);
    ADD_CONSTANT(GL_DOUBLE_MAT3x4);
    ADD_CONSTANT(GL_DOUBLE_MAT4x2);
    ADD_CONSTANT(GL_DOUBLE_MAT4x3);
    ADD_CONSTANT(GL_SAMPLER_1D);
    ADD_CONSTANT(GL_INT_SAMPLER_1D);
    ADD_CONSTANT(GL_UNSIGNED_INT_SAMPLER_1D);
    ADD_CONSTANT(GL_SAMPLER_2D);
    ADD_CONSTANT(GL_INT_SAMPLER_2D);
    ADD_CONSTANT(GL_UNSIGNED_INT_SAMPLER_2D);
    ADD_CONSTANT(GL_SAMPLER_3D);
    ADD_CONSTANT(GL_INT_SAMPLER_3D);
    ADD_CONSTANT(GL_UNSIGNED_INT_SAMPLER_3D);
    ADD_CONSTANT(GL_SAMPLER_CUBE);
    ADD_CONSTANT(GL_INT_SAMPLER_CUBE);
    ADD_CONSTANT(GL_UNSIGNED_INT_SAMPLER_CUBE);
    ADD_CONSTANT(GL_SAMPLER_2D_RECT);
    ADD_CONSTANT(GL_INT_SAMPLER_2D_RECT);
    ADD_CONSTANT(GL_UNSIGNED_INT_SAMPLER_2D_RECT);
    ADD_CONSTANT(GL_SAMPLER_1D_ARRAY);
    ADD_CONSTANT(GL_INT_SAMPLER_1D_ARRAY);
    ADD_CONSTANT(GL_UNSIGNED_INT_SAMPLER_1D_ARRAY);
    ADD_CONSTANT(GL_SAMPLER_2D_ARRAY);
    ADD_CONSTANT(GL_INT_SAMPLER_2D_ARRAY);
    ADD_CONSTANT(GL_UNSIGNED_INT_SAMPLER_2D_ARRAY);
    ADD_CONSTANT(GL_SAMPLER_CUBE_MAP_ARRAY);
    ADD_CONSTANT(GL_INT_SAMPLER_CUBE_MAP_ARRAY);
    ADD_CONSTANT(GL_UNSIGNED_INT_SAMPLER_CUBE_MAP_ARRAY);
    ADD_CONSTANT(GL_SAMPLER_BUFFER);
    ADD_CONSTANT(GL_INT_SAMPLER_BUFFER);
    ADD_CONSTANT(GL_UNSIGNED_INT_SAMPLER_BUFFER);
    ADD_CONSTANT(GL_SAMPLER_2D_MULTISAMPLE);
    ADD_CONSTANT(GL_INT_SAMPLER_2D_MULTISAMPLE);
    ADD_CONSTANT(GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE);
    ADD_CONSTANT(GL_SAMPLER_2D_MULTISAMPLE_ARRAY);
    ADD_CONSTANT(GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY);
    ADD_CONSTANT(GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY);
    ADD_CONSTANT(GL_SAMPLER_1D_SHADOW);
    ADD_CONSTANT(GL_SAMPLER_2D_SHADOW);
    ADD_CONSTANT(GL_SAMPLER_CUBE_SHADOW);
    ADD_CONSTANT(GL_SAMPLER_2D_RECT_SHADOW);
    ADD_CONSTANT(GL_SAMPLER_1D_ARRAY_SHADOW);
    ADD_CONSTANT(GL_SAMPLER_2D_ARRAY_SHADOW);

    ADD_CONSTANT(GL_RED);
    ADD_CONSTANT(GL_RG);
    ADD_CONSTANT(GL_RGB);
    ADD_CONSTANT(GL_RGBA);
    ADD_CONSTANT(GL_DEPTH_COMPONENT);
    ADD_CONSTANT(GL_RED_INTEGER);
    ADD_CONSTANT(GL_RG_INTEGER);
    ADD_CONSTANT(GL_RGB_INTEGER);
    ADD_CONSTANT(GL_RGBA_INTEGER);

    ADD_CONSTANT(GL_R8UI);
    ADD_CONSTANT(GL_R8I);
    ADD_CONSTANT(GL_R16UI);
    ADD_CONSTANT(GL_R16I);
    ADD_CONSTANT(GL_R32UI);
    ADD_CONSTANT(GL_R32I);
    ADD_CONSTANT(GL_R32F);

    ADD_CONSTANT(GL_RG8UI);
    ADD_CONSTANT(GL_RG8I);
    ADD_CONSTANT(GL_RG16UI);
    ADD_CONSTANT(GL_RG16I);
    ADD_CONSTANT(GL_RG32UI);
    ADD_CONSTANT(GL_RG32I);
    ADD_CONSTANT(GL_RG32F);

    ADD_CONSTANT(GL_RGB8UI);
    ADD_CONSTANT(GL_RGB8I);
    ADD_CONSTANT(GL_RGB16UI);
    ADD_CONSTANT(GL_RGB16I);
    ADD_CONSTANT(GL_RGB32UI);
    ADD_CONSTANT(GL_RGB32I);
    ADD_CONSTANT(GL_RGB32F);

    ADD_CONSTANT(GL_RGBA8UI);
    ADD_CONSTANT(GL_RGBA8I);
    ADD_CONSTANT(GL_RGBA16UI);
    ADD_CONSTANT(GL_RGBA16I);
    ADD_CONSTANT(GL_RGBA32UI);
    ADD_CONSTANT(GL_RGBA32I);
    ADD_CONSTANT(GL_RGBA32F);

    ADD_CONSTANT(GL_CLAMP_TO_EDGE);
    ADD_CONSTANT(GL_CLAMP_TO_BORDER);
    ADD_CONSTANT(GL_REPEAT);
    ADD_CONSTANT(GL_MIRRORED_REPEAT);

    ADD_CONSTANT(GL_NEAREST);
    ADD_CONSTANT(GL_LINEAR);
    ADD_CONSTANT(GL_NEAREST_MIPMAP_NEAREST);
    ADD_CONSTANT(GL_NEAREST_MIPMAP_LINEAR);
    ADD_CONSTANT(GL_LINEAR_MIPMAP_NEAREST);
    ADD_CONSTANT(GL_LINEAR_MIPMAP_LINEAR);

    ADD_CONSTANT(GL_TEXTURE_2D);

    ADD_CONSTANT(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS_VALUE);
    ADD_CONSTANT(GL_MAX_CLIP_DISTANCES_VALUE);

    ADD_CONSTANT(GL_NEVER);
    ADD_CONSTANT(GL_ALWAYS);
    ADD_CONSTANT(GL_LESS);
    ADD_CONSTANT(GL_LEQUAL);
    ADD_CONSTANT(GL_GREATER);
    ADD_CONSTANT(GL_GEQUAL);
    ADD_CONSTANT(GL_EQUAL);
    ADD_CONSTANT(GL_NOTEQUAL);

    ADD_CONSTANT(GL_ZERO);
    ADD_CONSTANT(GL_ONE);
    ADD_CONSTANT(GL_SRC_COLOR);
    ADD_CONSTANT(GL_ONE_MINUS_SRC_COLOR);
    ADD_CONSTANT(GL_DST_COLOR);
    ADD_CONSTANT(GL_ONE_MINUS_DST_COLOR);
    ADD_CONSTANT(GL_SRC_ALPHA);
    ADD_CONSTANT(GL_ONE_MINUS_SRC_ALPHA);
    ADD_CONSTANT(GL_DST_ALPHA);
    ADD_CONSTANT(GL_ONE_MINUS_DST_ALPHA);
    ADD_CONSTANT(GL_CONSTANT_COLOR);
    ADD_CONSTANT(GL_ONE_MINUS_CONSTANT_COLOR);
    ADD_CONSTANT(GL_CONSTANT_ALPHA);
    ADD_CONSTANT(GL_ONE_MINUS_CONSTANT_ALPHA);

    ADD_CONSTANT(GL_FUNC_ADD);
    ADD_CONSTANT(GL_FUNC_SUBTRACT);
    ADD_CONSTANT(GL_FUNC_REVERSE_SUBTRACT);
    ADD_CONSTANT(GL_MIN);
    ADD_CONSTANT(GL_MAX);

    ADD_CONSTANT(GL_FRONT);
    ADD_CONSTANT(GL_BACK);

    ADD_CONSTANT(GL_POINTS);
    ADD_CONSTANT(GL_LINES);
    ADD_CONSTANT(GL_LINE_STRIP);
    ADD_CONSTANT(GL_LINE_LOOP);
    ADD_CONSTANT(GL_TRIANGLES);
    ADD_CONSTANT(GL_TRIANGLE_STRIP);
    ADD_CONSTANT(GL_TRIANGLE_FAN);
    ADD_CONSTANT(GL_LINE_STRIP_ADJACENCY);
    ADD_CONSTANT(GL_LINES_ADJACENCY);
    ADD_CONSTANT(GL_TRIANGLE_STRIP_ADJACENCY);
    ADD_CONSTANT(GL_TRIANGLES_ADJACENCY);

    ADD_CONSTANT(GL_POINT);
    ADD_CONSTANT(GL_LINE);
    ADD_CONSTANT(GL_FILL);

    ADD_CONSTANT(GL_LOWER_LEFT);
    ADD_CONSTANT(GL_UPPER_LEFT);

    ADD_CONSTANT(GL_NEGATIVE_ONE_TO_ONE);
    ADD_CONSTANT(GL_ZERO_TO_ONE);

    {
        PyObject *eplatform = PyImport_ImportModule("eplatform");
        if (!eplatform){ return 0; }

        PyObject *platform_cls = PyObject_GetAttrString(eplatform, "Platform");
        Py_DECREF(eplatform);
        if (!platform_cls){ return 0; }

        PyObject *py_reset_module_state = PyObject_GetAttrString(module, "reset_module_state");
        if (!py_reset_module_state)
        {
            Py_DECREF(platform_cls);
            return 0;
        }

        PyObject *r = PyObject_CallMethod(
            platform_cls, "register_deactivate_callback", "O", py_reset_module_state
        );
        Py_DECREF(platform_cls);
        Py_DECREF(py_reset_module_state);
        if (!r){ return 0; }
        Py_DECREF(r);
    }

    return module;
}
