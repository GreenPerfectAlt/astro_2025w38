# engine/graphics.py
import glm

vertex_shader_source = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec3 aColor;
out vec3 FragPos;
out vec3 Normal;
out vec3 Color;
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
void main() {
    FragPos = vec3(model * vec4(aPos, 1.0));
    Normal = mat3(transpose(inverse(model))) * aNormal;
    Color = aColor;
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
"""
fragment_shader_source = """
#version 330 core
out vec4 FragColor;
in vec3 FragPos;
in vec3 Normal;
in vec3 Color;
uniform vec3 lightColor;
uniform vec3 lightPos;
uniform vec3 viewPos;
void main() {
    float ambientStrength = 0.3;
    vec3 ambient = ambientStrength * lightColor;
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(lightPos - FragPos);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * lightColor;
    vec3 result = (ambient + diffuse) * Color;
    FragColor = vec4(result, 1.0);
}
"""
class Frustum:
    def __init__(self):
        self.planes = [glm.vec4(0.0) for _ in range(6)]
    def update(self, projection_matrix, view_matrix):
        vp_matrix = glm.transpose(projection_matrix * view_matrix)
        self.planes[0] = vp_matrix[3] + vp_matrix[0]; self.planes[1] = vp_matrix[3] - vp_matrix[0]
        self.planes[2] = vp_matrix[3] + vp_matrix[1]; self.planes[3] = vp_matrix[3] - vp_matrix[1]
        self.planes[4] = vp_matrix[3] + vp_matrix[2]; self.planes[5] = vp_matrix[3] - vp_matrix[2]
        for i in range(6):
            try: self.planes[i] /= glm.length(glm.vec3(self.planes[i]))
            except ZeroDivisionError: pass
    def is_box_in_frustum(self, box_center, box_size):
        for i in range(6):
            plane = self.planes[i]
            dist = plane.x * box_center.x + plane.y * box_center.y + plane.z * box_center.z + plane.w
            if dist < -box_size: return False
        return True