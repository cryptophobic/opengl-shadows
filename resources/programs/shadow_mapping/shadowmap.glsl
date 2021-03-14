#version 330

#if defined VERTEX_SHADER

uniform mat4 m_model;

in vec3 in_position;

uniform mat4 mvp;

void main() {
    gl_Position = mvp * m_model * vec4(in_position, 1.0);
//
//    gl_Position = mvp * vec4(in_position, 1.0);
}

#endif
