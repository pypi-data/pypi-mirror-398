""" This module helps to upload shaders and textures in the GPU.
It also provides a lot of controls to ensure compatibility
of textures, samplers, uniforms types (because OpenGL is pretty
silent about them and incompatibilities lead to mindbending debugging)
It is very basic and tuned to our needs.
"""
import re
import os
import ctypes
import logging
from typing import Union
from pathlib import Path
# from traceback import print_stack

import numpy as np
from OpenGL.GL import (
    GL_MAX_TEXTURE_IMAGE_UNITS,
    glActiveTexture,
    GL_COLOR_ATTACHMENT0,
    GL_COLOR_ATTACHMENT1,
    GL_COLOR_ATTACHMENT2,
    GL_COLOR_ATTACHMENT3,
    GL_COLOR_ATTACHMENT4,
    GL_COLOR_ATTACHMENT5,
    GL_COLOR_ATTACHMENT6,
    GL_COLOR_ATTACHMENT7,
    GL_COLOR_ATTACHMENT8,
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE2,
    GL_TEXTURE3,
    GL_TEXTURE4,
    GL_TEXTURE5,
    GL_TEXTURE6,
    GL_TEXTURE7,
    GL_TEXTURE8,
    GL_TEXTURE9,
    GL_TEXTURE10,
    GL_TEXTURE11,
    GL_VERTEX_SHADER,
    GL_FRAGMENT_SHADER,
    GL_GEOMETRY_SHADER,
    GL_COMPUTE_SHADER,
    GL_MAX_VIEWPORT_DIMS,
    glCreateShader,
    glCompileShader,
    glDeleteShader,
    GL_COMPILE_STATUS,
    glShaderSource,
    glGetShaderiv,
    glGetShaderInfoLog,
    GL_FALSE,
    GL_TRUE,
    glDeleteProgram,
    GL_TEXTURE_RECTANGLE,
    GL_TEXTURE_2D,
    glGenTextures,
    glTexParameteri,
    GL_TEXTURE_MAG_FILTER,
    GL_NEAREST,
    GL_TEXTURE_MIN_FILTER,
    GL_NEAREST,
    GL_TEXTURE_WRAP_S,
    GL_CLAMP_TO_EDGE,
    GL_TEXTURE_WRAP_T,
    GL_CLAMP_TO_EDGE,
    glBindTexture,
    GL_R32F,
    GL_RED,
    GL_FLOAT,
    glTexImage2D,
    GL_RGB32F,
    GL_RGB32UI,
    GL_RGB,
    GL_RGBA,
    GL_RGBA_INTEGER,
    GL_R8UI,
    GL_R32UI,
    GL_R32I,
    GL_RG16UI,
    GL_RGB16UI,
    GL_RG_INTEGER,
    GL_RGB_INTEGER,
    GL_BGRA,
    GL_RGBA8,
    GL_RG32F,
    GL_RG,
    GL_RED_INTEGER,
    GL_UNSIGNED_BYTE,
    GL_UNSIGNED_INT,
    GL_UNSIGNED_SHORT,
    GL_SHORT,
    GL_INT,
    glBindFramebuffer,
    GL_FRAMEBUFFER,
    glGetError,
    GL_NO_ERROR,
    glReadBuffer,
    glReadPixels,
    glGetTexImage,
    glGenFramebuffers,
    glFramebufferTexture2D,
    glDrawBuffers,
    glCheckFramebufferStatus,
    GL_FRAMEBUFFER_COMPLETE,
    GL_NONE,
    glCreateProgram,
    glAttachShader,
    glLinkProgram,
    glGetProgramiv,
    GL_LINK_STATUS,
    glGetUniformLocation,
    glUniform1f,
    glUniform1ui,
    glUniform1i,
    glUniform2f,
    glUniformMatrix4fv,
    glGetIntegerv,
    GL_MAJOR_VERSION,
    GL_MINOR_VERSION,
    glGetString,
    GL_VERSION,
    GL_VENDOR,
    GL_SHADING_LANGUAGE_VERSION,
    glGetInteger,
    glClearTexImage,
    glGenVertexArrays,
    glBindVertexArray,
    glBindBuffer,
    GL_ARRAY_BUFFER,
    glBufferData,
    GL_STATIC_DRAW,
    glGenBuffers,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    glBindVertexArray,
    glPixelStorei,
    GL_UNPACK_ALIGNMENT,
    GL_PACK_ALIGNMENT,
    GL_CURRENT_PROGRAM
)

from OpenGL.GL import (
    GL_DEPTH_ATTACHMENT,
    glGenRenderbuffers,
    glBindRenderbuffer,
    GL_RENDERBUFFER,
    glRenderbufferStorage,
    GL_DEPTH_COMPONENT16,
    glFramebufferRenderbuffer,
    GL_DEPTH_COMPONENT32F,
    GL_READ_FRAMEBUFFER,
    glDeleteTextures,
    GL_FRAMEBUFFER_BINDING,
)

from OpenGL.GL import GL_READ_ONLY, GL_RGBA32F, GL_RGBA32UI, glBindImageTexture

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame

# I use these arrays to avoid dubious computations such as
# "GL_COLOR_ATTACHMENT0 + n".
# FIXME Populate them in function of the GPU's maximum values.

GL_COLOR_ATTACHMENTS = [
    GL_COLOR_ATTACHMENT0,
    GL_COLOR_ATTACHMENT1,
    GL_COLOR_ATTACHMENT2,
    GL_COLOR_ATTACHMENT3,
    GL_COLOR_ATTACHMENT4,
    GL_COLOR_ATTACHMENT5,
    GL_COLOR_ATTACHMENT6,
    GL_COLOR_ATTACHMENT7,
    GL_COLOR_ATTACHMENT8,
]
TEXTURE_UNITS = [
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE2,
    GL_TEXTURE3,
    GL_TEXTURE4,
    GL_TEXTURE5,
    GL_TEXTURE6,
    GL_TEXTURE7,
    GL_TEXTURE8,
    GL_TEXTURE9,
    GL_TEXTURE10,
    GL_TEXTURE11,
]
TEX_SAMPLERS_RE = re.compile(
    r".*uniform\s+(sampler2DRect|usampler2DRect|isampler2DRect|image2D|image2DRect|uimage2DRect)\s+(\w+)\s*;"
)
IMAGE_UNIT_RE = re.compile(r"layout([,]+, binding = [0-9]+)")


def check_gl_error():
    err = glGetError()
    assert err == GL_NO_ERROR, f"GlError = {err}"

def rgb_to_rgba(t):
    assert len(t.shape) == 3
    assert t.shape[2] == 3
    return np.pad(t, ((0, 0), (0, 0), (0, 1)))

def memory_aligned_byte_array(size, value):
    # OpenGL wants 4-byts aligned values
    # One can use:
    # from OpenGL.GL import glPixelStorei, GL_UNPACK_ALIGNMENT
    # glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    # but it's a global setting

    # This code doesn't work...
    logging.debug(f"memory_aligned_byte_array size={size} value={value}")
    assert ctypes.alignment(ctypes.c_uint32) == 4
    assert ctypes.alignment(ctypes.c_uint32) == glGetInteger(
        GL_UNPACK_ALIGNMENT
    ), "We must align on OpenGL alignment"
    v = value << 24 + value << 16 + value << 8 + value
    padded_len = (size + 3) // 4
    img_data = (ctypes.c_uint32 * padded_len)(*([v] * padded_len))
    assert ctypes.addressof(img_data) % 4 == 0
    # I bet the issue is that img_data being mapped only
    # it may be gc'ed before we have a chance to send it
    # to OpenGL...
    img_data2 = (ctypes.c_uint8 * size).from_buffer(img_data)
    logging.debug("memory_aligned_byte_array - done")
    return img_data2

