# engine/graphics.py
import glm

# --- Шейдеры (без изменений) ---
vertex_shader_source = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aColor;
out vec3 ourColor;
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
void main() {
    gl_Position = projection * view * model * vec4(aPos, 1.0);
    ourColor = aColor;
}
"""
fragment_shader_source = """
#version 330 core
out vec4 FragColor;
in vec3 ourColor;
void main() { FragColor = vec4(ourColor, 1.0f); }
"""

# --- Класс Frustum (ИСПРАВЛЕН) ---
class Frustum:
    def __init__(self):
        self.planes = [glm.vec4(0.0) for _ in range(6)]

    def update(self, projection_matrix, view_matrix):
        # !!! КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Транспонируем матрицу !!!
        vp_matrix = glm.transpose(projection_matrix * view_matrix)
        
        self.planes[0] = vp_matrix[3] + vp_matrix[0] # Левая
        self.planes[1] = vp_matrix[3] - vp_matrix[0] # Правая
        self.planes[2] = vp_matrix[3] + vp_matrix[1] # Нижняя
        self.planes[3] = vp_matrix[3] - vp_matrix[1] # Верхняя
        self.planes[4] = vp_matrix[3] + vp_matrix[2] # Ближняя
        self.planes[5] = vp_matrix[3] - vp_matrix[2] # Дальняя
        
        for i in range(6):
            # Нормализуем плоскость
            try:
                self.planes[i] /= glm.length(glm.vec3(self.planes[i]))
            except ZeroDivisionError:
                # В редких случаях нормаль может быть нулевой, избегаем падения
                pass


    def is_box_in_frustum(self, box_center, box_size):
        for i in range(6):
            plane = self.planes[i]
            dist = plane.x * box_center.x + plane.y * box_center.y + plane.z * box_center.z + plane.w
            if dist < -box_size:
                return False
        return True