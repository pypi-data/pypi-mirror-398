import logging

import pygame

FORMAT = (
    '{"time": "%(asctime)s", "level":"%(levelname)s", "message"="%(message)s"'
    '"logger":"%(name)s", "lineno":"%(lineno)s"'
)
logging.basicConfig(filename="mima.log", level=logging.DEBUG, format=FORMAT)

SIZE = 1920, 1080

# Pygame stuff
pygame.init()
pygame.font.init()
my_font = pygame.font.SysFont("Nimbus Sans", 20)
screen = pygame.display.set_mode(SIZE)
clock = pygame.time.Clock()

# Game specific stuff


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

    screen.fill((0, 0, 0))

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
