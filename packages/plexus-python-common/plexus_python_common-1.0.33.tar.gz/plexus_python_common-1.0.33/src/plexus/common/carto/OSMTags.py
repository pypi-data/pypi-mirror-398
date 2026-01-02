import datetime
from typing import Any, Self

from iker.common.utils.strutils import repr_data, str_conv


class OSMTags(object):
    """
    Represents tag in OSM
    """

    @classmethod
    def from_any_tags(cls, any_tags: dict[str, Any] = None) -> Self:
        """
        Creates an instance from any-typed tags by automatically inferring data types

        :param any_tags: tags with any-typed values

        :return: OSM tag instance
        """
        if any_tags is None:
            return OSMTags({})
        return OSMTags({k: str_conv(v) for k, v in any_tags.items()})

    def __init__(self, tags: dict[str, Any]):
        """
        Creates an instance from the given tags

        :param tags: given tags
        """
        self.tags = tags

    def __str__(self):
        return repr_data(self)

    def __iter__(self):
        return self.tags.__iter__()

    def __getitem__(self, k: str):
        return self.tags.__getitem__(k)

    def items(self):
        return self.tags.items()

    def set(self, key: str, value: Any) -> Any:
        old_value = self.tags.get(key)
        self.tags[key] = str_conv(value)
        return old_value

    def get(self, key: str, default: Any | None = None) -> Any | None:
        return self.tags.get(key, default)

    def getint(self, key: str, default: int | None = None) -> int | None:
        value = self.tags.get(key, default)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if default is None:
            return None
        if isinstance(default, int) and not isinstance(default, bool):
            return default
        raise TypeError("type of either the value or the given default is incompatible, should be 'int'")

    def getfloat(self, key: str, default: float | None = None) -> float | None:
        value = self.tags.get(key, default)
        if isinstance(value, float):
            return value
        if default is None:
            return None
        if isinstance(default, float):
            return default
        raise TypeError("type of either the value or the given default is incompatible, should be 'float'")

    def getboolean(self, key: str, default: bool | None = None) -> bool | None:
        value = self.tags.get(key, default)
        if isinstance(value, bool):
            return value
        if default is None:
            return None
        if isinstance(default, bool):
            return default
        raise TypeError("type of either the value or the given default is incompatible, should be 'bool'")

    def getdatetime(self, key: str, default: datetime.datetime | None = None) -> datetime.datetime | None:
        value = self.tags.get(key, default)
        if isinstance(value, datetime.datetime):
            return value
        if default is None:
            return None
        if isinstance(default, datetime.datetime):
            return default
        raise TypeError("type of either the value or the given default is incompatible, should be 'datetime.datetime'")

    def getstring(self, key: str, default: str | None = None) -> str | None:
        value = self.tags.get(key, default)
        if isinstance(value, str):
            return value
        if default is None:
            return None
        if isinstance(default, str):
            return default
        raise TypeError("type of either the value or the given default is incompatible, should be 'str'")
