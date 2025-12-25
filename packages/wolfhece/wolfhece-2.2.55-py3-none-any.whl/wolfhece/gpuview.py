"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
import textwrap
import sys
try:
    from OpenGL.GL import *
except:
    msg='Error importing OpenGL library'
    msg+='   Python version : ' + sys.version
    msg+='   Please check your version of opengl32.dll -- conflict may exist between different files present on your desktop'
    raise Exception(msg)

from math import sqrt,floor

from .drawing_obj import Element_To_Draw
import logging

_global_gpu_state = dict()

GRID_N=100

VECFIELD_VTX_SHADER = textwrap.dedent("""\
#version 460
    layout (location=0) in vec3 aVertex;
    //out vec4 vertex;

    void main(){
       //vertex = vec4(aVertex, 1.0);
       gl_Position = vec4(aVertex, 1.0);
    }
""")


VECFIELD_GEOM_SHADER = textwrap.dedent("""\
#version 460
#extension GL_EXT_geometry_shader4 : enable

    layout (points) in;
    layout (triangle_strip, max_vertices = 3) out;

    uniform sampler2D sArrowsTexture2;
    //uniform mat4 gl_ProjectionMatrix;

    uniform float to_tex_x_transl;
    uniform float to_tex_x_scale;
    uniform float to_tex_y_transl;
    uniform float to_tex_y_scale;
    uniform vec2 screen_aspect_ratio;
    uniform mat4 projection_matrix;

    out vec3 fColor;

    // Parametric color generation is said to be faster
    // than using tables/interpolation...
    // This one comes from :  https://www.shadertoy.com/view/XtGGzG

    float saturate( float x ) { return clamp( x, 0.0, 1.0 ); }
    vec3 plasma_quintic( float x )
    {
        x = saturate( x );
        vec4 x1 = vec4( 1.0, x, x * x, x * x * x ); // 1 x x2 x3
        vec4 x2 = x1 * x1.w * x; // x4 x5 x6 x7
        return vec3(
            dot( x1.xyzw, vec4( +0.063861086, +1.992659096, -1.023901152, -0.490832805 ) ) + dot( x2.xy, vec2( +1.308442123, -0.914547012 ) ),
            dot( x1.xyzw, vec4( +0.049718590, -0.791144343, +2.892305078, +0.811726816 ) ) + dot( x2.xy, vec2( -4.686502417, +2.717794514 ) ),
            dot( x1.xyzw, vec4( +0.513275779, +1.580255060, -5.164414457, +4.559573646 ) ) + dot( x2.xy, vec2( -1.916810682, +0.570638854 ) ) );
    }

    vec3 magma_quintic( float x )
    {
        x = clamp( x, 0.0, 1.0);
        vec4 x1 = vec4( 1.0, x, x * x, x * x * x ); // 1 x x2 x3
        vec4 x2 = x1 * x1.w * x; // x4 x5 x6 x7
        return vec3(
            dot( x1.xyzw, vec4( -0.023226960, +1.087154378, -0.109964741, +6.333665763 ) ) + dot( x2.xy, vec2( -11.640596589, +5.337625354 ) ),
            dot( x1.xyzw, vec4( +0.010680993, +0.176613780, +1.638227448, -6.743522237 ) ) + dot( x2.xy, vec2( +11.426396979, -5.523236379 ) ),
            dot( x1.xyzw, vec4( -0.008260782, +2.244286052, +3.005587601, -24.279769818 ) ) + dot( x2.xy, vec2( +32.484310068, -12.688259703 ) ) );
    }

    void main() {
        int i;
        for(i = 0; i < gl_VerticesIn; i++)
        {
            // Please note that this works because there's a mapping between
            // the vertex coordinates and a corresponding texel.

            vec4 t = texture(
                sArrowsTexture2,
                vec2(
                    (gl_in[i].gl_Position.y - to_tex_y_transl) * to_tex_y_scale,
                    (gl_in[i].gl_Position.x - to_tex_x_transl) * to_tex_x_scale) );
            float qx = t.r;
            float qy = t.g;

            // This has been normed in the texture, so value is between zero and one
            float value = sqrt(qx*qx+qy*qy);

            // These two vectors gives the direction of the arrow and its perpendicaular.
            // They are scaled in screen coordinates.
            vec4 arrow =       vec4(qx*screen_aspect_ratio.x,  qy*screen_aspect_ratio.y, 0, 0);
            vec4 perp_arrow =  vec4(qy*screen_aspect_ratio.x, -qx*screen_aspect_ratio.y, 0, 0) * 0.25;


            if (value >= 0) {

                // Give all arrow the same size in screen coordinates
                // by dividing by the norm.
                //arrow = arrow / value;
                //perp_arrow = perp_arrow / value;

                //vec3 color = magma_quintic(value);
                vec3 color = vec3(0.0,0.0,0.0);

                // Positions are in model space but
                // arrows are in screen space (normalized coordinates).
                // Therefore I apply the projection to the position
                // but not the arrow itself.

                gl_Position = projection_matrix * gl_in[i].gl_Position + arrow;
                fColor = color;
                EmitVertex();

                gl_Position = projection_matrix * gl_in[i].gl_Position + perp_arrow;
                fColor = color;
                EmitVertex();

                gl_Position = projection_matrix * gl_in[i].gl_Position - perp_arrow;
                fColor = color;
                EmitVertex();
            }
        }

        EndPrimitive();
    }
""")


