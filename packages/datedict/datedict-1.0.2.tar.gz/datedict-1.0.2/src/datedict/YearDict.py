from typing import TYPE_CHECKING
from .TimeDict import TimeDict
from .common import NAN

if TYPE_CHECKING:
    from .DateDict import DateDict


class YearDict(TimeDict[int]):
    @classmethod
    def _next_key(cls, key: int) -> int:
        return key + 1

    def to_datedict(self) -> "DateDict":
        from .DateDict import DateDict

        """
        Convert the YearDict to a DateDict.
        Each year in the YearDict is expanded to cover all dates in that year.
        """
        dd: DateDict = DateDict.fill(f"{self.start}-01-01", f"{self.end}-12-31", NAN)
        for k in dd.data.keys():
            dd.data[k] = self.get(int(k[:4]) if isinstance(k, str) else k.year, NAN)
        return dd
