from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from based_utils.cli import ArgsParser, check_integer_in_range
from based_utils.cli.args import CommandRunner
from based_utils.interpol import LinearMapping, mapped

from kleur import Color, ColorHighlighter, Highlighter, blend_colors

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Iterator


CP = Color.Props


def _input_comment(color: Color) -> str:
    return f"{Highlighter(color)(f' #{color.as_hex}; ')} {ColorHighlighter(color)()}"


class _CommandRunner(CommandRunner, ABC):
    def __init__(self, args: Namespace) -> None:
        self._label, self._include_input = (args.label, args.include_input_shades)
        ibw, ns = (args.include_black_and_white, args.number_of_shades + 1)
        self._shades = [s / ns for s in range(*((0, ns + 1) if ibw else (1, ns)))]

    @abstractmethod
    def _comment_lines(self) -> Iterator[str]: ...

    @abstractmethod
    def _colors(self) -> Iterator[tuple[Color, CP]]: ...

    def run(self) -> Iterator[str]:
        yield "/*"
        yield from self._comment_lines()
        yield "*/"

        # This intermediate dict will take care of duplicates as a nice side effect. 🫠
        colors = {f"{c.lightness * 100:03.0f}": (c, hp) for c, hp in self._colors()}
        for shade, (color, hl_ps) in sorted(colors.items()):
            hl, hl_c, is_hl = Highlighter(color), ColorHighlighter(color), bool(hl_ps)
            hex_str = f"{hl(' ')}{hl(f'#{color.as_hex};', inverted=is_hl)}{hl(' ')}"
            css_var = f"{hl(f'--{self._label}-{shade}', enabled=is_hl)}:{hex_str}"
            yield f"{css_var}/* {hl_c(hl_ps, enable_bounds_highlights=is_hl)} */"


class RunnerOneColor(_CommandRunner):
    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self._input = Color.from_hex(args.color1)

    def _comment_lines(self) -> Iterator[str]:
        yield f"Based on: {_input_comment(self._input)}"

    def _colors(self) -> Iterator[tuple[Color, CP]]:
        """Generate shades of a color."""
        for s in self._shades:
            yield self._input.shade(s), CP.NONE
        if self._include_input:
            yield self._input, CP.ALL


class RunnerTwoColors(_CommandRunner):
    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self._dynamic_range = args.dynamic_range / 100
        c1, c2 = Color.from_hex(args.color1), Color.from_hex(args.color2)
        self._dark, self._bright = sorted(c1.align_with(c2))

    def _comment_lines(self) -> Iterator[str]:
        yield "Based on:"
        yield f" Darkest:   {_input_comment(self._dark)}"
        yield f" Brightest: {_input_comment(self._bright)}"

    def _colors(self) -> Iterator[tuple[Color, CP]]:
        """
        Generate shades based on two colors.

        The dynamic range specifies to what degree the hue
        of the input colors will be used as boundaries:
        - dynamic range 0 (0%):
            The shades will interpolate (or extrapolate) between the input colors
        - dynamic range between 0 and 1 (between 0% and 100%):
            The shades will interpolate (or extrapolate) between
            darker / brighter shades of the input colors
        - dynamic range 1 (100%):
            The shades will interpolate (or extrapolate) between
            the darkest & brightest shades of the input colors
        """
        old_colors = self._dark, self._bright

        li_old = [c.lightness for c in old_colors]
        sm_old = LinearMapping(*li_old)

        li_new = [mapped(self._dynamic_range, (li, e)) for e, li in enumerate(li_old)]
        sm_new = LinearMapping(*li_new)

        blend_old = blend_colors(*old_colors)
        colors_l = [blend_old(sm_new.position_of(li)).shade(li) for li in li_old]
        blend_new = blend_colors(*colors_l)

        def blend(lightness: float) -> Color:
            return blend_new(sm_old.position_of(lightness))

        for s in self._shades:
            yield blend(s), CP.NONE

        if self._include_input:
            colors_hs = [blend(li) for li in li_new]
            for c_l, c_hs in zip(colors_l, colors_hs, strict=True):
                if c_l.as_rgb == c_hs.as_rgb:
                    yield c_l, CP.ALL
                else:
                    yield c_l, CP.L
                    yield c_hs, CP.NO_L


class ShadesGenerator(ArgsParser):
    _name = "shades"

    def __init__(self, parser: ArgumentParser) -> None:
        super().__init__(parser)
        parser.add_argument("-l", "--label", type=str, default="color")
        parser.add_argument("-c", "--color1", type=str, required=True)
        parser.add_argument("-k", "--color2", type=str)
        parser.add_argument(
            "-s", "--number-of-shades", type=check_integer_in_range(1, 99), default=19
        )
        parser.add_argument(
            "-b", "--include-black-and-white", action="store_true", default=False
        )
        parser.add_argument(
            "-i", "--include-input-shades", action="store_true", default=False
        )
        parser.add_argument(
            "-d", "--dynamic-range", type=check_integer_in_range(0, 100), default=0
        )

    def _runner_cls(self, args: Namespace) -> type[CommandRunner]:
        return RunnerTwoColors if args.color2 else RunnerOneColor
