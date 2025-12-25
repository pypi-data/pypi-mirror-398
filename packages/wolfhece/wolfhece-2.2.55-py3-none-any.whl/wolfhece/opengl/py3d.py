"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wx
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pathlib import Path
import logging
from enum import Enum

import numpy as np
from glm import lookAt, perspective, mat4, vec3, vec4, rotate, cross, dot, ortho, mat4x4, transpose, inverse, normalize, translate

from ..PyTranslate import _
from ..textpillow import Font_Priority, Text_Image, Text_Infos
from ..wolf_texture import Text_Image_Texture

def print_program_resource_names(program, verbose=False):
    """ Print the active resources in the program """

    glUseProgram(program)

    # Get the number of active resources
    num_active_resources = glGetProgramiv(program, GL_ACTIVE_ATTRIBUTES)
    num_active_uniforms = glGetProgramiv(program, GL_ACTIVE_UNIFORMS)

    if verbose:
        print(f"Number of active resources: {num_active_resources}")
        print(f"Number of active uniforms: {num_active_uniforms}")

        logging.info(f"Number of active resources: {num_active_resources}")
        logging.info(f"Number of active uniforms: {num_active_uniforms}")

    ret={}
    ret['attributes'] = []
    ret['uniforms'] = []

    # Iterate through each resource and print its name
    for i in range(num_active_resources):
        resource_name = glGetProgramResourceName(program, GL_PROGRAM_INPUT, i, 256)  # 256 is the maximum name length

        ressource = ''
        for i in range(resource_name[0]):
            ressource += chr(resource_name[1][i])

        if verbose:
            print(f"Resource {i}: {ressource}")
            logging.info(f"Resource {i}: {ressource}")

        ret['attributes'].append(ressource)


    for i in range(num_active_uniforms):
        resource_name = glGetProgramResourceName(program, GL_UNIFORM, i, 256)

        ressource = ''
        for i in range(resource_name[0]):
            ressource += chr(resource_name[1][i])

        if verbose:
            print(f"Uniform {i}: {ressource}")
            logging.info(f"Uniform {i}: {ressource}")

        ret['uniforms'].append(ressource)

    return ret


class TypeOfView(Enum):
    """ Type of view """
    PERSPECTIVE = 0
    ORTHOGRAPHIC = 1
    ORTHOGRAPHIC_2D = 2
