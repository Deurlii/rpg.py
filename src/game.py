import pygame
from enum import Enum

from config import Config
from graphics.renderer.camera import Camera
from graphics.renderer.text_renderer import TextRenderer
from menu import Menu, TitleScreen
from src.input_handler import InputHandler
from graphics.renderer.renderer import Renderer
from src.entities.player import Player
from world.tilemap import TileMap

class Game:
    class State(Enum):
        TITLE = "title"
        MENU = "menu"
        GAME = "game"
        OPTIONS = "options"
        LOAD = "load"

    def __init__(self):
        pygame.init()
        pygame.display.set_caption('RPG.py')
        self.config = Config()

        #Logic
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_state = Game.State.TITLE

        #Input
        self.input_handler = InputHandler()

        #Graphics
        self.screen = pygame.Surface(self.config.resolution)
        self.display = pygame.display.set_mode(self.config.resolution)
        buffer_width = self.config.resolution[0] // 2
        buffer_height = self.config.resolution[1] // 2
        self.buffer = pygame.Surface((buffer_width, buffer_height))
        self.map_dir = "src/world/maps"
        self.tileset_dir = "src/graphics/assets/tiles"
        self.tilemap = TileMap(f"{self.map_dir}/map1.txt", self.tileset_dir)
        self.player = Player(*self.tilemap.spawn)
        self.camera = Camera(self.player)
        self.renderer = Renderer(self.buffer, self.screen, self.camera)
        self.text_renderer = TextRenderer(self.screen)

        #Menus
        self.title_screen = TitleScreen(self.screen, self.text_renderer)
        self.menu = Menu(self.screen, self.text_renderer, self.input_handler)

    def load_map(self, map_path, spawn):
        self.tilemap = TileMap(map_path, self.tileset_dir)
        self.player.x, self.player.y = spawn
        self.player.last_tile = (
            int(spawn[0]) // self.tilemap.TILE_SIZE,
            int(spawn[1]) // self.tilemap.TILE_SIZE,
        )

    def check_map_transition(self):
        tile = (
            int(self.player.x) // self.tilemap.TILE_SIZE,
            int(self.player.y) // self.tilemap.TILE_SIZE,
        )
        if tile == self.player.last_tile:
            return
        self.player.last_tile = tile
        link = self.tilemap.link_at(self.player.x, self.player.y)
        if link is None:
            return
        target_path, target_char = self.tilemap.resolve_link(link)
        target_map = TileMap(target_path, self.tileset_dir)
        self.load_map(target_path, target_map.link_spawn(target_char))

    def handle_input(self):
        self.input_handler.update()
        self.input_state = self.input_handler.get_input_state()

    def handle_quit(self):
        keys = self.input_state["keys"]
        if pygame.K_ESCAPE in keys:
            self.running = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def options_screen(self):
        pass

    def game_screen(self):
        self.player.update(self.input_state, self.tilemap)
        self.check_map_transition()
        self.camera.update()
        self.renderer.mode7(self.tilemap)
        self.renderer.upscale()
        self.player.draw(self.screen, self.renderer, self.camera)

    def screen_selector(self):
        if self.current_state == Game.State.TITLE:
            action = self.title_screen.update()
            if action == "menu":
                self.current_state = Game.State.MENU
            self.title_screen.render()

        if self.current_state == Game.State.MENU:
            action = self.menu.update()
            if action == "start_game":
                self.current_state = Game.State.GAME
            elif action == "quit":
                self.running = False
            self.menu.render()

        if self.current_state == Game.State.GAME:
            self.game_screen()

        if self.current_state == Game.State.OPTIONS:
            self.options_screen()

    def draw(self):
        self.display.blit(self.screen, (0,0))
        pygame.display.update()

    def clear_screen(self):
        self.screen.fill((0, 0, 0))

    #Gameloop
    def run(self):
        while self.running:
            self.handle_input()
            self.handle_quit()
            self.clear_screen()
            self.screen_selector()
            self.draw()
            self.clock.tick(self.config.fps)
