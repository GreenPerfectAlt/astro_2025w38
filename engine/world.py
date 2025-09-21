# engine/world.py
import numpy as np
import OpenGL.GL as gl
import ctypes
import noise
import math
from multiprocessing import Process, Queue
import time
import glm
import queue

from .config import *

def chunk_worker(tasks_queue, results_queue):
    while True:
        try:
            chunk_pos, world_data = tasks_queue.get(timeout=1)
            blocks = generate_blocks_data(chunk_pos)
            mesh_data = generate_mesh(blocks, world_data, chunk_pos)
            results_queue.put((chunk_pos, blocks, mesh_data))
        except queue.Empty:
            continue

def generate_blocks_data(chunk_pos):
    blocks = np.zeros((CHUNK_SIZE, WORLD_HEIGHT_LIMIT, CHUNK_SIZE), dtype=np.uint8)
    for local_x in range(CHUNK_SIZE):
        for local_z in range(CHUNK_SIZE):
            world_x = chunk_pos[0] * CHUNK_SIZE + local_x
            world_z = chunk_pos[1] * CHUNK_SIZE + local_z
            height = noise.pnoise2(world_x/SCALE, world_z/SCALE, octaves=OCTAVES, persistence=PERSISTENCE, lacunarity=LACUNARITY, base=SEED)
            y_surface = int(height * HEIGHT_MULTIPLIER) + (WORLD_HEIGHT_LIMIT // 2)
            for y in range(y_surface):
                if y == y_surface-1: blocks[local_x, y, local_z] = 3
                elif y >= y_surface-5: blocks[local_x, y, local_z] = 2
                else: blocks[local_x, y, local_z] = 1
    return blocks

def generate_mesh(blocks, world_data, chunk_pos):
    verts = []
    CUBE_VERTICES = np.array([[-0.5,-0.5,-0.5], [0.5,-0.5,-0.5], [0.5,0.5,-0.5], [-0.5,0.5,-0.5], [-0.5,-0.5,0.5], [0.5,-0.5,0.5], [0.5,0.5,0.5], [-0.5,0.5,0.5]], dtype=np.float32)
    FACES = {(0,0,-1): [0,1,2,2,3,0], (0,0,1): [4,5,6,6,7,4], (1,0,0): [1,5,6,6,2,1], (-1,0,0): [4,0,3,3,7,4], (0,1,0): [3,2,6,6,7,3], (0,-1,0): [0,1,5,5,4,0]}
    for x in range(CHUNK_SIZE):
        for y in range(WORLD_HEIGHT_LIMIT):
            for z in range(CHUNK_SIZE):
                block_type = blocks[x, y, z]
                if block_type == 0: continue
                color = [0.4,0.4,0.4]; 
                if block_type == 2: color = [0.6,0.4,0.2]
                elif block_type == 3: color = [0.2,0.7,0.2]
                for normal, face_indices in FACES.items():
                    nx, ny, nz = normal
                    wx, wy, wz = chunk_pos[0]*CHUNK_SIZE+x+nx, y+ny, chunk_pos[1]*CHUNK_SIZE+z+nz
                    neighbor_chunk_pos = (wx // CHUNK_SIZE, wz // CHUNK_SIZE)
                    if neighbor_chunk_pos not in world_data or \
                       world_data.get(neighbor_chunk_pos, np.zeros((CHUNK_SIZE, WORLD_HEIGHT_LIMIT, CHUNK_SIZE), dtype=np.uint8))[wx % CHUNK_SIZE, wy, wz % CHUNK_SIZE] == 0:
                        for idx in face_indices:
                            vert = CUBE_VERTICES[idx]
                            verts.extend([chunk_pos[0]*CHUNK_SIZE+x+vert[0], y+vert[1], chunk_pos[1]*CHUNK_SIZE+z+vert[2], color[0], color[1], color[2]])
    return np.array(verts, dtype=np.float32)

class World:
    def __init__(self):
        self.chunks = {}
        self.last_camera_chunk_pos = None
        self.chunks_rendered_last_frame = 0
        self.tasks_queue = Queue()
        self.results_queue = Queue()
        self.worker_process = Process(target=chunk_worker, args=(self.tasks_queue, self.results_queue))
        self.worker_process.daemon = True
        self.worker_process.start()

    def update(self, camera_pos):
        camera_chunk_pos = (math.floor(camera_pos.x / CHUNK_SIZE), math.floor(camera_pos.z / CHUNK_SIZE))
        if camera_chunk_pos == self.last_camera_chunk_pos:
            return
        self.last_camera_chunk_pos = camera_chunk_pos
        
        visible_chunks_pos = set()
        for x in range(camera_chunk_pos[0] - VIEW_DISTANCE_IN_CHUNKS, camera_chunk_pos[0] + VIEW_DISTANCE_IN_CHUNKS + 1):
            for z in range(camera_chunk_pos[1] - VIEW_DISTANCE_IN_CHUNKS, camera_chunk_pos[1] + VIEW_DISTANCE_IN_CHUNKS + 1):
                visible_chunks_pos.add((x, z))
        
        chunks_to_unload_pos = set(self.chunks.keys()) - visible_chunks_pos
        for pos in chunks_to_unload_pos:
            if self.chunks.get(pos) is not None: self.chunks[pos].destroy()
            del self.chunks[pos]

        chunks_to_load_pos = visible_chunks_pos - set(self.chunks.keys())
        
        world_data_for_worker = {pos: chunk.blocks for pos, chunk in self.chunks.items() if chunk is not None}
        
        for pos in chunks_to_load_pos:
            self.chunks[pos] = None
            self.tasks_queue.put((pos, world_data_for_worker))

    def process_results_queue(self):
        while not self.results_queue.empty():
            try:
                chunk_pos, blocks, mesh_data = self.results_queue.get_nowait()
                if chunk_pos in self.chunks:
                    self.chunks[chunk_pos] = Chunk(self, chunk_pos, blocks, mesh_data)
            except queue.Empty:
                break
    
    def draw(self, shader_program, frustum):
        chunks_rendered = 0
        for chunk in self.chunks.values():
            if chunk is not None and chunk.VAO is not None:
                if frustum.is_box_in_frustum(chunk.bounding_box_center, chunk.bounding_box_size):
                    chunk.draw(shader_program)
                    chunks_rendered += 1
        self.chunks_rendered_last_frame = chunks_rendered
        
    def destroy(self):
        self.worker_process.terminate()

class Chunk:
    def __init__(self, world, position, blocks, mesh_data):
        self.world, self.position, self.blocks = world, position, blocks
        self.vertices_data = mesh_data
        self.num_vertices = len(self.vertices_data)
        
        self.VAO, self.VBO = None, None
        if self.num_vertices > 0:
            self._setup_opengl_buffers()

        center_x = position[0]*CHUNK_SIZE+CHUNK_SIZE/2; center_y = WORLD_HEIGHT_LIMIT/2; center_z = position[1]*CHUNK_SIZE+CHUNK_SIZE/2
        self.bounding_box_center = glm.vec3(center_x, center_y, center_z)
        self.bounding_box_size = glm.length(glm.vec3(CHUNK_SIZE/2, WORLD_HEIGHT_LIMIT/2, CHUNK_SIZE/2))

    def _setup_opengl_buffers(self):
        self.VAO, self.VBO = gl.glGenVertexArrays(1), gl.glGenBuffers(1)
        gl.glBindVertexArray(self.VAO); gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.vertices_data.nbytes, self.vertices_data, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 6*4, ctypes.c_void_p(0)); gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 6*4, ctypes.c_void_p(3*4)); gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)

    def draw(self, shader_program):
        if self.VAO is not None and self.num_vertices > 0:
            gl.glBindVertexArray(self.VAO)
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, self.num_vertices // 6)

    def destroy(self):
        if self.VAO is not None: gl.glDeleteVertexArrays(1, [self.VAO])
        if self.VBO is not None: gl.glDeleteBuffers(1, [self.VBO])