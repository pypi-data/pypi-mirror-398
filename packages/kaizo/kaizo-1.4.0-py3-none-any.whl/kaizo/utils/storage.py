from dataclasses import dataclass
from typing import Self

from .entry import DictEntry, Entry


@dataclass
class Storage:
    value: Entry | None
    items: DictEntry[str]

    @staticmethod
    def init() -> Self:
        return Storage(
            value=None,
            items=DictEntry(resolve=False),
        )

    def get(self, key: str | None = None) -> Entry | None:
        if key is None:
            return self.value

        return self.items.get(key)

    def set(self, key: str, value: Entry) -> None:
        self.items[key] = value
