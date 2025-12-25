# import cProfile
import random

import pygame

from mima.standalone.camera import Camera, CameraMode
from mima.standalone.geometry import (
    Circle,
    Rect,
    clamp,
    overlaps,
    resolve_collision,
)
from mima.standalone.spatial import SpatialGrid
from mima.standalone.transformed_view import (
    TileTransformedView,
    TransformedView,
)
from mima.standalone.user_input import (
    Input,
    InputManager,
    KeyboardMapping,
    Player,
)

WIDTH, HEIGHT = 960, 540
WORLD_WIDTH, WORLD_HEIGHT = 5000, 5000
N_OBJECTS = 1000
pygame.init()
pygame.font.init()
my_font = pygame.font.SysFont("Nimbus Sans", 20)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

tv1 = TileTransformedView(screen, pygame.Vector2(WIDTH // 2, HEIGHT))
tv2 = TileTransformedView(screen, pygame.Vector2(WIDTH // 2, HEIGHT))
tv2.set_pos(pygame.Vector2(WIDTH // 2, 0))


class SomeObjectWithArea:
    def __init__(self):
        self.hitbox: Rect | Circle = Rect()
        self.old_pos: pygame.Vector2 = pygame.Vector2(0, 0)
        self.vel: pygame.Vector2 = pygame.Vector2(0, 0)
        self.sprite: pygame.Surface | None = None
        self.sprite_src: pygame.Vector2 | None = None
        self.sprite_size: pygame.Vector2 | None = None
        self.color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
        self.can_move: bool = False

    def draw_self(self, tv: TransformedView):
        if isinstance(self.hitbox, Rect):
            tv.fill_rect(self.hitbox.pos, self.hitbox.size, self.color)
        elif isinstance(self.hitbox, Circle):
            tv.draw_circle(self.hitbox.pos, self.hitbox.radius, self.color)

        if self.sprite is not None:
            tv.draw_surface(
                self.hitbox.pos,
                self.sprite,
                src_pos=self.sprite_src,
                src_size=self.sprite_size,
            )

    def get_pos(self) -> pygame.Vector2:
        return self.hitbox.pos


grid = SpatialGrid[SomeObjectWithArea](
    pygame.Vector2(WORLD_WIDTH, WORLD_HEIGHT), 20
)
objects = []
for i in range(N_OBJECTS):
    obj = SomeObjectWithArea()
    hb = Rect()
    hb.pos = pygame.Vector2(
        random.random() * WORLD_WIDTH, random.random() * WORLD_HEIGHT
    )
    hb.size = pygame.Vector2(
        0.1 + random.random() * 100, 0.1 + random.random() * 100
    )
    obj.hitbox = hb
    objects.append(obj)
    grid.insert(obj, obj.hitbox.pos)

character = SomeObjectWithArea()
character.sprite = pygame.image.load("tests/fixtures/icon.png").convert_alpha()
character.hitbox = Circle(pygame.Vector2(20, 20), 16)
character.old_pos = character.hitbox.pos
character.vel = pygame.Vector2(0.0, 0.0)
character.can_move = True
grid.insert(character, character.get_pos())

creature = SomeObjectWithArea()
creature.sprite = pygame.image.load(
    "tests/fixtures/healing_dragon_color.png"
).convert_alpha()
creature.sprite_src = pygame.Vector2(0, 0)
creature.sprite_size = pygame.Vector2(16, 16)
creature.hitbox = Circle(pygame.Vector2(100, 100), 16)
creature.old_pos = creature.hitbox.pos
creature.can_move = True
grid.insert(creature, creature.get_pos())

camera = Camera[SomeObjectWithArea](pygame.Vector2(WIDTH // 2, HEIGHT))
camera.set_target(character)
camera.set_mode(CameraMode.LAZY_FOLLOW)
camera2 = Camera[SomeObjectWithArea](pygame.Vector2(WIDTH // 2, HEIGHT))
camera2.set_target(creature)
camera2.set_mode(CameraMode.LAZY_FOLLOW)


keys = InputManager()
keys.add_input_scheme(
    KeyboardMapping(
        {
            Player.P1: {
                Input.LEFT: ["a"],
                Input.RIGHT: ["d"],
                Input.A: ["space"],
            },
            Player.P2: {
                Input.LEFT: ["left"],
                Input.RIGHT: ["right"],
                Input.A: ["rshift"],
            },
        }
    )
)


def move_object(
    sgrid: SpatialGrid, obj: SomeObjectWithArea, new_pos: pygame.Vector2
) -> None:
    obj.old_pos = obj.hitbox.pos
    obj.hitbox.pos = new_pos
    sgrid.relocate(obj, obj.old_pos, obj.get_pos())


gravity = 400
jump_power = 200
jump_charge = 0.0
jump_charge2 = 0.0
running = True
frame_ctr = 0
frame_time = 0.0
elapsed_time = 0.016
# profiler = cProfile.Profile()
# profiler.enable()
view_tl_offset = pygame.Vector2(100.0, 100.0)
view_br_offet = pygame.Vector2(150.0, 150.0)
zoom_at = ""
while running:
    elapsed_time = clock.tick() / 1000.0

    events = [e for e in pygame.event.get()]
    keys.process_events(events)
    # events = tv.handle_pan_and_zoom(events=events)

    # tv2.handle_pan_and_zoom(mouse_button=1, events=events, zoom=False)
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        # if event.type == pygame.MOUSEWHEEL:
        #     if event.y == 1:
        #         tp = tv1.world_to_screen(camera.get_pos())
        #         tv1.zoom_at_screen_pos(1.1, tp)
        #         zoom_at = f"Zoom in at {tp}"
        #     if event.y == -1:
        #         tp = tv1.world_to_screen(camera.get_pos())
        #         tv1.zoom_at_screen_pos(0.9, tp)
        #         zoom_at = f"Zoom out at {tp}"#
        if event.type == pygame.KEYDOWN:
            # if event.key == pygame.K_d:
            #     character.vel.x += 100
            # if event.key == pygame.K_a:
            #     character.vel.x -= 100
            if event.key == pygame.K_SPACE:
                jump_charge = 0
            # if event.key == pygame.K_LEFT:
            #     creature.vel.x -= 100
            # if event.key == pygame.K_RIGHT:
            #     creature.vel.x += 100
            if event.key == pygame.K_RSHIFT:
                jump_charge2 = 0
        if event.type == pygame.KEYUP:
            # if event.key in (pygame.K_d, pygame.K_a):
            #     character.vel.x = 0
            # if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            #     creature.vel.x = 0
            if event.key == pygame.K_SPACE:
                character.vel.y = -jump_power * jump_charge
            if event.key == pygame.K_RSHIFT:
                creature.vel.y = -jump_power * jump_charge2

    if keys.held(Input.LEFT, Player.P1):
        character.vel.x = -100
    elif keys.held(Input.RIGHT, Player.P1):
        character.vel.x = 100
    else:
        character.vel.x = 0

    if keys.held(Input.LEFT, Player.P2):
        creature.vel.x = -100
    elif keys.held(Input.RIGHT, Player.P2):
        creature.vel.x = 100
    else:
        creature.vel.x = 0

    # Update
    jump_charge = clamp(jump_charge + elapsed_time * 2, 0, 1.0)
    jump_charge2 = clamp(jump_charge2 + elapsed_time * 2, 0, 1.0)

    character.vel.y = clamp(
        character.vel.y + gravity * elapsed_time, -400.0, 400.0
    )
    move_object(
        grid, character, character.get_pos() + character.vel * elapsed_time
    )
    # character.hitbox.pos += character.vel * elapsed_time

    creature.vel.y = clamp(
        creature.vel.y + gravity * elapsed_time, -400.0, 400.0
    )
    move_object(
        grid, creature, creature.get_pos() + creature.vel * elapsed_time
    )
    # creature.hitbox.pos += creature.vel * elapsed_time

    # Collision
    for tv, cam in [(tv1, camera), (tv2, camera2)]:
        view = Rect(tv.get_world_tl(), tv.get_world_br() - tv.get_world_tl())
        view_ext = Rect(view.pos - view_tl_offset, view.size + view_br_offet)
        visible_objects = grid.get_objects_in_region(view.pos, view.size)

        for obj in visible_objects:
            if not obj.can_move:
                continue
            for other in visible_objects:
                if obj == other:
                    continue

                if overlaps(obj.hitbox, other.hitbox):
                    if other.can_move:
                        res = resolve_collision(obj.hitbox, other.hitbox, True)
                        move_object(grid, obj, res[0])
                        move_object(grid, other, res[1])
                    else:
                        if obj.hitbox.pos.y < other.hitbox.pos.y:
                            obj.vel.y = 0
                        res = resolve_collision(obj.hitbox, other.hitbox)
                        move_object(grid, obj, res[0])

        cam.update(elapsed_time)
        # When zoom to camera view pos which is always top left, updating
        # world offset directly shifts away the zoomed position. To make
        # this work properly, the scale of the camera has to be changed as
        # well, ie. the view size
        tv.set_world_offset(cam.get_view_pos())

        # if overlaps(character.hitbox, creature_hitbox):
        #     creature_hitbox.pos = resolve_collision(
        #         creature_hitbox, character.hitbox
        #     )[0]

    screen.fill((0, 0, 0))
    for tv, cam, cam_x in [(tv1, camera, 0), (tv2, camera2, 400)]:
        view = Rect(tv.get_world_tl(), tv.get_world_br() - tv.get_world_tl())
        view_ext = Rect(view.pos - view_tl_offset, view.size + view_br_offet)

        screen.set_clip(((cam_x, 0), tv._view_area))

        for obj in grid.get_objects_in_region(view_ext.pos, view_ext.size):
            obj.draw_self(tv)

    screen.set_clip(None)
    pygame.draw.line(
        screen, (255, 255, 255), (WIDTH // 2, 0), (WIDTH // 2, HEIGHT)
    )
    pygame.draw.line(
        screen, (0, 0, 0), (WIDTH // 2 + 1, 0), (WIDTH // 2 + 1, HEIGHT)
    )
    text = (
        f"VZ: {character.vel.y:.3f} JUMP Charge: {jump_charge:.4f} \n"
        f"Cam: {tv1.world_to_screen(camera.get_pos())} WO: {tv1.get_world_offset()}\n"
        f"{zoom_at} \n"
        f"Char: {character.get_pos()} MP: {pygame.mouse.get_pos()}"
    )
    text_surf = my_font.render(text, False, (255, 255, 255))
    text_surf2 = my_font.render(text, False, (0, 0, 0))
    screen.blit(text_surf2, (6, 6))
    screen.blit(text_surf, (4, 4))
    pygame.display.flip()

    frame_ctr += 1
    frame_time += elapsed_time

    if frame_time >= 1.0:
        pygame.display.set_caption(f"FPS: {frame_ctr}")
        frame_ctr = 0
        frame_time -= 1.0

pygame.quit()

# profiler.disable()
# profiler.dump_stats("test2.prof")
