import pygame
import numpy as np
import math
from graphics.renderer.renderer_jit import render_mode7_jit

class Renderer:
    def __init__(self, buffer, screen, camera):
        self.buffer = buffer
        self.screen = screen
        self.camera = camera
        self.buffer_width = buffer.get_width()
        self.buffer_height = buffer.get_height()
        self.horizon = 50
        self.scale = 1
        self.fov = math.pi / 3
        self.void_color = np.array((38, 38, 52), dtype=np.uint8)
        self.cos_offsets = []
        self.sin_offsets = []
        self.tan_offsets = []
        tile = 64
        self.fog_start = 6.0 * tile
        self.fog_end = 18.0 * tile
        for x in range(self.buffer_width):
            angle_offset = (x - self.buffer_width / 2) / self.buffer_width * self.fov
            self.tan_offsets.append(math.tan(angle_offset))

    def mode7(self, tilemap):
        a = self.camera.angle
        cosa = math.cos(a)
        sina = math.sin(a)
        dir_x = [cosa - t * sina for t in self.tan_offsets]
        dir_y = [sina + t * cosa for t in self.tan_offsets]
        self.buffer.fill(tuple(self.void_color))
        self.buffer.fill((135, 206, 235), (0, 0, self.buffer_width, self.horizon))
        buffer_array = np.transpose(pygame.surfarray.pixels3d(self.buffer), (1, 0, 2))
        render_mode7_jit(
            buffer_array,
            tilemap.tileset_array,
            tilemap.tile_ids,
            dir_x, dir_y,
            self.camera.x, self.camera.y,
            self.horizon, self.scale,
            tilemap.TILE_SIZE,
            self.void_color, self.fog_start,
            self.fog_end
        )
        del buffer_array

    def world_to_buffer_row(self, distance):
        return int(self.horizon + (self.buffer_height - self.horizon) * self.scale * self.horizon / distance)

    def upscale(self):
        scaled = pygame.transform.scale(self.buffer, self.screen.get_size())
        self.screen.blit(scaled, (0, 0))