VECFIELD_FRAG_SHADER = textwrap.dedent("""\
#version 460
    layout(location = 0) out vec4 result;
    in vec3 fColor;

    void main() {
        result = vec4(fColor.x,fColor.y,fColor.z,0.5);
    }
""")



def _load_shader(shader_type, source):
    shader = glCreateShader(shader_type)

    if shader == 0:
        raise Exception("Can't load shader into GPU")

    glShaderSource(shader, source)
    glCompileShader(shader)

    if glGetShaderiv(shader, GL_COMPILE_STATUS, None) == GL_FALSE:
        info_log = glGetShaderInfoLog(shader)
        print(info_log)
        glDeleteProgram(shader)
        raise Exception("Can't compile shader on GPU")

    return shader


def _load_program(vertex_source, geometry_source, fragment_source):
    # returns the program

    vertex_shader = _load_shader(GL_VERTEX_SHADER, vertex_source)

    if vertex_shader == 0:
        raise Exception("Could not initialize vertex shader")

    if geometry_source is not None:
        geometry_shader = _load_shader(GL_GEOMETRY_SHADER, geometry_source)
        if geometry_shader == 0:
            raise Exception("Could not initialize geometry shader")

    if fragment_source is not None:
        fragment_shader = _load_shader(GL_FRAGMENT_SHADER, fragment_source)
        if fragment_shader == 0:
            raise Exception("Could not initialize fragment shader")

    program = glCreateProgram()

    if program == 0:
        raise Exception("Could not initialize shader program")

    # At this point, shaders are compiled but not linked to each other
    glAttachShader(program, vertex_shader)
    if geometry_source is not None:
        glAttachShader(program, geometry_shader)
    if fragment_source is not None:
        glAttachShader(program, fragment_shader)

    glLinkProgram(program)

    if glGetProgramiv(program, GL_LINK_STATUS, None) == GL_FALSE:
        glDeleteProgram(program)
        raise Exception("Could not link the shader program")


    glDeleteShader(vertex_shader)
    glDeleteShader(geometry_shader)
    glDeleteShader(fragment_shader)

    return program

