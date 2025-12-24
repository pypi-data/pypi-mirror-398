
#version 330

in vec3 in_vert;
in vec3 in_color;
in vec3 in_normal;

out vec3 frag_pos;
out vec3 frag_normal;
out vec3 frag_color;
out vec4 frag_pos_light_space;

uniform mat4 mvp;
uniform mat4 model;
uniform mat4 light_space_matrix;

void main() {
    vec4 world_pos = model * vec4(in_vert, 1.0);
    frag_pos = world_pos.xyz;
    frag_normal = mat3(transpose(inverse(model))) * in_normal;
    frag_color = in_color;
    frag_pos_light_space = light_space_matrix * world_pos;
    gl_Position = mvp * vec4(in_vert, 1.0);
}
