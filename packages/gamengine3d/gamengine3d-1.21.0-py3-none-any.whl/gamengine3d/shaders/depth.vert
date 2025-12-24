#version 330

layout(location = 0) in vec3 in_vert;
uniform mat4 light_space_matrix;
uniform mat4 model;

void main() {
    gl_Position = light_space_matrix * model * vec4(in_vert, 1.0);
}
