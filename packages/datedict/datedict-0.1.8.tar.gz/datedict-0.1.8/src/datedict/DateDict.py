from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Mapping

from .common import NAN, ONE, Decimable, to_decimal, ZERO

if TYPE_CHECKING:
    from .YearDict import YearDict


class DateDict:
    def __init__(self, data: Mapping[str, Decimable] = dict(), strict: bool = True):
        dates = sorted(data.keys())
        if len(dates) == 0:
            self.data = {}
            return
        if strict:
            # enforce contiguous coverage
            if dates != [
                (date.fromisoformat(dates[0]) + timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(
                    (date.fromisoformat(dates[-1]) - date.fromisoformat(dates[0])).days
                    + 1
                )
            ]:
                raise ValueError(
                    "Data must cover all dates in the contiguous range. "
                    "To disable this check, set strict=False."
                )
        self.start_date, self.end_date = dates[0], dates[-1]
        self.data: dict[str, Decimal] = {k: to_decimal(v) for k, v in data.items()}

    def fill(
        self, start_date: str | date, end_date: str | date, value: Decimable
    ) -> "DateDict":
        """
        Create a new graph with a specified range and value.
        The range is defined by start_date and end_date.
        """
        start = (
            start_date
            if isinstance(start_date, date)
            else date.fromisoformat(start_date)
        )
        end = end_date if isinstance(end_date, date) else date.fromisoformat(end_date)
        v = to_decimal(value)
        return DateDict(
            {
                (start + timedelta(days=i)).strftime("%Y-%m-%d"): v
                for i in range((end - start).days + 1)
            }
        )

    def get(self, key: str, default: Decimal = NAN) -> Decimal:
        """
        Get the value for a specific date. If the date does not exist, return the default value.
        The date should be in the format yyyy-mm-dd.
        If the value is None, return the default value.
        """
        temp = self.data.get(key, NAN)
        if temp.is_nan():
            return default
        return temp

    def __getitem__(self, key) -> Decimal:
        return self.data[key]

    def __setitem__(self, key: str, value) -> None:
        self.data[key] = to_decimal(value)

    def crop(
        self,
        start: str | None = None,
        end: str | None = None,
        initial_value: Decimable = NAN,
    ) -> "DateDict":
        """
        Crop the graph data to a specific range defined by start and end.
        If any of the parameters is None, it will not filter by that parameter.
        """
        if start is None and end is None:
            return self
        return DateDict(
            {
                k: (self.get(k, to_decimal(initial_value)))
                for k in map(
                    lambda x: x.strftime("%Y-%m-%d"),
                    [
                        (
                            date.fromisoformat(self.start_date)
                            if start is None
                            else date.fromisoformat(start)
                        )
                        + timedelta(days=i)
                        for i in range(
                            (
                                (
                                    date.fromisoformat(self.end_date)
                                    if end is None
                                    else date.fromisoformat(end)
                                )
                                - (
                                    date.fromisoformat(self.start_date)
                                    if start is None
                                    else date.fromisoformat(start)
                                )
                            ).days
                            + 1
                        )
                    ],
                )
            }
        )

    def non_negative(self) -> "DateDict":
        """
        Return a new DateDict with all negative values set to zero.
        """
        return DateDict(
            {
                k: (v if (not v.is_nan() and v >= ZERO) else ZERO)
                for k, v in self.data.items()
            }
        )

    def sum(
        self: "DateDict",
        start_date: str | date | None = None,
        end_date: str | date | None = None,
    ) -> Decimal:
        """
        Return the sum of values in the specified range.
        If a value is NaN, it is treated as zero.
        """
        start = (
            date.fromisoformat(self.start_date)
            if start_date is None
            else (
                start_date
                if isinstance(start_date, date)
                else date.fromisoformat(start_date)
            )
        )
        end = (
            date.fromisoformat(self.end_date)
            if end_date is None
            else (
                end_date if isinstance(end_date, date) else date.fromisoformat(end_date)
            )
        )
        return sum(
            [
                (self.get(k, ZERO))
                for k in map(
                    lambda x: x.strftime("%Y-%m-%d"),
                    [start + timedelta(days=i) for i in range((end - start).days + 1)],
                )
            ],
            ZERO,
        )

    def __mul__(self, other: "Decimable | DateDict") -> "DateDict":
        if isinstance(other, Decimable):
            return DateDict({k: v * to_decimal(other) for k, v in self.data.items()})
        elif isinstance(other, DateDict):
            return DateDict({k: v * other.get(k, ONE) for k, v in self.data.items()})

    def __rmul__(self, other: "Decimable | DateDict") -> "DateDict":
        return self.__mul__(other)

    def __neg__(self) -> "DateDict":
        return self * Decimal("-1")

    def __add__(self, other: "Decimable | DateDict") -> "DateDict":
        if isinstance(other, Decimable):
            return DateDict({k: (v + to_decimal(other)) for k, v in self.data.items()})
        else:
            return DateDict({k: v + other.get(k, ZERO) for k, v in self.data.items()})

    def __radd__(self, other: "Decimable | DateDict") -> "DateDict":
        return self.__add__(other)

    def __sub__(self, other: "Decimable | DateDict") -> "DateDict":
        if isinstance(other, Decimable):
            return self.__add__(-to_decimal(other))
        else:
            return self.__add__(-other)

    def __rsub__(self, other: "Decimable | DateDict") -> "DateDict":
        return (-self).__add__(other)

    def __truediv__(self, other: "Decimable | DateDict") -> "DateDict":
        if isinstance(other, Decimable):
            return DateDict({k: v / to_decimal(other) for k, v in self.data.items()})
        else:
            return DateDict({k: v / other.get(k, ONE) for k, v in self.data.items()})

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DateDict):
            return False
        for k in set(self.data.keys()).union(other.data.keys()):
            s = self.get(k)
            o = other.get(k)
            if s.is_nan() and o.is_nan():
                continue
            if s != o:
                return False
        return True

    def __str__(self) -> str:
        return "\n".join(f"{k}: {v}" for k, v in sorted(self.data.items()))

    def __repr__(self) -> str:
        return f"{self.data!r}"

    def to_array(self) -> list[Decimal]:
        """
        Convert the DateDict values to a list of Decimals, ordered by date.
        """
        return [self.data[k] for k in sorted(self.data.keys())]

    def to_dict(self) -> dict[str, Decimal]:
        """
        Convert the DateDict to a standard dictionary.
        """
        return dict(self.data)

    def average(self) -> Decimal:
        """
        Calculate the average of all values in the DateDict.
        If there are no valid values, return ZERO.
        """
        valid_values = [v for v in self.data.values() if not v.is_nan()]
        if not valid_values:
            return ZERO
        return Decimal(sum(valid_values)) / len(valid_values)

    def to_yeardict(self) -> "YearDict":
        """
        Convert the DateDict to a YearDict by summing values for each year.
        """
        from .YearDict import YearDict

        year_data: dict[int, Decimal] = {}
        for k, v in self.data.items():
            year = date.fromisoformat(k).year
            year_data[year] = year_data.get(year, ZERO) + v
        return YearDict(year_data)
