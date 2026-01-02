import datetime
import os
from collections.abc import Generator, Iterable
from typing import Any

import ujson as json
from iker.common.utils.dtutils import dt_format, dt_parse, extended_format
from iker.common.utils.jsonutils import JsonType, JsonValueCompatible
from iker.common.utils.jsonutils import json_reformat
from iker.common.utils.sequtils import batched

from plexus.common.utils.shutils import collect_volumed_filenames, populate_volumed_filenames

__all__ = [
    "json_datetime_decoder",
    "json_datetime_encoder",
    "json_loads",
    "json_dumps",
    "read_chunked_jsonl",
    "write_chunked_jsonl",
]


def json_datetime_decoder(v: Any) -> datetime.datetime:
    if isinstance(v, str):
        return json_datetime_decoder(dt_parse(v, extended_format(with_us=True, with_tz=True)))
    if isinstance(v, datetime.datetime):
        return v.replace(tzinfo=datetime.timezone.utc)
    raise ValueError("unexpected type of value for datetime decoder")


def json_datetime_encoder(v: Any) -> str:
    if isinstance(v, str):
        return json_datetime_encoder(dt_parse(v, extended_format(with_us=True, with_tz=True)))
    if isinstance(v, datetime.datetime):
        return dt_format(v.replace(tzinfo=datetime.timezone.utc), extended_format(with_us=True, with_tz=True))
    raise ValueError("unexpected type of value for datetime encoder")


def json_deserializer(obj):
    def value_formatter(value: JsonValueCompatible) -> JsonType:
        if not isinstance(value, str):
            return value
        try:
            return dt_parse(value, extended_format(with_us=True, with_tz=True))
        except Exception:
            return value

    return json_reformat(obj, value_formatter=value_formatter)


def json_serializer(obj):
    def unregistered_formatter(unregistered: Any) -> JsonType:
        if isinstance(unregistered, datetime.datetime):
            return dt_format(unregistered, extended_format(with_us=True, with_tz=True))
        return None

    return json_reformat(obj, raise_if_unregistered=False, unregistered_formatter=unregistered_formatter)


def json_loads(s: str) -> JsonType:
    return json_deserializer(json.loads(s))


def json_dumps(obj: JsonType) -> str:
    return json.dumps(json_serializer(obj), ensure_ascii=False, escape_forward_slashes=False)


def read_chunked_jsonl(template: str) -> Generator[tuple[JsonType, str], None, None]:
    for path, _ in collect_volumed_filenames(template):
        with open(path, mode="r", encoding="utf-8") as fh:
            for line in fh:
                yield json_loads(line), path


def write_chunked_jsonl(records: Iterable[JsonType], template: str, chunk_size: int) -> list[tuple[str, int]]:
    generator = populate_volumed_filenames(template)
    entry = []
    for batch_index, batch in enumerate(batched(records, chunk_size)):
        path, _ = next(generator)
        lines = 0
        with open(path, mode="w") as fh:
            for record in batch:
                fh.write(json_dumps(record))
                fh.write("\n")
                lines += 1
        entry.append((path, lines))
    if len(entry) == 1:
        path, lines = entry[0]
        os.rename(path, template)
        return [(template, lines)]
    return entry
