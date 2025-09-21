# engine/player.py
import glfw
import glm
from .config import *
import math

class Player:
    def __init__(self, position):
        self.position = position
        self.velocity = glm.vec3(0, 0, 0)
        self.width = 0.6
        self.height = 1.8
        self.on_ground = False
        self.gravity = 28.0
        self.jump_speed = 9.0

    def update(self, delta_time, world):
        # 1. Обрабатываем движение по горизонтали
        # (Мы делаем это до гравитации, чтобы определить, куда мы хотим двигаться)
        # self.velocity.x и self.velocity.z устанавливаются в process_input
        
        # 2. Применяем гравитацию
        if not self.on_ground:
            self.velocity.y -= self.gravity * delta_time

        # 3. Рассчитываем предполагаемую следующую позицию
        next_pos = self.position + self.velocity * delta_time

        # 4. Проверяем столкновения с миром и корректируем позицию
        self.resolve_collisions(next_pos, world)

    def resolve_collisions(self, next_pos, world):
        # --- Проверка по Y (падение / стояние на земле) ---
        
        # Получаем координаты 4-х углов "подошвы" игрока
        half_w = self.width / 2
        corners = [
            (next_pos.x - half_w, next_pos.z - half_w),
            (next_pos.x + half_w, next_pos.z - half_w),
            (next_pos.x - half_w, next_pos.z + half_w),
            (next_pos.x + half_w, next_pos.z + half_w)
        ]

        # Изначально считаем, что мы в воздухе
        self.on_ground = False
        
        # Проверяем, не проваливаемся ли мы
        if self.velocity.y <= 0:
            for x, z in corners:
                # Находим, на какой высоте находится земля в этой точке
                ix, iz = math.floor(x), math.floor(z)
                ground_y = -1
                for y_check in range(math.floor(next_pos.y + self.height), -1, -1):
                    if world.get_block(ix, y_check, iz) != 0:
                        ground_y = y_check + 1
                        break
                
                # Если под этим углом есть земля и мы в неё провалились...
                if ground_y != -1 and next_pos.y < ground_y:
                    # ...то ставим игрока на эту землю и останавливаем падение.
                    next_pos.y = ground_y
                    self.velocity.y = 0
                    self.on_ground = True
                    break # Прекращаем проверку, мы нашли опору
        
        # (Здесь в будущем будет проверка столкновений со стенами по X и Z)

        # Применяем финальную, скорректированную позицию
        self.position = next_pos


    def process_input(self, window, camera_front):
        speed = 5.0
        right = glm.normalize(glm.cross(camera_front, glm.vec3(0, 1, 0)))
        forward = glm.normalize(glm.cross(glm.vec3(0, 1, 0), right))
        
        move_direction = glm.vec3(0)
        if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS: move_direction += forward
        if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS: move_direction -= forward
        if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS: move_direction -= right
        if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS: move_direction += right
            
        # Задаем горизонтальную скорость (вертикальная управляется гравитацией)
        current_y_velocity = self.velocity.y
        self.velocity = glm.vec3(0)
        if glm.length(move_direction) > 0:
            move_direction = glm.normalize(move_direction)
            self.velocity.x = move_direction.x * speed
            self.velocity.z = move_direction.z * speed
        self.velocity.y = current_y_velocity

        if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS and self.on_ground:
            self.velocity.y = self.jump_speed