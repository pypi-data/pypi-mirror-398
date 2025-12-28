from typing import (
    Any, Callable, Dict, Generic, Iterable, List, Optional, TypeVar, Union
)

T = TypeVar('T')
V = TypeVar('V')

class Collection(Generic[T]):
    def __init__(self, items: Union[Dict[Any, T], Iterable[T]]):
        if isinstance(items, dict):
            self._items: Dict[Any, T] = items
        elif isinstance(items, Iterable):
            self._items = {i: item for i, item in enumerate(items)}
        else:
            raise TypeError("Items must be a dictionary or an iterable.")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list(self._items.values())})"

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterable[T]:
        return iter(self._items.values())

    def where(self, key: Any, value: Any) -> 'Collection[T]':
        filtered_items = [
            item for item in self._items.values()
            if isinstance(item, dict) and item.get(key) == value
        ]
        return self.__class__(filtered_items)

    def pluck(self, key: Any) -> List[Any]:
        return [
            item.get(key) for item in self._items.values()
            if isinstance(item, dict)
        ]

    def map(self, func: Callable[[T], V]) -> 'Collection[V]':
        return self.__class__([func(item) for item in self._items.values()])

    def filter(self, func: Callable[[T], bool]) -> 'Collection[T]':
        return self.__class__([item for item in self._items.values() if func(item)])

    def sort_by(self, key: Any) -> 'Collection[T]':
        sorted_items = sorted(
            self._items.values(),
            key=lambda item: item.get(key) if isinstance(item, dict) else None
        )
        return self.__class__(sorted_items)

    def group_by(self, key: Any) -> Dict[Any, List[T]]:
        grouped: Dict[Any, List[T]] = {}
        for item in self._items.values():
            if isinstance(item, dict) and key in item:
                group_key = item[key]
                grouped.setdefault(group_key, []).append(item)
        return grouped

    def unique(self) -> 'Collection[T]':
        seen = set()
        unique_items = []
        for item in self._items.values():
            try:
                if item not in seen:
                    unique_items.append(item)
                    seen.add(item)
            except TypeError:
                rep = tuple(sorted(item.items())) if isinstance(item, dict) else str(item)
                if rep not in seen:
                    unique_items.append(item)
                    seen.add(rep)
        return self.__class__(unique_items)

    def to_dict(self, key_name: Any, value_name: Any) -> Dict[Any, Any]:
        return {
            item.get(key_name): item.get(value_name)
            for item in self._items.values()
            if isinstance(item, dict) and key_name in item and value_name in item
        }

    def take(self, count: int) -> 'Collection[T]':
        if count < 0:
            return self.__class__([])
        return self.__class__(list(self._items.values())[:count])

    def is_empty(self) -> bool:
        return not self._items

    def is_not_empty(self) -> bool:
        return bool(self._items)

    def all(self) -> List[T]:
        return list(self._items.values())

    def first(self) -> Optional[T]:
        return next(iter(self._items.values()), None)