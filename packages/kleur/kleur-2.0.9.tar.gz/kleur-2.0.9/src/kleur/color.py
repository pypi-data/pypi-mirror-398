from dataclasses import dataclass, replace
from enum import IntFlag, auto
from functools import cached_property, total_ordering
from typing import TYPE_CHECKING, NamedTuple

from based_utils.class_utils import Modifier, WithAttrModifiers
from based_utils.interpol import mapped, mapped_cyclic, trim, trim_cyclic
from hsluv import hex_to_hsluv, hsluv_to_hex, hsluv_to_rgb, rgb_to_hsluv

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

_INCREASE_STEP = 0.2


def normalize_rgb_hex(rgb_hex: str) -> str:
    """
    Try to normalize a hex string into a rrggbb hex.

    :param rgb_hex: RGB hex string (may start with '#')
    :return: rrggbb hex

    >>> normalize_rgb_hex("3")
    '333333'
    >>> normalize_rgb_hex("03")
    '030303'
    >>> normalize_rgb_hex("303")
    '330033'
    >>> normalize_rgb_hex("808303")
    '808303'
    """
    rgb_hex, r, g, b = rgb_hex.removeprefix("#").lower(), "", "", ""

    match len(rgb_hex):
        case 1:
            # 3 -> r=33, g=33, b=33
            r = g = b = rgb_hex * 2

        case 2:
            # 03 -> r=03, g=03, b=03
            r = g = b = rgb_hex

        case 3:
            # 303 -> r=33, g=00, b=33
            r1, g1, b1 = iter(rgb_hex)
            r, g, b = r1 * 2, g1 * 2, b1 * 2

        case 6:
            # 808303 -> r=80, g=83, b=03
            r1, r2, g1, g2, b1, b2 = iter(rgb_hex)
            r, g, b = r1 + r2, g1 + g2, b1 + b2

        case _:
            raise ValueError(rgb_hex)

    return f"{r}{g}{b}"


type RGB = tuple[int, int, int]


class _HSLuv(NamedTuple):
    hue: float
    saturation: float
    lightness: float

    @classmethod
    def from_hex(cls, rgb_hex: str) -> _HSLuv:
        return cls(*hex_to_hsluv(f"#{rgb_hex}"))

    @property
    def as_hex(self) -> str:
        return hsluv_to_hex(self)[1:]

    @classmethod
    def from_rgb(cls, rgb: RGB) -> _HSLuv:
        r, g, b = rgb
        return cls(*rgb_to_hsluv((r / 255, g / 255, b / 255)))

    @property
    def as_rgb(self) -> RGB:
        r, g, b = hsluv_to_rgb(self)
        return round(r * 255), round(g * 255), round(b * 255)