class Cache_WolfArray_plot3D():
    """
    Cache for the WolfArray_plot3D class

    A cache is created for each canvas. The cache is responsible for the OpenGL resources associated to context.
    """

    def __init__(self,
                 parent:"WolfArray_plot3D",
                 context:glcanvas.GLContext,
                 canvas:"CanvasOGL",
                 idx:int = 0) -> None:

        self.parent = parent
        self.idx = idx

        self._vao = None
        self._vbo = None
        self._colorID = None
        self._textureID = None
        self._program = None
        self._sunintensity = 1.
        self._sunposition = vec3(0., 0., 1000.)

        self._mvpLoc = None
        self._dxloc = None
        self._dyloc = None
        self._origxloc = None
        self._origyloc = None
        self._widthloc = None
        self._heightloc = None
        self._zscaleloc = None
        self._ztextureloc = None
        self._palloc = None
        self._colorValuesLoc = None
        self._sunpositionLoc = None
        self._sunintensityLoc = None
        self._palettesizeLoc = None
        self.idxloc = None

        self.canvas = canvas
        self.context = context

        self._ztexture = None
        self._color_palette = None
        self._color_values = np.zeros(256, dtype=np.float32)

        self.params = None

    @property
    def sunposition(self):

        return self._sunposition

    @sunposition.setter
    def sunposition(self, sunposition:vec3):

        self._sunposition = sunposition

        glUseProgram(self._program)
        glUniform3f(self._sunpositionLoc, sunposition.x, sunposition.y, sunposition.z)
        glUseProgram(0)

    @property
    def sunintensity(self):
        return self._sunintensity

    @sunintensity.setter
    def sunintensity(self, sunintensity:float):
        self._sunintensity = sunintensity

        glUseProgram(self._program)
        glUniform1f(self._sunintensityLoc, sunintensity)
        glUseProgram(0)

    def initialize_color_palette(self):
        """ Initialize the color palette """

        if self._color_palette is None:
            self._color_palette = np.array([0., 0., 0., 1., 1., 1.], dtype=np.float32)

        if self._color_values is None:
            self._color_values[:2] = np.array([self._ztexture.min(), self._ztexture.max()], dtype=np.float32)

        self._colorID = glGenTextures(1)
        glBindTexture(GL_TEXTURE_1D, self._colorID)

        glTexImage1D(GL_TEXTURE_1D, 0, GL_RGB, len(self._color_palette)//3 , 0, GL_RGB, GL_FLOAT, self._color_palette.data)

        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)


    def __del__(self):
        """ release the resources """
        if self._vao is not None:
            glDeleteVertexArrays(1, [self._vao])
        if self._vbo is not None:
            glDeleteBuffers(1, [self._vbo])
        if self._colorID is not None:
            glDeleteTextures(1, [self._colorID])
        if self._textureID is not None:
            glDeleteTextures(1, [self._textureID])
        if self._program is not None:
            glDeleteProgram(self._program)
        if self._framebuffer is not None:
            glDeleteFramebuffers(1, [self._framebuffer])
        if self._textureout is not None:
            glDeleteTextures(1, [self._textureout])

    def  init_GL(self, quad_centers:np.ndarray, ztexture:np.ndarray):

        self.init_shader()
        self.loc_uniforms()
        self.update_ztexture(ztexture)
        self.initialize_color_palette()
        self.set_uniforms()

        self.update_quads(quad_centers)

    def init_shader(self):
        # Compile The Program and shaders

        _vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        with open(Path(__file__).parent.parent / "shaders/simple_vertex_shader_wo_mvp.glsl") as file:
            VERTEX_SHADER = file.read()
        glShaderSource(_vertex_shader, VERTEX_SHADER)
        glCompileShader(_vertex_shader)

        if glGetShaderiv(_vertex_shader, GL_COMPILE_STATUS, None) == GL_FALSE:
            info_log = glGetShaderInfoLog(_vertex_shader)
            print(info_log)
            glDeleteProgram(_vertex_shader)
            raise Exception("Can't compile shader on GPU")

        _fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        with open(Path(__file__).parent.parent / "shaders/quad_frag_shader.glsl") as file:
            FRAGMENT_SHADER = file.read()
        glShaderSource(_fragment_shader, FRAGMENT_SHADER)
        glCompileShader(_fragment_shader)

        if glGetShaderiv(_fragment_shader, GL_COMPILE_STATUS, None) == GL_FALSE:
            info_log = glGetShaderInfoLog(_fragment_shader)
            print(info_log)
            glDeleteProgram(_fragment_shader)
            raise Exception("Can't compile shader on GPU")

        _geometry_shader = glCreateShader(GL_GEOMETRY_SHADER)
        with open(Path(__file__).parent.parent / "shaders/quad_geom_shader.glsl") as file:
            GEOMETRY_SHADER = file.read()
        glShaderSource(_geometry_shader, GEOMETRY_SHADER)
        glCompileShader(_geometry_shader)

        if glGetShaderiv(_geometry_shader, GL_COMPILE_STATUS, None) == GL_FALSE:
            info_log = glGetShaderInfoLog(_geometry_shader)
            print(info_log)
            glDeleteProgram(_geometry_shader)
            raise Exception("Can't compile shader on GPU")

        self._program = glCreateProgram()
        glAttachShader(self._program, _vertex_shader)
        glAttachShader(self._program, _fragment_shader)
        glAttachShader(self._program, _geometry_shader)
        glLinkProgram(self._program)

        # Check if the program is compiled
        if glGetProgramiv(self._program, GL_LINK_STATUS) == GL_FALSE:
            info_log = glGetProgramInfoLog(self._program)
            print(info_log)
            raise Exception("Can't link shader program")

        glDeleteShader(_vertex_shader)
        glDeleteShader(_fragment_shader)
        glDeleteShader(_geometry_shader)

        self.params = print_program_resource_names (self._program)

    def loc_uniforms(self, which_prog = 0):
        """ Initialize the uniforms """

        program = self._program

        glUseProgram(program)
        self._mvpLoc = glGetUniformLocation(program, "mvp")

        self._dxloc = glGetUniformLocation(program, "dx")
        self._dyloc = glGetUniformLocation(program, "dy")

        self._widthloc    = glGetUniformLocation(program, "width")
        self._heightloc   = glGetUniformLocation(program, "height")

        self._origxloc    = glGetUniformLocation(program, "origx")
        self._origyloc    = glGetUniformLocation(program, "origy")
        self._zscaleloc   = glGetUniformLocation(program, "zScale")
        self._ztextureloc = glGetUniformLocation(program, "zText")

        self._palloc = glGetUniformLocation(program, "colorPalette")
        self._colorValuesLoc = glGetUniformLocation(program, "colorValues")

        self._sunpositionLoc = glGetUniformLocation(program, "sunPosition")
        self._sunintensityLoc = glGetUniformLocation(program, "sunIntensity")

        self._palettesizeLoc = glGetUniformLocation(program, "paletteSize")

        self._idxloc = glGetUniformLocation(program, "idx")

        glUseProgram(0)

    def set_uniforms(self, which_prog = 0):
        """ Set the uniforms """

        if which_prog == 0:
            glUseProgram(self._program)
        else:
            glUseProgram(self._program_pos)

        glUniform1f(self._dxloc, self.parent.dx)
        glUniform1f(self._dyloc, self.parent.dy)

        glUniform1i(self._idxloc, self.idx)

        glUniform1f(self._widthloc, self.canvas.width)
        glUniform1f(self._heightloc, self.canvas.height)

        glUniform1f(self._origxloc, self.parent.origx)
        glUniform1f(self._origyloc, self.parent.origy)
        glUniform1f(self._zscaleloc, self.parent.zscale)

        glBindTexture(GL_TEXTURE_RECTANGLE, self._textureID)

        if self._ztexture.flags.f_contiguous:
            w, h = self._ztexture.shape
        else:
            h, w = self._ztexture.shape

        glTexImage2D(GL_TEXTURE_RECTANGLE, 0, GL_R32F, w, h, 0, GL_RED, GL_FLOAT, self._ztexture.data)

        glBindTexture(GL_TEXTURE_RECTANGLE, 0)

        glBindTexture(GL_TEXTURE_1D, self._colorID)
        glTexImage1D(GL_TEXTURE_1D, 0, GL_RGB, len(self._color_palette)//3 , 0, GL_RGB, GL_FLOAT, self._color_palette.data)
        glBindTexture(GL_TEXTURE_1D, 0)

        glUniform1i(self._palettesizeLoc, len(self._color_palette)//3)

        glUniform1fv(self._colorValuesLoc, 256, self._color_values)

        glUniform1i(self._palloc, 1)

        glUseProgram(0)

    def update_quads(self, data:np.ndarray):
        """ Update the buffer with new data """

        if self._vbo is not None:
            glDeleteBuffers(1, [self._vbo])
            self._vbo = None

        if self._vao is not None:
            glDeleteVertexArrays(1, [self._vao])
            self._vao = None

        if self._vao is None:
            self._vao = glGenVertexArrays(1)
        if self._vbo is None:
            self._vbo = glGenBuffers(1)

        self.quad_centers = data

        glBindVertexArray(self._vao)
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def update_mvp(self, mvp:mat4x4):
        """ Update the model view projection matrix """
        glUseProgram(self._program)
        glUniformMatrix4fv(self._mvpLoc, 1, GL_FALSE, mvp)

        glUniform1f(self._widthloc, self.canvas.width)
        glUniform1f(self._heightloc, self.canvas.height)

        glUseProgram(0)

    def update_ztexture(self, ztexture:np.ndarray):
        """ Update the ztexture """

        self._ztexture = ztexture

        if self._textureID is not None:
            glDeleteTextures(1, [self._textureID])

        self._textureID = glGenTextures(1)

        glUseProgram(self._program)
        glBindTexture(GL_TEXTURE_RECTANGLE, self._textureID)
        glTexImage2D(GL_TEXTURE_RECTANGLE, 0, GL_R32F, ztexture.shape[1], ztexture.shape[0], 0, GL_RED, GL_FLOAT, ztexture)
        glBindTexture(GL_TEXTURE_RECTANGLE, 0)
        glUseProgram(0)

    def update_palette(self, color_palette:np.ndarray, color_values:np.ndarray):
        """ Update the color palette """

        self._color_palette = color_palette

        self._color_values[:len(color_values)] = color_values

        glUseProgram(self._program)

        if self._colorID is not None:
            glDeleteTextures(1, [self._colorID])

        self.initialize_color_palette()

        glUniform1fv(self._colorValuesLoc, 256, color_values)
        glUniform1i(self._palettesizeLoc, len(self._color_palette)//3)

        glUseProgram(0)

    def Draw(self):

        glUseProgram(self._program)

        glBindVertexArray(self._vao)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_RECTANGLE, self._textureID)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_1D, self._colorID)

        glDrawArrays(GL_POINTS, 0, len(self.quad_centers)//2)

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        glBindTexture(GL_TEXTURE_RECTANGLE, 0)
        glBindTexture(GL_TEXTURE_1D, 0)

        glUseProgram(0)

class WolfArray_plot3D():
    """
    Class to plot data in 3D viewer

    reference for texture 2D : https://registry.khronos.org/OpenGL-Refpages/gl4/html/glTexImage2D.xhtml

    OPENGL

    The first element corresponds to the lower left corner of the texture image.
    Subsequent elements progress left-to-right through the remaining texels in the lowest row of the texture image,
     and then in successively higher rows of the texture image.
    The final element corresponds to the upper right corner of the texture image.

       void glTexImage2D(	GLenum target,
           GLint level,
           GLint internalformat,
           GLsizei width,
           GLsizei height,
           GLint border,
           GLenum format,
           GLenum type,
           const void * data);

    NUMPY

    shape[0] is the number of rows and shape[1] is the number of columns.

    The "data" buffer is row-major order or column-major order, depending on the value of the order parameter.
       - row-major order : C order
       - column-major order : 'F' order (Fortran)

    So, in row-major order :
       - OpenGL Texture width = shape[1]
       - OpenGL Texture height = shape[0]
    and in column-major order :
       - OpenGL Texture width = shape[0]
       - OpenGL Texture height = shape[1]

    ++ IMPORTANT

    We assume that if data is row-major order, the indexing [i,j] is (y, x) and if data is column-major order, the indexing is (x, y)

    Example :
      - array[m,n] in row-major order is the element at the coordinate    (n * dx + dx/2. + origx, m * dy + dy/2. + origy)
      - array[m,n] in column-major order is the element at the coordinate (m * dx + dx/2. + origx, n * dy + dy/2. + origy)

    So:
       - the data buffer is the same as it is contiguous in memory. We ** don't need to transpose ** the data buffer.
       - Transposition is done by changing the indexing convention.
       - "texture" calls in shaders is the same for both row-major and column-major order.

    -- IMPORTANT
    """

    def __init__(self,
                 quad_centers:np.ndarray,
                 dx:float = 1., dy:float = 1.,
                 origx:float = 0., origy:float = 0.,
                 zscale:float = 0.0,
                 ztexture:np.ndarray = None,
                 color_palette:np.ndarray = None,
                 color_values:np.ndarray = None) -> None:
        """ Constructor

        :param quad_centers: The centers of the quads in WORLD space
        :param dx: The width of the quads in WORLD space
        :param dy: The height of the quads in WORLD space
        :param origx: The x origin of the mesh in WORLD space
        :param origy: The y origin of the mesh in WORLD space
        :param zscale: The z scale applied to the ztexture
        :param ztexture: The value used as Z coordinate in shaders in WORLD space
        :param color_palette: The color palette used to plot the quads
        :param color_values: The color values used to plot the quads


        Position
        --------
        Indexing is done in the shader with the following formula :
        i = (x - origx) / dx
        j = (y - origy) / dy

        If the data is row-major order, the indexing is (y, x) and if the data is column-major order, the indexing is (x, y).
        The data buffer in memory must be the same.
        The user must take care of the indexing convention and is responsible for the correct indexing.

        Palette
        -------
        The palette is a 1D texture. The color is interpolated between the colors in the palette.
        color_palette = [r1, g1, b1, r2, g2, b2, r3, g3, b3, ...] - 3 floats per color RGB (float32)
        color_values = [v1, v2, v3, ...] - 1 float per value (float32) - max 256 values


        """

        assert color_palette.dtype == np.float32, "Color palette must be np.float32"
        assert color_values.dtype == np.float32, "Color values must be np.float32"
        assert ztexture.dtype == np.float32, "Z texture must be np.float32"
        assert quad_centers.dtype == np.float32, "Quad centers must be np.float32"


        self.parents:dict["CanvasOGL", Cache_WolfArray_plot3D] = None
        self.active_parent:"CanvasOGL" = None

        self.dx = dx
        self.dy = dy
        self.origx = origx
        self.origy = origy
        self.zscale = zscale
        self.ztexture = ztexture
        self.quad_centers = quad_centers

        # palette is shared between all the caches
        self.color_palette = color_palette
        self.color_values = color_values

    @property
    def boundingbox(self):
        """ Return the bounding box of the quads """
        quads = self.quad_centers.reshape(-1, 2)
        return quads[:,0].min(), quads[:,0].max(), quads[:,1].min(), quads[:,1].max()

    @property
    def cache(self) -> Cache_WolfArray_plot3D:
        if self.active_parent is None:
            return None

        return self.parents[self.active_parent]

    def __del__(self):
        """ Destructor """
        for parent in self.parents:
            self.remove_parent(parent)

    def remove_parent(self, parent:"CanvasOGL"):
        """ Remove the parent from the object """
        if parent in self.parents:
            del self.parents[parent]

    def add_parent(self, parent:"CanvasOGL", idx:int=0):
        """ Add the parent to the object """
        if self.parents is None:
            self.parents = {}

        cache = self.parents[parent] = Cache_WolfArray_plot3D(self, parent.context, parent, idx)
        self.active_parent = parent

        cache.init_GL(self.quad_centers, self.ztexture)

        cache.update_palette(self.color_palette, self.color_values)
        cache.update_mvp(parent.mvp)
        cache.sunposition = parent.sunposition
        cache.sunintensity = parent.sunintensity


    def update_mvp(self, mvp:mat4x4):
        """ Update the model view projection matrix """
        if self.cache is None:
            return

        self.cache.update_mvp(mvp)

    def update_ztexture(self, ztexture:np.ndarray):
        """ Update the ztexture """

        for parent in self.parents:
            self.parents[parent].update_ztexture(ztexture)

    def update_palette(self, color_palette:np.ndarray, color_values:np.ndarray):
        """ Update the color palette """

        for parent in self.parents:
            self.parents[parent].update_palette(color_palette, color_values)

    @property
    def sunposition(self):

        if self.cache is None:
            return None

        return self.cache.sunposition

    @sunposition.setter
    def sunposition(self, sunposition:vec3):

        if self.cache is None:
            return

        self.cache.sunposition = sunposition

    @property
    def sunintensity(self):
        if self.cache is None:
            return None

        return self.cache.sunintensity

    @sunintensity.setter
    def sunintensity(self, sunintensity:float):
        if self.cache is None:
            return

        self.cache.sunintensity = sunintensity

    def Draw(self):

        if self.cache is None:
            return

        self.cache.Draw()

class CanvasOGL(glcanvas.GLCanvas):

    def __init__(self, parent):
        super(CanvasOGL, self).__init__(parent, -1, size=(640, 480))

        self.parent = parent

        self.arrays:dict[str, WolfArray_plot3D] = {}

        self.background = (0.1, 0.1, 0.1, 1)

        self.init = False

        self.persp_or_ortho = TypeOfView.PERSPECTIVE

        self.context = glcanvas.GLContext(self)
        self.SetCurrent(self.context)

        self.width, self.height = self.GetClientSize()
        self.ratio_woverh = self.width / self.height

        self.width_view = 40
        self.height_view = self.width_view / self.ratio_woverh

        self.eye = vec3(0., 0., 20.)
        self.center = vec3(0., 0., 0.)
        self.up = vec3(0., 1., 0.)

        self.left_view = self.center.x - self.width_view / 2.
        self.right_view = self.center.x + self.width_view / 2.
        self.bottom_view = self.center.y - self.height_view / 2.
        self.top_view = self.center.y + self.height_view / 2.

        self.fov = 45
        self.near = 0.1
        self.far = 10000

        self._sunintensity = 1.
        self._sunaltitude = 10000.
        self._sun_x = 10000.
        self._sun_y = 10000.
        self._sun_idx = 0
        # self._sunposition = vec3(1000., 1000., self._sunaltitude)

        self.grid = False
        self.drawposition = False

        self.x_plane = False
        self.y_plane = False
        self.z_plane = False
        self.xy_plane = False
        self.yz_plane = False
        self.xz_plane = False

        self.update_view()

        self.translation_speed = .1
        self.rotation_speed = 0.1
        self.zoom_speed = 0.05

        # list of moves
        self._moves:list[mat4x4] = []

        self._program_gizmo = self.init_gizmo_shader()

        # Local variables for mouse events
        self.mouseLeftDown = False
        self.mouseRightDown = False
        self.mouseLeftUp = False
        self.mouseWheelClick = False
        self.mouseWheel = 0
        self.deltaWheel = 0
        self.mousePos = wx.Point(0, 0)
        self.mouseStartPos = wx.Point(0, 0)
        self.oldeye = self.eye

        self._framebuffer = None
        self._textureout = None
        self._posout = None

        self.textTodraw = []

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.SetFocus()

    def force_view(self, x:float, y:float, z:float):
        """ Force the view to a specific position """
        self.center= vec3(x, y, z)
        self.eye = vec3(x, y, z+50.)
        self.update_view()
        self.Refresh()

    def init_gizmo_shader(self):

        self._program_gizmo = glCreateProgram()

        # Compile The Program and shaders
        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        with open(Path(__file__).parent.parent / "shaders/simple_vertex_shader_mvp.glsl") as file:
            VERTEX_SHADER = file.read()
        glShaderSource(vertex_shader, VERTEX_SHADER)
        glCompileShader(vertex_shader)

        if glGetShaderiv(vertex_shader, GL_COMPILE_STATUS, None) == GL_FALSE:
            info_log = glGetShaderInfoLog(vertex_shader)
            print(info_log)
            glDeleteProgram(vertex_shader)
            raise Exception("Can't compile shader on GPU")

        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        with open(Path(__file__).parent.parent / "shaders/simple_fragment_shader.glsl") as file:
            FRAGMENT_SHADER = file.read()
        glShaderSource(fragment_shader, FRAGMENT_SHADER)
        glCompileShader(fragment_shader)

        if glGetShaderiv(fragment_shader, GL_COMPILE_STATUS, None) == GL_FALSE:
            info_log = glGetShaderInfoLog(fragment_shader)
            print(info_log)
            glDeleteProgram(fragment_shader)
            raise Exception("Can't compile shader on GPU")

        glAttachShader(self._program_gizmo, vertex_shader)
        glAttachShader(self._program_gizmo, fragment_shader)
        glLinkProgram(self._program_gizmo)

        # Check if the program is compiled
        if glGetProgramiv(self._program_gizmo, GL_LINK_STATUS) == GL_FALSE:
            info_log = glGetProgramInfoLog(self._program_gizmo)
            print(info_log)
            raise Exception("Can't link shader program")

        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        return self._program_gizmo

    def draw_gizmo(self):

        glUseProgram(self._program_gizmo)

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        _mvpLoc = glGetUniformLocation(self._program_gizmo, "mvp")

        glUniformMatrix4fv(_mvpLoc, 1, GL_FALSE, self.mvp)

        self.draw_plane(0., 0., 0., 0., 1., 0., 0., 0., 1., 0., 1., 1., 1., 0., 0.) # Red

        self.draw_plane(0., 0., 0., 1., 0., 0., 0., 0., 1., 1., 0., 1., 0., 1., 0.) # Green

        self.draw_plane(0., 0., 0., 1., 0., 0., 0., 1., 0., 1., 1., 0., 0., 0., 1.) # Blue

        glUseProgram(0)

    def draw_plane(self, a, b, c, d, e, f, g, h, i, j, k, l, colr, colg, colb):

        # Create the vertices of the plane
        vertices = np.array([a, b, c, d, e, f, g, h, i, j, k, l], dtype=np.float32)
        colors = np.array([colr, colg, colb, colr, colg, colb, colr, colg, colb, colr, colg, colb], dtype=np.float32)

        # Create the VAO and VBO
        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)

        glBindVertexArray(vao)
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(1)

        vbo2 = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo2)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)

        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)

        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        glDeleteVertexArrays(1, [vao])
        glDeleteBuffers(2, [vbo, vbo2])

    def add_array(self, name:str, array:WolfArray_plot3D):
        """ Add an array to the canvas """
        self.SetCurrent(self.context)

        self.arrays[name] = array

        array.add_parent(self, len(self.arrays))

    @property
    def sunposition(self):
        return vec3(self._sun_x, self._sun_y, self._sunaltitude)

    @sunposition.setter
    def sunposition(self, sunposition:vec3):

        self._sun_x, self._sun_y, self._sunaltitude = sunposition.x, sunposition.y, sunposition.z

        for curarray in self.arrays.values():
            curarray.sunposition = sunposition #self.mvp_glm * sunposition

    @property
    def sunaltitude(self):
        return self._sunaltitude

    @sunaltitude.setter
    def sunaltitude(self, sunaltitude:float):
        self._sunaltitude = sunaltitude
        self.sunposition = vec3(self._sun_x, self._sun_y, sunaltitude)

    @property
    def sunx(self):
        return self._sun_x

    @sunx.setter
    def sunx(self, sunx:float):
        self._sun_x = sunx
        self.sunposition = vec3(sunx, self._sun_y, self._sunaltitude)

    @property
    def suny(self):
        return self._sun_y

    @suny.setter
    def suny(self, suny:float):
        self._sun_y = suny
        self.sunposition = vec3(self._sun_x, suny, self._sunaltitude)

    @property
    def sunintensity(self):
        return self._sunintensity

    @sunintensity.setter
    def sunintensity(self, sunintensity:float):
        self._sunintensity = sunintensity
        for curarray in self.arrays.values():
            curarray.sunintensity = sunintensity

    @property
    def mvp(self):
        """ Return the model view projection matrix as np.array in column major order """
        mvp = self.mvp_glm
        mvp = transpose(mvp)

        return np.asarray(mvp, np.float32, order='F')

    @property
    def moves_matrix4x4(self):
        """ Return the list of moves as a list of glm.mat4 """
        move4x4 = mat4x4(1.)
        for cur in self._moves:
            move4x4 = cur * move4x4

        return move4x4

    @property
    def mvp_glm(self):
        """ Return the model view projection matrix as glm.mat4 """
        self.SetCurrent(self.context)

        if self.persp_or_ortho == TypeOfView.ORTHOGRAPHIC:
            # orthographic projection
            self.proj = ortho(self.left_view, self.right_view, self.bottom_view, self.top_view, -99999, 99999)
            # self.mv   = lookAt(self.eye, self.center, self.up)
            self.mv   = lookAt(vec3(self.center.x, self.center.y, self.center.z+20.), self.center, (0., 1., 0.))
            self.mv   = self.moves_matrix4x4 * self.mv

        elif self.persp_or_ortho == TypeOfView.ORTHOGRAPHIC_2D:
            # orthographic projection 2D
            self.proj = ortho(self.left_view, self.right_view, self.bottom_view, self.top_view, -99999, 99999)
            self.mv   = mat4x4(1.)

        else:
            # perspective projection
            self.proj = perspective(self.fov, self.ratio_woverh, self.near, self.far)
            self.mv   = lookAt(self.eye, self.center, self.up)

        mvp = self.proj * self.mv

        return mvp

    @property
    def right(self):
        """Return the right vector of the camera"""
        right = self._cross(self._normalize(self._direction()), self.up)
        return self._normalize(right)

    @property
    def distance(self):
        """Return the distance between the eye and the center of the view"""
        return np.linalg.norm(self.center - self.eye)

    @property
    def ppi(self):
        """Return the pixels per inch of the view"""
        return self.width / self.width_view

    def ray_pick(self, x, y):
        """ Get the ray direction from the camera to the mouse position """

        # Get the viewport and projection matrix
        viewport = glGetIntegerv(GL_VIEWPORT)
        projection_matrix = self.mvp_glm

        # Normalize the coordinates
        normalized_x = 2.0 * x / self.width - 1.0
        normalized_y = 1.0 - 2.0 * y / self.height

        # Create ray direction in view space
        ray_dir_view = vec3(normalized_x, normalized_y, -1.0)

        # Get the inverse of the projection matrix
        inv_projection_matrix = inverse(projection_matrix)

        # Transform ray direction to world space
        ray_dir_world = vec3(inv_projection_matrix * vec4(ray_dir_view, 0.0))

        # Normalize the ray direction
        ray_dir_world = normalize(ray_dir_world)

        return ray_dir_world

    def intersect_ray_plane(self, ray_direction, plane_point):
        """ Calculer l'intersection entre un rayon et un plan horizontal """

        # Calculer la distance entre le rayon et le plan
        numerator = dot(plane_point - self.eye, vec3(0.,0.,1.))
        denominator = dot(ray_direction, vec3(0.,0.,1.))

        # Vérifier si le rayon est parallèle au plan
        if abs(denominator) < 1e-6:
            return None, False  # Rayon parallèle au plan, pas d'intersection

        # Calculer la distance le long du rayon jusqu'au point d'intersection
        t = numerator / denominator

        # Vérifier si le point d'intersection est derrière le rayon d'origine
        if t < 0:
            return None, False  # Point d'intersection derrière le rayon d'origine

        # Calculer les coordonnées du point d'intersection
        intersection_point = self.eye + t * ray_direction

        return intersection_point, True

    def intersect_ray_quad(self, ray_direction, quad_lowerleft, quad_upperright):
        """Calculer l'intersection entre un rayon et un quad"""

        inter, ok = self.intersect_ray_plane(ray_direction, quad_lowerleft)

        if ok:
            if inter.x >= quad_lowerleft.x and inter.x <= quad_upperright.x and inter.y >= quad_lowerleft.y and inter.y <= quad_upperright.y:
                return inter, True
            else:
                return None, False
        else:
            return None, False

    def update_view(self):

        self.SetCurrent(self.context)

        self.left_view  = self.center.x  - self.width_view/2
        self.right_view = self.left_view + self.width_view

        self.bottom_view = self.center.y    - self.height_view/2
        self.top_view    = self.bottom_view + self.height_view

        for curarray in self.arrays.values():
            curarray.update_mvp(self.mvp)

    def _direction(self):
        return self.center - self.eye

    def _normalize(self, v):
        return v / np.linalg.norm(v)

    def _cross(self, v1, v2):
        return cross(v1, v2)

    def _dot(self, v1, v2):
        return dot(v1, v2)

    def _rotate(self, angle, axis):
        """Rotation matrix around axis by angle degrees"""
        return rotate(angle, axis)

    def closer(self, factor=1.):
        """Move the camera closer to the center of the view"""

        if self.persp_or_ortho in (TypeOfView.ORTHOGRAPHIC, TypeOfView.ORTHOGRAPHIC_2D):
            self.width_view *= 1. - self.zoom_speed * factor
            self.height_view = self.width_view / self.ratio_woverh

        else:
            self.eye = self.center - self._direction() * (1.-self.zoom_speed * factor)

        self.update_view()

    def further_away(self, factor=1.):
        """Move the camera further away from the center of the view"""

        if self.persp_or_ortho in (TypeOfView.ORTHOGRAPHIC, TypeOfView.ORTHOGRAPHIC_2D):
            self.width_view /= 1. - self.zoom_speed * factor
            self.height_view = self.width_view / self.ratio_woverh

        else:
            self.eye = self.center - self._direction() * (1.+self.zoom_speed * factor)

        self.update_view()

    def rotate_up(self, angle):
        """Rotate the camera up by angle degrees"""

        direction = self._direction()
        direction = self._normalize(direction)
        self.up = self._rotate(angle, direction) *self.up
        self.up = self._normalize(self.up)

        if self.persp_or_ortho == TypeOfView.ORTHOGRAPHIC:
            self.add_move_rotation(-angle, self.up, self.center)

    def rotate_z_center(self, angle):
        """ Rotate the camera around the z axis, passing at center, by angle degrees """

        direction = self._direction()
        rotation_z = self._rotate(angle, vec3(0.,0.,1.))
        self.eye = self.center - rotation_z * direction
        self.up = rotation_z * self.up
        self.up = self._normalize(self.up)

        if self.persp_or_ortho == TypeOfView.ORTHOGRAPHIC:
            self.add_move_rotation(-angle, vec3(0.,0.,1.), self.center)

    def rotate_x_center(self, angle):
        """ Rotate the camera around the x axis, passing at center, by angle degrees """

        direction = self._direction()
        rotation_x = self._rotate(angle, vec3(1.,0.,0.))
        self.eye = self.center - rotation_x * direction
        self.up = rotation_x * self.up
        self.up = self._normalize(self.up)

        if self.persp_or_ortho == TypeOfView.ORTHOGRAPHIC:
            self.add_move_rotation(-angle, vec3(1.,0.,0.), self.center)

    def rotate_y_center(self, angle):
        """ Rotate the camera around the y axis, passing at center, by angle degrees """

        direction = self._direction()
        rotation_y = self._rotate(angle, vec3(0.,1.,0.))
        self.eye = self.center - rotation_y * direction
        self.up = rotation_y * self.up
        self.up = self._normalize(self.up)

        if self.persp_or_ortho == TypeOfView.ORTHOGRAPHIC:
            self.add_move_rotation(-angle, vec3(0.,1.,0.), self.center)

    def add_move_rotation(self, angle:float, axis:vec3, center:vec3):
        """ Add a rotation to the list of moves """

        self._moves.append(translate(center) * rotate(angle, axis) * translate(-center))

    def add_move_translation(self, translation:vec3):
        """ Add a translation to the list of moves """

        self._moves.append(translate(translation))

    def rotate_right_eye(self, angle):
        """Rotate the camera to the right by angle degrees"""

        right = self.right

        if self.persp_or_ortho == TypeOfView.ORTHOGRAPHIC:
            self.add_move_rotation(-angle, right, self.center)

        self.up = self._rotate(angle, right) * self.up
        self.up = self._normalize(self.up)

        direction = self._cross(self.up, right)
        self.center = self.eye + self._normalize(direction) * self.distance

    def rotate_right_center(self, angle):
        """Rotate the camera to the right by angle degrees"""

        right = self.right

        if self.persp_or_ortho == TypeOfView.ORTHOGRAPHIC:
            self.add_move_rotation(-angle, right, self.center)

        self.up = self._rotate(angle, right) * self.up
        self.up = self._normalize(self.up)

        direction = self._cross(self.up, right)
        self.eye = self.center - self._normalize(direction) * self.distance

    def translate(self, amplitude, orient):
        """Translate the camera by amplitude in the direction of the vector orient"""
        self.eye += amplitude * orient
        self.center += amplitude * orient
        self.update_view()

    def OnPaint(self, event):
        """Called when the window is exposed."""
        dc = wx.PaintDC(self)
        self.SetCurrent(self.context)
        if not self.init:
            self.InitGL()
            self.init = True
        self.Draw()

    def OnSize(self, event):
        """Called when the window is resized"""
        self.width, self.height = self.GetClientSize()

        glViewport(0, 0, self.width, self.height)

        self.ratio_woverh = self.width / self.height
        self.height_view = self.width_view / self.ratio_woverh

        self.update_view()
        self.create_fbo()
        self._update_colpos = True

        self.Draw()

    def OnWheel(self, event:wx.MouseEvent):
        """ Called when the mouse wheel is scrolled. """

        self.mouseWheelClick = True
        self.mouseWheel = event.GetWheelRotation()
        self.deltaWheel = event.GetWheelDelta()

        ctrldown = event.ControlDown()
        shiftdown = event.ShiftDown()

        if self.mouseWheel > 0:
            if shiftdown:
                self.closer(self.deltaWheel / 120 * 5)
            else:
                self.closer(self.deltaWheel / 120)
        elif self.mouseWheel < 0:
            if shiftdown:
                self.further_away(self.deltaWheel / 120 * 5)
            else:
                self.further_away(self.deltaWheel / 120)

        self.Refresh()

    def OnLeftDown(self, event:wx.MouseEvent):
        """ Called when the left mouse button is pressed."""
        self.mouseLeftDown = True
        self.mouseStartPos = event.GetPosition()

        self.oldeye = self.eye

        self.Refresh()

    def OnRightDown(self, event:wx.MouseEvent):
        """ Called when the right mouse button is pressed."""
        self.mouseRightDown = True
        mousePos = event.GetPosition()

        self.drawposition = not self.drawposition

        self.Draw()

        locx = mousePos.x
        locy = self.height - mousePos.y

        logging.info('mouse: {} ; {}'.format(mousePos.x, mousePos.y))
        logging.info('indices: {} ; {}'.format(locx, locy))

        x,y,idx,alpha = self.picker[locx, locy]

        # r,g,b = self.colors[locx, locy]
        # logging.info('color: {} - {} - {}'.format(r,g,b))

        self.drawposition = not self.drawposition

        curarray = self.arrays[list(self.arrays.keys())[int(idx)-1]]
        i = int(x)
        j = int(y)

        if i > 0 and i < curarray.ztexture.shape[0] and j > 0 and j < curarray.ztexture.shape[1]:
            z = curarray.ztexture[i, j]

            logging.info('coords: {} - {} - {}'.format(x,y,z))

            # xyz = self.mvp_glm * vec4(x, y, z, 1.)

            # self.textTodraw.append(Text_Image_Texture('{z:.3f}', self.parent, Text_Infos(Font_Priority.FONTSIZE, colour=(255,255,255,255)), None, x, y))

            # self.Refresh()

    def OnRightUp(self, event:wx.MouseEvent):
        """ Called when the right mouse button is released."""
        self.mouseRightDown = False
        self.Refresh()

    def OnLeftUp(self, event:wx.MouseEvent):
        """ Called when the left mouse button is released."""
        self.mouseLeftUp = True
        self.mouseLeftDown = False

        self.Refresh()

    def OnMouseMove(self, event:wx.MouseEvent):
        """ Called when the mouse is in motion."""
        self.mousePos = event.GetPosition()

        if self.mouseLeftDown:
            self.mouseDelta = (self.mousePos - self.mouseStartPos)

            self.translate(-self.mouseDelta.x / self.ppi /2, self.right)
            self.translate( self.mouseDelta.y / self.ppi /2, self.up)

            self.mouseStartPos = self.mousePos

            self.Refresh()

    @property
    def boundingbox(self):
        """ Return the bounding box of the view """

        bounds = []

        for curarray in self.arrays.values():
            bounds.append(curarray.boundingbox)

        xmin = min([b[0] for b in bounds])
        xmax = max([b[1] for b in bounds])
        ymin = min([b[2] for b in bounds])
        ymax = max([b[3] for b in bounds])

        return xmin, xmax, ymin, ymax

    @property
    def z_extrema(self):
        """ Return the extrema of the ztexture """
        zmin = 0
        zmax = 0
        for curarray in self.arrays.values():
            if curarray.ztexture is not None:
                zmin = min(zmin, curarray.ztexture.min())
                zmax = max(zmax, curarray.ztexture.max())
        return zmin, zmax

    def autoscale(self):
        """ Auto scale the view to fit all the arrays """
        xmin, xmax, ymin, ymax = self.boundingbox
        zmin, zmax = self.z_extrema

        if xmax - xmin > ymax - ymin:
            self.width_view = (xmax - xmin)*1.5
            self.height_view = self.width_view / self.ratio_woverh
        else:
            self.height_view = (ymax - ymin)*1.5
            self.width_view = self.height_view * self.ratio_woverh

        center_x = (xmin + xmax) / 2
        center_y = (ymin + ymax) / 2

        if self.persp_or_ortho == TypeOfView.ORTHOGRAPHIC:
            center_x /= 2.
            center_y /= 2.

            self.eye = vec3(center_x, center_y, 10000.)
            self.center = vec3(center_x, center_y, 0.)

        else:
            self.eye = vec3(center_x, center_y, zmax + (zmax - zmin) * 2.)
            self.center = vec3(center_x, center_y, 0.)

        self.up = vec3(0., 1., 0.)

        if self.persp_or_ortho == TypeOfView.ORTHOGRAPHIC:
            self._moves = []

        self.update_view()

    def copy_to_clipboard(self):
        """ Copy the image to the clipboard """
        self.SetCurrent(self.context)
        pixels = glReadPixels(0, 0, self.width, self.height, GL_RGB, GL_UNSIGNED_BYTE)
        image = wx.Image(self.width, self.height, pixels)
        with wx.TheClipboard as clipboard:
            clipboard.Open()
            clipboard.SetData(wx.BitmapDataObject(wx.Bitmap(image)))
            clipboard.Close()

    def save_to_file(self):
        """ Save the image to a file """
        with wx.FileDialog(self, _("Save file"), wildcard="PNG files (*.png)|*.png",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            self.SetCurrent(self.context)
            pixels = glReadPixels(0, 0, self.width, self.height, GL_RGB, GL_UNSIGNED_BYTE)
            image = wx.Image(self.width, self.height, pixels)
            image.SaveFile(pathname, wx.BITMAP_TYPE_PNG)

    def print_shortcuts(self) -> str:
        """ Print shortcuts """

        shortcuts = _("Definitions:\n")
        shortcuts += "------------\n\n"
        shortcuts = _("Camera is the eye position\n")
        shortcuts += _("Center is the center of the view\n")
        shortcuts += _("Direction is the vector from the eye to the center\n")
        shortcuts += _("Up is the up vector, perpendicular to the direction\n")
        shortcuts += _("Right is the vector normal to the direction-up plan\n\n")

        shortcuts += _("Clicks\n")
        shortcuts += "-------\n\n"
        shortcuts += _("Left click and drag: translate the view in the up-right plane\n")
        shortcuts += _("Right click: display the position of the mouse -- to improve\n")
        shortcuts += "\n\n"
        shortcuts += _("Zoom\n")
        shortcuts += "----\n"
        shortcuts += "\n\n"
        shortcuts += _("0 or Home: autoscale\n")
        shortcuts += _("Mouse wheel: zoom in/out  (eye closer or further from the center)\n")
        shortcuts += _("Shift + mouse wheel: zoom in/out faster\n")
        shortcuts += _("+ or - or mouse wheel: zoom in/out\n")
        shortcuts += "\n\n"
        shortcuts += _("Translation\n")
        shortcuts += "-----------\n"
        shortcuts += "\n\n"
        shortcuts += _("Arrow keys: move the view\n")
        shortcuts += _("Shift + arrow keys: move the view 0\n")
        shortcuts += _("Page up/Page down: move the view along eye-center direction\n")
        shortcuts += "\n\n"
        shortcuts += _("Rotation\n")
        shortcuts += "-----------\n"
        shortcuts += "\n\n"
        shortcuts += _("Ctrl + arrow keys: rotate the view around eye\n")
        shortcuts += _("Alt + arrow keys: rotate the view around center\n")
        shortcuts += "\n\n"
        shortcuts += _("Projection/Orthographic\n")
        shortcuts += "-----------------------\n"
        shortcuts += "\n\n"
        shortcuts += _("Space: switch between perspective and orthographic view\n")
        shortcuts += "\n\n"
        shortcuts += _("Sun\n")
        shortcuts += "----\n"
        shortcuts += "\n\n"
        shortcuts += _("Ctrl+F1: sun position North-West\n")
        shortcuts += _("Ctrl+F2: sun position South-West\n")
        shortcuts += _("Ctrl+F3: sun position South-East\n")
        shortcuts += _("Ctrl+F4: sun position North-East\n")
        shortcuts += _("Ctrl+F5: decrease sun intensity\n")
        shortcuts += _("Ctrl+F6: increase sun intensity\n")
        shortcuts += _("Ctrl+F7: decrease sun altitude\n")
        shortcuts += _("Ctrl+F8: increase sun altitude\n")
        shortcuts += _("Ctrl+F9: iterate on precalculated sun positions (0->8)\n")

        shortcuts += "\n\n"
        shortcuts += _("Miscellaneous (experimental)\n")
        shortcuts += "----------------------------\n"
        shortcuts += "\n\n"
        shortcuts += _("G: display/hide the grid\n")
        shortcuts += _("X: display/hide the x plane\n")
        shortcuts += _("Y: display/hide the y plane\n")
        shortcuts += _("Z: display/hide the z plane\n")
        shortcuts += _("C: display/hide the xy plane\n")
        shortcuts += _("V: display/hide the yz plane\n")
        shortcuts += _("B: display/hide the xz plane\n")
        shortcuts += _("H: display the shortcuts\n")

        return shortcuts

    def OnKeyDown(self, event):
        """ Called when a key is pressed."""

        shiftdown = event.ShiftDown()
        altdown = event.AltDown()
        ctrldown = event.ControlDown()

        keycode = event.GetKeyCode()

        if ctrldown:
            if keycode == wx.WXK_LEFT:
                self.rotate_up(self.rotation_speed)

            elif keycode == wx.WXK_RIGHT:
                self.rotate_up(-self.rotation_speed)

            elif keycode == wx.WXK_UP:
                self.rotate_right_eye(self.rotation_speed)

            elif keycode == wx.WXK_DOWN:
                self.rotate_right_eye(-self.rotation_speed)

            elif keycode == ord('C'):
                # copy image to clipboard
                self.copy_to_clipboard()

            elif keycode == ord('S'):
                # save image to file
                self.save_to_file()

            elif keycode == wx.WXK_F9:
                # rotate sunposition
                if self._sun_idx == 0:
                    self.sunposition = vec3(0., 0., self.sunaltitude) #+ self.center
                    self._sun_idx +=1
                elif self._sun_idx == 1:
                    self.sunposition = vec3(-10000., 0., self.sunaltitude)
                    self._sun_idx +=1
                elif self._sun_idx == 2:
                    self.sunposition = vec3(-10000., -10000, self.sunaltitude)
                    self._sun_idx +=1
                elif self._sun_idx == 3:
                    self.sunposition = vec3(0., -10000, self.sunaltitude)
                    self._sun_idx +=1
                elif self._sun_idx == 4:
                    self.sunposition = vec3(10000., -10000, self.sunaltitude)
                    self._sun_idx +=1
                elif self._sun_idx == 5:
                    self.sunposition = vec3(10000., 0., self.sunaltitude)
                    self._sun_idx +=1
                elif self._sun_idx == 6:
                    self.sunposition = vec3(10000., 10000, self.sunaltitude)
                    self._sun_idx +=1
                elif self._sun_idx == 7:
                    self.sunposition = vec3(0., 10000, self.sunaltitude)
                    self._sun_idx +=1
                elif self._sun_idx == 8:
                    self.sunposition = vec3(-10000., 10000, self.sunaltitude)
                    self._sun_idx = 0

                logging.info('sun position: {}'.format(self.sunposition))

            elif keycode == wx.WXK_F1:
                # sun position North-West
                self.sunposition = vec3(-10000., 10000., self.sunaltitude)
                logging.info(_('sun position: North-West'))

            elif keycode == wx.WXK_F2:
                # sun position South-West
                self.sunposition = vec3(-10000., -10000., self.sunaltitude)
                logging.info(_('sun position: South-West'))

            elif keycode == wx.WXK_F3:
                # sun position South-East
                self.sunposition = vec3(10000., -10000., self.sunaltitude)
                logging.info(_('sun position: South-East'))

            elif keycode == wx.WXK_F4:
                # sun position North-East
                self.sunposition = vec3(10000., 10000., self.sunaltitude)
                logging.info(_('sun position: North-East'))

            elif keycode == wx.WXK_F5:
                # sun intensity increase
                self.sunintensity /= 1.1
                logging.info(_('sun intensity: {}'.format(self.sunintensity)))

            elif keycode == wx.WXK_F6:
                # sun intensity decrease
                self.sunintensity *= 1.1
                logging.info(_('sun intensity: {}'.format(self.sunintensity)))

            elif keycode == wx.WXK_F8:
                # sun altitude increase
                self.sunaltitude += 100.
                logging.info(_('sun altitude: {}'.format(self.sunaltitude)))

            elif keycode == wx.WXK_F7:
                # sun altitude decrease
                self.sunaltitude -= 100.
                logging.info(_('sun altitude: {}'.format(self.sunaltitude)))

        elif altdown:
            if keycode == wx.WXK_LEFT:
                self.rotate_z_center(-self.rotation_speed)

            elif keycode == wx.WXK_RIGHT:
                self.rotate_z_center(self.rotation_speed)

            elif keycode == wx.WXK_UP:
                self.rotate_right_center(self.rotation_speed)

            elif keycode == wx.WXK_DOWN:
                self.rotate_right_center(-self.rotation_speed)

        else:

            if keycode == wx.WXK_LEFT:
                if shiftdown:
                    self.translate(self.translation_speed*10, self.right)
                else:
                    self.translate(self.translation_speed, self.right)

            elif keycode == wx.WXK_RIGHT:
                if shiftdown:
                    self.translate(-self.translation_speed*10, self.right)
                else:
                    self.translate(-self.translation_speed, self.right)

            elif keycode == wx.WXK_UP:
                if shiftdown:
                    self.translate(self.translation_speed*10, self.up)
                else:
                    self.translate(-self.translation_speed, self.up)

            elif keycode == wx.WXK_DOWN:
                if shiftdown:
                    self.translate(-self.translation_speed*10, self.up)
                else:
                    self.translate(self.translation_speed, self.up)

            elif keycode == wx.WXK_PAGEUP:
                self.translate(-self.translation_speed, self._direction())

            elif keycode == wx.WXK_PAGEDOWN:
                self.translate(self.translation_speed, self._direction())

            elif keycode == ord('G'):
                self.grid = not self.grid

            elif keycode == wx.WXK_SPACE:

                if self.persp_or_ortho == TypeOfView.ORTHOGRAPHIC:
                    self.persp_or_ortho = TypeOfView.ORTHOGRAPHIC_2D

                elif self.persp_or_ortho == TypeOfView.ORTHOGRAPHIC_2D:
                    self.persp_or_ortho = TypeOfView.PERSPECTIVE

                else:
                    self.persp_or_ortho = TypeOfView.ORTHOGRAPHIC

                self.autoscale()

            elif keycode == wx.WXK_NUMPAD_ADD or keycode == wx.WXK_ADD or keycode == 61:
                self.closer()

            elif keycode == wx.WXK_NUMPAD_SUBTRACT or keycode == wx.WXK_SUBTRACT or keycode == 45:
                self.further_away()

            elif keycode == wx.WXK_NUMPAD0 or keycode == 48 or keycode == wx.WXK_HOME:

                self.autoscale()

            elif keycode == ord('X'):
                self.x_plane = not self.x_plane
                self.y_plane = False
                self.z_plane = False
                self.xy_plane = False
                self.yz_plane = False
                self.xz_plane = False

            elif keycode == ord('Y'):
                self.y_plane = not self.y_plane
                self.x_plane = False
                self.z_plane = False
                self.xy_plane = False
                self.yz_plane = False
                self.xz_plane = False

            elif keycode == ord('Z'):
                self.z_plane = not self.z_plane
                self.x_plane = False
                self.y_plane = False
                self.xy_plane = False
                self.yz_plane = False
                self.xz_plane = False

            elif keycode == ord('C'):
                self.xy_plane = not self.xy_plane
                self.x_plane = False
                self.y_plane = False
                self.z_plane = False
                self.yz_plane = False
                self.xz_plane = False

            elif keycode == ord('V'):
                self.yz_plane = not self.yz_plane
                self.x_plane = False
                self.y_plane = False
                self.z_plane = False
                self.xy_plane = False
                self.xz_plane = False

            elif keycode == ord('B'):
                self.xz_plane = not self.xz_plane
                self.x_plane = False
                self.y_plane = False
                self.z_plane = False
                self.xy_plane = False
                self.yz_plane = False

            elif keycode == ord('H'):
                frmshortcuts = wx.Frame(self, -1, "Shortcuts", size=(400, 800))
                panel = wx.Panel(frmshortcuts, -1)
                st = wx.StaticText(panel, -1, self.print_shortcuts(), (10, 10))
                frmshortcuts.Show()
                logging.info(self.print_shortcuts())


        self.update_view()

        self.Refresh()

    def OnKeyUp(self, event):
        self.Refresh()

    def InitGL(self):
        glClearColor(self.background[0], self.background[1], self.background[2], self.background[3])
        glEnable(GL_DEPTH_TEST)

    def create_fbo(self):
        """ Create a framebuffer object """

        if self._framebuffer is not None:
            glDeleteFramebuffers(1, [self._framebuffer])
            self._framebuffer = None
        if self._textureout is not None:
            glDeleteTextures(1, [self._textureout])
            self._textureout = None
        if self._posout is not None:
            glDeleteTextures(1, [self._posout])
            self._posout = None

        self._framebuffer = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self._framebuffer)

        self._textureout = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self._textureout)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._textureout, 0)

        self._posout = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self._posout)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None)
        glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, GL_TEXTURE_2D, self._posout, 0)

        glDrawBuffers(2, [GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1])

        ret = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if ret != GL_FRAMEBUFFER_COMPLETE:
            print(f"Framebuffer is not complete: {ret}")

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def Draw(self):

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        if self.drawposition and self._update_colpos:
            glBindFramebuffer(GL_FRAMEBUFFER, self._framebuffer)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            for curarray in self.arrays.values():
                curarray.Draw()

            glFinish()

            # glBindTexture(GL_TEXTURE_2D, self._textureout)
            # self.colors = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            # glGetTexImage(GL_TEXTURE_2D, 0, GL_RGB, GL_UNSIGNED_BYTE, self.colors, np.uint8)
            # self.colors = self.colors.swapaxes(0, 1)

            glBindTexture(GL_TEXTURE_2D, self._posout)
            self.picker = np.zeros((self.height, self.width, 4), dtype=np.float32)
            glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_FLOAT, self.picker, np.float32)
            self.picker = self.picker.swapaxes(0, 1)

            glBindFramebuffer(GL_FRAMEBUFFER, 0)

        else:

            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            if self.grid:
                self.draw_gizmo()

            for curarray in self.arrays.values():
                curarray.Draw()

            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glLoadMatrixf(self.mvp)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            for curtext in self.textTodraw:
                curtext.paint()


            self.SwapBuffers()

    def update_palette(self, idx, color_palette, color_values):
        """ Update the color palette of the array """
        if idx in self.arrays:
            self.SetCurrent(self.context)

            self.arrays[idx].update_palette(color_palette, color_values)

            self.Refresh()


