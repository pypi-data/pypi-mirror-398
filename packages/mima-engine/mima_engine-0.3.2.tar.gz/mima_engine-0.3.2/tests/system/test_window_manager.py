from typing import Any, Protocol

import pygame

from mima.advanced.scene import Position, Scene, SceneManager, View, Window

SIZE = 1920, 1080
# SIZE = 960, 540
pygame.init()
pygame.font.init()
flags = (
    pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED  # | pygame.FULLSCREEN
)
my_font = pygame.font.SysFont("Nimbus Sans", 20)
screen = pygame.display.set_mode(SIZE)
clock = pygame.time.Clock()

TITLE_SCENE = 0
GAME_SCENE = 1

TITLE_VIEW = 0
GAME_VIEW = 1
MENU_VIEW = 2



class TitleView(View[int]):
    def __init__(self) -> None:
        super().__init__(TITLE_VIEW, screen)

    def handle_input(
        self, events: list[pygame.event.Event] | None
    ) -> list[pygame.event.Event]:
        events = self.ttv.handle_pan_and_zoom(events=events)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_d:
                    self.push_scene(GAME_SCENE)
                if e.key == pygame.K_f:
                    self.push_scene(
                        GAME_SCENE, {"layout": [Position.TOP, Position.BOTTOM]}
                    )
                if e.key == pygame.K_c:
                    self.push_scene(
                        GAME_SCENE, {"layout": [Position.LEFT, Position.RIGHT]}
                    )
                if e.key == pygame.K_x:
                    self.push_scene(
                        GAME_SCENE,
                        {
                            "layout": [
                                Position.TOP_LEFT,
                                Position.TOP_RIGHT,
                                Position.BOTTOM_LEFT,
                                Position.BOTTOM_RIGHT,
                            ]
                        },
                    )

        return events

    def update(self, elapsed_time: float) -> bool:
        return True

    def draw(self) -> None:
        self.ttv.fill_rect(self._pos, self._size, (246, 204, 64))


class GameView(View[int]):
    def __init__(self) -> None:
        super().__init__(GAME_VIEW, screen)

    def handle_input(
        self, events: list[pygame.event.Event] | None
    ) -> list[pygame.event.Event]:
        events = self.ttv.handle_pan_and_zoom(events=events)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if self._position in [
                    Position.FULL,
                    Position.TOP,
                    Position.LEFT,
                    Position.TOP_LEFT,
                ]:
                    if e.key == pygame.K_a:
                        self.pop_scene(empty_ok=True)
                    if e.key == pygame.K_s:
                        self.push_view(MENU_VIEW)
                else:
                    if e.key == pygame.K_l:
                        self.push_view(MENU_VIEW)

        return events

    def draw(self) -> None:
        if self._position == Position.FULL:
            color = (0, 183, 69)
        else:
            color = (
                0,
                (self._position.value * 186 + self._position.value) % 256,
                (self._position.value * 64 + self._position.value) % 256,
            )
        self.ttv.fill_rect(pygame.Vector2(0, 0), self._size, color)

        self.ttv.draw_surface(
            pygame.Vector2(10, 10),
            my_font.render(f"{self._position.name}", False, (255, 255, 255)),
        )


class MenuView(View[int]):
    def __init__(self) -> None:
        super().__init__(MENU_VIEW, screen)

    def handle_input(
        self, events: list[pygame.event.Event] | None
    ) -> list[pygame.event.Event]:
        events = self.ttv.handle_pan_and_zoom(events=events)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if self._position in [
                    Position.FULL,
                    Position.TOP,
                    Position.LEFT,
                    Position.TOP_LEFT,
                ]:
                    if e.key == pygame.K_a:
                        self.pop_scene(empty_ok=True)
                    if e.key == pygame.K_w:
                        self.pop_view()
                else:
                    if e.key == pygame.K_j:
                        self.pop_view()
        return events

    def draw(self) -> None:
        self.ttv.fill_rect(pygame.Vector2(0, 0), self._size, (0, 144, 54))

        txt = f"{self._position.name}"

        self.ttv.draw_surface(
            pygame.Vector2(10, 10), my_font.render(txt, False, (255, 255, 255))
        )


class TitleScene(Scene):
    def enter_focus(self, data: dict[str, Any]) -> None:
        self._windows[0] = Window[int](Position.FULL)
        self._windows[0].add_view(TitleView())
        self._windows[0].push_view(TITLE_VIEW)
        self._windows[0]._scene = self

    def exit_focus(self) -> dict[str, Any]:
        self._windows.clear()
        return {}


class GameScene(Scene):
    def __init__(self):
        super().__init__()

    def enter_focus(self, data: dict[str, Any]) -> None:
        layout = data.get("layout", [Position.FULL])
        for pos in layout:
            self._windows[pos.value] = Window[int](pos)
            self._windows[pos.value].add_view(GameView())
            self._windows[pos.value].add_view(MenuView())
            self._windows[pos.value].push_view(GAME_VIEW)
            self._windows[pos.value]._scene = self

    def exit_focus(self) -> dict[str, Any]:
        self._windows.clear()
        return {}


sm = SceneManager[int, int]()
sm.add_scene(TitleScene(), TITLE_SCENE)
sm.add_scene(GameScene(), GAME_SCENE)
sm.push_scene(TITLE_SCENE)


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

    sm.handle_input(events)
    sm.update(elapsed_time)

    screen.fill((0, 0, 0))
    sm.draw()

    fps_text = f"{fps}"
    screen.blit(
        my_font.render(fps_text, False, (0, 0, 0)),
        (SIZE[0] - len(fps_text) * 14 - 1, SIZE[1] - 21),
    )
    screen.blit(
        my_font.render(fps_text, False, (255, 255, 255)),
        (SIZE[0] - len(fps_text) * 14, SIZE[1] - 20),
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
