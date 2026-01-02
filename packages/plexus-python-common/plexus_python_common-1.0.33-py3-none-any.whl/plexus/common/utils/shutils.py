import os
from collections.abc import Callable, Generator

import pyparsing as pp
from iker.common.utils.funcutils import singleton
from iker.common.utils.strutils import is_blank

__all__ = [
    "volume_template_parser",
    "make_volume_parser",
    "make_volume_generator",
    "collect_volumed_filenames",
    "populate_volumed_filenames",
]


@singleton
def volume_template_parser() -> pp.ParserElement:
    lbrace_token = pp.Char("{")
    rbrace_token = pp.Char("}")
    colon_token = pp.Char(":")
    chars_token = pp.Regex(r"[^{}]*")
    name_token = pp.Regex(r"[a-z][a-z0-9_]*")

    parser_expr = pp.Combine(lbrace_token +
                             (name_token("name") + colon_token)[0, 1] +
                             chars_token("prefix") +
                             lbrace_token +
                             rbrace_token +
                             chars_token("suffix") +
                             rbrace_token)
    return parser_expr


def make_trivial_volume_func() -> Callable[[str], int]:
    """
    Creates a trivial volume function that generates unique integer volumes for each name.

    The function maintains a generator for each unique name and increments the volume
    value each time the function is called with the same name. If a new name is provided,
    a new generator is created for that name.

    :return: a callable function that takes a name (str) and returns the next integer volume.
    """

    def trivial_volume_generator() -> Generator[int, None, None]:
        volume = 0
        while True:
            yield volume
            volume += 1

    volume_generators = {}

    def volume_func(name: str) -> int:
        if name not in volume_generators:
            volume_generators[name] = trivial_volume_generator()
        return next(volume_generators[name])

    return volume_func


def make_volume_parser(template: str) -> Callable[[str], dict[str, int]]:
    """
    Creates a parser function for extracting volume information from filenames based on a given template.

    The template defines the structure of filenames, including placeholders for volume values.
    The returned parser function takes a filename as input and extracts the volume values
    as a dictionary where the keys are the placeholder names and the values are the corresponding integers.

    :param template: a string template defining the filename structure with placeholders for volumes.
                     Placeholders are enclosed in double curly braces `{{}}` and can optionally include
                     a name, a prefix, and a suffix (e.g., `{name:prefix{}suffix}`).

    :return: a callable function that takes a filename (str) and returns a dictionary mapping
             placeholder names to their extracted integer values.

    :raises ValueError: if the template is invalid or cannot be parsed.
    """
    try:
        scan_result = list(volume_template_parser().scan_string(template, overlap=False))
    except pp.ParseException as e:
        raise ValueError(f"bad template '{template}'") from e

    volume_token = pp.Regex(r"\d+")

    parser_expr = pp.Literal("")
    prev_end_pos = 0
    index = 0
    for parse_results, begin_pos, end_pos in scan_result:
        if prev_end_pos < begin_pos:
            parser_expr = parser_expr + pp.Literal(template[prev_end_pos:begin_pos])
        prefix = parse_results.get("prefix")
        suffix = parse_results.get("suffix")
        name = parse_results.get("name")
        if is_blank(name):
            name = str(index)
            index += 1
        if not is_blank(prefix):
            parser_expr = parser_expr + pp.Literal(prefix)
        parser_expr = parser_expr + volume_token(name)
        if not is_blank(suffix):
            parser_expr = parser_expr + pp.Literal(suffix)
        prev_end_pos = end_pos
    if prev_end_pos < len(template):
        parser_expr = parser_expr + pp.Literal(template[prev_end_pos:])

    parser_expr = pp.Combine(pp.StringStart() + parser_expr + pp.StringEnd())

    def parser(s: str) -> dict[str, int]:
        parser_results = parser_expr.parse_string(s, parse_all=True)

        volumes = {}
        for name in parser_results.keys():
            volume = parser_results.get(name)
            volumes[name] = int(volume)

        return volumes

    return parser