def _get_format_type_from_internal_format(internal_format):
    if internal_format == GL_R32F:
        format, type_ = GL_RED, GL_FLOAT
    elif internal_format == GL_RGB32F:
        format, type_ = GL_RGB, GL_FLOAT
    elif internal_format == GL_RGBA32F:
        format, type_ = GL_RGBA, GL_FLOAT
    elif internal_format == GL_RGBA32UI:
        format, type_ = GL_RGBA_INTEGER, GL_UNSIGNED_INT
    elif internal_format == GL_R32UI:
        format, type_ = GL_RED_INTEGER, GL_UNSIGNED_INT
        # See https://stackoverflow.com/questions/59542891/opengl-integer-texture-raising-gl-invalid-value
        # GL_RED_INTEGER is for unnormalized values (such as uint's)
    elif internal_format == GL_R8UI:
        format, type_ = GL_RED_INTEGER, GL_UNSIGNED_BYTE
    elif internal_format == GL_R32I:
        format, type_ = GL_RED_INTEGER, GL_INT
    elif internal_format == GL_RG16UI:
        # FIXME This doesn't work, but it should...
        # pyopengl sayz : ValueError: Unrecognised image format: GL_RG_INTEGER
        format, type_ = GL_RG_INTEGER, GL_UNSIGNED_SHORT
    elif internal_format == GL_RGB16UI:
        format, type_ = GL_RGB_INTEGER, GL_UNSIGNED_SHORT
    elif internal_format == GL_RGB32UI:
        format, type_ = GL_RGB_INTEGER, GL_UNSIGNED_INT
    else:
        raise Exception(f"Unsupported format {internal_format}")

    return format, type_

def read_texture2(tex_id, desired_format, width:int = None, height:int = None) -> np.ndarray:
    """ Read a texture `tex_id` out of the GPU and returns it as an array.

    The desired_fromat is the one you want to get the texture in. Be aware that
    some formats are not supported by python OpenGL (right now, we know of
    RG16UI).
    """
    format, type_ = _get_format_type_from_internal_format(desired_format)
    glBindTexture(GL_TEXTURE_RECTANGLE, tex_id)

    # No need to know the height/width.
    # npa will be "bytes".
    npa =  glGetTexImage (
        GL_TEXTURE_RECTANGLE,
        0, # mipmap level
        format,       #format, // GL will convert to this format
        type_      #type,   // Using this data type per-pixel
        )

    if format == GL_RED and type_ == GL_FLOAT:
        assert width is None and height is None, "For this specific format, I will figure height/width myself."

        # For some reasons, glGetTexImage returns a transposed array
        # with an additional, useless dimension... I fix that but
        # it seems strange to me.
        s = list(npa.shape)
        s[0], s[1] = s[1], s[0]

        if len(s) == 3 and s[2] == 1:
            a = np.squeeze(npa,axis=2)
            return a.reshape(tuple(s[0:2]))
        else:
            return npa.reshape(tuple(s))

    elif format == GL_RED_INTEGER and type_ == GL_UNSIGNED_BYTE:
        assert width is not None and height is not None, "For this specific format, I can't figure height/width myself."
        assert len(npa) == width*height, f"Dimensions {width}*{height} don't match size: {npa.size} elements"
        return np.ndarray( (height, width) , np.uint8, npa)

    elif format == GL_RGB_INTEGER and type_ in (GL_UNSIGNED_SHORT, GL_UNSIGNED_INT):
        s = list(npa.shape)
        s[0], s[1] = s[1], s[0]

        if len(s) == 4 and s[2] == 1:
            a = np.squeeze(npa,axis=2)
            return a.reshape((s[0], s[1], 3))
        else:
            return npa.reshape(tuple(s))
        return np.ndarray( (height, width, 3) , np.uint16, npa)

    elif format == GL_RGBA and type_ == GL_FLOAT:
        assert width is None and height is None, "For this specific format, I will figure height/width myself."
        s = list(npa.shape)
        assert len(s) == 4 and s[2] == 1
        a = np.squeeze(npa,axis=2)
        return a.reshape( (s[1], s[0], s[3]) )

    elif format == GL_RGBA_INTEGER and type_ == GL_UNSIGNED_INT:
        #assert width is None and height is None, "For this specific format, I will figure height/width myself."
        s = list(npa.shape)
        assert len(s) == 4 and s[2] == 1
        a = np.squeeze(npa,axis=2)
        return a.reshape( (s[1], s[0], s[3]) )

    else:
        raise Exception(f"Unsupported format/type combination: {format} - {type_}")


def read_texture(frame_buffer_id, color_attachment_ndx, width, height, internal_format):
    """
    DEPRECATED Use the version 2 (this one needs framebuffers which is painful to manage).

    Read a rectangle (0,0,width, height) in a texture of size at least
    (width, height).

    color_attachment_ndx:  either an int or a GL_COLOR_ATTACHMENTx

    FIXME Check things up with : https://registry.khronos.org/OpenGL-Refpages/gl4/html/glGetFramebufferAttachmentParameter.xhtml

    FIXME This code is limited as we read from a frame buffer (and not directly
    from a texture id). So one has to provide framebuffer and attachment number
    (which is not quite convenient).

    The internal format of a texture can be found in the dictioneary `textures_formats`
    FIXME again, this is sub optimal. It'd be nicer to resolve a texture ID
    to its corresponding frame buffer/attachment (but it dosen't make too much
    sense since a texture may be attached to several FB and since I sometimes
    hack the fb/textures directly (so I don't maintaint an FB/attach <-> tex. id correspondance)
    """
    assert frame_buffer_id > 0

    format, type_ = _get_format_type_from_internal_format(internal_format)

    # This function exists to codify some of the knowledge I gathered
    # while learning how to download a texture.

    # The fact is that reading a texture from the GPU is much
    # more difficult than reading a frame buffer color attachment.

    # Right now we don't actually read from texture. We read from
    # a color attachment. It means that we can only read it
    # when it has the data we need.

    # Make sure the right buffer is selected
    # GL_FRAMEBUFFER binds framebuffer to both the read and draw framebuffer targets

    # old_framebuffer_id = glGetIntegerv(GL_FRAMEBUFFER_BINDING)
    # glBindFramebuffer(GL_READ_FRAMEBUFFER, old_framebuffer_id)

    glBindFramebuffer(GL_READ_FRAMEBUFFER, frame_buffer_id)
    logging.debug(f"Bound FrameBuffer {frame_buffer_id} for read_texture")
    err = glGetError()
    assert (
        err == GL_NO_ERROR
    ), f"GL Error : {err} (0x{err:x}). glBindFramebuffer(GL_READ_FRAMEBUFFER, {frame_buffer_id}) failed."

    # select a color buffer source for pixels
    if color_attachment_ndx in GL_COLOR_ATTACHMENTS:
        ca = color_attachment_ndx
    else:
        ca = GL_COLOR_ATTACHMENTS[color_attachment_ndx]
    glReadBuffer(ca)
    assert glGetError() == GL_NO_ERROR

    # GL_FLOAT = np.float32
    t = glReadPixels(0, 0, width, height, format, type_)
    assert glGetError() == GL_NO_ERROR

    if format == GL_RGB and type_ == GL_FLOAT:
        return t.reshape(height, width, 3)
    if format == GL_RGBA and type_ == GL_FLOAT:
        return t.reshape(height, width, 4)
    elif format == GL_RED and type_ == GL_FLOAT:
        return t.reshape(height, width)
    elif format == GL_RED_INTEGER and type_ == GL_INT:
        return t.reshape(height, width)
    elif format == GL_RED_INTEGER and type_ == GL_UNSIGNED_INT:
        return t.reshape(height, width)
    elif format == GL_RED_INTEGER and type_ == GL_UNSIGNED_BYTE:
        # For some reason, PyOpenGL doesn't return a numpy array here but
        # `bytes`. So I have to do some extra step to cast the texture into a
        # numpy array myself.
        return np.frombuffer(t, np.uint8).reshape(height, width)
    else:
        raise Exception(
            f"Unsupported format/type combination: {internal_format} - {type_}"
        )

