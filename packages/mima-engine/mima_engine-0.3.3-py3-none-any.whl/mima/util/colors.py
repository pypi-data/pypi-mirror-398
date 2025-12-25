from typing import Tuple


class Color:
    def __init__(self, red: int, green: int, blue: int, alpha: int = 255):
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha

    def getRGBA(self) -> Tuple[int, int, int, int]:
        return (self.red, self.green, self.blue, self.alpha)

    def getRGB(self) -> Tuple[int, int, int]:
        return (self.red, self.green, self.blue)

    def __repr__(self):
        return (
            f"Color(red={self.red}, green={self.green}, "
            f"blue={self.blue}, alpha={self.alpha})"
        )

    def short_name(self):
        return f"{self.red}-{self.green}-{self.blue}-{self.alpha}"


BLACK = Color(0, 0, 0)
WHITE = Color(255, 255, 255)
ALPHA = Color(254, 253, 254)
LIGHTGREY = Color(100, 100, 100)
DARK_GREY = Color(64, 64, 64, 160)
VERY_LIGHT_GREY = Color(195, 195, 195)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
YELLOW = Color(255, 255, 0)
CYAN = Color(0, 255, 255)
PURPLE = Color(128, 0, 128)
DARK_RED = Color(64, 0, 0, 160)
DARK_GREEN = Color(0, 64, 0, 160)
DARK_BLUE = Color(0, 0, 64, 160)
DARK_YELLOW = Color(64, 64, 0, 160)
DARK_CYAN = Color(0, 64, 64, 160)
DARK_PURPLE = Color(64, 0, 64, 160)
TRANS_CYAN = Color(0, 64, 64, 128)
TRANS_LIGHT_RED = Color(255, 0, 0, 128)
TRANS_LIGHT_YELLOW = Color(255, 255, 0, 128)
TRANS_LIGHT_CYAN = Color(0, 255, 255, 128)
TRANS_LIGHT_PURPLE = Color(255, 0, 255, 128)
TRANS_LIGHT_GREEN = Color(0, 255, 0, 128)
