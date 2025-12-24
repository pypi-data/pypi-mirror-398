from __future__ import annotations
from collections.abc import Iterable, Iterator, MutableSet
from typing import Callable, Generic, Hashable, TypeVar

T = TypeVar("T")

#------------------------------------------------------
# OrderedSet
#------------------------------------------------------

class OrderedSet(Generic[T], MutableSet[T]):
    __slots__ = ("_dict",)
    _dict: dict[T, None]

    def __init__(self, iterable: Iterable[T] | None = None) -> None:
        self._dict = {}
        if iterable is not None:
            self.update(iterable)

    def __contains__(self, item: object) -> bool:  # type: ignore[override]
        return item in self._dict

    def __iter__(self) -> Iterator[T]:
        return iter(self._dict.keys())

    def __len__(self) -> int:
        return len(self._dict)

    def __getitem__(self, index: int) -> T:
        if index < 0:
            index += len(self._dict)
        if index < 0 or index >= len(self._dict):
            raise IndexError("OrderedSet index out of range")
        for i, key in enumerate(self._dict):
            if i == index:
                return key
        # This point should never be reached
        raise IndexError("OrderedSet index out of range")

    def add(self, value: T) -> None:
        if value not in self._dict:
            self._dict[value] = None

    def discard(self, value: T) -> None:
        self._dict.pop(value, None)

    def update(self, iterable: Iterable[T]) -> None:
        for x in iterable:
            self.add(x)

    def first(self) -> T | None:
        for x in self._dict:
            return x
        return None

    def try_replace(self, old: T, new: T) -> None:
        """Replace a potentially existing item with a new one, keeping its position if possible."""
        if new in self._dict or old not in self._dict:
            return
        self._dict = { (new if k == old else k): None for k in self._dict }

    def __repr__(self) -> str:
        items = ", ".join(repr(x) for x in self._dict)
        return f"OrderedSet([{items}])"

#------------------------------------------------------
# KeyedDict
#------------------------------------------------------

K = TypeVar("K")
V = TypeVar("V")

class KeyedDict(Generic[K, V]):
    __slots__ = ("_dict", "_key")
    _dict: dict[Hashable, tuple[K, V]]
    _key: Callable[[K], Hashable]

    def __init__(self, key: Callable[[K], Hashable], iterable: Iterable[tuple[K, V]] | None = None) -> None:
        self._dict = {}
        self._key = key
        for k, v in iterable or ():
            self._dict[self._key(k)] = (k, v)

    def __setitem__(self, k: K, v: V) -> None:
        self._dict[self._key(k)] = (k, v)

    def __getitem__(self, k: K) -> V:
        return self._dict[self._key(k)][1]

    def __delitem__(self, k: K) -> None:
        del self._dict[self._key(k)]

    def __contains__(self, k: object) -> bool:
        try: return self._key(k) in self._dict  # type: ignore[arg-type]
        except Exception: return False

    def __len__(self) -> int:
        return len(self._dict)

    def get(self, k: K, default: V | None = None) -> V | None:
        entry = self._dict.get(self._key(k))
        return default if entry is None else entry[1]

    def items(self) -> Iterator[tuple[K, V]]:
        yield from self._dict.values()

    def values(self) -> Iterator[V]:
        for _, v in self._dict.values():
            yield v

    def update(self, iterable: KeyedDict[K, V]|Iterable[tuple[K, V]]) -> None:
        if isinstance(iterable, KeyedDict):
            self._dict.update(iterable._dict)
        else:
            for k, v in iterable:
                self._dict[self._key(k)] = (k, v)


#------------------------------------------------------
# KeyedSet
#------------------------------------------------------

class KeyedSet(Generic[K], MutableSet[K]):
    __slots__ = ("_dict", "_key")
    _dict: dict[Hashable, K]
    _key: Callable[[K], Hashable]

    def __init__(self, key: Callable[[K], Hashable], iterable: Iterable[K] | None = None) -> None:
        self._dict = {}
        self._key = key
        if iterable is not None:
            self.update(iterable)

    def __contains__(self, item: K) -> bool:  # type: ignore[override]
        return self._key(item) in self._dict

    def __iter__(self) -> Iterator[K]:
        return iter(self._dict.values())

    def __len__(self) -> int:
        return len(self._dict)

    def add(self, value: K) -> None:
        if self._key(value) not in self._dict:
            self._dict[self._key(value)] = value

    def discard(self, value: K) -> None:
        self._dict.pop(self._key(value), None)

    def update(self, iterable: Iterable[K]) -> None:
        for x in iterable:
            self.add(x)

    def first(self) -> K | None:
        for _, v in self._dict.items():
            return v
        return None

    def __repr__(self) -> str:
        items = ", ".join(repr(x) for x in self._dict)
        return f"KeyedSet([{items}])"