class Wolf_Viewer3D(wx.Frame):

    def __init__(self, parent, title):

        super(Wolf_Viewer3D, self).__init__(parent, title=title, size=(640, 480))
        self.canvas = CanvasOGL(self)
        self.sx = 1.
        self.sy = 1.
        self.Show()

    @property
    def context(self):
        return self.canvas.context

    def GetSize(self):
        return self.canvas.GetSize()

    @property
    def xmin(self):
        return self.canvas.boundingbox[0]

    @property
    def xmax(self):
        return self.canvas.boundingbox[1]

    @property
    def ymin(self):
        return self.canvas.boundingbox[2]

    @property
    def ymax(self):
        return self.canvas.boundingbox[3]

    def add_array(self, name:str, array:WolfArray_plot3D):
        """ Add an array to the canvas """
        self.canvas.add_array(name, array)

    def force_view(self, x, y, z= -1):
        """ Force the view to the specified coordinates.

        if z == -1, the z value is the same as the current z value."""
        if z==-1:
            curx,cury,curz = self.canvas.center
            self.canvas.force_view(x, y, curz)
        else:
            self.canvas.force_view(x, y, z)

    def autoscale(self):
        """ Auto scale the view to fit all the arrays """
        self.canvas.autoscale()

    def update_palette(self, idx, color_palette, color_values):
        """ Update the color palette of the array """
        self.canvas.update_palette(idx, color_palette, color_values)

