from decimal import Decimal
from typing import Callable, Generic, Mapping, Protocol, Self, TypeVar
from .common import NAN, ONE, ZERO, Decimable, to_decimal


K = TypeVar("K", bound="SupportsLe")


class SupportsLe(Protocol):
    def __le__(self: K, other: K, /) -> bool: ...
    def __lt__(self: K, other: K, /) -> bool: ...


class TimeDict(Generic[K]):

    @classmethod
    def _next_key(cls, key: K) -> K:
        _ = key
        raise NotImplementedError("_next_key must be implemented in subclasses")

    @classmethod
    def _inclusive_range(cls, start: K, end: K) -> list[K]:
        keys = []
        current = start
        while current <= end:
            keys.append(current)
            current = cls._next_key(current)
        return keys

    def __init__(self, data: Mapping[K, Decimable] = dict(), strict: bool = True):
        keys = sorted(data.keys())
        if not keys:
            self.data = {}
            return
        if strict:
            # enforce contiguous coverage
            if keys != self._inclusive_range(keys[0], keys[-1]):
                raise ValueError(
                    "Data must cover all keys in the contiguous range. "
                    "To disable this check, set strict=False."
                )
        self.start, self.end = keys[0], keys[-1]
        self.data = {k: to_decimal(v) for k, v in data.items()}

    @classmethod
    def fill(cls, start: K, end: K, value: Decimable) -> "Self":
        """
        Create a new graph with a specified range and value.
        The range is defined by start and end.
        """
        v = to_decimal(value)
        return cls({k: v for k in cls._inclusive_range(start, end)})

    def get(self, key: K, default: Decimal = NAN) -> Decimal:
        """
        Get the value for a specific key.
        If the key does not exist, return the default value.
        If the value is None, return the default value.
        """
        temp = self.data.get(key, NAN)
        if temp.is_nan():
            return default
        return temp

    def __getitem__(self, key: K) -> Decimal:
        return self.data[key]

    def __setitem__(self, key: K, value) -> None:
        self.data[key] = to_decimal(value)

    def crop(
        self,
        start: K | None = None,
        end: K | None = None,
        initial_value: Decimable = NAN,
    ) -> "Self":
        if start is None and end is None:
            return self
        return type(self)(
            {
                k: (self.get(k, to_decimal(initial_value)))
                for k in self._inclusive_range(
                    start if start is not None else self.start,
                    end if end is not None else self.end,
                )
            }
        )

    def non_negative(self) -> "Self":
        """
        Return a new TimeDict with all negative values set to zero.
        """
        return type(self)(
            {
                k: (v if (not v.is_nan() and v >= ZERO) else ZERO)
                for k, v in self.data.items()
            }
        )

    def sum(self, start: K | None = None, end: K | None = None) -> Decimal:
        total = ZERO
        for k in self._inclusive_range(
            start if start is not None else self.start,
            end if end is not None else self.end,
        ):
            v = self.data.get(k, NAN)
            if not v.is_nan():
                total += v
        return total

    def _binary_op(
        self,
        other: "Decimable | Self",
        op: Callable[[Decimal, Decimal], Decimal],
        neutral: Decimal,
    ) -> "Self":
        if isinstance(other, Decimable):
            other_value = to_decimal(other)
            return type(self)({k: op(v, other_value) for k, v in self.data.items()})
        elif isinstance(other, type(self)):
            return type(self)(
                {
                    k: op(
                        self[k],
                        other.get(k, neutral),
                    )
                    for k in self.data.keys()
                }
            )
        else:
            raise TypeError(
                "Unsupported operand type(s) for operation: "
                f"'TimeDict' and '{type(other)}'"
            )

    def __mul__(self, other: "Decimable | Self") -> "Self":
        return self._binary_op(other, lambda x, y: x * y, ONE)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __neg__(self) -> "Self":
        return self * Decimal("-1")

    def __add__(self, other: "Decimable | Self") -> "Self":
        return self._binary_op(other, lambda x, y: x + y, ZERO)

    def __radd__(self, other: "Decimable | Self") -> "Self":
        return self.__add__(other)

    def __sub__(self, other: "Decimable | Self") -> "Self":
        return self._binary_op(other, lambda x, y: x - y, ZERO)

    def __rsub__(self, other: "Decimable | Self") -> "Self":
        return (-self).__add__(other)

    def __truediv__(self, other: "Decimable | Self") -> "Self":
        return self._binary_op(other, lambda x, y: x / y, ONE)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
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
        return [self.data[k] for k in self.data.keys()]

    def to_dict(self) -> dict:
        return self.data.copy()

    def average(self) -> Decimal:
        """
        Return the average of the values in the TimeDict.
        If there are no valid (non-NaN) values, return ZERO.
        """
        valid_values = [v for v in self.data.values() if not v.is_nan()]
        if not valid_values:
            return ZERO
        return sum(valid_values) / Decimal(len(valid_values))
