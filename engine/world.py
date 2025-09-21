# engine/world.py
import numpy as np
import OpenGL.GL as gl
import ctypes, noise, math, glm
from .config import *

class World:
    def __init__(self):
        self.chunks = {}
        self.chunks_rendered_last_frame = 0
        self._generate_world()

    def _generate_world(self):
        print("Генерация мира (однопоточная)...")
        all_blocks = {}
        for x in range(WORLD_SIZE_IN_CHUNKS):
            for z in range(WORLD_SIZE_IN_CHUNKS):
                all_blocks[(x, z)] = self._generate_chunk_blocks((x, z))
        
        print("Построение мешей...")
        for x in range(WORLD_SIZE_IN_CHUNKS):
            for z in range(WORLD_SIZE_IN_CHUNKS):
                pos = (x, z)
                self.chunks[pos] = Chunk(pos, all_blocks[pos], all_blocks)
        print("Мир сгенерирован!")

    def _generate_chunk_blocks(self, chunk_pos):
        blocks = np.zeros((CHUNK_SIZE, WORLD_HEIGHT_LIMIT, CHUNK_SIZE), dtype=np.uint8)
        for lx in range(CHUNK_SIZE):
            for lz in range(CHUNK_SIZE):
                wx, wz = chunk_pos[0]*CHUNK_SIZE+lx, chunk_pos[1]*CHUNK_SIZE+lz
                height = noise.pnoise2(wx/SCALE, wz/SCALE, octaves=OCTAVES, persistence=PERSISTENCE, lacunarity=LACUNARITY, base=SEED)
                y_surf = int(height * HEIGHT_MULTIPLIER) + (WORLD_HEIGHT_LIMIT // 2)
                for y in range(y_surf):
                    if y == y_surf-1: blocks[lx, y, lz] = 3
                    elif y >= y_surf-5: blocks[lx, y, lz] = 2
                    else: blocks[lx, y, lz] = 1
        return blocks
    
    # ---!!! ВОТ НЕДОСТАЮЩАЯ ФУНКЦИЯ !!!---
    def get_block(self, world_x, world_y, world_z):
        if not (0 <= world_y < WORLD_HEIGHT_LIMIT):
            return 0 # Воздух, если выше или ниже мира

        chunk_x = world_x // CHUNK_SIZE
        chunk_z = world_z // CHUNK_SIZE

        chunk_pos = (chunk_x, chunk_z)
        if chunk_pos not in self.chunks:
            return 0 # Воздух, если чанк не существует

        local_x = world_x % CHUNK_SIZE
        local_z = world_z % CHUNK_SIZE

        return self.chunks[chunk_pos].blocks[local_x, world_y, local_z]
    
    def draw(self, shader_program, frustum):
        rendered = 0
        for chunk in self.chunks.values():
            if frustum.is_box_in_frustum(chunk.bounding_box_center, chunk.bounding_box_size):
                chunk.draw(shader_program); rendered += 1
        self.chunks_rendered_last_frame = rendered

class Chunk:
    _CUBE_VERTICES = np.array([[-0.5,-0.5,-0.5], [0.5,-0.5,-0.5], [0.5,0.5,-0.5], [-0.5,0.5,-0.5], [-0.5,-0.5,0.5], [0.5,-0.5,0.5], [0.5,0.5,0.5], [-0.5,0.5,0.5]], dtype=np.float32)
    _FACES = {(0,0,-1): [0,1,2,2,3,0], (0,0,1): [4,5,6,6,7,4], (1,0,0): [1,5,6,6,2,1], (-1,0,0): [4,0,3,3,7,4], (0,1,0): [3,2,6,6,7,3], (0,-1,0): [0,1,5,5,4,0]}

    def __init__(self, position, blocks, world_blocks):
        self.position = position
        self.vertices_data = self._generate_mesh(blocks, world_blocks)
        self.num_vertices = len(self.vertices_data)
        
        self.VAO, self.VBO = None, None
        if self.num_vertices > 0: self._setup_opengl_buffers()

        cx,cy,cz = position[0]*CHUNK_SIZE+CHUNK_SIZE/2, WORLD_HEIGHT_LIMIT/2, position[1]*CHUNK_SIZE+CHUNK_SIZE/2
        self.bounding_box_center = glm.vec3(cx,cy,cz)
        self.bounding_box_size = glm.length(glm.vec3(CHUNK_SIZE/2, WORLD_HEIGHT_LIMIT/2, CHUNK_SIZE/2))

    def _generate_mesh(self, blocks, world_blocks):
        verts = []
        for x in range(CHUNK_SIZE):
            for y in range(WORLD_HEIGHT_LIMIT):
                for z in range(CHUNK_SIZE):
                    block_type = blocks[x,y,z]
                    if block_type == 0: continue
                    color = [0.5, 0.5, 0.5]
                    if block_type == 2: color = [0.6, 0.4, 0.2]
                    elif block_type == 3: color = [0.2, 0.7, 0.2]
                    for norm, face_idx in self._FACES.items():
                        nx,ny,nz = norm
                        wx,wy,wz = self.position[0]*CHUNK_SIZE+x+nx, y+ny, self.position[1]*CHUNK_SIZE+z+nz
                        n_chunk_pos = (wx//CHUNK_SIZE, wz//CHUNK_SIZE)
                        
                        neighbor_block_type = 0
                        if n_chunk_pos in world_blocks and 0 <= wy < WORLD_HEIGHT_LIMIT:
                            neighbor_block_type = world_blocks[n_chunk_pos][wx%CHUNK_SIZE, wy, wz%CHUNK_SIZE]

                        if neighbor_block_type == 0:
                            for idx in face_idx:
                                vert = self._CUBE_VERTICES[idx]
                                verts.extend([
                                    self.position[0]*CHUNK_SIZE+x+vert[0], y+vert[1], self.position[1]*CHUNK_SIZE+z+vert[2],
                                    nx, ny, nz,
                                    color[0], color[1], color[2]
                                ])
        return np.array(verts, dtype=np.float32)

    def _setup_opengl_buffers(self):
        self.VAO,self.VBO = gl.glGenVertexArrays(1), gl.glGenBuffers(1)
        gl.glBindVertexArray(self.VAO); gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.vertices_data.nbytes, self.vertices_data, gl.GL_STATIC_DRAW)
        stride = 9 * 4
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(0)); gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(3*4)); gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(2, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(6*4)); gl.glEnableVertexAttribArray(2)
        gl.glBindVertexArray(0)

    def draw(self, shader_program):
        if self.VAO is not None:
            gl.glBindVertexArray(self.VAO)
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, self.num_vertices // 9)