def main_test():
    """
    Test the Wolf_Viewer3D class

    2 arrays can be added to the canvas. The first one is in row major order and the second one is in column major order.
    The plt must be the same for both arrays.
    """

    origx = origy = 1000.
    dx = dy = 1.

    app = wx.App()
    frame1 = Wolf_Viewer3D(None, "3D - row major order")
    frame2 = Wolf_Viewer3D(None, "3D - column major order")

    # Array in row major order
    points = np.asarray([1.5,1.5, 2.5,2.5, 2.5,3.5, 7.5,7.5, 1.5,2.5, 3.5,2.5, 2.5,1.5], dtype=np.float32)
    points += origx
    zvalues = np.zeros((10, 20), dtype=np.float32, order='C')

    zvalues[1,1] = 1.
    zvalues[2,2] = 2.
    zvalues[7,7] = 3.
    zvalues[2,1] = 4.
    zvalues[3,2] = 5.
    zvalues[2,3] = 6.

    colors = np.array([1., 0., 1., 0., 0., 1.], dtype=np.float32)

    myarray = WolfArray_plot3D(points,
                               dx = dx, dy = dy,
                               origx = origx, origy = origy,
                               zscale = 1.,
                               ztexture = zvalues,
                               color_palette = colors,
                               color_values = np.array([0., 4.], dtype=np.float32))

    frame1.add_array("array", myarray)

    # Array in column major order
    points2 = np.asarray([1.5,1.5, 2.5,2.5, 2.5,3.5, 7.5,7.5, 1.5,2.5, 3.5,2.5, 2.5,1.5], dtype=np.float32)
    points2 += origx
    zvalues_2 = np.zeros((20, 10), dtype=np.float32, order='F')

    zvalues_2[1,1] = 1.
    zvalues_2[2,2] = 2.
    zvalues_2[7,7] = 3.
    zvalues_2[1,2] = 4.
    zvalues_2[2,3] = 5.
    zvalues_2[3,2] = 6.

    colors2 = np.array([1., 0., 1., 0., 0., 1.], dtype=np.float32)

    flat_zvalues  = zvalues.flatten(order='K').copy()
    flat_zvalues2 = zvalues_2.flatten(order='K').copy()

    assert zvalues.tobytes(order='A') == zvalues_2.tobytes(order='A')

    assert flat_zvalues.shape == flat_zvalues2.shape
    assert len(flat_zvalues) == len(flat_zvalues2)
    assert len(flat_zvalues) == 200
    assert flat_zvalues[21] == 1.
    assert flat_zvalues[42] == 2.
    assert flat_zvalues[147] == 3.
    assert flat_zvalues[41] == 4.
    assert flat_zvalues[62] == 5.
    assert flat_zvalues[43] == 6.
    assert np.all(flat_zvalues == flat_zvalues2)

    myarray2 = WolfArray_plot3D(points2,
                                dx = dx, dy = dy,
                                origx = origx, origy = origy,
                                zscale = 1.,
                                ztexture = zvalues_2,
                                color_palette = colors2,
                                color_values = np.array([0., 4.], dtype=np.float32))

    frame2.add_array("array2", myarray2)

    app.MainLoop()

if __name__ == "__main__":
    main_test()