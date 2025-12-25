"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wx
import numpy as np
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective, gluOrtho2D

vertex_shader_source = """
#version 460 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;
layout(location = 2) in vec3 color;

out vec3 FragPos;
out vec3 Normal;
out vec3 Color;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    FragPos = vec3(model * vec4(position, 1.0));
    Normal = mat3(transpose(inverse(model))) * normal;
    Color = color;
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
"""

vertex_shader_source = """
#version 460 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;
layout(location = 2) in vec3 color;

out vec3 FragPos;
out vec3 Normal;
out vec3 Color;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

uniform float pointSize;

void main()
{
    FragPos = vec3(model * vec4(position, 1.0));
    Normal = mat3(transpose(inverse(model))) * normal;
    Color = color;
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
"""

geometry_shader_source="""
#version 460 core

layout (points) in;
layout (triangle_strip, max_vertices = 4) out;

in vec3 FragPos[];
in vec3 Normal[];
in vec3 Color[];

out vec3 FragPosWorld;
out vec3 NormalWorld;
out vec3 FragColor;

uniform float pointSize;

void main()
{
    float halfSize = pointSize * 0.5;

    for (int i = 0; i < 4; ++i)
    {
        FragPosWorld = FragPos[0];
        NormalWorld = Normal[0];
        FragColor = Color[0];

        gl_Position = gl_in[0].gl_Position + vec4(
            (i == 0 || i == 1) ? -halfSize : halfSize,
            (i == 0 || i == 2) ? -halfSize : halfSize,
            0.0, 0.0);

        EmitVertex();
    }

    EndPrimitive();
}

"""

fragment_shader_source = """
#version 460 core

in vec3 FragPosWorld;
in vec3 NormalWorld;
in vec3 FragColor;

out vec4 FragColorOutput;

uniform float metallic;
uniform float roughness;

void main()
{
    vec3 viewDir = normalize(-FragPosWorld);
    vec3 normal = normalize(NormalWorld);

    vec3 lightDir = normalize(vec3(1.0, 1.0, 1.0));
    vec3 halfwayDir = normalize(lightDir + viewDir);

    float NdotL = max(dot(normal, lightDir), 0.0);
    float NdotH = max(dot(normal, halfwayDir), 0.0);
    float VdotH = max(dot(viewDir, halfwayDir), 0.0);

    float roughnessSquared = roughness * roughness;
    float denom = (roughnessSquared * NdotH * NdotH + VdotH * VdotH);

    float D = (roughnessSquared) / (denom * denom * 3.14159265 * 3.14159265);

    // Calcul de la réflectance spéculaire F0
    vec3 F0 = (1.0 - metallic) * vec3(0.04) + metallic * FragColor;

    // Correction de la composante spéculaire
    vec3 kS = F0;
    vec3 kD = 1.0 - kS;
    vec3 F = kS + (1.0 - kS) * pow(1.0 - VdotH, 5.0);

    vec3 specular = F * D;

    vec3 diffuse = FragColor / 3.14159265;

    FragColorOutput = vec4(diffuse + specular, 1.0);
}
"""

