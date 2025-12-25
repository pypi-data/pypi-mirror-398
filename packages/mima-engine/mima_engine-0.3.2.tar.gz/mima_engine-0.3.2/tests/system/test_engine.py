import os
import random

from mima.core.engine import MimaEngine
from mima.util.colors import Color


class MyTestEngine(MimaEngine):
    def __init__(self):
        super().__init__(
            init_file=os.path.abspath("tests/fixtures/assets.txt"),
            config_path="mima_config.ini",
            default_config=None,
            platform="PC",
            caption="TestEngine",
        )
        self.timer = 0.0

    def on_user_create(self):
        # print("On Create")
        return True

    def on_user_update(self, elapsed_time):
        # print("On Update:", self.elapsed_time)
        self.timer += elapsed_time
        if self.timer >= 5.0:
            return False

        for x in range(0, self.backend.render_width, 16):
            for y in range(0, self.backend.render_height, 16):
                self.backend.draw_pixel(
                    x,
                    y,
                    Color(
                        random.randint(0, 255),
                        random.randint(0, 255),
                        random.randint(0, 255),
                    ),
                )
        return True


if __name__ == "__main__":
    game = MyTestEngine()
    if game.construct(256, 240, 1):
        game.start()
