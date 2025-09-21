# engine/camera.py
import glfw
import glm

from .config import *

class Camera:
    def __init__(self):
        self.pos = glm.vec3(CHUNK_SIZE * VIEW_DISTANCE_IN_CHUNKS / 2, WORLD_HEIGHT_LIMIT / 2 + 20.0, CHUNK_SIZE * VIEW_DISTANCE_IN_CHUNKS / 2)
        self.front = glm.vec3(0.0, 0.0, -1.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)
        
        self.first_mouse = True
        self.yaw = -90.0
        self.pitch = 0.0
        self.last_x = SCR_WIDTH / 2
        self.last_y = SCR_HEIGHT / 2

    def process_input(self, window, delta_time):
        camera_speed = 15.0 * delta_time
        if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS: self.pos += camera_speed * self.front
        if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS: self.pos -= camera_speed * self.front
        if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS: self.pos -= glm.normalize(glm.cross(self.front, self.up)) * camera_speed
        if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS: self.pos += glm.normalize(glm.cross(self.front, self.up)) * camera_speed
        if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS: self.pos += self.up * camera_speed
        if glfw.get_key(window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS: self.pos -= self.up * camera_speed

    def mouse_callback(self, window, xpos, ypos):
        if self.first_mouse:
            self.last_x, self.last_y = xpos, ypos
            self.first_mouse = False
        
        xoffset, yoffset = xpos - self.last_x, self.last_y - ypos
        self.last_x, self.last_y = xpos, ypos
        
        sensitivity = 0.1
        xoffset *= sensitivity
        yoffset *= sensitivity
        
        self.yaw += xoffset
        self.pitch += yoffset
        
        if self.pitch > 89.0: self.pitch = 89.0
        if self.pitch < -89.0: self.pitch = -89.0
        
        front = glm.vec3()
        front.x = glm.cos(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        front.y = glm.sin(glm.radians(self.pitch))
        front.z = glm.sin(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        self.front = glm.normalize(front)

    def get_view_matrix(self):
        return glm.lookAt(self.pos, self.pos + self.front, self.up)