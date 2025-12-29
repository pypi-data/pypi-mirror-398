from .color import Color


def c(h: int) -> Color:
    return Color(h / 360)


GREY = Color(saturation=0)
BLACK = GREY.shade(0)
WHITE = GREY.shade(1)


class Colors:
    """
    Highly opinionated (though carefully selected) color palette.

    Custom color palettes can be specified by creating a very basic class
    that solely consists of a different set of hues (in degrees), for example:
    >>> from math import pi
    >>> class MyColors:
    ...     tomato = c(15)
    ...     turquoise = c(175)
    ...     very_random = tomato.blend(turquoise, 1 / pi)
    >>> for name in ["tomato", "turquoise", "very_random"]:
    ...     print(f"{getattr(MyColors, name)} <-- {name}")
    HSLuv( 15.00°, 100.00%,  50.00%) <-- tomato
    HSLuv(175.00°, 100.00%,  50.00%) <-- turquoise
    HSLuv( 65.93°, 100.00%,  50.00%) <-- very_random
    """

    red = c(12)
    orange = c(33)
    yellow = c(69)
    poison = c(101)
    green = c(127)
    ocean = c(190)
    blue = c(248)
    indigo = c(267)
    purple = c(281)
    pink = c(329)

    brown = orange.blend(yellow, 0.25).saturated(0.69)


class AltColors:
    """Alternative color palette."""

    red = c(10)
    orange = c(35)
    yellow = c(75)
    poison = c(100)
    green = c(126)
    ocean = c(184)
    blue = c(242)
    indigo = c(268)
    purple = c(280)
    pink = c(325)

    brown = orange.blend(yellow, 0.3).saturated(0.69)
