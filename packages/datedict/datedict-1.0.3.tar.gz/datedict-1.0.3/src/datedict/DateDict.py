from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from .TimeDict import TimeDict

from .common import ZERO

if TYPE_CHECKING:
    from .YearDict import YearDict

DateKey = str | date


class DateDict(TimeDict[DateKey]):
    @classmethod
    def _next_key(cls, key: DateKey) -> DateKey:
        if isinstance(key, str):
            key_date = date.fromisoformat(key)
        else:
            key_date = key
        next_date = key_date + timedelta(days=1)
        return next_date.strftime("%Y-%m-%d")

    @classmethod
    def _inclusive_range(cls, start: DateKey, end: DateKey) -> list[DateKey]:
        start_date: str = (
            str(start) if isinstance(start, str) else start.strftime("%Y-%m-%d")
        )
        end_date: str = str(end) if isinstance(end, str) else end.strftime("%Y-%m-%d")
        return super()._inclusive_range(start_date, end_date)

    def to_yeardict(self) -> "YearDict":
        """
        Convert the DateDict to a YearDict by summing values for each year.
        """
        from .YearDict import YearDict

        year_data: dict[int, Decimal] = {}
        for k, v in self.data.items():
            year = int(k[:4]) if isinstance(k, str) else k.year
            year_data[year] = year_data.get(year, ZERO) + v
        return YearDict(year_data)

    def to_dict(self) -> dict[str, Decimal]:
        return {str(k): v for k, v in self.data.items()}
