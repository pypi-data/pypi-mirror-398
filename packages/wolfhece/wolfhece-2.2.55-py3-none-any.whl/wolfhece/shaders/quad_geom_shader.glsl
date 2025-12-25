#version 460 core

layout (points) in;
layout (triangle_strip, max_vertices = 20) out;

uniform sampler2DRect zText;
uniform float zScale;
uniform float dx;
uniform float dy;
uniform float origx;
uniform float origy;
uniform float width;
uniform float height;
uniform mat4 mvp;
uniform int idx;

uniform sampler1D colorPalette;  // Texture de gradient représentant la palette de couleurs

uniform int paletteSize;  // Taille de la palette
uniform float colorValues[256];  // Tableau de couleurs de la palette

out vec3 ourColor;
out vec3 Normal;   // Normale du fragment dans l'espace du monde
out vec4 FragPos;  // Position du fragment dans l'espace du monde
out vec3 ourCoord;

vec3 mapColor(float zValue) {
    float zColor = 0.0;

    // Mapper la valeur sur base d'intervalles
    if (zValue <= colorValues[0]) {
        zColor = 0.0;
    }
    else if (zValue >= colorValues[paletteSize-1]) {
        zColor = 1.0;
    }
    else {
        for (int i = 1; i < paletteSize; i++) {
        if (zValue <= colorValues[i]) {
            float lower = colorValues[i-1];
            float upper = colorValues[i];

            zColor = ((zValue - lower) / (upper - lower) + float(i-1)) / float(paletteSize-1);

            break;
        }
        }
    }

    // Interpoler entre les couleurs dans la palette
    return texture(colorPalette, zColor).rgb;
}

float get_value(sampler2DRect tex, vec2 pos) {

    float posx = (pos.x - origx) / dx;
    float posy = (pos.y - origy) / dy;

    //vec2 texCoord = vec2(posx, posy);
    vec2 texCoord = vec2(posy, posx);

    float zValue = texture(tex, texCoord).r * zScale;
    return zValue;
}

void horizontal(){

    float halfdx = dx/2.0;
    float halfdy = dy/2.0;

    float zValue = get_value(zText, gl_in[0].gl_Position.xy);
    float zColor = 0.0;

    vec3 color = mapColor(zValue);

    float posx = (gl_in[0].gl_Position.x - origx) / dx ;// /width;
    float posy = (gl_in[0].gl_Position.y - origy) / dy ;// /height;
    ourCoord = vec3(posx, posy, idx);

    gl_Position = mvp * vec4(gl_in[0].gl_Position.x - halfdx, gl_in[0].gl_Position.y - halfdy, zValue, 1.0);
    ourColor = color;
    Normal = vec3(0.0, 0.0, 1.0);
    FragPos = vec4(gl_in[0].gl_Position.x - halfdx, gl_in[0].gl_Position.y - halfdy, zValue, 1.0);
    EmitVertex();

    gl_Position = mvp * vec4(gl_in[0].gl_Position.x + halfdx, gl_in[0].gl_Position.y - halfdy, zValue, 1.0);
    ourColor = color;
    Normal = vec3(0.0, 0.0, 1.0);
    FragPos = vec4(gl_in[0].gl_Position.x + halfdx, gl_in[0].gl_Position.y - halfdy, zValue, 1.0);
    EmitVertex();

    gl_Position = mvp * vec4(gl_in[0].gl_Position.x - halfdx, gl_in[0].gl_Position.y + halfdy, zValue, 1.0);
    ourColor = color;
    Normal = vec3(0.0, 0.0, 1.0);
    FragPos = vec4(gl_in[0].gl_Position.x - halfdx, gl_in[0].gl_Position.y + halfdy, zValue, 1.0);
    EmitVertex();

    gl_Position = mvp * vec4(gl_in[0].gl_Position.x + halfdx, gl_in[0].gl_Position.y + halfdy, zValue, 1.0);
    ourColor = color;
    Normal = vec3(0.0, 0.0, 1.0);
    FragPos = vec4(gl_in[0].gl_Position.x + halfdx, gl_in[0].gl_Position.y + halfdy, zValue, 1.0);
    EmitVertex();

    EndPrimitive();

}

