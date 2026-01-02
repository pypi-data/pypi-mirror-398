import os
import unittest
from collections.abc import Callable, Generator

import ddt
from iker.common.utils.dtutils import dt_parse_iso

from plexus.common.utils.shutils import collect_volumed_filenames, populate_volumed_filenames
from plexus_tests import resources_directory


@ddt.ddt
class ShUtilsTest(unittest.TestCase):
    data_collect_volumed_filenames = [
        ("dummy.txt", [("dummy.txt", {})]),
        (
            "dummy.{{}}.jsonl",
            [
                ("dummy.0.jsonl", {"0": 0}),
                ("dummy.1.jsonl", {"0": 1}),
                ("dummy.2.jsonl", {"0": 2}),
            ],
        ),
        (
            "dummy.{{}}.{{}}.jsonl",
            [
                ("dummy.0.0.jsonl", {"0": 0, "1": 0}),
                ("dummy.1.1.jsonl", {"0": 1, "1": 1}),
                ("dummy.2.2.jsonl", {"0": 2, "1": 2}),
            ],
        ),
        (
            "dummy.{foo:{}}.{bar:{}}.jsonl",
            [
                ("dummy.0.0.jsonl", {"foo": 0, "bar": 0}),
                ("dummy.1.1.jsonl", {"foo": 1, "bar": 1}),
                ("dummy.2.2.jsonl", {"foo": 2, "bar": 2}),
            ],
        ),
        (
            "dummy.{foo:{}}.{bar:{}}.{vol-{}}.jsonl",
            [
                ("dummy.0.0.vol-0.jsonl", {"foo": 0, "bar": 0, "0": 0}),
                ("dummy.1.1.vol-1.jsonl", {"foo": 1, "bar": 1, "0": 1}),
                ("dummy.2.2.vol-2.jsonl", {"foo": 2, "bar": 2, "0": 2}),
            ],
        ),
        (
            "dummy{sn:.{}}.jsonl",
            [
                ("dummy.0.jsonl", {"sn": 0}),
                ("dummy.1.jsonl", {"sn": 1}),
                ("dummy.2.jsonl", {"sn": 2}),
            ],
        ),
        (
            "dummy.csv{sn:.part{}}",
            [
                ("dummy.csv.part0", {"sn": 0}),
                ("dummy.csv.part1", {"sn": 1}),
                ("dummy.csv.part2", {"sn": 2}),
            ],
        ),
        (
            "{sn:{}-}dummy",
            [
                ("0-dummy", {"sn": 0}),
                ("1-dummy", {"sn": 1}),
                ("2-dummy", {"sn": 2}),
            ],
        ),
    ]

    @ddt.idata(data_collect_volumed_filenames)
    @ddt.unpack
    def test_collect_volumed_filenames(self, template, names):
        self.assertEqual(
            list((os.path.join(resources_directory, "unittest/shutils", name), volumes)
                 for name, volumes in names),
            list(sorted(
                collect_volumed_filenames(os.path.join(resources_directory, "unittest/shutils", template)))),
        )

    data_populate_volumed_filenames = [
        ("dummy.txt", [("dummy.txt", {}), ("dummy.txt", {}), ("dummy.txt", {})]),
        (
            "dummy.{{}}.jsonl",
            [
                ("dummy.0.jsonl", {"0": 0}),
                ("dummy.1.jsonl", {"0": 1}),
                ("dummy.2.jsonl", {"0": 2}),
            ],
        ),
        (
            "dummy.{{}}.{{}}.jsonl",
            [
                ("dummy.0.0.jsonl", {"0": 0, "1": 0}),
                ("dummy.1.1.jsonl", {"0": 1, "1": 1}),
                ("dummy.2.2.jsonl", {"0": 2, "1": 2}),
            ],
        ),
        (
            "dummy.{foo:{}}.{bar:{}}.jsonl",
            [
                ("dummy.0.0.jsonl", {"foo": 0, "bar": 0}),
                ("dummy.1.1.jsonl", {"foo": 1, "bar": 1}),
                ("dummy.2.2.jsonl", {"foo": 2, "bar": 2}),
            ],
        ),
        (
            "dummy.{foo:{}}.{bar:{}}.{vol-{}}.jsonl",
            [
                ("dummy.0.0.vol-0.jsonl", {"foo": 0, "bar": 0, "0": 0}),
                ("dummy.1.1.vol-1.jsonl", {"foo": 1, "bar": 1, "0": 1}),
                ("dummy.2.2.vol-2.jsonl", {"foo": 2, "bar": 2, "0": 2}),
            ],
        ),
        (
            "dummy{sn:.{}}.jsonl",
            [
                ("dummy.0.jsonl", {"sn": 0}),
                ("dummy.1.jsonl", {"sn": 1}),
                ("dummy.2.jsonl", {"sn": 2}),
            ],
        ),
        (
            "dummy.csv{sn:.part{}}",
            [
                ("dummy.csv.part0", {"sn": 0}),
                ("dummy.csv.part1", {"sn": 1}),
                ("dummy.csv.part2", {"sn": 2}),
            ],
        ),
        (
            "{sn:{}-}dummy",
            [
                ("0-dummy", {"sn": 0}),
                ("1-dummy", {"sn": 1}),
                ("2-dummy", {"sn": 2}),
            ],
        ),
    ]

    @ddt.idata(data_populate_volumed_filenames)
    @ddt.unpack
    def test_populate_volumed_filenames(self, template, names):
        generator = populate_volumed_filenames(os.path.join(resources_directory, "unittest/shutils", template))
        self.assertEqual(
            list((os.path.join(resources_directory, "unittest/shutils", name), volumes)
                 for name, volumes in names),
            list(next(generator) for _ in names),
        )

    data_populate_volumed_filenames__custom_volume_gen = [
        ("dummy.txt", [("dummy.txt", {}), ("dummy.txt", {}), ("dummy.txt", {})]),
        (
            "dummy.{{}}.jsonl",
            [
                ("dummy.1.jsonl", {"0": 1}),
                ("dummy.2.jsonl", {"0": 2}),
                ("dummy.4.jsonl", {"0": 4}),
            ],
        ),
        (
            "dummy.{{}}.{{}}.jsonl",
            [
                ("dummy.1.1.jsonl", {"0": 1, "1": 1}),
                ("dummy.2.2.jsonl", {"0": 2, "1": 2}),
                ("dummy.4.4.jsonl", {"0": 4, "1": 4}),
            ],
        ),
        (
            "dummy.{foo:{}}.{bar:{}}.jsonl",
            [
                ("dummy.1.1.jsonl", {"foo": 1, "bar": 1}),
                ("dummy.2.2.jsonl", {"foo": 2, "bar": 2}),
                ("dummy.4.4.jsonl", {"foo": 4, "bar": 4}),
            ],
        ),
        (
            "dummy.{foo:{}}.{bar:{}}.{vol-{}}.jsonl",
            [
                ("dummy.1.1.vol-1.jsonl", {"foo": 1, "bar": 1, "0": 1}),
                ("dummy.2.2.vol-2.jsonl", {"foo": 2, "bar": 2, "0": 2}),
                ("dummy.4.4.vol-4.jsonl", {"foo": 4, "bar": 4, "0": 4}),
            ],
        ),
        (
            "dummy{sn:.{}}.jsonl",
            [
                ("dummy.1.jsonl", {"sn": 1}),
                ("dummy.2.jsonl", {"sn": 2}),
                ("dummy.4.jsonl", {"sn": 4}),
            ],
        ),
        (
            "dummy.csv{sn:.part{}}",
            [
                ("dummy.csv.part1", {"sn": 1}),
                ("dummy.csv.part2", {"sn": 2}),
                ("dummy.csv.part4", {"sn": 4}),
            ],
        ),
        (
            "{sn:{}-}dummy",
            [
                ("1-dummy", {"sn": 1}),
                ("2-dummy", {"sn": 2}),
                ("4-dummy", {"sn": 4}),
            ],
        ),
        (
            "dummy.{dt:{}}.{ts:{}}.{sn:vol-{}}.jsonl",
            [
                ("dummy.20250101.1735689600.vol-1.jsonl", {"dt": 20250101, "ts": 1735689600, "sn": 1}),
                ("dummy.20250102.1735776000.vol-2.jsonl", {"dt": 20250102, "ts": 1735776000, "sn": 2}),
                ("dummy.20250103.1735862400.vol-4.jsonl", {"dt": 20250103, "ts": 1735862400, "sn": 4}),
            ],
        ),
    ]

    @ddt.idata(data_populate_volumed_filenames__custom_volume_gen)
    @ddt.unpack
    def test_populate_volumed_filenames__custom_volume_gen(self, template, names):

        def make_custom_volume_func() -> Callable[[str], int]:
            def datetime_volume_generator() -> Generator[int, None, None]:
                volume = 20250101
                while True:
                    yield volume
                    volume += 1

            def timestamp_volume_generator() -> Generator[int, None, None]:
                volume = int(dt_parse_iso("2025-01-01").timestamp())
                while True:
                    yield volume
                    volume += 86400

            def sequence_volume_generator() -> Generator[int, None, None]:
                volume = 1
                while True:
                    yield volume
                    volume *= 2

            volume_generators = {}

            def volume_func(name: str) -> int:
                if name not in volume_generators:
                    match name:
                        case "dt":
                            volume_generator = datetime_volume_generator()
                        case "ts":
                            volume_generator = timestamp_volume_generator()
                        case _:
                            volume_generator = sequence_volume_generator()
                    volume_generators[name] = volume_generator
                return next(volume_generators[name])

            return volume_func

        generator = populate_volumed_filenames(os.path.join(resources_directory, "unittest/shutils", template),
                                               volume_func=make_custom_volume_func())
        self.assertEqual(
            list((os.path.join(resources_directory, "unittest/shutils", name), volumes)
                 for name, volumes in names),
            list(next(generator) for _ in names),
        )
