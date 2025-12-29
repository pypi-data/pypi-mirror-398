from based_utils.cli import run_command

from .palette_gen import PaletteGenerator
from .shades_gen import ShadesGenerator


def main() -> None:
    run_command(PaletteGenerator, ShadesGenerator)