void walls(){

    float halfdx = dx/2.0;
    float halfdy = dy/2.0;

    vec2 posCenter = gl_in[0].gl_Position.xy;
    vec2 posLeft   = vec2(posCenter.x - dx, posCenter.y);
    vec2 posRight  = vec2(posCenter.x + dx, posCenter.y);
    vec2 posUp     = vec2(posCenter.x     , posCenter.y + dy);
    vec2 posDown   = vec2(posCenter.x     , posCenter.y - dy);

    vec2 texCenter = vec2(((posCenter.x - origx) / dx ), ((posCenter.y - origy) / dy));
    vec2 texLeft = vec2(((posLeft.x - origx) / dx ), ((posLeft.y - origy) / dy));
    vec2 texRight = vec2(((posRight.x - origx) / dx ), ((posRight.y - origy) / dy));
    vec2 texUp = vec2(((posUp.x - origx) / dx ), ((posUp.y - origy) / dy));
    vec2 texDown = vec2(((posDown.x - origx) / dx ), ((posDown.y - origy) / dy));

    // float zCenter = texture(zText, texCenter).r * zScale;
    // float zLeft = texture(zText, texLeft).r * zScale;
    // float zRight = texture(zText, texRight).r * zScale;
    // float zUp = texture(zText, texUp).r * zScale;
    // float zDown = texture(zText, texDown).r * zScale;

    float zCenter = get_value(zText, posCenter);
    float zLeft = get_value(zText, posLeft);
    float zRight = get_value(zText, posRight);
    float zUp = get_value(zText, posUp);
    float zDown = get_value(zText, posDown);

    if (zCenter > zLeft) {
        gl_Position = mvp * vec4(posCenter.x - halfdx, posCenter.y - halfdy, zCenter, 1.0);
        ourColor = mapColor(zCenter);
        Normal = vec3(-1.0, 0.0, 0.0);
        FragPos = vec4(posCenter.x - halfdx, posCenter.y - halfdy, zCenter, 1.0);
        EmitVertex();

        gl_Position = mvp * vec4(posCenter.x - halfdx, posCenter.y + halfdy, zCenter, 1.0);
        ourColor = mapColor(zCenter);
        Normal = vec3(-1.0, 0.0, 0.0);
        FragPos = vec4(posCenter.x - halfdx, posCenter.y + halfdy, zCenter, 1.0);
        EmitVertex();

        gl_Position = mvp * vec4(posCenter.x - halfdx, posCenter.y - halfdy, zLeft, 1.0);
        ourColor = mapColor(zLeft);
        Normal = vec3(-1.0, 0.0, 0.0);
        FragPos = vec4(posCenter.x - halfdx, posCenter.y - halfdy, zLeft, 1.0);
        EmitVertex();

        gl_Position = mvp * vec4(posCenter.x - halfdx, posCenter.y + halfdy, zLeft, 1.0);
        ourColor = mapColor(zLeft);
        Normal = vec3(-1.0, 0.0, 0.0);
        FragPos = vec4(posCenter.x - halfdx, posCenter.y + halfdy, zLeft, 1.0);
        EmitVertex();

        EndPrimitive();
    }

    if (zCenter > zRight) {
        gl_Position = mvp * vec4(posCenter.x + halfdx, posCenter.y - halfdy, zCenter, 1.0);
        ourColor = mapColor(zCenter);
        Normal = vec3(1.0, 0.0, 0.0);
        FragPos = vec4(posCenter.x + halfdx, posCenter.y - halfdy, zCenter, 1.0);
        EmitVertex();

        gl_Position = mvp * vec4(posCenter.x + halfdx, posCenter.y + halfdy, zCenter, 1.0);
        ourColor = mapColor(zCenter);
        Normal = vec3(1.0, 0.0, 0.0);
        FragPos = vec4(posCenter.x + halfdx, posCenter.y + halfdy, zCenter, 1.0);
        EmitVertex();

        gl_Position = mvp * vec4(posCenter.x + halfdx, posCenter.y - halfdy, zRight, 1.0);
        ourColor = mapColor(zRight);
        Normal = vec3(1.0, 0.0, 0.0);
        FragPos = vec4(posCenter.x + halfdx, posCenter.y - halfdy, zRight, 1.0);
        EmitVertex();

        gl_Position = mvp * vec4(posCenter.x + halfdx, posCenter.y + halfdy, zRight, 1.0);
        ourColor = mapColor(zRight);
        Normal = vec3(1.0, 0.0, 0.0);
        FragPos = vec4(posCenter.x + halfdx, posCenter.y + halfdy, zRight, 1.0);
        EmitVertex();

        EndPrimitive();
    }

    if (zCenter > zUp) {
        gl_Position = mvp * vec4(posCenter.x - halfdx, posCenter.y + halfdy, zCenter, 1.0);
        ourColor = mapColor(zCenter);
        Normal = vec3(0.0, 1.0, 0.0);
        FragPos = vec4(posCenter.x - halfdx, posCenter.y + halfdy, zCenter, 1.0);
        EmitVertex();

        gl_Position = mvp * vec4(posCenter.x + halfdx, posCenter.y + halfdy, zCenter, 1.0);
        ourColor = mapColor(zCenter);
        Normal = vec3(0.0, 1.0, 0.0);
        FragPos = vec4(posCenter.x + halfdx, posCenter.y + halfdy, zCenter, 1.0);
        EmitVertex();

        gl_Position = mvp * vec4(posCenter.x - halfdx, posCenter.y + halfdy, zUp, 1.0);
        ourColor = mapColor(zUp);
        Normal = vec3(0.0, 1.0, 0.0);
        FragPos = vec4(posCenter.x - halfdx, posCenter.y + halfdy, zUp, 1.0);
        EmitVertex();

        gl_Position = mvp * vec4(posCenter.x + halfdx, posCenter.y + halfdy, zUp, 1.0);
        ourColor = mapColor(zUp);
        Normal = vec3(0.0, 1.0, 0.0);
        FragPos = vec4(posCenter.x + halfdx, posCenter.y + halfdy, zUp, 1.0);
        EmitVertex();

        EndPrimitive();
    }

    if (zCenter > zDown) {
        gl_Position = mvp * vec4(posCenter.x - halfdx, posCenter.y - halfdy, zCenter, 1.0);
        ourColor = mapColor(zCenter);
        Normal = vec3(0.0, -1.0, 0.0);
        FragPos = vec4(posCenter.x - halfdx, posCenter.y - halfdy, zCenter, 1.0);
        EmitVertex();

        gl_Position = mvp * vec4(posCenter.x + halfdx, posCenter.y - halfdy, zCenter, 1.0);
        ourColor = mapColor(zCenter);
        Normal = vec3(0.0, -1.0, 0.0);
        FragPos = vec4(posCenter.x + halfdx, posCenter.y - halfdy, zCenter, 1.0);
        EmitVertex();

        gl_Position = mvp * vec4(posCenter.x - halfdx, posCenter.y - halfdy, zDown, 1.0);
        ourColor = mapColor(zDown);
        Normal = vec3(0.0, -1.0, 0.0);
        FragPos = vec4(posCenter.x - halfdx, posCenter.y - halfdy, zDown, 1.0);
        EmitVertex();

        gl_Position = mvp * vec4(posCenter.x + halfdx, posCenter.y - halfdy, zDown, 1.0);
        ourColor = mapColor(zDown);
        Normal = vec3(0.0, -1.0, 0.0);
        FragPos = vec4(posCenter.x + halfdx, posCenter.y - halfdy, zDown, 1.0);
        EmitVertex();

        EndPrimitive();
    }


}


void main() {

    horizontal();
    walls();


}