def make_volume_generator(template: str) -> Callable[[Callable[[str], int]], tuple[str, dict[str, int]]]:
    """
    Creates a generator function for producing filenames and their associated volume values
    based on a given template.

    The template defines the structure of filenames, including placeholders for volume values.
    The returned generator function takes a volume function as input, which determines the
    volume values for each placeholder, and produces filenames with the corresponding volumes.

    :param template: a string template defining the filename structure with placeholders for volumes.
                     Placeholders are enclosed in double curly braces `{{}}` and can optionally include
                     a name, a prefix, and a suffix (e.g., `{name:prefix{}suffix}`).

    :return: a callable generator function that takes a volume function (Callable[[str], int]) as input
             and returns a tuple containing the generated filename (str) and a dictionary mapping
             placeholder names to their corresponding volume values (dict[str, int]).

    :raises ValueError: if the template is invalid or cannot be parsed.
    """
    try:
        scan_result = list(volume_template_parser().scan_string(template, overlap=False))
    except pp.ParseException as e:
        raise ValueError(f"bad template '{template}'") from e

    def generator(volume_func: Callable[[str], int]) -> tuple[str, dict[str, int]]:
        volumes = {}

        volume_expr = ""
        prev_end_pos = 0
        index = 0
        for parse_results, begin_pos, end_pos in scan_result:
            if prev_end_pos < begin_pos:
                volume_expr = volume_expr + template[prev_end_pos:begin_pos]
            prefix = parse_results.get("prefix")
            suffix = parse_results.get("suffix")
            name = parse_results.get("name")
            if is_blank(name):
                name = str(index)
                index += 1
            if not is_blank(prefix):
                volume_expr = volume_expr + prefix
            volumes[name] = int(volume_func(name))
            volume_expr = volume_expr + str(volumes[name])
            if not is_blank(suffix):
                volume_expr = volume_expr + suffix
            prev_end_pos = end_pos
        if prev_end_pos < len(template):
            volume_expr = volume_expr + template[prev_end_pos:]

        return volume_expr, volumes

    return generator


def collect_volumed_filenames(template: str) -> Generator[tuple[str, dict[str, int]], None, None]:
    """
    Collects filenames in a folder that match a given template and extracts their volume information.

    The template defines the structure of filenames, including placeholders for volume values.
    This function scans the folder containing the template and attempts to parse filenames
    to extract volume values based on the template.

    :param template: a string template defining the filename structure with placeholders for volumes.
                     Placeholders are enclosed in double curly braces `{{}}` and can optionally include
                     a name, a prefix, and a suffix (e.g., `{name:prefix{}suffix}`).

    :return: a generator yielding tuples where the first element is the full path of the filename
             and the second element is a dictionary mapping placeholder names to their extracted
             integer volume values.
    """
    folder = os.path.dirname(template)
    basename = os.path.basename(template)

    parser = make_volume_parser(basename)

    for name in os.listdir(folder):
        try:
            volumes = parser(name)
            yield os.path.join(folder, name), volumes
        except pp.ParseException:
            pass


def populate_volumed_filenames(
    template: str,
    *,
    volume_func: Callable[[str], int] = None,
) -> Generator[tuple[str, dict[str, int]], None, None]:
    """
    Generates filenames and their associated volume values based on a given template.

    The template defines the structure of filenames, including placeholders for volume values.
    This function uses a volume function to generate unique volume values for each placeholder
    and produces filenames with the corresponding volumes.

    :param template: a string template defining the filename structure with placeholders for volumes.
                     Placeholders are enclosed in double curly braces `{{}}` and can optionally include
                     a name, a prefix, and a suffix (e.g., `{name:prefix{}suffix}`).
    :param volume_func: a callable function that takes a placeholder name (str) and returns the next
                        integer volume value. If not provided, a trivial volume function is used.

    :return: a generator yielding tuples where the first element is the generated filename (str)
             and the second element is a dictionary mapping placeholder names to their corresponding
    """
    folder = os.path.dirname(template)
    basename = os.path.basename(template)

    generator = make_volume_generator(basename)
    volume_func = volume_func or make_trivial_volume_func()

    while True:
        name, volumes = generator(volume_func)
        yield os.path.join(folder, name), volumes