def upload_geometry_to_vao(triangles: np.ndarray, attr_loc: int = 0, normalized: bool = True):
    """
    Geometry is a n rows * [x,y,z] columns matrix representing the vertices,
    each having x,y,z coordinates (NDC coordinates, that is, each in [-1,+1].

    The vertices will be wired to the vertex attribute `attr_loc`

    VAO only stores info about buffers (not transformation, not parameters,
    etc.)

    Returns a Vertex Array Object.
    """

    assert triangles.dtype == np.float32
    vao_id = glGenVertexArrays(1)
    glBindVertexArray(vao_id)

    vertex_buffer_object_id = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer_object_id)
    # OpenGL doc: creates and initializes a buffer object's data store
    glBufferData(GL_ARRAY_BUFFER, triangles.nbytes, triangles.ravel(), GL_STATIC_DRAW)

    # print(f"Size: {triangles.nbytes} bytes")

    # NOTE You don't need to glUseProgram() before; this is just an
    # attribute number.
    # Array access is enabled by binding the VAO in question and calling
    glEnableVertexAttribArray(attr_loc)

    # Tell OpenGL we want the attribute 0 to be enabled and wired to our vertices coordinates.
    # In the vertex shader, we'll have to do something like:
    #    layout(location = 0) in vec4 my_vertex;
    # to connect that "attribute 0" to the shader.

    if normalized:
        gl_norm = GL_TRUE
    else:
        gl_norm = GL_FALSE

    glVertexAttribPointer(attr_loc, 3, GL_FLOAT, gl_norm, 0, None)

    # order important else you clear the buffer's bind located in
    # the vertex array object :-)
    glBindVertexArray(GL_NONE)
    glBindBuffer(GL_ARRAY_BUFFER, GL_NONE)
    return vao_id