@total_ordering
@dataclass(frozen=True)
class Color(WithAttrModifiers):
    class Props(IntFlag):
        H = auto()
        S = auto()
        L = auto()
        NONE = 0
        NO_L = H | S
        NO_S = H | L
        ALL = H | S | L

    hue: float = 0  # 0 - 1 (full circle angle)
    saturation: float = 1  # 0 - 1 (ratio)
    lightness: float = 0.5  # 0 - 1 (ratio)

    @property
    def _attr_modifiers(self) -> dict[str, Modifier]:
        return {"hue": trim_cyclic, "saturation": trim, "lightness": trim}

    def __repr__(self) -> str:
        sh, ss, sl = self.prop_strings()
        return f"HSLuv({sh}, {ss}, {sl})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Color):
            return self.as_rgb == other.as_rgb
        raise NotImplementedError

    def __hash__(self) -> int:
        return hash(iter(self))

    def __lt__(self, other: Color) -> bool:
        return self.as_sortable_tuple < other.as_sortable_tuple

    def __iter__(self) -> Iterator[float]:
        yield self.hue
        yield self.saturation
        yield self.lightness

    def __add__(self, other: Color) -> Color:
        return Color(
            self.hue + other.hue,
            self.saturation + other.saturation,
            self.lightness + other.lightness,
        )

    def __sub__(self, other: Color) -> Color:
        return Color(
            self.hue - other.hue,
            self.saturation - other.saturation,
            self.lightness - other.lightness,
        )

    def with_props(self, props: Props) -> Color:
        """
        Color built up with from a selection of its original hue, saturation, lightness.

        This could be helpful for understanding how colors
        are built up and relate to each other.
        """
        prop_values = zip(self, self.Props, strict=True)
        return Color(*[v for v, p in prop_values if p in props])

    def prop_strings(self) -> Iterator[str]:
        for v, s in zip(self._as_hsluv, ("°", "%", "%"), strict=True):
            yield f"{v:.2f}{s}".rjust(7)

    @cached_property
    def as_sortable_tuple(self) -> tuple[float, float, float]:
        """Will decide the sort order."""
        return self.lightness, self.saturation, self.hue

    @classmethod
    def _from_hsluv(cls, hsluv: _HSLuv) -> Color:
        return cls(hsluv.hue / 360, hsluv.saturation / 100, hsluv.lightness / 100)

    @cached_property
    def _as_hsluv(self) -> _HSLuv:
        return _HSLuv(self.hue * 360, self.saturation * 100, self.lightness * 100)

    @classmethod
    def from_hex(cls, rgb_hex: str) -> Color:
        """
        Create a Color from an RGB hex string.

        :param rgb_hex: RGB hex string (may start with '#')
        :return: Color instance

        >>> c = Color.from_hex("808303")
        >>> c.as_hex, c.as_rgb
        ('808303', (128, 131, 3))
        >>> k = Color.from_hex("0af")
        >>> k.as_hex, k.as_rgb
        ('00aaff', (0, 170, 255))
        """
        return cls._from_hsluv(_HSLuv.from_hex(normalize_rgb_hex(rgb_hex)))

    @cached_property
    def as_hex(self) -> str:
        return self._as_hsluv.as_hex

    @classmethod
    def from_rgb(cls, rgb: RGB) -> Color:
        """
        Create a Color from RGB values.

        :param rgb: RGB instance
        :return: Color instance

        >>> c = Color.from_rgb((128, 131, 3))
        >>> c.as_hex, c.as_rgb
        ('808303', (128, 131, 3))
        >>> k = Color.from_rgb((0, 170, 255))
        >>> k.as_hex, k.as_rgb
        ('00aaff', (0, 170, 255))
        """
        return cls._from_hsluv(_HSLuv.from_rgb(rgb))

    @cached_property
    def as_rgb(self) -> RGB:
        return self._as_hsluv.as_rgb

    def with_hue(self, hue: float) -> Color:
        return replace(self, hue=hue)

    def saturated(self, saturation: float) -> Color:
        return replace(self, saturation=saturation)

    def shade(self, lightness: float) -> Color:
        return replace(self, lightness=lightness)

    def shades(self, n_intervals: int) -> Iterator[Color]:
        for step in range(1, n_intervals):
            yield self.shade(step / n_intervals)

    @cached_property
    def very_dark(self) -> Color:
        return self.shade(1 / 8)

    @cached_property
    def dark(self) -> Color:
        return self.shade(2 / 8)

    @cached_property
    def slightly_dark(self) -> Color:
        return self.shade(3 / 8)

    @cached_property
    def slightly_bright(self) -> Color:
        return self.shade(5 / 8)

    @cached_property
    def bright(self) -> Color:
        return self.shade(6 / 8)

    @cached_property
    def very_bright(self) -> Color:
        return self.shade(7 / 8)

    def brighter(self, relative_amount: float = _INCREASE_STEP) -> Color:
        return self + Color(hue=0, saturation=0, lightness=relative_amount)

    @cached_property
    def slightly_brighter(self) -> Color:
        return self.brighter(_INCREASE_STEP * 0.5)

    @cached_property
    def much_brighter(self) -> Color:
        return self.brighter(_INCREASE_STEP * 1.5)

    def darker(self, relative_amount: float = _INCREASE_STEP) -> Color:
        return self - Color(hue=0, saturation=0, lightness=relative_amount)

    @cached_property
    def slightly_darker(self) -> Color:
        return self.darker(_INCREASE_STEP * 0.5)

    @cached_property
    def much_darker(self) -> Color:
        return self.darker(_INCREASE_STEP * 1.5)

    @cached_property
    def has_ambiguous_hue(self) -> bool:
        """
        Determine if this color has a visually ambiguous hue.

        This can occur in three cases:
        1. With lightness set to 0, any color becomes black
        2. With lightness set to 1, any color becomes white
        3. With saturation set to 0, any color becomes grey
        """
        # We can use the fact here that all three cases will result in equal RGB values.
        r, g, b = self.as_rgb
        return r == g == b

    def align_with(self, other: Color) -> tuple[Color, Color]:
        """
        Align two colors with each other, when their hues are visually ambiguous.

        This can come out handy for producing gradients from grey values to colors
        with consistent hue. Since the grey color could have any hue, the gradient
        would show an unpredictable (and most likely unwanted) hue shift otherwise.

        >>> Color(0.4, 1, 0.5).align_with(Color(0.6, 0.25, 0.75))
        (HSLuv(144.00°, 100.00%,  50.00%), HSLuv(216.00°,  25.00%,  75.00%))

        >>> Color(0.4, 0, 0.5).align_with(Color(0.6, 0.25, 0.75))
        (HSLuv(216.00°,   0.00%,  50.00%), HSLuv(216.00°,  25.00%,  75.00%))
        >>> Color(0.4, 1, 0.5).align_with(Color(0.6, 0, 0.75))
        (HSLuv(144.00°, 100.00%,  50.00%), HSLuv(144.00°,   0.00%,  75.00%))
        >>> Color(0.4, 0, 0.5).align_with(Color(0.6, 0, 0.75))
        (HSLuv(216.00°,   0.00%,  50.00%), HSLuv(216.00°,   0.00%,  75.00%))

        >>> Color(0.4, 1, 0).align_with(Color(0.6, 0.25, 0.75))
        (HSLuv(216.00°, 100.00%,   0.00%), HSLuv(216.00°,  25.00%,  75.00%))
        >>> Color(0.4, 1, 0.5).align_with(Color(0.6, 0.25, 0))
        (HSLuv(144.00°, 100.00%,  50.00%), HSLuv(144.00°,  25.00%,   0.00%))
        >>> Color(0.4, 1, 0).align_with(Color(0.6, 0.25, 0))
        (HSLuv(216.00°, 100.00%,   0.00%), HSLuv(216.00°,  25.00%,   0.00%))

        >>> Color(0.4, 1, 1).align_with(Color(0.6, 0.25, 0.75))
        (HSLuv(216.00°, 100.00%, 100.00%), HSLuv(216.00°,  25.00%,  75.00%))
        >>> Color(0.4, 1, 0.5).align_with(Color(0.6, 0.25, 1))
        (HSLuv(144.00°, 100.00%,  50.00%), HSLuv(144.00°,  25.00%, 100.00%))
        >>> Color(0.4, 1, 1).align_with(Color(0.6, 0.25, 1))
        (HSLuv(216.00°, 100.00%, 100.00%), HSLuv(216.00°,  25.00%, 100.00%))
        """
        c, k = self, other
        if c.has_ambiguous_hue:
            c = c.with_hue(k.hue)
        if k.has_ambiguous_hue:
            k = k.with_hue(c.hue)
        return c, k

    def blend(self, other: Color, amount: float = 0.5) -> Color:
        """
        Blend two colors.

        >>> Color(0.1, 1, 0.5).blend(Color(0.3, 0.25, 0.75), 0.25)
        HSLuv( 54.00°,  81.25%,  56.25%)
        >>> Color(0.1, 1, 0.5).blend(Color(0.9, 0.25, 0.75), 0.25)
        HSLuv( 18.00°,  81.25%,  56.25%)
        >>> Color(0.9, 1, 0.5).blend(Color(0.1, 0.25, 0.75), 0.25)
        HSLuv(342.00°,  81.25%,  56.25%)

        >>> Color(0.4, 1, 0.5).blend(Color(0.6, 0.25, 0.75), 0.25)
        HSLuv(162.00°,  81.25%,  56.25%)

        >>> Color(0.4, 0, 0.5).blend(Color(0.6, 0.25, 0.75), 0.25)
        HSLuv(216.00°,   6.25%,  56.25%)
        >>> Color(0.4, 1, 0.5).blend(Color(0.6, 0, 0.75), 0.25)
        HSLuv(144.00°,  75.00%,  56.25%)
        >>> Color(0.4, 0, 0.5).blend(Color(0.6, 0, 0.75), 0.25)
        HSLuv(216.00°,   0.00%,  56.25%)

        >>> Color(0.4, 1, 0).blend(Color(0.6, 0.25, 0.75), 0.25)
        HSLuv(216.00°,  81.25%,  18.75%)
        >>> Color(0.4, 1, 0.5).blend(Color(0.6, 0.25, 0), 0.25)
        HSLuv(144.00°,  81.25%,  37.50%)
        >>> Color(0.4, 1, 0).blend(Color(0.6, 0.25, 0), 0.25)
        HSLuv(216.00°,  81.25%,   0.00%)

        >>> Color(0.4, 1, 1).blend(Color(0.6, 0.25, 0.75), 0.25)
        HSLuv(216.00°,  81.25%,  93.75%)
        >>> Color(0.4, 1, 0.5).blend(Color(0.6, 0.25, 1), 0.25)
        HSLuv(144.00°,  81.25%,  62.50%)
        >>> Color(0.4, 1, 1).blend(Color(0.6, 0.25, 1), 0.25)
        HSLuv(216.00°,  81.25%, 100.00%)
        """
        c, k = self.align_with(other)
        hs, ss, ls = zip(c, k, strict=True)
        return Color(mapped_cyclic(amount, hs), mapped(amount, ss), mapped(amount, ls))

    @cached_property
    def contrasting_shade(self) -> Color:
        """
        Color with a lightness that contrasts with the current color.

        Color with a 50% lower or higher lightness than the current color,
        while maintaining the same hue and saturation (so it can for example
        be used as background color).

        :return: Color representation of the contrasting shade

        >>> hex_strs = ["08f", "0f8", "80f", "8f0", "f08", "f80"]
        >>> for c, k in [Color.from_hex(h).contrasting_shade_pair for h in hex_strs]:
        ...     print(f"{c.as_hex} <-> {k.as_hex}")
        0088ff <-> 001531
        00ff88 <-> 006935
        8800ff <-> ebe4ff
        88ff00 <-> 366b00
        ff0088 <-> 2b0012
        ff8800 <-> 4a2300
        """
        return self.shade((self.lightness + 0.5) % 1)

    @cached_property
    def contrasting_shade_pair(self) -> tuple[Color, Color]:
        """
        Return this color together with its contrasting shade.

        Turns out to be useful quite commonly in practice, especially in situations
        when you'd want to accommodate a color with a background that would deliver the
        best contrast in terms of visibility.
        """
        return self, self.contrasting_shade

    @cached_property
    def contrasting_hue(self) -> Color:
        """
        Color with a hue that contrasts with the current color.

        Color with a 180° different hue than the current color,
        while maintaining the same saturation and perceived lightness.

        :return: Color representation of the contrasting hue

        >>> hex_strs = ["08f", "0f8", "80f", "8f0", "f08", "f80"]
        >>> for c, k in [Color.from_hex(h).contrasting_hue_pair for h in hex_strs]:
        ...     print(f"{c.as_hex} <-> {k.as_hex}")
        0088ff <-> 9c8900
        00ff88 <-> ffd1f5
        8800ff <-> 5c6900
        88ff00 <-> f6d9ff
        ff0088 <-> 009583
        ff8800 <-> 00b8d1
        """
        return self.with_hue(self.hue + 0.5)

    @cached_property
    def contrasting_hue_pair(self) -> tuple[Color, Color]:
        """Return this color together with its contrasting hue."""
        return self, self.contrasting_hue


def blend_colors(c: Color, k: Color) -> Callable[[float], Color]:
    def wrapped(amount: float) -> Color:
        return c.blend(k, amount)

    return wrapped
