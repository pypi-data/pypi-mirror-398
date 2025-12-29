import uuid
from abc import ABC, abstractmethod
from collections.abc import Generator, Iterable, MutableMapping, MutableSequence
from dataclasses import dataclass, field
from typing import Any, Generic, Self, SupportsIndex, TypeVar

from .cache import Cacheable
from .fn import FnWithKwargs

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class Entry(ABC):
    key: str

    @abstractmethod
    def __call__(self) -> Any:
        pass


class DictEntry(MutableMapping, Cacheable, Generic[K]):
    _data: dict[K, Entry]
    _resolve: bool

    def __init__(self, data: dict[K, Entry] | None = None, *, resolve: bool = True) -> None:
        super().__init__()

        self._data = data or {}
        self._resolve = resolve

    @staticmethod
    def from_raw(
        root_key: str | None = None,
        raw_data: dict[K, Any] | None = None,
        *,
        resolve: bool = True,
    ) -> Self:
        if root_key is None:
            root_key = uuid.uuid4().hex

        if raw_data is None:
            raw_data = {}

        data = {
            key: FieldEntry(key=root_key, value=value) for key, value in raw_data.items()
        }

        return DictEntry(data=data, resolve=resolve)

    def __setitem__(self, key: K, value: Any) -> None:
        if not isinstance(value, Entry):
            msg = f"Value must be an Entry instance, got {type(value)}"
            raise TypeError(msg)

        self._data[key] = value
        self._update_id()

    def __getitem__(self, key: K) -> Any:
        value = self._data[key]

        if not isinstance(value, Entry):
            msg = f"Value must be an Entry instance, got {type(value)}"
            raise TypeError(msg)

        if self._resolve:
            return value.__call__()

        return value

    def __delitem__(self, key: K) -> None:
        self._data.__delitem__(key)
        self._update_id()

    def __iter__(self) -> Generator[K]:
        yield from self._data

    def __len__(self) -> int:
        return self._data.__len__()

    def __contains__(self, key: K) -> bool:
        return self._data.__contains__(key)


class ListEntry(MutableSequence, Cacheable):
    _data: list[Entry]
    _resolve: bool

    def __init__(self, data: list[Entry] | None = None, *, resolve: bool = True) -> None:
        super().__init__()

        self._data = data or []
        self._resolve = resolve

    @staticmethod
    def from_raw(
        root_key: str | None = None,
        raw_data: list[Any] | None = None,
        *,
        resolve: bool = True,
    ) -> Self:
        if root_key is None:
            root_key = uuid.uuid4().hex

        if raw_data is None:
            raw_data = []

        data = [FieldEntry(key=root_key, value=value) for value in raw_data]

        return ListEntry(data=data, resolve=resolve)

    def __setitem__(self, i: SupportsIndex, value: Any) -> None:
        if isinstance(value, Iterable):
            for value_i in value:
                if not isinstance(value_i, Entry):
                    msg = f"Value must be an Entry instance, got {type(value_i)}"
                    raise TypeError(msg)

        elif not isinstance(value, Entry):
            msg = f"Value must be an Entry instance, got {type(value)}"
            raise TypeError(msg)

        self._data[i] = value
        self._update_id()

    def __getitem__(self, i: SupportsIndex) -> Any:
        value = self._data.__getitem__(i)

        if isinstance(value, Iterable):
            new_values = []
            for value_i in value:
                if not isinstance(value_i, Entry):
                    msg = f"Value must be an Entry instance, got {type(value_i)}"
                    raise TypeError(msg)

                if self._resolve:
                    new_values.append(value_i.__call__())
                else:
                    new_values.append(value_i)

            return new_values

        if isinstance(value, Entry):
            if self._resolve:
                return value.__call__()

            return value

        msg = f"Value must be an Entry instance, got {type(value)}"
        raise TypeError(msg)

    def __delitem__(self, i: SupportsIndex) -> None:
        self._data.__delitem__(i)
        self._update_id()

    def __len__(self) -> int:
        return self._data.__len__()

    def insert(self, index: SupportsIndex, value: Any) -> None:
        if not isinstance(value, Entry):
            msg = f"Value must be an Entry instance, got {type(value)}"
            raise TypeError(msg)

        self._data.insert(index, value)
        self._update_id()


@dataclass
class FieldEntry(Entry, Generic[V]):
    value: V

    def __call__(self) -> V:
        return self.value


@dataclass
class ModuleEntry(Entry):
    obj: Any
    call: Any
    lazy: bool
    args: DictEntry[str] | ListEntry | None = None
    cache: bool = True
    fn: FnWithKwargs = field(init=False)
    bucket: dict[str] = field(init=False)

    def __post_init__(self) -> None:
        self.bucket = {}

        if self.call is False:
            return

        kwargs = {}
        args = ()

        if isinstance(self.args, DictEntry):
            kwargs = self.args
        elif isinstance(self.args, ListEntry):
            args = self.args

        if self.call is True:
            if not callable(self.obj):
                msg = f"'{self.obj}' is not callable"
                raise TypeError(msg)

            self.fn = FnWithKwargs(fn=self.obj, args=args, kwargs=kwargs)
            return

        if not hasattr(self.obj, self.call):
            msg = f"'{self.obj}' has no attribute '{self.call}'"
            raise AttributeError(msg)

        fn = getattr(self.obj, self.call)

        if not callable(fn):
            msg = f"'{fn}' is not callable"
            raise TypeError(msg)

        self.fn = FnWithKwargs(fn=fn, args=args, kwargs=kwargs)

    def __call__(self) -> Any | FnWithKwargs:
        if self.call is False:
            return self.obj

        if self.lazy:
            return self.fn

        if not self.cache:
            return self.fn.__call__()

        uid = None

        if self.args is not None:
            uid = self.args.uid

        if uid not in self.bucket:
            self.bucket[uid] = self.fn.__call__()

        return self.bucket[uid]
