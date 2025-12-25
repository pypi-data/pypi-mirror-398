#version 460 core

layout (points) in;
layout (triangle_strip, max_vertices = 20) out;

uniform sampler2DRect zText;
uniform float zScale;
uniform float dx;
uniform float dy;
uniform float origx;
uniform float origy;
uniform mat4 mvp;

uniform sampler1D colorPalette;  // Texture de gradient représentant la palette de couleurs

uniform int paletteSize;  // Taille de la palette
uniform float colorValues[256];  // Tableau de couleurs de la palette

out vec3 ourColor;
out vec4 FragPos;  // Position du fragment dans l'espace du monde


float get_value(sampler2DRect tex, vec2 pos) {

    float posx = (pos.x - origx) / dx;
    float posy = (pos.y - origy) / dy;

    vec2 texCoord = vec2(posx, posy);

    float zValue = texture(tex, texCoord).r * zScale;
    return zValue;
}

void horizontal(){

    float halfdx = dx/2.0;
    float halfdy = dy/2.0;

    float zValue = get_value(zText, gl_in[0].gl_Position.xy);
    float zColor = 0.0;

    // float posx = (gl_in[0].gl_Position.x - origx) / dx;
    // float posy = (gl_in[0].gl_Position.y - origy) / dy;
    float posx = 1.;
    float posy = 1.;

    gl_Position = mvp * vec4(gl_in[0].gl_Position.x - halfdx, gl_in[0].gl_Position.y - halfdy, zValue, 1.0);
    ourColor = vec3(1.,0.,0.);
    FragPos = vec4(gl_in[0].gl_Position.x - halfdx, gl_in[0].gl_Position.y - halfdy, zValue, 1.0);
    EmitVertex();

    gl_Position = mvp * vec4(gl_in[0].gl_Position.x + halfdx, gl_in[0].gl_Position.y - halfdy, zValue, 1.0);
    ourColor = vec3(0.,1.,0.);
    FragPos = vec4(gl_in[0].gl_Position.x + halfdx, gl_in[0].gl_Position.y - halfdy, zValue, 1.0);
    EmitVertex();

    gl_Position = mvp * vec4(gl_in[0].gl_Position.x - halfdx, gl_in[0].gl_Position.y + halfdy, zValue, 1.0);
    ourColor = vec3(0.,0.,1.);
    FragPos = vec4(gl_in[0].gl_Position.x - halfdx, gl_in[0].gl_Position.y + halfdy, zValue, 1.0);
    EmitVertex();

    gl_Position = mvp * vec4(gl_in[0].gl_Position.x + halfdx, gl_in[0].gl_Position.y + halfdy, zValue, 1.0);
    ourColor = vec3(1.,0.,0.);
    FragPos = vec4(gl_in[0].gl_Position.x + halfdx, gl_in[0].gl_Position.y + halfdy, zValue, 1.0);
    EmitVertex();

    EndPrimitive();

}


void main() {

    horizontal();

}
