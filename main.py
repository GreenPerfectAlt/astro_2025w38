# main.py
import glfw
import OpenGL.GL as gl
import glm

from engine.config import *
from engine.graphics import vertex_shader_source, fragment_shader_source, Frustum
from engine.camera import Camera
from engine.world import World
from engine.player import Player

def main():
    if not glfw.init(): return
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3); glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    window = glfw.create_window(SCR_WIDTH, SCR_HEIGHT, "Движок v2.3: Аватар", None, None)
    if not window: glfw.terminate(); return
    glfw.make_context_current(window)
    gl.glEnable(gl.GL_DEPTH_TEST)

    camera = Camera()
    # Создаем игрока и ставим его высоко над центром мира
    start_pos = glm.vec3(CHUNK_SIZE * WORLD_SIZE_IN_CHUNKS / 2, WORLD_HEIGHT_LIMIT + 20, CHUNK_SIZE * WORLD_SIZE_IN_CHUNKS / 2)
    player = Player(start_pos)
    
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    glfw.set_cursor_pos_callback(window, lambda win, x, y: camera.mouse_callback(win, x, y))

    # --- Код компиляции шейдеров, создания мира и frustum (без изменений) ---
    vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER); gl.glShaderSource(vertex_shader, vertex_shader_source); gl.glCompileShader(vertex_shader)
    fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER); gl.glShaderSource(fragment_shader, fragment_shader_source); gl.glCompileShader(fragment_shader)
    shader_program = gl.glCreateProgram(); gl.glAttachShader(shader_program, vertex_shader); gl.glAttachShader(shader_program, fragment_shader); gl.glLinkProgram(shader_program)
    world = World()
    frustum = Frustum()
    
    last_frame, delta_time = 0.0, 0.0
    frame_count, last_time = 0, glfw.get_time()

    while not glfw.window_should_close(window):
        current_frame = glfw.get_time()
        delta_time = current_frame - last_frame
        last_frame = current_frame
        
        # --- Код отладочного вывода FPS (без изменений) ---
        frame_count += 1
        if current_frame - last_time >= 1.0:
            print(f"FPS: {frame_count} | Chunks Rendered: {world.chunks_rendered_last_frame}/{len(world.chunks)} | Player Y: {player.position.y:.2f}")
            frame_count, last_time = 0, current_frame
        
        if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(window, True)
            
        # --- Новая логика обновления ---
        player.process_input(window, camera.front) # Игрок получает команды
        player.update(delta_time, world)           # Игрок обновляет свое состояние (физика)
        camera.update(player.position)             # Камера следует за игроком
        
        # --- Код отрисовки (без изменений) ---
        gl.glClearColor(0.5, 0.8, 1.0, 1.0); gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glUseProgram(shader_program)
        projection = glm.perspective(glm.radians(45.0), SCR_WIDTH / SCR_HEIGHT, 0.1, 1000.0)
        view = camera.get_view_matrix()
        model = glm.mat4(1.0)
        frustum.update(projection, view)
        light_pos = camera.pos + glm.vec3(-50, 100, -50)
        light_color = glm.vec3(1.0, 1.0, 1.0)
        gl.glUniform3fv(gl.glGetUniformLocation(shader_program, "lightPos"), 1, glm.value_ptr(light_pos))
        gl.glUniform3fv(gl.glGetUniformLocation(shader_program, "viewPos"), 1, glm.value_ptr(camera.pos))
        gl.glUniform3fv(gl.glGetUniformLocation(shader_program, "lightColor"), 1, glm.value_ptr(light_color))
        gl.glUniformMatrix4fv(gl.glGetUniformLocation(shader_program, "projection"), 1, gl.GL_FALSE, glm.value_ptr(projection))
        gl.glUniformMatrix4fv(gl.glGetUniformLocation(shader_program, "view"), 1, gl.GL_FALSE, glm.value_ptr(view))
        gl.glUniformMatrix4fv(gl.glGetUniformLocation(shader_program, "model"), 1, gl.GL_FALSE, glm.value_ptr(model))
        world.draw(shader_program, frustum)

        glfw.swap_buffers(window); glfw.poll_events()
        
    glfw.terminate()

if __name__ == "__main__":
    main()