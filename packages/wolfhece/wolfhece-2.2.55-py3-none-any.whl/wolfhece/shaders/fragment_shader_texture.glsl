#version 460

    in vec2 OutTexCoords;

    out vec4 outColor;
    uniform sampler2D samplerTex;

void main() {

    outColor = texture(samplerTex, OutTexCoords);

}