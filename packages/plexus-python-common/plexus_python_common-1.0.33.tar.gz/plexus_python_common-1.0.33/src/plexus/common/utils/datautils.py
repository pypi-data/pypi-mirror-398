import datetime
from collections.abc import Callable, Generator
from typing import Any

import pyparsing as pp
import ujson as json
from iker.common.utils.funcutils import singleton
from iker.common.utils.jsonutils import JsonType
from iker.common.utils.randutils import randomizer

from plexus.common.utils.strutils import BagName, UserName, VehicleName
from plexus.common.utils.strutils import colon_tag_parser, slash_tag_parser
from plexus.common.utils.strutils import dot_case_parser, kebab_case_parser, snake_case_parser
from plexus.common.utils.strutils import hex_string_parser
from plexus.common.utils.strutils import parse_bag_name, parse_user_name, parse_vehicle_name
from plexus.common.utils.strutils import semver_parser, uuid_parser
from plexus.common.utils.strutils import strict_abspath_parser, strict_relpath_parser
from plexus.common.utils.strutils import topic_parser, vin_code_chars, vin_code_parser


def make_compute_vin_code_check_digit() -> Callable[[str], str]:
    trans_nums = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 7, 9, 2, 3, 4, 5, 6, 7, 8, 9]
    weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]

    trans_dict = {vin_code_char: trans_num for vin_code_char, trans_num in zip(vin_code_chars, trans_nums)}

    def func(vin_code: str) -> str:
        remainder = sum(trans_dict[vin_code_char] * weight for vin_code_char, weight in zip(vin_code, weights)) % 11
        return "X" if remainder == 10 else str(remainder)

    return func


compute_vin_code_check_digit = make_compute_vin_code_check_digit()


def make_validate_string(element: pp.ParserElement) -> Callable[[str], None]:
    def func(s: str) -> None:
        try:
            if not element.parse_string(s, parse_all=True):
                raise ValueError(f"failed to parse '{s}'")
        except Exception as e:
            raise ValueError(f"encountered error while parsing '{s}'") from e

    return func


validate_hex_string = make_validate_string(hex_string_parser)

validate_snake_case = make_validate_string(snake_case_parser)
validate_kebab_case = make_validate_string(kebab_case_parser)
validate_dot_case = make_validate_string(dot_case_parser)

validate_uuid = make_validate_string(uuid_parser)

validate_strict_relpath = make_validate_string(strict_relpath_parser)
validate_strict_abspath = make_validate_string(strict_abspath_parser)

validate_semver = make_validate_string(semver_parser)

validate_colon_tag = make_validate_string(colon_tag_parser)
validate_slash_tag = make_validate_string(slash_tag_parser)

validate_topic = make_validate_string(topic_parser)


def validate_vin_code(vin_code: str):
    make_validate_string(vin_code_parser)(vin_code)
    check_digit = compute_vin_code_check_digit(vin_code)
    if check_digit != vin_code[8]:
        raise ValueError(f"get wrong VIN code check digit from '{vin_code}', expected '{check_digit}'")


def make_validate_parse_string(parse: Callable[[str], Any]) -> Callable[[str], None]:
    def func(s: str) -> None:
        try:
            if not parse(s):
                raise ValueError(f"failed to parse '{s}'")
        except Exception as e:
            raise ValueError(f"encountered error while parsing '{s}'") from e

    return func


validate_user_name = make_validate_parse_string(parse_user_name)
validate_vehicle_name = make_validate_parse_string(parse_vehicle_name)
validate_bag_name = make_validate_parse_string(parse_bag_name)


def validate_dt_timezone(dt: datetime.datetime):
    if dt.tzinfo != datetime.timezone.utc:
        raise ValueError(f"dt '{dt}' is not in UTC")


def validate_json_type_dump_size(json_type: JsonType, dump_size_limit: int = 10000):
    dump_string = json.dumps(json_type, ensure_ascii=False)
    if len(dump_string) > dump_size_limit:
        raise ValueError(f"dump size exceeds the maximum length '{dump_size_limit}'")


def random_vin_code() -> str:
    vin_code = randomizer().random_string(vin_code_chars, 17)
    check_digit = compute_vin_code_check_digit(vin_code)
    return vin_code[:8] + check_digit + vin_code[9:]


