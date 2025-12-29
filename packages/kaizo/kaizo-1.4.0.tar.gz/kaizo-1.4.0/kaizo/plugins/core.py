from dataclasses import dataclass
from typing import Self

from kaizo.utils.entry import DictEntry, ListEntry


@dataclass
class PluginMetadata:
    args: DictEntry[str] | ListEntry | None = None


class Plugin:
    metadata: PluginMetadata

    @classmethod
    def dispatch(cls: type[Self], metadata: PluginMetadata) -> Self:
        kwargs = {}
        args = ()

        if isinstance(metadata.args, DictEntry):
            kwargs = metadata.args
        elif isinstance(metadata.args, ListEntry):
            args = metadata.args

        plugin = cls(*args, **kwargs)
        plugin.metadata = metadata

        return plugin
