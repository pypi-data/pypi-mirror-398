import math
from dataclasses import dataclass


@dataclass
class Resolution:
    width: int
    height: int

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height

    @property
    def aspect_ratio_str(self) -> str:
        divisor = math.gcd(self.width, self.height)
        return f"{self.width//divisor}:{self.height//divisor}"

    def __str__(self):
        return f"{self.width}x{self.height}"

    def __eq__(self, value: "Resolution"):
        return self.width == value.width and self.height == value.height

    def __lt__(self, value: "Resolution"):
        return self.width * self.height < value.width * value.height

    def __gt__(self, value: "Resolution"):
        return self.width * self.height > value.width * value.height

    def make_even(self):
        return Resolution(_make_even(self.width), _make_even(self.height))


def _make_even(n):
    return n if n % 2 == 0 else n - 1
