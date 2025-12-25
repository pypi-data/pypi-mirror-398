#version 330 core

layout (lines) in;
layout (triangle_strip, max_vertices = 4) out;

uniform float gridSize;
uniform vec3 gridColor;

void main()
{
    vec4 lineStart = gl_in[0].gl_Position;
    vec4 lineEnd = gl_in[1].gl_Position;
    
    vec3 lineDir = normalize(lineEnd.xyz - lineStart.xyz);
    vec3 lineNormal = vec3(-lineDir.y, lineDir.x, 0.0);
    
    vec3 offset = gridSize * lineNormal;
    
    gl_Position = lineStart + vec4(offset, 0.0);
    EmitVertex();
    
    gl_Position = lineStart - vec4(offset, 0.0);
    EmitVertex();
    
    gl_Position = lineEnd + vec4(offset, 0.0);
    EmitVertex();
    
    gl_Position = lineEnd - vec4(offset, 0.0);
    EmitVertex();
    
    EndPrimitive();
}
