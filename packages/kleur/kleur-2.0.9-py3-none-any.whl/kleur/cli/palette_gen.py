from typing import TYPE_CHECKING

from based_utils.class_utils import get_class_vars
from based_utils.cli import (
    ArgsParser,
    CommandRunner,
    check_integer_in_range,
    parse_key_value_pair,
)
from based_utils.data import try_convert
from based_utils.interpol import LinearMapping

from kleur import BLACK, GREY, WHITE, AltColors, Color, Colors, ColorStr, Highlighter, c

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Iterable, Iterator


def _perc(s: float) -> str:
    return f"{round(s * 100, 1):n}%"


class _CommandRunner(CommandRunner):
    def __init__(self, args: Namespace) -> None:
        ns, nv = args.number_of_shades, args.number_of_vibrances
        self._shades = [s / (ns + 1) for s in range(1, ns + 1)]
        self._vibrances = [v / nv for v in range(1, nv + 1)]

        colors: dict[str, Color] = {}

        if args.merge_with_default_palette or not args.colors:
            # Add colors from default palette.
            palette_cls = AltColors if args.alt_default_palette else Colors
            colors |= get_class_vars(palette_cls, value_type=Color)

        # Add custom colors from args.
        for name, hue in args.colors:
            h = try_convert(int, hue, default=333) % 360
            colors[name] = c(h)

        self._colors = dict(sorted(colors.items(), key=lambda i: i[1].hue))
        self._label_length = max(len(n) for n in self._colors) + 6
        # Shades percentages are right above the first color, so let's give them a
        # contrasting hue. Furthermore, making them slightly brighter as the shade
        # increases will give them a more uniform appearance to the human eye.
        self._percentage_color = next(iter(self._colors.values())).contrasting_hue
        # Values based on experimenting with palettes differing in starting color.
        # Overall this seems to work well, or at least to my eyes :)
        self._neutral_shade_lo, self._neutral_shade_hi = 0.6, 0.75
        self._shade_map = LinearMapping(self._neutral_shade_lo, self._neutral_shade_hi)

    def _percentage_columns(self, v: float) -> Iterator[str]:
        cp, sm = self._percentage_color.saturated(v), self._shade_map
        c0 = cp.shade(self._neutral_shade_lo)
        yield ColorStr(f" {_perc(v)}".ljust(self._label_length), c0.brighter(), c0)

        for s in self._shades:
            yield ColorStr(" ", bg=cp.shade(s))
            yield ColorStr(_perc(s).center(7), cp.shade(sm.value_at(s)))

        yield ColorStr(" ", bg=WHITE)

    def _color_columns(self, name: str, color: Color) -> Iterable[str]:
        hue = f"{color.hue * 360:3.0f}" if color.saturation else ""
        c0 = color.shade(self._neutral_shade_lo)
        yield ColorStr(f" {hue:>3} {name}".ljust(self._label_length), c0, BLACK)

        for s in self._shades:
            k = color.shade(s)
            yield Highlighter(k)(k.as_hex.center(8))

        yield ColorStr(" ", bg=WHITE)

    def _rows(self) -> Iterator[Iterable[str]]:
        yield []
        yield self._percentage_columns(0)
        yield self._color_columns("grey", GREY)
        for v in self._vibrances:
            yield []
            yield self._percentage_columns(v)
            for name, k in self._colors.items():
                yield self._color_columns(name, k.saturated(v))
        yield []

    def run(self) -> Iterator[str]:
        for columns in self._rows():
            yield "".join(columns)


class PaletteGenerator(ArgsParser):
    _name = "palette"

    def __init__(self, parser: ArgumentParser) -> None:
        super().__init__(parser)
        parser.add_argument(
            "-c",
            "--colors",
            nargs="+",
            metavar="NAME=HUE (1-360)",
            type=parse_key_value_pair,
            default={},
        )
        parser.add_argument(
            "-m", "--merge-with-default-palette", action="store_true", default=False
        )
        parser.add_argument(
            "-a", "--alt-default-palette", action="store_true", default=False
        )
        parser.add_argument(
            "-s", "--number-of-shades", type=check_integer_in_range(1, 99), default=9
        )
        parser.add_argument(
            "-v", "--number-of-vibrances", type=check_integer_in_range(1, 99), default=2
        )

    def _runner_cls(self, _args: Namespace) -> type[CommandRunner]:
        return _CommandRunner
