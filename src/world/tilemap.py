import os
import numpy as np
import pygame

class TileMap:
    TILE_SIZE = 64

    TILE_CHARS = {
        ".": 1,
        "#": 2,
        "p": 3,
        "$": 4,
    }

    SOLID_IDS = {2}

    FLOOR_ID = 1
    LINK_CHARS = {chr(c) for c in range(ord("A"), ord("Z") + 1)}

    _tileset_cache = {}

    def __init__(self, map_path, tileset_dir):
        self.map_path = map_path
        self.tile_ids, self.spawn, self.links, self.link_tiles = self._load_map(map_path)
        self.tileset_array = self._get_tileset(tileset_dir)

    @classmethod
    def _get_tileset(cls, tileset_dir):
        key = os.path.abspath(tileset_dir)
        if key not in cls._tileset_cache:
            cls._tileset_cache[key] = cls._load_tileset(key)
        return cls._tileset_cache[key]

    @classmethod
    def clear_tileset_cache(cls, tileset_dir=None):
        if tileset_dir is None:
            cls._tileset_cache.clear()
        else:
            cls._tileset_cache.pop(os.path.abspath(tileset_dir), None)

    @classmethod
    def _load_tileset(cls, tileset_dir):
        ts = cls.TILE_SIZE
        tile_files = []
        for f in os.listdir(tileset_dir):
            stem, ext = os.path.splitext(f)
            if ext == ".png" and stem.isdigit():
                tile_files.append(f)
        tileset_array = np.zeros((len(tile_files), ts, ts, 3), dtype=np.uint8)
        background = pygame.Surface((ts, ts))
        background.fill((0, 0, 0))

        for filename in tile_files:
            tile_id = int(os.path.splitext(filename)[0])
            path = os.path.join(tileset_dir, filename)
            surface = pygame.image.load(path).convert_alpha()
            if surface.get_size() != (ts, ts):
                factor = ts // surface.get_width()
                surface = pygame.transform.scale_by(surface, factor)
            background.blit(surface, (0, 0))
            if tile_id >= len(tileset_array):
                tileset_array = np.resize(tileset_array, (tile_id + 1, ts, ts, 3))
            tileset_array[tile_id] = pygame.surfarray.array3d(background).transpose(1, 0, 2)
            background.fill((0, 0, 0))

        return tileset_array

    def _load_map(self, path):
        with open(path) as f:
            lines = [line.rstrip("\n") for line in f if line.strip()]

        links = {}
        grid_lines = lines
        for i, line in enumerate(lines):
            if line.startswith("L"):
                parts = line.split()
                if len(parts) != 4 or parts[0] != "L":
                    raise ValueError(f"{path}: bad link header '{line}'")
                char, target, target_char = parts[1], parts[2], parts[3]
                for c in (char, target_char):
                    if c not in self.LINK_CHARS:
                        raise ValueError(f"{path}: link char '{c}' must be a single uppercase letter")
                if char in links:
                    raise ValueError(f"{path}: duplicate link header for '{char}'")
                links[char] = (target, target_char)
            else:
                grid_lines = lines[i:]
                break

        width = len(grid_lines[0])
        for i, line in enumerate(grid_lines):
            if len(line) != width:
                raise ValueError(f"{path}: row {i} is {len(line)} chars, expected {width}")

        tile_ids = np.zeros((len(grid_lines), width), dtype=np.int64)
        spawn_tile = None
        link_tiles = {}

        for y, line in enumerate(grid_lines):
            for x, char in enumerate(line):
                if char == "P":
                    if spawn_tile is not None:
                        raise ValueError(f"{path}: multiple spawn points")
                    spawn_tile = (x, y)
                    char = "."
                if char in self.LINK_CHARS:
                    if char not in links:
                        raise ValueError(f"{path}: undeclared link char '{char}' at ({x}, {y})")
                    if char in link_tiles:
                        raise ValueError(f"{path}: link char '{char}' used more than once")
                    link_tiles[char] = (x, y)
                    char = "."
                if char not in self.TILE_CHARS:
                    raise ValueError(f"{path}: unknown tile char '{char}' at ({x}, {y})")
                tile_ids[y, x] = self.TILE_CHARS[char]

        if spawn_tile is None:
            raise ValueError(f"{path}: no spawn point 'P'")

        for char in links:
            if char not in link_tiles:
                raise ValueError(f"{path}: link '{char}' declared but not placed in grid")

        spawn = (
            (spawn_tile[0] + 0.5) * self.TILE_SIZE,
            (spawn_tile[1] + 0.5) * self.TILE_SIZE,
        )
        return tile_ids, spawn, links, link_tiles

    def link_at(self, world_x, world_y):
        tile = self.tile_at(world_x, world_y)
        if tile is None:
            return None
        tx = int(world_x) // self.TILE_SIZE
        ty = int(world_y) // self.TILE_SIZE
        for char, (lx, ly) in self.link_tiles.items():
            if (lx, ly) == (tx, ty):
                return char
        return None

    def link_spawn(self, char):
        if char not in self.link_tiles:
            raise ValueError(f"{self.map_path}: link '{char}' not placed in grid")
        x, y = self.link_tiles[char]
        return (
            (x + 0.5) * self.TILE_SIZE,
            (y + 0.5) * self.TILE_SIZE,
        )

    def resolve_link(self, char):
        if char not in self.links:
            return None
        target, target_char = self.links[char]
        target_path = os.path.join(os.path.dirname(self.map_path), target)
        return target_path, target_char

    @property
    def width(self):
        return self.tile_ids.shape[1] * self.TILE_SIZE

    @property
    def height(self):
        return self.tile_ids.shape[0] * self.TILE_SIZE

    def tile_at(self, world_x, world_y):
        tx = int(world_x) // self.TILE_SIZE
        ty = int(world_y) // self.TILE_SIZE
        if not (0 <= tx < self.tile_ids.shape[1] and 0 <= ty < self.tile_ids.shape[0]):
            return None
        return int(self.tile_ids[ty, tx])

    def is_passable(self, world_x, world_y):
        tile = self.tile_at(world_x, world_y)
        return tile is not None and tile not in self.SOLID_IDS
