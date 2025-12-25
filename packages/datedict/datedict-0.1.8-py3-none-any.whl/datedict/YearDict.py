from decimal import Decimal
from typing import TYPE_CHECKING, Mapping

from .common import NAN, ONE, Decimable, to_decimal, ZERO

if TYPE_CHECKING:
    from .DateDict import DateDict


class YearDict:
    def __init__(self, data: Mapping[int, Decimable] = dict(), strict: bool = True):
        years = sorted(data.keys())
        if len(years) == 0:
            self.data = {}
            return
        if strict:
            # enforce contiguous coverage
            if years != list(range(years[0], years[-1] + 1)):
                raise ValueError(
                    "Data must cover all years in the contiguous range. "
                    "To disable this check, set strict=False."
                )
        self.start_year, self.end_year = years[0], years[-1]
        self.data = {k: to_decimal(v) for k, v in data.items()}

    def fill(self, start_year: int, end_year: int, value: Decimable) -> "YearDict":
        """
        Create a new graph with a specified range and value.
        The range is defined by start_year and end_year.
        """
        v = to_decimal(value)
        return YearDict({y: v for y in range(int(start_year), int(end_year) + 1)})

    def get(self, year: int, default: Decimal = NAN) -> Decimal:
        """
        Get the value for a specific year. If the year does not exist, return the default value.
        If the value is None, return the default value.
        """
        temp = self.data.get(year, NAN)
        if temp.is_nan():
            return default
        return temp

    def __getitem__(self, year: int) -> Decimal:
        return self.data[year]

    def __setitem__(self, year: int, value) -> None:
        self.data[int(year)] = to_decimal(value)

    def crop(
        self,
        start: int | None = None,
        end: int | None = None,
        initial_value: Decimable = NAN,
    ) -> "YearDict":
        if start is None and end is None:
            return self
        return YearDict(
            {
                k: (self.get(k, to_decimal(initial_value)))
                for k in range(
                    self.start_year if start is None else int(start),
                    self.end_year if end is None else int(end) + 1,
                )
            }
        )

    def non_negative(self) -> "YearDict":
        """
        Return a new YearDict with all negative values set to zero.
        """
        return YearDict(
            {
                y: (v if (not v.is_nan() and v >= ZERO) else ZERO)
                for y, v in self.data.items()
            }
        )

    def sum(self, start: int | None = None, end: int | None = None) -> Decimal:
        """
        Return the sum of values in the specified range.
        If a value is NaN, it is treated as zero.
        """
        s = self.start_year if start is None else start
        e = self.end_year if end is None else end
        return sum((self.get(y, ZERO) for y in range(s, e + 1) if y in self.data), ZERO)

    def __mul__(self, other: "Decimable | YearDict") -> "YearDict":
        if isinstance(other, Decimable):
            return YearDict({k: v * to_decimal(other) for k, v in self.data.items()})
        elif isinstance(other, YearDict):
            return YearDict({k: v * other.get(k, ONE) for k, v in self.data.items()})

    def __rmul__(self, other):
        return self.__mul__(other)

    def __neg__(self) -> "YearDict":
        return self * Decimal("-1")

    def __add__(self, other: "Decimable | YearDict") -> "YearDict":
        if isinstance(other, Decimable):
            return YearDict({k: v + to_decimal(other) for k, v in self.data.items()})
        elif isinstance(other, YearDict):
            return YearDict({k: v + other.get(k, ZERO) for k, v in self.data.items()})

    def __radd__(self, other: "Decimable | YearDict") -> "YearDict":
        return self.__add__(other)

    def __sub__(self, other: "Decimable | YearDict") -> "YearDict":
        if isinstance(other, Decimable):
            return self.__add__(-to_decimal(other))
        elif isinstance(other, YearDict):
            return self.__add__(-other)

    def __rsub__(self, other: "Decimable | YearDict") -> "YearDict":
        return (-self).__add__(other)

    def __truediv__(self, other: "Decimable | YearDict") -> "YearDict":
        if isinstance(other, Decimable):
            return YearDict({k: v / to_decimal(other) for k, v in self.data.items()})
        elif isinstance(other, YearDict):
            return YearDict({k: v / other.get(k, ONE) for k, v in self.data.items()})

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, YearDict):
            return False
        for k in set(self.data.keys()).union(other.data.keys()):
            s = self.get(k)
            o = other.get(k)
            if s.is_nan() and o.is_nan():
                continue
            if s != o:
                return False
        return True

    def __str__(self):
        return "\n".join(f"{y}: {v}" for y, v in sorted(self.data.items()))

    def __repr__(self):
        return f"{self.data!r}"

    def to_array(self):
        return [self.data[k] for k in self.data.keys()]

    def to_dict(self):
        return dict(self.data)

    def average(self) -> Decimal:
        """
        Return the average of the values in the YearDict.
        If there are no years, return Zero
        """
        valid_values = [v for v in self.data.values() if not v.is_nan()]
        if not valid_values:
            return ZERO
        return sum(valid_values, ZERO) / Decimal(len(valid_values))

    def to_datedict(self) -> "DateDict":
        from .DateDict import DateDict

        """
        Convert YearDict to a Datedict by applying each year's value to every date in that year.
        """
        dd = DateDict().fill(f"{self.start_year}-01-01", f"{self.end_year}-12-31", NAN)
        for k in dd.data.keys():
            dd.data[k] = self.get(int(k[:4]), NAN)
        return dd
