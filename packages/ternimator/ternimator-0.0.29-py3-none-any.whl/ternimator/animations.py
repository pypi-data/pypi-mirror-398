from functools import reduce
from itertools import count
from typing import TYPE_CHECKING

from based_utils.cli import term_size
from based_utils.math import randf
from kleur import Color, Colored

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from based_utils.cli import Lines


type Animation = Callable[[Lines, int], Lines]


def _frame(n: int) -> Callable[[Lines, Animation], Lines]:
    def wrapped(f: Lines, anim: Animation) -> Lines:
        return anim(f, n)

    return wrapped


def _frame0(lines: Lines, *, fill_char: str = " ") -> Lines:
    lines = list(lines)
    w_block = max(len(line) for line in lines)
    w_term, _max_height = term_size()
    for line in lines:
        yield line.ljust(w_block, fill_char).center(w_term, fill_char)


def animated_lines(
    lines: Lines | str, *animations: Animation, fill_char: str = " "
) -> Iterator[Lines]:
    if isinstance(lines, str):
        lines = lines.splitlines()
    frame_0 = list(_frame0(lines, fill_char=fill_char))
    for n in count():
        yield reduce(_frame(n), animations, frame_0)


def _fixed_length(anim: Animation, n_frames: int = None) -> Animation:
    if not n_frames:
        n_frames, _max_height = term_size()

    def wrapped_anim(frame_0: Lines, n: int) -> Lines:
        yield from anim(frame_0, n % n_frames)

    return wrapped_anim


def moving_forward(n_frames: int = None) -> Animation:
    def anim(frame_0: Lines, n: int) -> Lines:
        for line in frame_0:
            yield line[-n:] + line[:-n]

    return _fixed_length(anim, n_frames)


def fuck_me_sideways(n_frames: int = None) -> Animation:
    def anim(frame_0: Lines, n: int) -> Lines:
        lines = list(frame_0)
        height = len(lines) - 1
        half_height = height // 2
        for y, line in enumerate(lines):
            x = n * (half_height - ((half_height + y) % height))
            yield line[x:] + line[:x]

    return _fixed_length(anim, n_frames)


def _colorful(
    colors: Callable[[float, float], tuple[Color, Color]], amount_of_hues: int = 360
) -> Animation:
    def anim(frame_0: Lines, n: int) -> Lines:
        c = Colored(*colors(n, n / amount_of_hues))
        for line in frame_0:
            yield c(line)

    return anim


def changing_colors(*, amount_of_hues: int = 360) -> Animation:
    def colors(_n: float, hue: float) -> tuple[Color, Color]:
        c = Color(hue, lightness=0.75)
        return c, c.contrasting_hue.contrasting_shade

    return _colorful(colors, amount_of_hues)


def flashing(
    *,
    amount_of_hues: int = 360,
    intensity: float = 0.03,
    flash_ratio: int = 3,
    fg: Color = None,
    bg: Color = None,
) -> Animation:
    def colors(n: float, hue: float) -> tuple[Color, Color]:
        flash = n % flash_ratio == 0 and randf() < intensity * flash_ratio
        if flash:
            c_flash = Color(hue + 0.5 if fg else randf())
            return c_flash.shade(0.3), c_flash.shade(0.8)
        c = Color(hue)
        return fg or c.shade(0.5), bg or c.shade(0.2)

    return _colorful(colors, amount_of_hues)
