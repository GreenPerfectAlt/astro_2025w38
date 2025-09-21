# main.py - Движок v0.3 (Интерактивная камера)
import glfw
import OpenGL.GL as gl
import numpy as np
import glm
import noise
import ctypes

# --- Настройки окна ---
SCR_WIDTH = 1200
SCR_HEIGHT = 800

# --- Настройки камеры ---
camera_pos   = glm.vec3(0.0, 15.0, 3.0)
camera_front = glm.vec3(0.0, 0.0, -1.0)
camera_up    = glm.vec3(0.0, 1.0, 0.0)

# Переменные для управления мышью
first_mouse = True
yaw   = -90.0 
pitch =  0.0
last_x =  SCR_WIDTH / 2
last_y =  SCR_HEIGHT / 2

# --- Тайминг ---
delta_time = 0.0
last_frame = 0.0

# --- Параметры ландшафта ---
MAP_SIZE = 100
SCALE = 20.0
OCTAVES = 4
PERSISTENCE = 0.5
LACUNARITY = 2.0
HEIGHT_MULTIPLIER = 5.0
SEED = 42

# --- Шейдеры (без изменений) ---
vertex_shader_source = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aColor;
out vec3 ourColor;
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
void main()
{
    gl_Position = projection * view * model * vec4(aPos, 1.0);
    ourColor = aColor;
}
"""
fragment_shader_source = """
#version 330 core
out vec4 FragColor;
in vec3 ourColor;
void main()
{
    FragColor = vec4(ourColor, 1.0f);
}
"""

def main():
    global last_frame # Указываем, что будем менять глобальную переменную

    if not glfw.init():
        return
    
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(SCR_WIDTH, SCR_HEIGHT, "Наш процедурный движок v0.3", None, None)
    if not window:
        glfw.terminate()
        return
    glfw.make_context_current(window)

    # --- Новое: Захват мыши и регистрация коллбэков ---
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    
    gl.glEnable(gl.GL_DEPTH_TEST)

    # --- Компиляция шейдеров (без изменений) ---
    vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
    gl.glShaderSource(vertex_shader, vertex_shader_source)
    gl.glCompileShader(vertex_shader)
    fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
    gl.glShaderSource(fragment_shader, fragment_shader_source)
    gl.glCompileShader(fragment_shader)
    shader_program = gl.glCreateProgram()
    gl.glAttachShader(shader_program, vertex_shader)
    gl.glAttachShader(shader_program, fragment_shader)
    gl.glLinkProgram(shader_program)
    gl.glDeleteShader(vertex_shader)
    gl.glDeleteShader(fragment_shader)

    # --- Генерация ландшафта (без изменений) ---
    vertices = []
    indices = []
    for z in range(MAP_SIZE):
        for x in range(MAP_SIZE):
            height = noise.pnoise2(x / SCALE, z / SCALE, octaves=OCTAVES, persistence=PERSISTENCE, lacunarity=LACUNARITY, base=SEED) * HEIGHT_MULTIPLIER
            color_r, color_g, color_b = 0.0, 0.0, 0.0
            if height < -HEIGHT_MULTIPLIER * 0.3: color_r, color_g, color_b = 0.0, 0.0, 0.4
            elif height < -HEIGHT_MULTIPLIER * 0.1: color_r, color_g, color_b = 0.2, 0.5, 0.8
            elif height < HEIGHT_MULTIPLIER * 0.1: color_r, color_g, color_b = 0.9, 0.9, 0.7
            elif height < HEIGHT_MULTIPLIER * 0.5: color_r, color_g, color_b = 0.2, 0.7, 0.2
            elif height < HEIGHT_MULTIPLIER * 0.8: color_r, color_g, color_b = 0.5, 0.3, 0.1
            else: color_r, color_g, color_b = 0.9, 0.9, 0.9
            vertices.extend([x - MAP_SIZE/2, height, z - MAP_SIZE/2, color_r, color_g, color_b])
            if x < MAP_SIZE - 1 and z < MAP_SIZE - 1:
                base_idx = z * MAP_SIZE + x
                indices.extend([base_idx, base_idx + MAP_SIZE, base_idx + 1])
                indices.extend([base_idx + 1, base_idx + MAP_SIZE, base_idx + MAP_SIZE + 1])
    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)

    # --- Настройка VAO, VBO, EBO (без изменений) ---
    VAO = gl.glGenVertexArrays(1)
    VBO = gl.glGenBuffers(1)
    EBO = gl.glGenBuffers(1)
    gl.glBindVertexArray(VAO)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, EBO)
    gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
    gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 6 * 4, ctypes.c_void_p(0))
    gl.glEnableVertexAttribArray(0)
    gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 6 * 4, ctypes.c_void_p(3 * 4))
    gl.glEnableVertexAttribArray(1)

    # --- Главный цикл (сильно изменен) ---
    while not glfw.window_should_close(window):
        # --- Новое: Расчет времени кадра ---
        current_frame = glfw.get_time()
        global delta_time
        delta_time = current_frame - last_frame
        last_frame = current_frame

        # --- Новое: Обработка ввода ---
        process_input(window)

        # --- Отрисовка ---
        gl.glClearColor(0.2, 0.3, 0.3, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        gl.glUseProgram(shader_program)
        
        # --- Новое: Динамические матрицы ---
        projection = glm.perspective(glm.radians(45.0), SCR_WIDTH / SCR_HEIGHT, 0.1, 100.0)
        # Матрица вида (камера) теперь обновляется каждый кадр!
        view = glm.lookAt(camera_pos, camera_pos + camera_front, camera_up)
        model = glm.mat4(1.0)
        
        model_loc = gl.glGetUniformLocation(shader_program, "model")
        view_loc = gl.glGetUniformLocation(shader_program, "view")
        projection_loc = gl.glGetUniformLocation(shader_program, "projection")

        gl.glUniformMatrix4fv(model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
        gl.glUniformMatrix4fv(view_loc, 1, gl.GL_FALSE, glm.value_ptr(view))
        gl.glUniformMatrix4fv(projection_loc, 1, gl.GL_FALSE, glm.value_ptr(projection))

        gl.glBindVertexArray(VAO)
        gl.glDrawElements(gl.GL_TRIANGLES, len(indices), gl.GL_UNSIGNED_INT, None)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

# --- Новая функция: Обработка нажатий клавиатуры ---
def process_input(window):
    if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
        glfw.set_window_should_close(window, True)

    camera_speed = 5.5 * delta_time
    global camera_pos
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        camera_pos += camera_speed * camera_front
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        camera_pos -= camera_speed * camera_front
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        camera_pos -= glm.normalize(glm.cross(camera_front, camera_up)) * camera_speed
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        camera_pos += glm.normalize(glm.cross(camera_front, camera_up)) * camera_speed
    if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS:
        camera_pos += camera_up * camera_speed
    if glfw.get_key(window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS:
        camera_pos -= camera_up * camera_speed

# --- Новая функция: Обработка движений мыши ---
def mouse_callback(window, xpos, ypos):
    global first_mouse, last_x, last_y, yaw, pitch

    if first_mouse:
        last_x = xpos
        last_y = ypos
        first_mouse = False

    xoffset = xpos - last_x
    yoffset = last_y - ypos # Инвертировано, т.к. y-координаты идут снизу вверх
    last_x = xpos
    last_y = ypos

    sensitivity = 0.1
    xoffset *= sensitivity
    yoffset *= sensitivity

    yaw += xoffset
    pitch += yoffset

    # Ограничиваем угол обзора по вертикали, чтобы избежать "сальто"
    if pitch > 89.0:
        pitch = 89.0
    if pitch < -89.0:
        pitch = -89.0

    # Вычисляем новый вектор направления камеры
    front = glm.vec3()
    front.x = glm.cos(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    front.y = glm.sin(glm.radians(pitch))
    front.z = glm.sin(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    global camera_front
    camera_front = glm.normalize(front)


if __name__ == "__main__":
    main()