class Rectangle:
    def __init__(self, x, y=None, width=None, height=None):
        if type(x) in (list, tuple):
            x,y,width,height = x[0][0], x[0][1], x[1][0], x[1][1]

        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def intersection(self, r):
        left = max(self.xmin, r.xmin)
        right = min(self.xmax, r.xmax)
        bottom = max(self.ymin, r.ymin)
        top = min(self.ymax, r.ymax)

        if left < right and bottom < top:
            return Rectangle(left,bottom, right-left, top-bottom)
        else:
            return None

    def zoom(self, sx: float, sy:float):
        return Rectangle( self.xmin * sx, self.ymin * sy, self.width * sx, self.height * sy)


    @property
    def xmin(self):
        return self.x

    @property
    def xmax(self):
        return self.x + self.width

    @property
    def ymin(self):
        """ I use ymin to not use "bottom" because "bottom" depends
        on the y-coord orientation which can differ between screen coord or GL coord.
        """
        return self.y

    @property
    def ymax(self):
        return self.y + self.height

    def __str__(self) -> str:
        return f"x:{self.x:.2f} y:{self.y:.2f} w:{self.width:.2f} h:{self.height:.2f}"


class VectorField(Element_To_Draw):
    """ Draws a field of arrows.

    The arrow are defined by an x and and y extent (in matrices) and
    drawn based on a grid (which we compute here).

    """
    def __init__(self, x_extent, y_extent, bounds, dx, dy, idx: str = '', plotted: bool = True, mapviewer=None, need_for_wx: bool = False, minsize = .1) -> None:
        global _global_gpu_state

        super().__init__(idx, plotted, mapviewer, need_for_wx)

        if self.mapviewer is None:
            logging.error("No mapviewer defined for VectorField")
            return

        try:
            self.mapviewer.SetCurrentContext()
        except:
            logging.error("Error during OpenGL context setup -- VectorField")
            return

        self._gpu_program_ref = 1
        while self._gpu_program_ref in _global_gpu_state:
            self._gpu_program_ref +=1

        if self._gpu_program_ref not in _global_gpu_state:
            _global_gpu_state[self._gpu_program_ref] = _load_program(
                VECFIELD_VTX_SHADER,
                VECFIELD_GEOM_SHADER,
                VECFIELD_FRAG_SHADER)

        self._gl_texture = None
        self._gl_buffer = None
        self._aspect_ratio = 1.0
        self._arrow_scale_x = 1.0
        self._arrow_scale_y = 1.0
        self._gl_buffer = []

        self._bounds = bounds
        self._dx = dx
        self._dy = dy

        # facteurs liés au dessin
        self.min_size = minsize     # valeur adim minimale associée à la norme minimale --> la norme variera entre [minsize , 1.]
        self.arrow_pixel_size = 20  # taille en pixels de la flèche pour une norme_adim == 1.
        self.zoom_factor = 1        # facteur de mise à l'échelle du débit vis-à-vis d'un débit max dans un autre bloc s'il existe
        self.zoom_2      = 2        # facteur de zoom "strictement graphique"

        """
        Logique de calcul :
            - on normalise les composantes vectorielles --> [0, 1]
            - on redistribue les normes entre [minsize , 1.] --> minsize==1 => toutes les flèches sont de taille identique
            - on recalcule les composantes vectorielles sur base de cette nouvelle norme
            - lors du dessin, on multiplie le facteur de mise à l'échelle par (self.zoom_factor * self.zoom_2)
                - le premier facteur tient compte de la mise à l'échelle globale du champ vectoriel sur base d'une combinaison de blocs --> Wolfresults_2D
                - le second facteur est purement graphique et sert à augmenter/réduire la taille tout en gardent la proportionnalité
        """

        self._set_data(x_extent, y_extent)

    def __del__(self):

        self.mapviewer.SetCurrentContext()

        if self._gl_texture is not None:
            glDeleteTextures(1,[self._gl_texture])

        if self._gpu_program_ref in _global_gpu_state:
            glDeleteProgram(_global_gpu_state[self._gpu_program_ref])


    def update_zoom_factor(self, newfactor):

        self.zoom_factor = newfactor

    def update_zoom_2(self, newfactor):

        self.zoom_2 *= newfactor

    def _set_data(self, x_extent, y_extent, max_norm=None):
        # x/y_extent : extent of arrows. Rperesented by a matrix.
        # Model bounds : the world coordinates of the box encompassing the arrows field.

        # Convert all vectors norms to [0,1]
        x = x_extent.data.copy()
        y = y_extent.data.copy()

        # calcul de la norme
        norms = np.sqrt(x ** 2 + y ** 2)
        # rechreche des éléments non nuls
        mask = norms > 0

        if max_norm is None:
            max_norm = np.max(norms)

        # adimensionnalisation des composantes
        x[mask] /= norms[mask]
        y[mask] /= norms[mask]

        # adimensionnalisation de la norme
        newnorms = norms[mask] / max_norm

        # déformation de 0-->1 vers min_size-->1
        newnorms += self.min_size*(1.-newnorms)

        # MAJ des composantes sur base de la norme ajustée
        x[mask] *= newnorms
        y[mask] *= newnorms

        # recherche du maximum
        if newnorms.size > 0:
            self.max_norm = np.max(newnorms)
        else:
            self.max_norm = 0

        # x[mask] += np.sign(x[mask])*self.min_size*(1.-norms[mask])
        # y[mask] += np.sign(y[mask])*self.min_size*(1.-norms[mask])

        # The goal is to make the arrow more legible.
        # We do this by transforming the norm from
        # [0,1] to [0.5,1] so that small arrows
        # appear bigger. Then we draw the arrows
        # in a size proportional to the norm.

        # # Move the norm to [0,0.5]
        # x = x / 2
        # y = y / 2

        # # Add a 0.5-normed vector in the direction of
        # # the (x,y) vector.
        # norms = np.sqrt(x ** 2 + y ** 2)

        # mask = norms > 0
        # # x[mask] += (x[mask] / norms[mask])*(1/(2*sqrt(2)))
        # # y[mask] += (y[mask] / norms[mask])*(1/(2*sqrt(2)))
        # x[mask] += (x[mask] / norms[mask])*.5
        # y[mask] += (y[mask] / norms[mask])*.5

        # Pack both extents into one texture
        data_for_gl = np.stack([x, y, np.zeros(x.shape)],axis=2)

        # Make sure OpenGL understands our data
        data_for_gl = data_for_gl.astype(dtype=np.float32)
        h, w, _ = data_for_gl.shape

        # Replace the previous texture if any
        if self._gl_texture is not None:
            glDeleteTextures(1,[self._gl_texture])

        self._gl_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self._gl_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        # Upload texture to GPU
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, w, h, 0, GL_RGB, GL_FLOAT, data_for_gl)

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):

        # bornes du bloc
        model_bounds = Rectangle(self._bounds[0][0],self._bounds[1][0],
                                    self._bounds[0][1]-self._bounds[0][0], self._bounds[1][1]-self._bounds[1][0])

        # zone visible
        view_bounds = Rectangle(xmin, ymin, xmax-xmin, ymax-ymin)

        # intersection des 2 zones
        inter = model_bounds.intersection(view_bounds)

        if inter is not None:
            # We clear the projection matrix because we will handle
            # the transformation ourselves.
            glMatrixMode(GL_PROJECTION)
            # glPushMatrix()

            glLoadIdentity()
            zmin, zmax = -99999, 99999
            pm = np.array([2/(xmax-xmin), 0.0, 0.0,  -(xmax+xmin)/(xmax-xmin),
                        0.0, 2/(ymax-ymin), 0.0,  -(ymax+ymin)/(ymax-ymin),
                        0.0, 0.0, -2/(zmax-zmin), -(zmax+zmin)/(zmax-zmin),
                        0.0, 0.0, 0.0,            1.0],
                       np.float32)

            # I wire the step size to the view size because it is independent
            # of the displayed bloc. If you wire to the model bounds, then the
            # grid density will change from one bloc to another, making compariosn
            # between arrow difficult inter-blockwise.

            # Read the GL viewport coordinates and size. (same as PyDraw.canvas.getsize())
            vp_data = (GLfloat * 4)()
            glGetFloatv(GL_VIEWPORT, vp_data)
            vp_width, vp_height = vp_data[2], vp_data[3]

            # Size of the arrow on screen (will be multiplied
            # by the norm of the vector which is in [0,1])
            # in normalized coordinates

            arrow_scale_x = self.arrow_pixel_size/vp_width
            arrow_scale_y = self.arrow_pixel_size/vp_height

            # The step is expressed in world coordinates
            #  evaluated as = world_length / pixels_length * araow_pixel_size --> arrow_world_size
            step_x = view_bounds.width   * arrow_scale_x
            step_y = view_bounds.height  * arrow_scale_y

            # The arrows average norm is smaller than 1. Therefore
            # if we'd use an arrow size eqaul to the norm, we'd
            # use only a portion of the area available to us
            # so we apply a zoom.
            # Don't forget that during the plot, there are also
            # various transformation done to make the norm
            # more "legible" through the arrows sizes.

            arrow_scale_x *= self.zoom_factor * self.zoom_2
            arrow_scale_y *= self.zoom_factor * self.zoom_2

            if step_x < self._dx:
                # Now we make sure that if the texels are big on the screen
                # then only one arrow is displayed for each of them.
                # arrow_scale_x = arrow_scale_x * self._dx / step_x
                step_x = self._dx
            elif step_x > self._dx:
                # But if the step is wider than a texel, then we need
                # to make sure each arrow is still rooted on the center
                # of a texel.
                step_x = round(step_x/self._dx)*self._dx

            if step_y < self._dy:
                # arrow_scale_y = arrow_scale_y * self._dy / step_y
                step_y = self._dy
            elif step_y > self._dy:
                step_y = round(step_y/self._dy)*self._dy

            nb_arrows_x = floor(inter.width  / step_x)
            nb_arrows_y = floor(inter.height / step_y)

            # These "x,y_base" computations ensure that model_bounds are
            # locked on a grid defined by the step size. This
            # ensures that all blocks (of the multi block results)
            # arrows are aligned.

            # We add dx, dy in the formula to make sure the arrows are in the center of the texels.
            # x_base = floor( floor(model_bounds.x/step_x)*step_x / self._dx) * self._dx + self._dx/2
            # y_base = floor( floor(model_bounds.y/step_y)*step_y / self._dy) * self._dy + self._dy/2
            x_base = model_bounds.x + self._dx/2
            y_base = model_bounds.y + self._dy/2

            gridded_inter = Rectangle(
                x=x_base + floor( (inter.x-x_base) / step_x) * step_x,
                y=y_base + floor( (inter.y-y_base) / step_y) * step_y ,
                width= nb_arrows_x * step_x,
                height= nb_arrows_y * step_y )

            #aspect_ratio = vp_width / vp_height
            self.update_geometry(model_bounds, gridded_inter, nb_arrows_x, nb_arrows_y,
                arrow_scale_x, arrow_scale_y, 1)
            self._plot(pm)

            if False and array.shape[0] > 2250:
                print(f"model:{model_bounds} // view:{view_bounds} // inter: {inter}")
                print(f"gridded inter: {gridded_inter} // nb_cells: {nb_arrows_x},{nb_arrows_y} // scale:{sx:.3f},{sy:.3f}")
                print(f"apsect ratio:{aspect_ratio:3f} viewport: {vp_width}x{vp_height}")

            # Restore the matrix so that next OpenGL programming in the caller is not
            # broken.
            glMatrixMode(GL_PROJECTION)
            # glPopMatrix()
            # glLoadIdentity()
            self.get_mapviewer()._set_gl_projection_matrix()

    def _plot(self, projection_matrix):
        assert self._gl_texture is not None, "Did you set the data ?"
        if self._gl_buffer == []:
            return

        self.mapviewer.SetCurrentContext()
        # We reuse the current model transformation matrix
        # as well the current viewport.

        program = _global_gpu_state[self._gpu_program_ref]
        glUseProgram(program)
        glBindTexture(GL_TEXTURE_2D, self._gl_texture)
        glActiveTexture(GL_TEXTURE0)
        glUniform1i( glGetUniformLocation(program, "sArrowsTexture2"), 0)

        glUniform1f( glGetUniformLocation(program, "to_tex_x_transl"), self._model_bounds.xmin)
        glUniform1f( glGetUniformLocation(program, "to_tex_x_scale"), 1.0/self._model_bounds.width)
        glUniform1f( glGetUniformLocation(program, "to_tex_y_transl"), self._model_bounds.ymin)
        glUniform1f( glGetUniformLocation(program, "to_tex_y_scale"), 1.0/self._model_bounds.height)

        glUniform2f( glGetUniformLocation(program, "screen_aspect_ratio"),
            self._arrow_scale_x, self._arrow_scale_y*self._aspect_ratio)

        glUniformMatrix4fv(glGetUniformLocation(program, "projection_matrix"), 1, GL_TRUE, projection_matrix)

        # Make sure polygons are filled (this is sometimes disabled
        # somewhere else in Wolf)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        cmo_aVertex = glGetAttribLocation(program, "aVertex")
        glEnableVertexAttribArray(cmo_aVertex)

        for buffer in self._gl_buffer:
            # Bind buffer first, will affect the behavior glVertexAttribPointer afterwards
            glBindBuffer(GL_ARRAY_BUFFER, buffer)
            # Bind to c_void_p(0) so that the buffer is used instead of cpu RAM
            glVertexAttribPointer(cmo_aVertex, 3, GL_FLOAT, normalized=GL_FALSE, stride=0, pointer=ctypes.c_void_p(0))
            glDrawArrays(GL_POINTS, 0, 64)

        # Don't pollute the rest of the application!
        glUseProgram(0)
        glDisable(GL_BLEND)


    def update_geometry(self, model_bounds: Rectangle, grid_bounds: Rectangle,
        nb_arrows_x: int, nb_arrows_y: int,
        arrow_scale_x: float, arrow_scale_y: float, aspect_ratio: float):
        """
        Model bounds: the coordinates of the full model we draw (world coord)
        Grid bounds : the coordinates over which the grid will be computed (world coord);
        nb_arrows: number of vector to plot in x/y dimension
        expected to be a subset of model bounds.
        arrow_scale : scale factor for arrows (expected to be used to maintain
        the arrow size constant on screen)
        aspect_ration: to adapt to screen's aspect ratio.
        """

        self._model_bounds = model_bounds
        self._arrow_scale_x = arrow_scale_x
        self._arrow_scale_y = arrow_scale_y
        self._aspect_ratio = aspect_ratio

        # Reminder: np.linspace(0,3,3) --> array([0. , 1.5, 3. ])
        grid_vertices = np.array(
            np.meshgrid(
                np.linspace(grid_bounds.xmin, grid_bounds.xmax, nb_arrows_x+1),
                np.linspace(grid_bounds.ymin, grid_bounds.ymax, nb_arrows_y+1),indexing='ij')).reshape(2,-1).transpose()
        # Give a zero z coordinate to each 2D points (making them 3D points)
        grid_vertices= np.hstack([grid_vertices,
            0.0 * np.ones((grid_vertices.shape[0],1))])
        grid_vertices= grid_vertices.flatten()
        grid_vertices= grid_vertices.astype(dtype=np.float32)  # Make it ready to be handled by OpenGL

        if self._gl_buffer:
            glDeleteBuffers( len(self._gl_buffer), self._gl_buffer)
            self._gl_buffer = []

        # FIXME subop)timal (bad understanding of GL/SL) => move that to
        # instanced rendering ?

        N = 64*3
        for i in range(0,grid_vertices.shape[0],N):
            subbuf = grid_vertices[i:min(grid_vertices.shape[0], i+N)]

            buffer = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, buffer)
            # ARRAY_BUFFER means vertex buffer
            # STATIC_DRAW: The data store contents will be modified once and used many times.
            glBufferData(GL_ARRAY_BUFFER, subbuf.nbytes, subbuf, GL_STATIC_DRAW)
            self._gl_buffer.append(buffer)
