#version 460

in vec3 aPos;
in vec2 InTexCoords;

out vec2 OutTexCoords;

uniform mat4 transform;

void main() {

    gl_Position = transform * vec4(aPos, 1.0f);
    OutTexCoords = InTexCoords;

    }