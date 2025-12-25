import logging
from pathlib import Path

import pygame
from pygame import Vector2

from mima.standalone.tiled_map import MapManager
from mima.standalone.transformed_view import TileTransformedView

FORMAT = (
    '{"time": "%(asctime)s", "level":"%(levelname)s", "message"="%(message)s"'
    '"logger":"%(name)s", "lineno":"%(lineno)s"'
)
logging.basicConfig(filename="mima.log", level=logging.DEBUG, format=FORMAT)

SIZE = 480 * 2, 270 * 2

# Pygame stuff
pygame.init()
pygame.font.init()
my_font = pygame.font.SysFont("Nimbus Sans", 20)
screen = pygame.display.set_mode(SIZE)
clock = pygame.time.Clock()

# Game specific stuff
data_path = Path(__file__).parent.parent / "fixtures"
mapman = MapManager()
tmap = mapman.get_map(data_path / "test_map.tmx")
tmap.prerender_layers()

tv = TileTransformedView(screen, Vector2(SIZE), Vector2(16, 16))
tv.enable_caching(True)

# Game loop stuff
running = True
frame_ctr = 0
frame_time = 0.0
fps = 1
while running:
    elapsed_time = clock.tick() / 1000.0

    # TODO: Fix pan and zoom behaving strange
    events = tv.handle_pan_and_zoom()
    for e in events:
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False

    tmap.start_new_frame()
    tmap.update(elapsed_time)

    screen.fill((0, 0, 0))

    for layer in tmap.get_rendered_layers():
        layer.draw(tv)

    pygame.display.flip()

    frame_ctr += 1
    frame_time += elapsed_time
    if frame_time >= 1.0:
        fps = frame_ctr
        frame_ctr = 0
        frame_time -= 1.0
        pygame.display.set_caption(f"FPS: {fps}")

pygame.font.quit()
pygame.quit()
