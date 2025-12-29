import os
import sys
from functools import cache
from typing import TYPE_CHECKING, Literal, Self, overload

from based_utils.cli import apply_ansi_style
from based_utils.data import ignore

from .color import Color
from .palettes import Colors

if TYPE_CHECKING:
    from collections.abc import Callable

    from based_utils.cli.io import StringStyler

    from .color import RGB


@cache
def _has_colors() -> bool:
    no = "NO_COLOR" in os.environ
    yes = "CLICOLOR_FORCE" in os.environ
    maybe = sys.stdout.isatty()
    return not no and (yes or maybe)


type _StringStyler = Callable[[str], str]


def _wrap_ansi_style(*values: int) -> StringStyler:
    return apply_ansi_style(*values) if _has_colors() else ignore


bold = _wrap_ansi_style(1)
faint = _wrap_ansi_style(2)
italic = _wrap_ansi_style(3)
underlined = _wrap_ansi_style(4)
inverse = _wrap_ansi_style(7)
strikethrough = _wrap_ansi_style(9)

black = _wrap_ansi_style(30)
red = _wrap_ansi_style(31)
green = _wrap_ansi_style(32)
yellow = _wrap_ansi_style(33)
blue = _wrap_ansi_style(34)
magenta = _wrap_ansi_style(35)
cyan = _wrap_ansi_style(36)
gray = _wrap_ansi_style(37)

black_background = _wrap_ansi_style(40)
red_background = _wrap_ansi_style(41)
green_background = _wrap_ansi_style(42)
yellow_background = _wrap_ansi_style(43)
blue_background = _wrap_ansi_style(44)
magenta_background = _wrap_ansi_style(45)
cyan_background = _wrap_ansi_style(46)
gray_background = _wrap_ansi_style(47)

light_gray = _wrap_ansi_style(90)
light_red = _wrap_ansi_style(91)
light_green = _wrap_ansi_style(92)
light_yellow = _wrap_ansi_style(93)
light_blue = _wrap_ansi_style(94)
light_magenta = _wrap_ansi_style(95)
light_cyan = _wrap_ansi_style(96)
white = _wrap_ansi_style(97)


def color_8bit(fg: int = None, bg: int = None) -> _StringStyler:
    values = []
    if fg:
        values += [38, 5, fg]
    if bg:
        values += [48, 5, bg]
    return _wrap_ansi_style(*values)


def color_rgb(fg: RGB = None, bg: RGB = None) -> _StringStyler:
    values = []
    if fg:
        values += [38, 2, *fg]
    if bg:
        values += [48, 2, *bg]
    return _wrap_ansi_style(*values)


class ColorStr[T](str):
    value: T
    bg: Color | None
    fg: Color | None
    __slots__ = "bg", "fg", "value"

    def __new__(cls, value: T, fg: Color = None, bg: Color = None) -> Self:
        fg_rgb, bg_rgb = fg.as_rgb if fg else None, bg.as_rgb if bg else None
        instance = super().__new__(cls, color_rgb(fg_rgb, bg_rgb)(str(value)))
        instance.value, instance.fg, instance.bg = (value, fg, bg)
        return instance

    def __len__(self) -> int:
        return len(str(self.value))

    def with_color(self, color: Color) -> ColorStr:
        return ColorStr(self.value, color, self.bg)

    def with_background(self, background: Color) -> ColorStr:
        return ColorStr(self.value, self.fg, background)


class Colored:
    def __init__(self, fg: Color = None, bg: Color = None) -> None:
        self._fg, self._bg = fg, bg

    def __call__(self, v: object) -> ColorStr:
        return ColorStr(v, self._fg, self._bg)


OK = Colored(Colors.green)("✔")
FAIL = Colored(Colors.red)("✘")


class Highlighter:
    def __init__(self, color: Color) -> None:
        self._color = color

    @overload
    def __call__(
        self, v: object, *, inverted: bool = False, enabled: Literal[True] = True
    ) -> ColorStr: ...

    @overload
    def __call__(
        self, v: object, *, inverted: bool = False, enabled: bool = True
    ) -> str: ...

    def __call__(
        self, v: object, *, inverted: bool = False, enabled: bool = True
    ) -> ColorStr | str:
        if not enabled:
            return str(v)
        c, k = self._color.contrasting_shade_pair
        return Colored(*((c, k) if inverted else (k, c)))(v)


CP = Color.Props


class ColorHighlighter:
    def __init__(self, color: Color) -> None:
        self._color = color

    def __call__(
        self, highlighted: CP = CP.ALL, *, enable_bounds_highlights: bool = False
    ) -> str:
        c = self._color
        # Colors progressively built up with hue, saturation & lightness
        decomposed = [c.with_props(CP.H), c.with_props(CP.NO_L), c]
        # Go over each color property and highlight it if necessary.
        values = " ".join(
            Highlighter(k)(f" {s} ", enabled=p in highlighted)
            for (s, k, p) in zip(c.prop_strings(), decomposed, CP, strict=True)
        )
        n, start, end = b = "HSLuv", "[", "]"
        if enable_bounds_highlights:
            # When some of the values were highlighted, highlight the outer brackets
            # as well to make it visually stand out more.
            n, start, end = [Highlighter(c)(s, enabled=bool(highlighted)) for s in b]
        return f"{n} {start} {values} {end}"
