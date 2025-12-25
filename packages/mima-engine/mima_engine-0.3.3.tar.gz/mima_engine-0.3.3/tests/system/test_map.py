import logging
import logging.config
from pathlib import Path

import pygame

from mima.standalone.tiled_map import MapManager

SIZE = 688, 384

FORMAT = (
    '{"time": "%(asctime)s", "logger":"%(name)s", "level":"%(levelname)s", '
    '"message":"%(message)s", "lineno":"%(lineno)s"}'
)
logging.basicConfig(
    filename="mima_log.json", level=logging.DEBUG, format=FORMAT
)

# Pygame stuff
pygame.init()
pygame.font.init()
my_font = pygame.font.SysFont("Nimbus Sans", 20)
screen = pygame.display.set_mode(SIZE)
clock = pygame.time.Clock()

# Game specific stuff
data_path = (Path(__file__) / ".." / ".." / "fixtures").resolve()
mapman = MapManager()
tmap = mapman.get_map(data_path / "test_map.tmx")


# Game loop stuff
running = True
frame_ctr = 0
frame_time = 0.0
fps = 1
while running:
    elapsed_time = clock.tick() / 1000.0

    events = []
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        else:
            events.append(e)
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False

    tmap.update(elapsed_time)
    screen.fill((0, 0, 0))
    tmap.draw_to_surface(
        screen,
        pygame.Vector2(0, 0),
        pygame.Vector2(0, 0),
        pygame.Vector2(44, 24),
    )

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
