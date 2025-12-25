#version 460 core
layout (location = 0) in vec2 aVertex;
layout (location = 1) in vec3 aColor;

out vec3 ourColor;

uniform mat4 modelview;
uniform mat4 projection;

void main()
{
    gl_Position = projection * modelview * vec4(aVertex, 0.0, 1.0);
    ourColor = aColor;
}