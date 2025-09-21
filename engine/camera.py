# engine/camera.py
import glfw
import glm
from .config import *

class Camera:
    def __init__(self):
        self.pos = glm.vec3(0)
        self.front = glm.vec3(0.0, 0.0, -1.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)
        
        self.first_mouse = True
        self.yaw = -90.0
        self.pitch = 0.0
        self.last_x = SCR_WIDTH / 2
        self.last_y = SCR_HEIGHT / 2
    
    # Метод process_input УДАЛЁН из камеры

    def update(self, player_position):
        # Позиция камеры = позиция ног игрока + 1.6м по вертикали (уровень глаз)
        self.pos = player_position + glm.vec3(0, 1.6, 0)

    def mouse_callback(self, window, xpos, ypos):
        if self.first_mouse: self.last_x, self.last_y, self.first_mouse = xpos, ypos, False
        xoffset = xpos - self.last_x
        yoffset = self.last_y - ypos
        self.last_x, self.last_y = xpos, ypos
        sensitivity = 0.1; xoffset *= sensitivity; yoffset *= sensitivity
        self.yaw += xoffset; self.pitch += yoffset
        if self.pitch > 89.0: self.pitch = 89.0
        if self.pitch < -89.0: self.pitch = -89.0
        front = glm.vec3(); front.x = glm.cos(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch)); front.y = glm.sin(glm.radians(self.pitch)); front.z = glm.sin(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        self.front = glm.normalize(front)

    def get_view_matrix(self):
        return glm.lookAt(self.pos, self.pos + self.front, self.up)