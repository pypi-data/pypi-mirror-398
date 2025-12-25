from .constants import BIG_FONT_WIDTH


def strtobool(val: str) -> bool:
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0", ""):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))


def wrap_text(text: str, n_chars: int = 0) -> list[str]:
    if n_chars == 0:
        return [text]

    words = text.split(" ")
    lines: list[str] = []
    new_text = ""
    for idx, word in enumerate(words):
        if len(new_text + word) > n_chars:
            lines.append(new_text)
            new_text = ""

        new_text += f"{word.strip()} "
    # new_text.strip()
    lines.append(new_text.strip())
    return lines


def text_to_center(text: str, ppx: int, pwidth: int, font_width=BIG_FONT_WIDTH):
    return int(ppx + pwidth / 2 - (len(text) / 2 * BIG_FONT_WIDTH))
