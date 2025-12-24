from functools import reduce
from math import gcd
from typing import List

FRAMERATE_MAP = {
    12.5: (12500, 1000),
    # ATSC classic
    14.985: (15000, 1001),
    29.97: (30000, 1001),
    24.98: (25000, 1001),
    23.976: (24000, 1001),
    59.94: (60000, 1001),
}


class InvalidFrameRateError(ValueError):
    def __init__(self, message):
        super().__init__(message)


class FrameRate(object):
    def __init__(self, value: str | float | int | tuple, second_value: int = None):
        try:
            if second_value is not None and isinstance(value, int):
                self.numerator = value
                self.denominator = second_value

            elif isinstance(value, str):
                self._from_string(value)
            elif isinstance(value, tuple):
                # check that the values are integers
                if not all(isinstance(v, int) for v in value):
                    raise InvalidFrameRateError(
                        f"Invalid input type for FrameRate: {value}"
                    )
                self.numerator, self.denominator = value
            elif isinstance(value, float):
                self._from_float(value)
            elif isinstance(value, int):
                self._from_int(value)
            elif isinstance(value, FrameRate):
                self.numerator = value.numerator
                self.denominator = value.denominator

        except ValueError as e:
            raise InvalidFrameRateError(f"Invalid input: {value} - {e}")

        self._convert_to_canonical()

    def _from_float(self, value):
        if int(value) == value:
            self._from_int(value)
            return
        else:
            # If rate is within 0.01 of a known ATSC rate, return it
            for r in FRAMERATE_MAP:
                if abs(value - r) <= 0.011:
                    self.numerator, self.denominator = FRAMERATE_MAP[r]
                    return

        raise InvalidFrameRateError(f"Unrecognised frame rate: {value}")

    def _from_int(self, value: int):
        self.numerator = value
        self.denominator = 1

    def _from_string(self, input: str):
        if "/" in input:
            self.numerator, self.denominator = map(int, input.split("/"))
        else:
            self._from_float(float(input))

    def _convert_to_canonical(self):
        # if denominator can be divided by 1000, divide numerator by 1000
        quotient, remainder = divmod(self.denominator, 1000)
        if remainder == 0:
            self.numerator = int(self.numerator / quotient)
            self.denominator = int(self.denominator / quotient)
            return
        # if 1000 can be divided by denonminator, multiply to get to 1000
        quotient, remainder = divmod(1000, self.denominator)
        if remainder == 0:
            self.numerator = int(self.numerator * quotient)
            self.denominator = int(self.denominator * quotient)
            return

    def __str__(self):
        return f"{self.numerator}/{self.denominator}"

    def __eq__(self, value: "FrameRate"):
        return (
            self.numerator == value.numerator and self.denominator == value.denominator
        )

    def __lt__(self, value: "FrameRate"):
        return self.numerator / self.denominator < value.numerator / value.denominator

    def __gt__(self, value: "FrameRate"):
        return self.numerator / self.denominator > value.numerator / value.denominator

    def __float__(self):
        return self.numerator / self.denominator

    @property
    def fps(self):
        return float(self)

    def to_obj(self, mode="bkt2"):
        if mode == "bkt2":
            return {"num": self.numerator, "den": self.denominator}
        return {"numerator": self.numerator, "denominator": self.denominator}

    def is_integer(self):
        return float(self) == int(float(self))

    @staticmethod
    def get_common_framerate(rates: List["FrameRate"]):
        # Ensure that they all have the same denominator
        denominators = set([r.denominator for r in rates])
        if len(denominators) != 1:
            raise ValueError(
                f"Cannot determine common framerate for different denominators: {denominators}"
            )

        # Ensure that the numerators are all multiples of the lowest one
        numerators = [r.numerator for r in rates]
        if len(numerators) == 1:
            return FrameRate(numerators[0], denominators.pop())
        gcd_num = reduce(gcd, numerators)
        if gcd_num not in numerators:
            raise ValueError(
                f"Cannot determine common framerate for different numerators: {numerators}"
            )
        return FrameRate(gcd_num, denominators.pop())

    def __hash__(self):
        return hash((self.numerator, self.denominator))