@singleton
def known_topics() -> list[str]:
    return [
        "/sensor/camera/front_center",
        "/sensor/camera/front_left",
        "/sensor/camera/front_right",
        "/sensor/camera/side_left",
        "/sensor/camera/side_right",
        "/sensor/camera/rear_left",
        "/sensor/camera/rear_right",
        "/sensor/lidar/front_center",
        "/sensor/lidar/front_left_corner",
        "/sensor/lidar/front_right_corner",
        "/sensor/lidar/side_left",
        "/sensor/lidar/side_right",
    ]


@singleton
def known_user_names() -> list[UserName]:
    return [
        UserName("adam", "anderson"),
        UserName("ben", "bennett"),
        UserName("charlie", "clark"),
        UserName("david", "dixon"),
        UserName("evan", "edwards"),
        UserName("frank", "fisher"),
        UserName("george", "graham"),
        UserName("henry", "harrison"),
        UserName("isaac", "irving"),
        UserName("jack", "jacobs"),
        UserName("kevin", "kennedy"),
        UserName("luke", "lawson"),
        UserName("michael", "mitchell"),
        UserName("nathan", "newton"),
        UserName("oscar", "owens"),
        UserName("paul", "peterson"),
        UserName("quincy", "quinn"),
        UserName("ryan", "robinson"),
        UserName("sam", "stevens"),
        UserName("tom", "thomas"),
        UserName("umar", "underwood"),
        UserName("victor", "vaughan"),
        UserName("william", "walker"),
        UserName("xander", "xavier"),
        UserName("yale", "young"),
        UserName("zane", "zimmerman"),
    ]


@singleton
def known_vehicle_names() -> list[VehicleName]:
    return [
        VehicleName("cascadia", "antelope", "00000", "3AKJGLD5XLS000000"),
        VehicleName("cascadia", "bear", "00001", "3AKJGLD51LS000001"),
        VehicleName("cascadia", "cheetah", "00002", "3AKJGLD53LS000002"),
        VehicleName("cascadia", "dolphin", "00003", "3AKJGLD55LS000003"),
        VehicleName("cascadia", "eagle", "00004", "3AKJGLD57LS000004"),
        VehicleName("cascadia", "falcon", "00005", "3AKJGLD59LS000005"),
        VehicleName("cascadia", "gorilla", "00006", "3AKJGLD50LS000006"),
        VehicleName("cascadia", "hawk", "00007", "3AKJGLD52LS000007"),
        VehicleName("cascadia", "iguana", "00008", "3AKJGLD54LS000008"),
        VehicleName("cascadia", "jaguar", "00009", "3AKJGLD56LS000009"),
        VehicleName("cascadia", "koala", "00010", "3AKJGLD52LS000010"),
        VehicleName("cascadia", "leopard", "00011", "3AKJGLD54LS000011"),
        VehicleName("cascadia", "mongoose", "00012", "3AKJGLD56LS000012"),
        VehicleName("cascadia", "narwhal", "00013", "3AKJGLD58LS000013"),
        VehicleName("cascadia", "otter", "00014", "3AKJGLD5XLS000014"),
        VehicleName("cascadia", "panther", "00015", "3AKJGLD51LS000015"),
        VehicleName("cascadia", "quail", "00016", "3AKJGLD53LS000016"),
        VehicleName("cascadia", "rhino", "00017", "3AKJGLD55LS000017"),
        VehicleName("cascadia", "snake", "00018", "3AKJGLD57LS000018"),
        VehicleName("cascadia", "tiger", "00019", "3AKJGLD59LS000019"),
        VehicleName("cascadia", "urial", "00020", "3AKJGLD55LS000020"),
        VehicleName("cascadia", "vulture", "00021", "3AKJGLD57LS000021"),
        VehicleName("cascadia", "wolf", "00022", "3AKJGLD59LS000022"),
        VehicleName("cascadia", "xerus", "00023", "3AKJGLD50LS000023"),
        VehicleName("cascadia", "yak", "00024", "3AKJGLD52LS000024"),
        VehicleName("cascadia", "zebra", "00025", "3AKJGLD54LS000025"),
    ]


def random_bag_names_sequence(
    min_record_dt: datetime.datetime,
    max_record_dt: datetime.datetime,
    min_sequence_length: int,
    max_sequence_length: int,
) -> Generator[BagName, None, None]:
    vehicle_name = randomizer().choose(known_vehicle_names())
    record_dt = randomizer().random_datetime(begin=min_record_dt, end=max_record_dt)
    bags_count = randomizer().next_int(min_sequence_length, max_sequence_length)

    for record_sn in range(bags_count):
        yield BagName(vehicle_name=vehicle_name, record_dt=record_dt, record_sn=record_sn)