def make_quad(xmin, xmax, ymin, ymax):
    # print(f"{xmin:.2f}-{xmax:.2f}: {ymin:.2f}-{ymax:.2f}")
    quad_vertices = [
        (xmax, ymin, 0.5),
        (xmax, ymax, 0.5),
        (xmin, ymax, 0.5),
        (xmin, ymin, 0.5),
    ]

    quad_vertex_triangles = [(0, 1, 2), (0, 2, 3)]

    quad_normals = [(0.000000, 0.000000, 1.000000), (0.000000, 0.000000, 1.000000)]

    quad_texcoords = [(1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]

    quad_texture_triangles = [(0, 1, 2), (0, 2, 3)]

    quad_normal_triangles = [(1, 1, 1), (1, 1, 1)]

    np_quad_vertices = np.array(
        [quad_vertices[index] for indices in quad_vertex_triangles for index in indices]
    )

    np_quad_normals = np.array(
        [quad_normals[index] for indices in quad_normal_triangles for index in indices]
    )

    np_quad_texcoords = np.array(
        [
            quad_texcoords[index]
            for indices in quad_texture_triangles
            for index in indices
        ]
    )

    # Texture coordintaes remain in floats
    np_quad_texcoords_rectangle = np_quad_texcoords
    return np_quad_vertices, np_quad_texcoords_rectangle


def make_unit_quad(texture_width, texture_height):
    return make_quad(-1.0, 1.0, -1.0, 1.0)


def query_gl_caps():
    """ Query the GPU for its capabilities. """
    MAX_GEOMETRY_TEXTURE_IMAGE_UNITS_ARB = (
        35881  # useful for geometry shader limitations; see https://community.khronos.org/t/textures-in-the-geometry-shader/75766/3
    )

    from OpenGL.GL import (
        GL_MAX_COMPUTE_WORK_GROUP_SIZE,
        glGetIntegeri_v,
        glGetInteger,
        GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS,
        GL_MAX_COMPUTE_WORK_GROUP_COUNT,
        GL_MAX_COLOR_ATTACHMENTS,
        GL_MAX_DRAW_BUFFERS,
        GL_MAX_TEXTURE_IMAGE_UNITS,
        GL_MAX_VERTEX_UNIFORM_VECTORS,
        GL_MAX_FRAGMENT_UNIFORM_VECTORS,
        GL_MAX_TEXTURE_SIZE,
        GL_MAX_GEOMETRY_TOTAL_OUTPUT_COMPONENTS,
        GL_MAX_SHADER_STORAGE_BLOCK_SIZE,
        GL_MAX_TEXTURE_BUFFER_SIZE,
    )
    from math import sqrt

    logging.info(
        f"OpenGl version: {glGetIntegerv(GL_MAJOR_VERSION)}.{glGetIntegerv(GL_MINOR_VERSION)}; {glGetString(GL_VERSION)}; {glGetString(GL_VENDOR)} -- GL/SL:{glGetString(GL_SHADING_LANGUAGE_VERSION) }; MAX_GEOMETRY_TEXTURE_IMAGE_UNITS_ARB={glGetInteger(MAX_GEOMETRY_TEXTURE_IMAGE_UNITS_ARB)} max viewport={glGetIntegerv(GL_MAX_VIEWPORT_DIMS)}"
    )
    # Maximum dimension of a texture => maximum size of the computation domain.
    # In cas you wonder, it's pretty difficult (and totally out of the OpenGL spec) to
    # know how much memory there is on the GPU. That's because memory is swapped there
    # too, just like in any OS. And therefore it's also tricky (impossible ?) to know which texture
    # is in GPU RAM or swapped out...
    logging.info("Texture info:")
    logging.info(
        f"GL_MAX_TEXTURE_SIZE = {glGetIntegerv(GL_MAX_TEXTURE_SIZE)}x{glGetIntegerv(GL_MAX_TEXTURE_SIZE)} texels"
    )
    max_buffer_size = glGetInteger(
        GL_MAX_TEXTURE_BUFFER_SIZE
    )  # In texels ! See: https://www.khronos.org/opengl/wiki/Buffer_Texture
    logging.info(
        f"GL_MAX_TEXTURE_BUFFER_SIZE = {max_buffer_size / (1024**2):.1f} mega-texels"
    )
    d = int(sqrt(max_buffer_size))
    logging.info(f"Texture buffer max square size given memory limit.: {d}x{d} texels")

    logging.info("SSBO info:")
    max_ssbo_size = glGetInteger(GL_MAX_SHADER_STORAGE_BLOCK_SIZE)
    logging.info(
        f"GL_MAX_SHADER_STORAGE_BLOCK_SIZE = {max_ssbo_size / (1024**2):.1f} Mbytes"
    )
    d = int(sqrt(max_ssbo_size / 16))
    logging.info(f"SSBO max square size: {d}x{d} RGBAf32 elements")
    # logging.info(f"If one float per buffer SSBO max square size: {d}x{d} RGBAf32 elements")

    logging.info(
        f"GL_MAX_COMPUTE_WORK_GROUP_COUNT = x:{glGetIntegeri_v(GL_MAX_COMPUTE_WORK_GROUP_COUNT,0)[0]} y:{glGetIntegeri_v(GL_MAX_COMPUTE_WORK_GROUP_COUNT,0)[0]}"
    )
    logging.info(
        f"GL_MAX_COMPUTE_WORK_GROUP_SIZE = x:{glGetIntegeri_v(GL_MAX_COMPUTE_WORK_GROUP_SIZE,0)[0]} y:{glGetIntegeri_v(GL_MAX_COMPUTE_WORK_GROUP_SIZE,1)[0]} (== max tile size)"
    )
    logging.info(
        f"GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS = { glGetInteger(GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS)}"
    )

    logging.info(
        f"GL_MAX_COLOR_ATTACHMENTS = { glGetIntegerv(GL_MAX_COLOR_ATTACHMENTS)}"
    )
    logging.info(f"GL_MAX_DRAW_BUFFERS = { glGetIntegerv(GL_MAX_DRAW_BUFFERS)}")
    logging.info(
        f"GL_MAX_TEXTURE_IMAGE_UNITS = { glGetIntegerv(GL_MAX_TEXTURE_IMAGE_UNITS)}"
    )
    logging.info(
        f"GL_MAX_VERTEX_UNIFORM_VECTORS = { glGetIntegerv(GL_MAX_VERTEX_UNIFORM_VECTORS)}"
    )
    logging.info(
        f"GL_MAX_FRAGMENT_UNIFORM_VECTORS = { glGetIntegerv(GL_MAX_FRAGMENT_UNIFORM_VECTORS)}"
    )

    logging.info(
        f"GL_MAX_GEOMETRY_TOTAL_OUTPUT_COMPONENTS = { glGetIntegerv(GL_MAX_GEOMETRY_TOTAL_OUTPUT_COMPONENTS)}"
    )

    # I don't think we use these
    # logging.debug(f"GL_MAX_ARRAY_TEXTURE_LAYERS = { glGetIntegerv(GL_MAX_ARRAY_TEXTURE_LAYERS)}")



class GL_cache_tools():
    """ This class helps to upload shaders and textures in the GPU. """

    samplers_in_shader: dict[tuple[int, str], str]
    shaders_programs: dict[int, int] = dict()  # program id -> shaders
    shaders_names: dict[int, str] = dict()  # shader_id -> string

    def __init__(self) -> None:

        # Recall the type of a sampler associated to a shader.
        # So maps (shader id, sampler's name) to sampler's type name.
        self.samplers_in_shader = dict()

        self.all_textures_sizes = dict()

        # Maps texture id to (context, texture internal format)
        # Texture interanl format are loike: GL_RGB32F...
        self.textures_formats = dict()

        self._set_uniform_cache = dict()

    # def gl_clear_all_caches(self):
    #     self.samplers_in_shader.clear()
    #     self.shaders_programs.clear()
    #     self.shaders_names.clear()
    #     self.all_textures_sizes.clear()
    #     self.textures_formats.clear()
    #     self._set_uniform_cache.clear()

    # def clear_uniform_cache(self):
    #     self._set_uniform_cache.clear()

    def describe_program(self, pid:int):
        return ",".join([self.shaders_names[sid] for sid in self.shaders_programs[pid]])


    def load_shader_from_source(self, shader_type, source: str) -> int:
        assert shader_type in (
            GL_VERTEX_SHADER,
            GL_FRAGMENT_SHADER,
            GL_GEOMETRY_SHADER,
            GL_COMPUTE_SHADER,
        )

        # OpenGL will silently do nothing if you don't activate the extension
        # which is pretty tough to debug.
        # https://www.khronos.org/opengl/wiki/GL_EXT_texture_integer

        gl_ext_texture_integer = (
            "GL_EXT_gpu_shader4" in source
            or "#extension GL_ARB_texture_rectangle" in source
        )
        for s in ["usampler2DRect", "isampler2DRect", "sampler2DRect"]:
            if s in source:
                assert (
                    gl_ext_texture_integer
                ), f"To use {s} you need the extension GL_EXT_gpu_shader4"

        shader_id: int = glCreateShader(shader_type)  # type: ignore

        if shader_id == 0:
            raise Exception("Shader loading failed")
            return 0

        glShaderSource(shader_id, source)
        glCompileShader(shader_id)

        if glGetShaderiv(shader_id, GL_COMPILE_STATUS, None) == GL_FALSE:
            info_log = glGetShaderInfoLog(shader_id)
            logging.error(info_log.decode("ASCII"))
            try:
                glDeleteProgram(shader_id)
            except:
                pass
            finally:
                raise Exception(f"Unable to load shader. {info_log.decode('ASCII')}")

        # Keep track of types.
        for line in source.split("\n"):
            m = TEX_SAMPLERS_RE.match(line)
            if m:
                type_name = m.groups()[0]
                sampler_name = m.groups()[1]
                logging.debug(
                    f"Load shader: (shader:{shader_id}, sampler name:{sampler_name}) -> type={type_name}"
                )
                self.samplers_in_shader[(shader_id, sampler_name)] = type_name

        self.shaders_names[shader_id] = "from source"
        return shader_id



    def track_texture_size(self, tex_id:int, img_data, w:int, h:int, format) -> int:
        if isinstance(img_data, np.ndarray):
            s = img_data.nbytes
        else:
            s = ctypes.sizeof(img_data)

        logging.debug(
            f"Uploaded {w}x{h} texels, {s} bytes ({s/(1024**2):.1f} MB) to GPU, format={format}"
        )
        self.all_textures_sizes[tex_id] = s
        return s

    def total_textures_size(self) -> int:
        """ Return the total size of all textures in bytes. """
        s = []
        for tex_id, size in self.all_textures_sizes.items():
            s.append( size )
        return sum(s)


    def drop_textures(self, texture_ids: Union[list[int], int]):
        """ Drop one or more textures. Expect texture id's.
        """
        assert texture_ids is not None
        if not isinstance(texture_ids, list):
            texture_ids = [texture_ids]

        # In some rare occurences, we reuse twice the same
        # texture.
        texture_ids = list(set(texture_ids))
        for tid in texture_ids:
            assert tid in self.textures_formats, f"Never seen that texture `{tid}` before"
            del self.textures_formats[tid]

        assert glGetError() == GL_NONE
        #print(f"deleteing {texture_ids}")
        glDeleteTextures(texture_ids)


    def upload_np_array_to_gpu(self,
                               context,
                               format,
                               img_data: np.ndarray,
                               texture_id: Union[int, None] = None
                               ) -> int:
        """The goal of this function is to standardize textures
        configuration and upload to GPU. We trade generality for
        ease of use.

        If you pass in a texture_id, then the texture will be updated
        instead of created.

        Returns the texture OpenGL id.
        """

        assert context in (GL_TEXTURE_RECTANGLE, GL_TEXTURE_2D)
        assert isinstance(img_data, np.ndarray)

        # From : https://registry.khronos.org/OpenGL-Refpages/gl4/html/glTexImage2D.xhtml

        # "The first element corresponds to the lower left corner of the texture
        # image. Subsequent elements progress left-to-right through the remaining
        # texels in the lowest row of the texture image, and then in successively
        # higher rows of the texture image. The final element corresponds to the
        # upper right corner of the texture image. "

        assert img_data.flags["C"], "I believe pyOpenGL prefer C-contiguous data array"

        if texture_id is None:
            new_texture = True
            texture_id = glGenTextures(1)  # Name one new texture
            # if texture_id == 10:
            #     print("**********************************************")
            #     print_stack()
            #assert texture_id not in textures_formats, f"I just generated a texture ID that already exists in my database ({textures_formats[texture_id]}) ??? Maybe you need to clear the DB first ?"
            self.textures_formats[texture_id] = (context, format)
        else:
            assert (
                texture_id in self.textures_formats
            ), "Can't update a texture I have never seen before"
            assert self.textures_formats[texture_id] == (
                context,
                format,
            ), "You're changing the nature of the texture"
            new_texture = False

        glBindTexture(
            context, texture_id
        )  # Bind the texture to context target (kind of assocaiting it to a type)

        # Prevent texture interpolation with samplers
        glTexParameteri(context, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(context, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        # GL_CLAMP_TO_EDGE: Clamps the coordinates between 0 and 1. The result is
        # that higher coordinates become clamped to the edge, resulting in a
        # stretched edge pattern.
        glTexParameteri(context, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(context, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        if format == GL_R32F:
            assert len(img_data.shape) == 2, "We only accept 2D textures for GL_R32F format"
            assert img_data.dtype in (
                float,
                np.float32,
            ), f"We only accept floats, you gave {img_data.dtype}"
            h, w = img_data.shape
            # internal format; format; type.
            glTexImage2D(context, 0, GL_R32F, w, h, 0, GL_RED, GL_FLOAT, img_data)
        elif format == GL_RGB32F:
            assert (
                len(img_data.shape) == 3 and img_data.shape[2] == 3
            ), "We only accept 2D RGB textures, shape=(h,w,3) for GL_RGB32F format"
            assert img_data.dtype in (float, np.float32)
            h, w, _ = img_data.shape
            glTexImage2D(context, 0, GL_RGB32F, w, h, 0, GL_RGB, GL_FLOAT, img_data)
        elif format == GL_RG16UI:
            assert (
                len(img_data.shape) == 3 and img_data.shape[2] == 2
            ), "We only accept 2D RG textures, shape=(h,w,2) for GL_RG16UI format"
            assert img_data.dtype == np.uint16
            h, w, _ = img_data.shape
            # FIXME Why do I need to suffix GL_RG with INTEGER (I don't do it elsewhere
            # but here it is mandatory)
            glTexImage2D(context, 0, GL_RG16UI, w, h, 0, GL_RG_INTEGER, GL_UNSIGNED_SHORT, img_data)
        elif format == GL_RGB16UI:
            assert (
                len(img_data.shape) == 3 and img_data.shape[2] == 3
            ), f"We only accept 2D RGB textures, shape=(h,w,3) for GL_RGB16UI format. You gave: {img_data.shape}"
            assert img_data.dtype == np.uint16, "Expecting unsigned short"
            h, w, _ = img_data.shape
            glTexImage2D(context, 0, GL_RGB16UI, w, h, 0, GL_RGB_INTEGER, GL_UNSIGNED_SHORT, img_data)
        elif format == GL_RGB32UI:
            assert (
                len(img_data.shape) == 3 and img_data.shape[2] == 3
            ), f"We only accept 2D RGB textures, shape=(h,w,3) for GL_RGB16UI format. You gave: {img_data.shape}"
            assert img_data.dtype == np.uint32, f"Expecting unsigned int, got {img_data.dtype}"
            h, w, _ = img_data.shape
            glTexImage2D(context, 0, GL_RGB32UI, w, h, 0, GL_RGB_INTEGER, GL_UNSIGNED_INT, img_data)
        elif format == GL_RGBA32F:
            assert (
                len(img_data.shape) == 3 and img_data.shape[2] == 4
            ), "We only accept 2D RGBA textures, shape=(h,w,3) for GL_RGBA32F format"
            assert img_data.dtype in (float, np.float32)
            h, w, _ = img_data.shape
            glTexImage2D(context, 0, GL_RGBA32F, w, h, 0, GL_RGBA, GL_FLOAT, img_data)
        elif format == GL_RGBA32UI:
            assert (
                len(img_data.shape) == 3 and img_data.shape[2] == 4
            ), f"We only accept 2D RGBA textures, shape=(h,w,3) for GL_RGBA32UI format, you gave {img_data.shape}"
            assert img_data.dtype in (np.uint32, )
            h, w, _ = img_data.shape
            glTexImage2D(context, 0, GL_RGBA32UI, w, h, 0, GL_RGBA_INTEGER, GL_UNSIGNED_INT, img_data)
        elif format == GL_R32UI:
            assert (
                len(img_data.shape) == 2
            ), "We only accept 2D textures for GL_R32UI format"
            assert (
                img_data.dtype == np.uint32
            ), f"We only accept uint32, you gave {img_data.dtype}"
            h, w = img_data.shape
            # See https://stackoverflow.com/questions/59542891/opengl-integer-texture-raising-gl-invalid-value
            # GL_RED_INTEGER is for unnormalized values (such as uint's)
            glTexImage2D(
                context, 0, GL_R32UI, w, h, 0, GL_RED_INTEGER, GL_UNSIGNED_INT, img_data
            )
        elif format == GL_R8UI:
            assert (
                len(img_data.shape) == 2
            ), "We only accept 2D textures for GL_R32UI format"
            assert (
                img_data.dtype == np.uint8
            ), f"We only accept uint8, you gave {img_data.dtype}"
            h, w = img_data.shape
            glTexImage2D(
                context, 0, GL_R8UI, w, h, 0, GL_RED_INTEGER, GL_UNSIGNED_INT, img_data
            )
        elif format == GL_R32I:
            assert len(img_data.shape) == 2, "We only accept 2D textures for GL_R32I format"
            assert (
                img_data.dtype == np.int32
            ), f"We only accept int32, you gave {img_data.dtype}"
            h, w = img_data.shape
            glTexImage2D(context, 0, GL_R32I, w, h, 0, GL_RED_INTEGER, GL_INT, img_data)
        else:
            raise Exception(f"Unsupported format {format}")

        check_gl_error()
        self.track_texture_size(texture_id, img_data, w, h, format)
        return texture_id


    def upload_blank_texture_to_gpu(self, w: int, h: int, context, format=GL_R32F, value=0.0):
        """
        Make and upload a blank (or one color) texture to the GPU.

        `format`: some texture format. The way it is done here means that
        we will derive the texture format in the GPU as well as the texture
        format of the "value" data.
        `context`: either GL_TEXTURE_RECTANGLE, GL_TEXTURE_2D
        `value`: will be set on each components of the texels.
        """
        # FIXME Wire this to upload_np_array_to_gpu(...)

        assert context in (GL_TEXTURE_RECTANGLE, GL_TEXTURE_2D)

        texture_id = glGenTextures(1)  # Name one new texture
        # if texture_id == 10:
        #     print("**********************************************")
        #     print_stack()
        #assert texture_id not in textures_formats, "A brand new texture can't already exist!"
        self.textures_formats[texture_id] = (context, format)
        glBindTexture(
            context, texture_id
        )  # Bind the texture to context target (kind of assocaiting it to a type)
        glTexParameteri(context, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(context, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(context, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(context, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        #logging.debug(f"Uploading {w}x{h} constant pixels to GPU. Format= {format}")

        if format in (GL_R32UI, GL_R8UI, GL_RGBA8) and value == 0.0:
            # Quality of life when leaving value to its default.
            value = 0

        if format == GL_R32F:
            img_data = (ctypes.c_float * (w * h * 1))(*([value] * (w * h * 1)))
            glTexImage2D(context, 0, GL_R32F, w, h, 0, GL_RED, GL_FLOAT, img_data)
        elif format == GL_RG32F:
            img_data = (ctypes.c_float * (w * h * 2))(*([value] * (w * h * 2)))
            glTexImage2D(context, 0, GL_RG32F, w, h, 0, GL_RG, GL_FLOAT, img_data)
        elif format == GL_RGB32F:
            if type(value) == list:
                value: list
                assert len(value) == 3, "I expect three components for R,G,B"
                img_data = (ctypes.c_float * (w * h * 3))(*(value * (w * h)))
            else:
                # img_data = (ctypes.c_float * (w * h * 3))(*([value] * (w*h*3)))
                img_data = np.full((w * h * 3,), value, dtype=np.float32)
            glTexImage2D(context, 0, GL_RGB32F, w, h, 0, GL_RGB, GL_FLOAT, img_data)
        elif format == GL_RGBA32F:
            if type(value) == list:
                value: list
                assert len(value) == 4, "I expect three components for R,G,B"
                img_data = (ctypes.c_float * (w * h * 4))(*(value * (w * h)))
            else:
                # img_data = (ctypes.c_float * (w * h * 4))(*([value] * (w*h*4)))
                img_data = np.full((w * h * 4,), value, dtype=np.float32)

            glTexImage2D(context, 0, GL_RGBA32F, w, h, 0, GL_RGBA, GL_FLOAT, img_data)
        elif format == GL_RGBA8:
            if type(value) == list:
                value: list
                assert len(value) == 4, "I expect three components for R,G,B"
                img_data = (ctypes.c_uint8 * (w * h * 4))(*(value * (w * h)))
            else:
                assert type(value) in (
                    np.uint8,
                    int,
                ), f"I expect unsigned 8 bits integer, you gave {type(value)}"
                assert 0 <= value <= 255
                img_data = (ctypes.c_uint8 * (w * h * 4))(*([value] * (w * h * 4)))
            # glTexImage2D( ctx, "base internal formats" (see Table2 and Table1 of https://registry.khronos.org/OpenGL-Refpages/gl4/html/glTexImage2D.xhtml )==format of the texture in the GPU memory,
            # w,h,0, format=format of the source pixels data, typz=data type of the source pixels  data)
            glTexImage2D(context, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        elif format == GL_R32UI:
            assert type(value) == int and value >= 0
            img_data = (ctypes.c_uint32 * (w * h * 1))(*([value] * (w * h * 1)))
            # internal format; format (of pixel data); (data) type (of pixel data)
            glTexImage2D(
                context, 0, GL_R32UI, w, h, 0, GL_RED_INTEGER, GL_UNSIGNED_INT, img_data
            )
        elif format == GL_R8UI:
            logging.debug("Creataing data")
            assert type(value) in (
                np.uint8,
                int,
            ), f"I expect unsigned 8 bits integer, you gave {type(value)}"
            assert 0 <= value <= 255

            # I tried to allocate memory in an 4-bytes aligned way
            # but it doesn't work => I use glPixelStore
            img_data = np.full((h * w,), value, dtype=np.uint8)
            logging.debug("Uploading data")
            pixels_align_old = glGetInteger(GL_UNPACK_ALIGNMENT)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexImage2D(
                context, 0, GL_R8UI, w, h, 0, GL_RED_INTEGER, GL_UNSIGNED_BYTE, img_data
            )
            glPixelStorei(GL_UNPACK_ALIGNMENT, pixels_align_old)  # Restore old value
            logging.debug("Uploaded data")

            # size = w*h
            # logging.debug(f"memory_aligned_byte_array size={size} value={value}")
            # assert ctypes.alignment(ctypes.c_uint32) == 4
            # assert ctypes.alignment(ctypes.c_uint32) == glGetInteger(GL_UNPACK_ALIGNMENT), "We must align on OpenGL alignment"
            # v = value << 24 + value << 16 + value << 8 + value
            # padded_len = (size + 3) // 4
            # img_data = (ctypes.c_uint32 * padded_len)(*([v] * padded_len))
            # assert ctypes.addressof(img_data) % 4 == 0
            # img_data2 = (ctypes.c_uint8 * size).from_buffer(img_data)
            # logging.debug("memory_aligned_byte_array - done")
            # img_data2 = np.frombuffer(img_data2, dtype=np.uint8)
            # glTexImage2D(context, 0, GL_R8UI, w, h, 0, GL_RED_INTEGER, GL_UNSIGNED_BYTE, img_data2)

        elif format == GL_R32I:
            assert type(value) == int
            # img_data = (ctypes.c_int32 * (w * h * 1))(*([value] * (w*h*1)))
            img_data = np.full((h * w,), value, dtype=np.int32)
            # internal format; format (of pixel data); (data) type (of pixel data)
            # glTexImage2D(context, 0, GL_R8UI, w, h, 0, GL_RED_INTEGER, GL_UNSIGNED_BYTE, img_data)
            glTexImage2D(context, 0, GL_R32I, w, h, 0, GL_RED_INTEGER, GL_INT, img_data)
        else:
            raise Exception(f"Unsupported texture format : {format}")

        check_gl_error()
        self.track_texture_size(texture_id, img_data, w, h, format)

        return texture_id


    def clear_texture(self, texture_id:int):
        assert (
            texture_id in self.textures_formats
        ), "I can't find your texture_id (textures_formats) in the textures I have created..."
        context_, internal_format = self.textures_formats[texture_id]

        if internal_format == GL_R32F:
            format, type_ = GL_RED, GL_FLOAT
        elif internal_format == GL_RGB32F:
            format, type_ = GL_RGB, GL_FLOAT
        elif internal_format == GL_RGBA32F:
            format, type_ = GL_RGBA, GL_FLOAT
        elif internal_format == GL_R32UI:
            format, type_ = GL_RED_INTEGER, GL_UNSIGNED_INT
            # See https://stackoverflow.com/questions/59542891/opengl-integer-texture-raising-gl-invalid-value
            # GL_RED_INTEGER is for unnormalized values (such as uint's)
        elif internal_format == GL_R8UI:
            format, type_ = GL_RED_INTEGER, GL_UNSIGNED_BYTE
        elif internal_format == GL_R32I:
            format, type_ = GL_RED_INTEGER, GL_INT
        else:
            raise Exception(f"Unsupported format {internal_format}")

        if type_ == GL_FLOAT:
            ct = ctypes.c_float
        elif type_ == GL_INT:
            ct = ctypes.c_int32
        elif type_ == GL_UNSIGNED_BYTE:
            ct = ctypes.c_uint8
        else:
            raise Exception("Unsupported type : {}", type_)

        if format in (GL_RED, GL_RED_INTEGER):
            size = 1
        elif format == GL_RGB:
            size = 3
        elif format == GL_RGBA:
            size = 4
        else:
            raise Exception("Unsupported format : {}", format)

        img_data = (ct * size)(*([0] * size))
        glClearTexImage(texture_id, 0, format, type_, img_data)



    def load_shader_from_file(self, fpath: Path, log_path: Path = None, shader_type=None):
        """ Load a shader from a file - can contain %%includes.
        The extension of the file determines the type of shader :
            - .vs : vertex shader
            - .frs : fragment shader
            - .gs : geometry shader
            - .comp : compute shader (.cs is deprecated)
        """
        shader_dir = fpath.parent
        with open(fpath, "r") as source:

            if shader_type is None:
                suffix = fpath.suffix
                if suffix == ".vs":
                    shader_type = GL_VERTEX_SHADER
                elif suffix == ".frs":
                    shader_type = GL_FRAGMENT_SHADER
                elif suffix == ".gs":
                    shader_type = GL_GEOMETRY_SHADER
                elif suffix in (".comp", ".cs"):
                    if suffix == ".cs":
                        logging.warning(".cs extension is deprecated")

                    shader_type = GL_COMPUTE_SHADER
                else:
                    raise Exception(f"Unrecognized shader extension {suffix}")
            else:
                assert shader_type in [GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, GL_GEOMETRY_SHADER, GL_COMPUTE_SHADER], f"Unknown shader type {shader_type}"

            try:
                # print(f"Loading {fpath} as {shader_type}")
                INCLUDE_MARK = "%%include"
                source_lines = []
                for line in source.readlines():
                    if line.strip().startswith(INCLUDE_MARK):
                        fn = shader_dir / line.replace(INCLUDE_MARK, "").strip()
                        logging.debug(f"Including {fn} in {fpath}")
                        source_lines.extend([f"\n// Included from {fn}\n\n"])
                        with open(fn) as include:
                            source_lines.extend(include.readlines())
                    else:
                        source_lines.append(line)

                full_text = "".join(source_lines)

                logging.debug(f"Loaded {fpath}")
                if log_path:
                    logged_path = f"{log_path / fpath.name}_log"
                    with open(logged_path, "w") as logged:
                        logged.write(full_text)
                else:
                    logged_path = None

                shader_id = self.load_shader_from_source(shader_type, full_text)
                assert shader_dir not in self.shaders_names, "The shader is new, so it must be unknown to us"
                self.shaders_names[shader_id] = fpath.name
                return shader_id
            except Exception as ex:
                if logged_path is not None:
                    lm = f"Log file at {logged_path}"
                else:
                    lm = ""
                raise Exception(f"Error while loading {fpath}. {lm}") from ex


    def create_frame_buffer_for_computation(self,
        destination_texture:Union[int,list[int]],
        out_to_fragdata:bool=False,
        depth_buffer:bool=False,
        texture_target=GL_TEXTURE_RECTANGLE,
    ):
        """
        destination_texture: a texture or a list of textures. If list of textures,
        one frame buffer will be attached to each texture, via
        COLOR_ATTACHMENT0,1,2,... (in list order)

        out_to_fragdata: if the FB will be used as output of a shader that issues
        FragData instead of colors. In that case, we create link buffers so that
        will receive these FragData.

        depth_buffer: attach a depth buffer to the framebuffer. None or pass in the
        dimensions of the buffer. # FIXME don't pass the dimensions, guess them from
        the texture.

        """

        # texture is where the result of the render will be
        # the stencil and depth information will be stored in a
        # RenderBuffer (which we don't make available here)

        fb = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, fb)

        # Wire the destination texture(s)
        if type(destination_texture) == list:
            assert len(destination_texture) <= len(
                GL_COLOR_ATTACHMENTS
            ), "The GL_COLOR_ATTACHMENTS predefined values are not numerous enough !"

            for i in range(len(destination_texture)):
                assert (
                    destination_texture[i] is not None
                ), f"The {i+1}th texture in the list of textures is None ?!"
                assert (
                    destination_texture[i] in self.textures_formats
                ), f"The {i+1}th texture in the list of textures has not format defined. Was it correctly initialized ?"
                # We read from the cached texture formats.
                context, format = self.textures_formats[destination_texture[i]]
                # glFramebufferTexture2D: attach a texture image to a framebuffer object
                glFramebufferTexture2D(
                    GL_FRAMEBUFFER,
                    GL_COLOR_ATTACHMENTS[i],
                    context,
                    destination_texture[i],
                    0,
                )

            if out_to_fragdata:
                # FIXME CRITICAL Is this really needed ? When I read:
                # https://registry.khronos.org/OpenGL-Refpages/gl4/html/glDrawBuffers.xhtml
                # I get the impression that glDrawBuffers must be called when a shader
                # is in context (as glDrawBuffers will wire the shader to some buffer).
                # Therefore doing this here, without some shader context, is useless...

                # Redirect FragData out's of fragment shader to the destination texture
                # (they're connected via GL_COLOR_ATTACHMENTx)
                # FragData[0] corresponds to GL_COLOR_ATTACHMENT0 which was set to destination_textures[0] above.
                # So the buffer we create here is quite small, it's just an array of pointers.

                # FIXME Replace the complicated ctypes code below with the simpler one right below.
                # The complex expression just pass texture id's to glDrawBuffers
                # under one or more GL_COLOR_ATTACHMENT0,1,2,...
                # glDrawBuffers — Specifies a list of color buffers to be drawn into
                # drawBuffers = gl_ca[0:len(destination_texture)]
                drawBuffers = (ctypes.c_int32 * len(destination_texture))(
                    *[int(ca) for ca in GL_COLOR_ATTACHMENTS[0 : len(destination_texture)]]
                )
                # print(drawBuffers)
                # print([int(ca) for ca in gl_ca[0:len(destination_texture)]])
                glDrawBuffers(
                    drawBuffers
                )  # pyOpenGl figures the count based on drawBuffers array length
        else:
            assert destination_texture is not None, "Null texture id ???"
            assert type(destination_texture) in (
                np.uintc,
                int,
            ), f"I want an integer texture id (you gave '{type(destination_texture)}')"
            glFramebufferTexture2D(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, texture_target, destination_texture, 0
            )

        if not out_to_fragdata:
            glDrawBuffers(GL_NONE)
        # glReadBuffer(GL_NONE) # FIXME Maybe useless

        if depth_buffer:
            if True:
                # see http://www.songho.ca/opengl/gl_fbo.html
                rb_id = glGenRenderbuffers(1)  # create one render buffer
                glBindRenderbuffer(GL_RENDERBUFFER, rb_id)
                glRenderbufferStorage(
                    GL_RENDERBUFFER, GL_DEPTH_COMPONENT32F, depth_buffer[0], depth_buffer[1]
                )
                glBindRenderbuffer(GL_RENDERBUFFER, 0)  # unbind
                # Attach to currently bound F.B.
                glFramebufferRenderbuffer(
                    GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rb_id
                )
            else:
                pass
            assert glGetError() == GL_NO_ERROR

        assert glGetError() == GL_NO_ERROR
        # GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT=_C('GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT',0x8CD6)
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE, f"Framebuffer is not complete, it is 0x{glCheckFramebufferStatus(GL_FRAMEBUFFER):04X}"
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        return fb


    def load_program(self,
                     vertex_shader:int=None,
                     fragment_shader:int=None,
                     geometry_shader:int=None,
                     compute_shader:int=None
    ):
        assert compute_shader is not None or vertex_shader is not None
        # returns the program

        program = glCreateProgram()
        if program == 0:
            return 0

        # At this point, shaders are compiled but not linked to each other

        shaders = []
        if compute_shader is None:
            glAttachShader(program, vertex_shader)
            shaders.append(vertex_shader)
            if geometry_shader is not None:
                glAttachShader(program, geometry_shader)
                shaders.append(geometry_shader)
            if fragment_shader is not None:
                glAttachShader(program, fragment_shader)
                shaders.append(fragment_shader)
        else:
            # Compute shader
            glAttachShader(program, compute_shader)
            shaders.append(compute_shader)

        glLinkProgram(program)

        if glGetProgramiv(program, GL_LINK_STATUS, None) == GL_FALSE:
            glDeleteProgram(program)
            raise Exception("Failed to create a rpogram")

        assert glGetError() == GL_NO_ERROR
        self.shaders_programs[program] = shaders

        # Mark all shaders for removal once their corresponding programs will be
        # gone (read the documentation of glDeleteShader).
        # So be sure to do this *after* the shaders have been attached to their
        # program.
        for shader in shaders:
            glDeleteShader(shader)

        return program



    def set_uniform(self, program:int, name:str, value):
        # We cache the uniform settings because calls to `glUniform`
        # are super expensive (like *unbelievably* *expensive*)
        k = f"{program},{name}"
        if k in self._set_uniform_cache:
            current = self._set_uniform_cache[k]
            if isinstance(value, np.ndarray):
                if np.allclose(value, current):
                    return
            elif current == value:
                return
        self._set_uniform_cache[k] = value

        try:
            location = glGetUniformLocation(program, name)
        except Exception as ex:
            raise Exception(f"Can't get uniform location for '{name}'") from ex

        if not location >= 0:
            logging.error(
                f"Can't find '{name}' uniform in *compiled* GL/SL program {program} (with shaders {[self.shaders_names[sid] for sid in  self.shaders_programs[program]]}). Maybe you mixed uniforms and texture samplers ? Remember that shaders' compiler may remove uniforms that are not actually used in the GLSL code !"
            )
            return

        # OpenGl: This (glGetUniformLocation) function returns -1 if name does not
        # correspond to an active uniform variable in program, if name starts with
        # the reserved prefix "gl_", or if name is associated with an atomic counter
        # or a named uniform block.
        assert (
            location >= 0
        ), f"Can't find '{name}' uniform in *compiled* GL/SL program. Maybe you mixed uniforms and texture samplers ? Remember that shaders' compiler may remove uniforms that are not actually used in the GLSL code !"

        if type(value) == float:
            glUniform1f(location, value)
        elif type(value) == bool:
            glUniform1ui(location, int(value))
        elif type(value) in (int, np.intc):
            try:
                #logging.debug(f"glUniform1i({name} as {location}, {value})")
                glUniform1i(location, value)
            except Exception as ex:
                logging.error(
                    f"Error while setting integer uniform '{name}' at location '{location}' to value '{value}' (of type {type(value)})"
                )
                raise ex
        elif type(value) == np.uintc:  # A 32 bit (uint32 is "at least 32 bits")
            try:
                glUniform1ui(location, value)
            except Exception as ex:
                logging.error(
                    f"Error while setting integer uniform '{name}' at location '{location}' to value '{value}' (of type {type(value)})"
                )
                raise ex
        elif (
            type(value) in (tuple, list)
            and len(value) == 2
            and type(value[0]) == float
            and type(value[1]) == float
        ):
            glUniform2f(location, value[0], value[1])
        elif isinstance(value, np.ndarray) and value.shape == (4, 4):
            # Attention! OpenGL matrices are column-major
            # At this point of the code we don't make any hypothesis
            # about the ordering of data in the numpy array => the caller
            # must ensure the OpenGL order (column major).

            # glUniformMatrix4fv( loc, count, transpose, value)
            glUniformMatrix4fv(location, 1, GL_FALSE, value)  # GL_FALSE= do not transpose
        else:
            if type(value) in (tuple, list):
                raise Exception(f"Error while setting uniform '{name}' at location '{location}' to value '{value}': Unsupported type: {type(value)} or types of parts are not supported.")
            else:
                raise Exception(f"Error while setting uniform '{name}' at location '{location}' to value '{value}': Unsupported type: {type(value)}")
        assert glGetError() == GL_NO_ERROR


    def set_texture(self, program:int, unif_name:str, tex_index:int, tex_unit):
        glActiveTexture(TEXTURE_UNITS[tex_unit])
        glBindTexture(GL_TEXTURE_RECTANGLE, tex_index)
        self.set_uniform(program, unif_name, tex_unit)


    def wire_program(self, program: int, uniforms=dict(), textures=dict()):
        """
        Binds texture to (read) sampler.
        Sets uniforms.
        This doesn't touch the framebuffer bindings.

        `program` : OpenGL id of the program
        `uniforms`: map uniform names (str) to their values
        `textures`: map texture sampler names to their texture id. Instead of texture_id you can
        pass a tuple (texture_id, access) where access is either: GL_READ_ONLY, GL_WRITE_ONLY, or GL_READ_WRITE.
        See https://www.khronos.org/opengl/wiki/Image_Load_Store
        """

        # logging.debug(f"Wiring program {textures}")
        assert glGetIntegerv(GL_CURRENT_PROGRAM) == program, "Seems like you program is no glUseProgram'ed"

        # Wire uniforms
        for unif_name, unif_value in uniforms.items():
            self.set_uniform(program, unif_name, unif_value)

        # Wire the texture samplers to texture units
        # We arbitrarily set the texture unit
        texture_unit = texture_image_unit = 0
        for sampler_name, tex_index in textures.items():
            if type(tex_index) == tuple:
                # We wire an image texture, with a image unit (instead of a texture
                # with a texture unit)
                tex_index, access = tex_index
            else:
                access = GL_READ_ONLY

            assert type(tex_index) in (
                int,
                np.uintc,
            ), f"Texture ID must be integer (sampler='{sampler_name}'). You gave {type(tex_index)}."

            # Check that textures of a given type are compatible with their
            # sampler's type (for example a *u*sampler will make sense
            # only on a uint texture).
            # This is done because OpenGL is completely silent on these
            # mesimatches and it makes debugging very difficult.

            # Check all shaders associated with the `program`
            sampler_found = False
            context = None
            for shader in self.shaders_programs[program]:
                k = (shader, sampler_name)
                if k in self.samplers_in_shader:
                    image_texture = None
                    sampler_type = self.samplers_in_shader[k]
                    context, format = self.textures_formats[tex_index]
                    msg = f"Wiring sampler '{sampler_name}' of type '{sampler_type}' to shader {shader} in program {program} to a texture of context {context} seems wrong. You gave {format} which looks incompatible/unsupported."
                    if sampler_type == "usampler2DRect":
                        assert (
                            context == GL_TEXTURE_RECTANGLE
                        ), f"For sampler '{sampler_type}', OpenGL expects a GL_TEXTURE_RECTANGLE context"
                        assert format in (GL_R32UI, GL_R8UI, GL_RGBA8, GL_RG16UI, GL_RGB16UI, GL_RGB32UI), msg
                        image_texture = False
                    elif sampler_type == "sampler2DRect":
                        assert (
                            context == GL_TEXTURE_RECTANGLE
                        ), f"For sampler '{sampler_type}', OpenGL expects a GL_TEXTURE_RECTANGLE context"
                        assert format in (GL_R32F, GL_RGB32F, GL_RGBA32F), msg
                        image_texture = False
                    elif sampler_type == "isampler2DRect":
                        assert (
                            context == GL_TEXTURE_RECTANGLE
                        ), f"For sampler '{sampler_type}', OpenGL expects a GL_TEXTURE_RECTANGLE context"
                        assert format in (GL_R32I,), msg
                        image_texture = False
                    elif sampler_type == "image2D":
                        # This is introduced to support compute shaders
                        assert (
                            context == GL_TEXTURE_2D
                        ), f"For sampler '{sampler_type}', OpenGL expects a GL_TEXTURE_2D context"
                        assert format in (GL_RGBA32F,), msg
                        image_texture = True
                    elif sampler_type == "image2DRect":
                        # This is introduced to support compute shaders
                        assert (
                            context == GL_TEXTURE_RECTANGLE
                        ), f"For sampler '{sampler_type}', OpenGL expects a GL_TEXTURE_RECTANGLE context"
                        assert format in (GL_RGBA32F, GL_RGB32F, GL_R32F, GL_RG32F), msg
                        image_texture = True
                    elif sampler_type == "uimage2DRect":
                        # This is introduced to support compute shaders
                        assert (
                            context == GL_TEXTURE_RECTANGLE
                        ), f"For sampler '{sampler_type}', OpenGL expects a GL_TEXTURE_RECTANGLE context"
                        assert format in (GL_R8UI, GL_RGBA32UI, GL_RG16UI), msg
                        image_texture = True
                    else:
                        raise Exception(f"Unsupported sampler type: {sampler_type}")
                    sampler_found = True
                    logging.debug(
                        f"Ready to wire {['Texture','ImageTexture'][image_texture]} number {tex_index} on sampler '{sampler_name}' of type '{sampler_type}' to shader {self.shaders_names[shader]} ({shader}) in program {program} to a texture of context {context}. Format is {format}"
                    )
                    break

            assert (
                sampler_found
            ), f"Wiring program: Unknown sampler '{sampler_name}' in program {program} ({self.describe_program(program)})"

            # How to bind texture and images is described here :
            # https://www.khronos.org/opengl/wiki/Texture#GLSL_binding

            assert image_texture is not None
            if not image_texture:
                # glActiveTexture selects which texture unit subsequent texture state
                # calls will affect.
                glActiveTexture(TEXTURE_UNITS[texture_unit])

                # Bind texture to active texture unit
                glBindTexture(context, tex_index)

                logging.debug(f"glActiveTexture(texture_unit={TEXTURE_UNITS[texture_unit]}); glBindTexture({context}, texture_name={tex_index})")

                # Tell the shader to use the texture unit `tex_unit` which we just
                # have wired a texture to.
                self.set_uniform(program, sampler_name, texture_unit)
                texture_unit += 1

            elif image_texture:
                # https://stackoverflow.com/questions/37136813/what-is-the-difference-between-glbindimagetexture-and-glbindtexture
                # Right now this is used for compute shaders.
                # From: https://learnopengl.com/Guest-Articles/2022/Compute-Shaders/Introduction
                # Here the glBindImageTexture function is used to bind a specific level of a texture to an image unit.

                # So one can have a single texture associated to one texture unit
                # and several images linked to that texture unit, each associated to
                # one image unit. (there's one level of indirection when compared to
                # the usual texture/texture unit connections).

                # Now to simplify things, since we don't (so far) use sveral
                # layers of the same texture in different image unit, we'll
                # make a STRONG assumption: if one chooses an image unit "i"
                # then we automatically binds it to the texture unit "i".

                # If we have three texture we want access to, we'll
                # need three image units. Each of them will be wired
                # to the corresponding texture unit.

                # Given the current texture, binds a single image of it to
                # the shader program.
                logging.debug(
                    f"glBindImageTexture( texunit= {texture_image_unit}, tex_id={tex_index}, level=0, layered=GL_FALSE, layer=0, {access}, {format})"
                )
                if format == GL_RGB32F:
                    logging.error(
                        "ImageTexture can't be GL_RGB32F. See OpengGL documentation."
                    )

                # Bind the texture tex_index to the texture unit texture_image_unit.
                glBindImageTexture(
                    texture_image_unit, tex_index, 0, GL_FALSE, 0, access, format
                )


                # It's not done in the OpenGl tutorial here : https://learnopengl.com/Guest-Articles/2022/Compute-Shaders/Introduction
                # But according to the official doc here : https://www.khronos.org/opengl/wiki/Texture#GLSL_binding
                # it should be done too...
                self.set_uniform(program, sampler_name, texture_image_unit)
                #texture_image_unit += 1
                texture_image_unit += 1

            mtu = glGetInteger(GL_MAX_TEXTURE_IMAGE_UNITS)
            # FIXME I'm absolutely NOT sure of this test.
            # First question are texture_image_unit and textre_unit the same thing ???
            if texture_unit + texture_image_unit > mtu - 1:
                raise Exception(f"Not enough TEXTURE_UNITS in gl (max is {mtu})")


def init_gl(width, height):
    """ Initialize the OpenGL context and create a window with pygame """
    pygame.init()

    display_nfo = pygame.display.Info()
    res = pygame.display.set_mode((width, height), pygame.DOUBLEBUF | pygame.OPENGL)
    return res


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    init_gl(256, 256)
    query_gl_caps()
