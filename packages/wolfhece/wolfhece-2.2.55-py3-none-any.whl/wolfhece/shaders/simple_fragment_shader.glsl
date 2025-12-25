#version 460 core
in vec3 ourColor;
out vec4 FragColor;

out vec2 FragCoord;

void main()
{
    FragColor = vec4(ourColor, 1.0);
    FragCoord = gl_FragCoord.xy;
}