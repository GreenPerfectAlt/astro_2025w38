# main.py
import glfw
import OpenGL.GL as gl
import glm
# Мы должны импортировать multiprocessing здесь, чтобы использовать его в __main__
import multiprocessing

from engine.config import *
from engine.graphics import vertex_shader_source, fragment_shader_source, Frustum
from engine.camera import Camera
from engine.world import World

def main():
    if not glfw.init(): return
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3); glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    window = glfw.create_window(SCR_WIDTH, SCR_HEIGHT, "Движок v1.5: Мультипроцессинг", None, None)
    if not window: glfw.terminate(); return
    glfw.make_context_current(window)
    gl.glEnable(gl.GL_DEPTH_TEST)

    camera = Camera()
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    glfw.set_cursor_pos_callback(window, lambda win, x, y: camera.mouse_callback(win, x, y))

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
        
        frame_count += 1
        if current_frame - last_time >= 1.0:
            print(f"FPS: {frame_count} | Chunks Rendered: {world.chunks_rendered_last_frame}/{len(world.chunks)}")
            frame_count, last_time = 0, current_frame
        
        if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(window, True)
            
        camera.process_input(window, delta_time)
        
        world.update(camera.pos)
        world.process_results_queue()

        gl.glClearColor(0.5, 0.8, 1.0, 1.0); gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glUseProgram(shader_program)
        
        projection = glm.perspective(glm.radians(45.0), SCR_WIDTH / SCR_HEIGHT, 0.1, 500.0)
        view = camera.get_view_matrix()
        model = glm.mat4(1.0)
        
        frustum.update(projection, view)
        
        projection_loc = gl.glGetUniformLocation(shader_program, "projection"); view_loc = gl.glGetUniformLocation(shader_program, "view"); model_loc = gl.glGetUniformLocation(shader_program, "model")
        gl.glUniformMatrix4fv(projection_loc, 1, gl.GL_FALSE, glm.value_ptr(projection))
        gl.glUniformMatrix4fv(view_loc, 1, gl.GL_FALSE, glm.value_ptr(view))
        gl.glUniformMatrix4fv(model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
        
        world.draw(shader_program, frustum)

        glfw.swap_buffers(window); glfw.poll_events()
        
    world.destroy()
    glfw.terminate()

if __name__ == "__main__":
    # Для multiprocessing в Windows (и иногда в macOS) важно защитить запуск
    multiprocessing.freeze_support()
    main()