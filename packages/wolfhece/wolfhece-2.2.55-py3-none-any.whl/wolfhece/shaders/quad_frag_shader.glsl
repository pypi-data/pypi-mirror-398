#version 460 core

uniform vec3 sunPosition;
uniform float sunIntensity;

in vec4 gl_FragCoord ;
in vec3 Normal;
in vec3 ourColor;
in vec3 ourCoord;

layout(location=0) out vec4 FragColor;
layout(location=1) out vec4 CoordColor;

void main() {
    // Calculate the direction from the fragment position to the sun position
    vec3 sunDirection = normalize(vec4(sunPosition, 1.) - gl_FragCoord).xyz;

    // Calculate the dot product between the surface normal and the sun direction
    float lightIntensity = dot(Normal, sunDirection) * sunIntensity;

    // Calculate the reflection direction for specular lighting
    vec3 viewDirection = normalize(-gl_FragCoord.xyz);
    vec3 reflectionDirection = reflect(-sunDirection, Normal);

    // Calculate the specular intensity using the reflection direction
    float specularIntensity = pow(max(dot(reflectionDirection, viewDirection), 0.0), 32.0);

    // Apply the diffuse and specular intensities to the fragment color
    vec3 diffuseColor = lightIntensity * ourColor.rgb;
    vec3 specularColor = specularIntensity * vec3(1.0, 1.0, 1.0);
    FragColor = vec4(diffuseColor + specularColor, 1.0);
    CoordColor = vec4(ourCoord, 1.);
    
}