class MyGLCanvas(glcanvas.GLCanvas):
    def __init__(self, parent, point_size, points, normals, colors, metallic, roughness):
        glcanvas.GLCanvas.__init__(self, parent, -1, size=(800, 600))

        self.context = glcanvas.GLContext(self)
        self.shader_program = None
        self.point_size = point_size
        self.points = points.astype(np.float32)
        self.normals = normals.astype(np.float32)
        self.colors = colors.astype(np.float32)
        self.metallic = metallic
        self.roughness = roughness

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)

        self.SetCurrent(self.context)
        self.InitShaderProgram()
        self.SetupBuffers()

        self.mouse_x = 0
        self.mouse_y = 0
        self.zoom_factor = 1.0

    def InitShaderProgram(self):
        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex_shader, vertex_shader_source)
        glCompileShader(vertex_shader)
        if glGetShaderiv(vertex_shader, GL_COMPILE_STATUS) != GL_TRUE:
            raise RuntimeError("Vertex shader compilation failed")

        geometry_shader = glCreateShader(GL_GEOMETRY_SHADER)
        glShaderSource(geometry_shader, geometry_shader_source)
        glCompileShader(geometry_shader)
        if glGetShaderiv(geometry_shader, GL_COMPILE_STATUS) != GL_TRUE:
            raise RuntimeError("Geometry shader compilation failed")

        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, fragment_shader_source)
        glCompileShader(fragment_shader)
        if glGetShaderiv(fragment_shader, GL_COMPILE_STATUS) != GL_TRUE:
            raise RuntimeError("Fragment shader compilation failed")

        self.shader_program = glCreateProgram()
        glAttachShader(self.shader_program, vertex_shader)
        glAttachShader(self.shader_program, geometry_shader)
        glAttachShader(self.shader_program, fragment_shader)
        glLinkProgram(self.shader_program)

        if glGetProgramiv(self.shader_program, GL_LINK_STATUS) != GL_TRUE:
            raise RuntimeError("Shader program linking failed")

        glDeleteShader(vertex_shader)
        glDeleteShader(geometry_shader)
        glDeleteShader(fragment_shader)

    def SetupBuffers(self):
        self.points_buffer = glGenBuffers(1)
        self.normals_buffer = glGenBuffers(1)
        self.colors_buffer = glGenBuffers(1)

        glBindBuffer(GL_ARRAY_BUFFER, self.points_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.points, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        glBindBuffer(GL_ARRAY_BUFFER, self.normals_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.normals, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        glBindBuffer(GL_ARRAY_BUFFER, self.colors_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.colors, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def OnPaint(self, event):
        self.SetCurrent(self.context)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glUseProgram(self.shader_program)

        model_loc = glGetUniformLocation(self.shader_program, "model")
        view_loc = glGetUniformLocation(self.shader_program, "view")
        projection_loc = glGetUniformLocation(self.shader_program, "projection")
        point_size_loc = glGetUniformLocation(self.shader_program, "pointSize")
        metallic_loc = glGetUniformLocation(self.shader_program, "metallic")
        roughness_loc = glGetUniformLocation(self.shader_program, "roughness")

        glUniformMatrix4fv(model_loc, 1, GL_TRUE, np.identity(4, dtype=np.float32))
        view_matrix = self.GetViewMatrix()
        # view_matrix = np.identity(4, dtype=np.float32)
        glUniformMatrix4fv(view_loc, 1, GL_FALSE, view_matrix)
        glUniformMatrix4fv(projection_loc, 1, GL_FALSE, np.identity(4, dtype=np.float32))
        glUniform1f(point_size_loc, self.point_size)
        glUniform1f(metallic_loc, self.metallic)
        glUniform1f(roughness_loc, self.roughness)

        glBindBuffer(GL_ARRAY_BUFFER, self.points_buffer)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        glBindBuffer(GL_ARRAY_BUFFER, self.normals_buffer)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)

        glBindBuffer(GL_ARRAY_BUFFER, self.colors_buffer)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 0, None)

        glDrawArrays(GL_POINTS, 0, len(self.points))

        glDisableVertexAttribArray(0)
        glDisableVertexAttribArray(1)
        glDisableVertexAttribArray(2)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        glUseProgram(0)

        self.SwapBuffers()

    def OnSize(self, event):
        size = self.GetClientSize()

        self.SetCurrent(self.context)
        glViewport(0, 0, size.width, size.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (size.width / size.height), 0.1, 50.0)
        # gluOrtho2D(0, size.width, 0, size.height)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        self.Refresh()

    def OnMouse(self, event):
        if event.Dragging():
            self.SetCurrent(self.context)
            delta_x = event.GetX() - self.mouse_x
            delta_y = event.GetY() - self.mouse_y

            view_matrix = self.GetViewMatrix()
            translation_matrix = np.identity(4, dtype=np.float32)
            translation_matrix[3, 0] = -delta_x * 0.01
            translation_matrix[3, 1] = delta_y * 0.01

            new_view_matrix = np.dot(view_matrix, translation_matrix)

            # new_view_matrix = translation_matrix

            glUseProgram(self.shader_program)
            view_loc = glGetUniformLocation(self.shader_program, "view")
            glUniformMatrix4fv(view_loc, 1, GL_FALSE, new_view_matrix)
            glUseProgram(0)

            self.Refresh()

        elif event.GetWheelRotation() > 0:
            self.zoom_factor *= 1.1
            self.Refresh()
        elif event.GetWheelRotation() < 0:
            self.zoom_factor /= 1.1
            self.Refresh()

        self.mouse_x = event.GetX()
        self.mouse_y = event.GetY()

    def GetViewMatrix(self):
        view_matrix = np.identity(4, dtype=np.float32)
        # view_matrix[2, 2] = 1.0  # Move the camera back along the z-axis
        view_matrix = np.dot(view_matrix, self.GetRotationMatrix())
        view_matrix[3, 2] = -self.zoom_factor

        return view_matrix

    def GetRotationMatrix(self):
        rotation_matrix = np.identity(4, dtype=np.float32)

        # Calculate the rotation angles based on mouse movement
        rotation_x = (self.mouse_y - self.GetClientSize().height / 2) * 0.01
        rotation_y = (self.mouse_x - self.GetClientSize().width / 2) * 0.01

        # Apply the rotation around the x-axis
        rotation_matrix[1, 1] = np.cos(rotation_x)
        rotation_matrix[1, 2] = -np.sin(rotation_x)
        rotation_matrix[2, 1] = np.sin(rotation_x)
        rotation_matrix[2, 2] = np.cos(rotation_x)

        # Apply the rotation around the y-axis
        rotation_matrix[0, 0] = np.cos(rotation_y)
        rotation_matrix[0, 2] = np.sin(rotation_y)
        rotation_matrix[2, 0] = -np.sin(rotation_y)
        rotation_matrix[2, 2] = np.cos(rotation_y)

        return rotation_matrix

    def __del__(self):
        glDeleteBuffers(1, [self.points_buffer, self.normals_buffer, self.colors_buffer])

class MyFrame(wx.Frame):
    def __init__(self, parent, title, point_size, points, normals, colors, metallic, roughness):
        wx.Frame.__init__(self, parent, title=title, size=(800, 600))
        self.canvas = MyGLCanvas(self, point_size, points, normals, colors, metallic, roughness)
        self.Show()

if __name__ == '__main__':
    app = wx.App(False)
    
    # Créez des données factices pour tester
    points = np.random.rand(100, 3) * 1.0 - .5
    normals = np.random.rand(100, 3)
    colors = np.random.rand(100, 3)
    metallic = 0.5
    roughness = 0.3
    
    frame = MyFrame(None, "wxPython PBR with Glossiness", point_size=0.02, points=points, normals=normals, colors=colors, metallic=metallic, roughness=roughness)
    app.MainLoop()
