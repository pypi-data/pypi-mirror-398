import colorsys
import random
from typing import Self, Sequence

from nature.utils import clamp


class Color:
    def __init__(self, rgb: Sequence[int]):
        self.rgb = list(rgb)

    @classmethod
    def random(cls, luminosity: float | None = None, hue: float | None = None) -> Self:
        color = cls(tuple(random.randint(0, 255) for _ in range(3)))
        if luminosity is not None:
            color.luminosity = luminosity
        if hue is not None:
            color.hue = hue
        return color

    @property
    def brightness(self) -> float:
        return sum(self.rgb) / (3 * 255)

    @brightness.setter
    def brightness(self, value: float) -> None:
        self.rgb = [int(clamp(c * value, 0, 255)) for c in self.rgb]

    @property
    def luminosity(self) -> float:
        r, g, b = [x / 255 for x in self.rgb]
        _, l, _ = colorsys.rgb_to_hls(r, g, b)
        return l

    @luminosity.setter
    def luminosity(self, value: float) -> None:
        r, g, b = [x / 255 for x in self.rgb]
        h, _, s = colorsys.rgb_to_hls(r, g, b)
        r, g, b = colorsys.hls_to_rgb(h, value, s)
        self.rgb = tuple(int(clamp(c * 255, 0, 255)) for c in (r, g, b))

    @property
    def hue(self) -> float:
        r, g, b = [x / 255 for x in self.rgb]
        h, _, _ = colorsys.rgb_to_hls(r, g, b)
        return h

    @hue.setter
    def hue(self, value: float) -> None:
        r, g, b = [x / 255 for x in self.rgb]
        _, l, s = colorsys.rgb_to_hls(r, g, b)
        r, g, b = colorsys.hls_to_rgb(value, l, s)
        self.rgb = tuple(int(clamp(c * 255, 0, 255)) for c in (r, g, b))

    def to_hex(self) -> str:
        return "#{:02x}{:02x}{:02x}".format(*self.rgb)

    def copy(self) -> "Color":
        return Color(self.rgb)
