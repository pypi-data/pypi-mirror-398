import dataclasses
import datetime
import re
from collections.abc import Callable

import pyparsing as pp
from iker.common.utils.dtutils import basic_format, dt_format, dt_parse
from iker.common.utils.funcutils import singleton

__all__ = [
    "hex_string_pattern",
    "hex_string_parser",
    "snake_case_pattern",
    "snake_case_parser",
    "kebab_case_pattern",
    "kebab_case_parser",
    "dot_case_pattern",
    "dot_case_parser",
    "uuid_pattern",
    "uuid_parser",
    "strict_relpath_pattern",
    "strict_relpath_parser",
    "strict_abspath_pattern",
    "strict_abspath_parser",
    "strict_archive_relpath_pattern",
    "strict_archive_relpath_parser",
    "strict_archive_abspath_pattern",
    "strict_archive_abspath_parser",
    "email_address_pattern",
    "email_address_parser",
    "semver_pattern",
    "semver_parser",
    "colon_tag_pattern",
    "colon_tag_parser",
    "slash_tag_pattern",
    "slash_tag_parser",
    "topic_pattern",
    "topic_parser",
    "vin_code_chars",
    "vin_code_pattern",
    "vin_code_parser",
    "to_colon_tag",
    "to_slash_tag",
    "UserName",
    "UserEmail",
    "VehicleName",
    "BagName",
    "parse_user_name",
    "parse_user_email",
    "parse_vehicle_name",
    "parse_bag_name",
]


def token_check(cond: Callable[[str], bool]) -> Callable[[pp.ParseResults], bool]:
    def cond_func(results: pp.ParseResults) -> bool:
        token, *_ = results
        return cond(token)

    return cond_func


def token_reparse(elem: pp.ParserElement, negate: bool = False) -> Callable[[pp.ParseResults], bool]:
    def cond_func(results: pp.ParseResults) -> bool:
        token, *_ = results
        try:
            elem.parse_string(token, parse_all=True)
            return not negate
        except pp.ParseException:
            return negate

    return cond_func


def make_string_pattern(pattern: re.Pattern[str]) -> re.Pattern[str]:
    return re.compile(rf"^{pattern.pattern}$")


def make_string_parser(element: pp.ParserElement) -> pp.ParserElement:
    return pp.Combine(pp.StringStart() + element + pp.StringEnd())


underscore_token: pp.ParserElement = pp.Char("_")
hyphen_token: pp.ParserElement = pp.Char("-")
period_token: pp.ParserElement = pp.Char(".")
colon_token: pp.ParserElement = pp.Char(":")
slash_token: pp.ParserElement = pp.Char("/")
plus_token: pp.ParserElement = pp.Char("+")
sharp_token: pp.ParserElement = pp.Char("#")

lower_regexp: re.Pattern[str] = re.compile(r"[a-z]")
upper_regexp: re.Pattern[str] = re.compile(r"[A-Z]")
digit_regexp: re.Pattern[str] = re.compile(r"[0-9]")
lower_digit_regexp: re.Pattern[str] = re.compile(r"[a-z0-9]")
upper_digit_regexp: re.Pattern[str] = re.compile(r"[A-Z0-9]")
alpha_digit_regexp: re.Pattern[str] = re.compile(r"[a-zA-Z0-9]")
hex_digit_regexp: re.Pattern[str] = re.compile(r"[a-f0-9]")

lowers_regexp: re.Pattern[str] = re.compile(rf"{lower_regexp.pattern}+")
uppers_regexp: re.Pattern[str] = re.compile(rf"{upper_regexp.pattern}+")
digits_regexp: re.Pattern[str] = re.compile(rf"{digit_regexp.pattern}+")
lower_digits_regexp: re.Pattern[str] = re.compile(rf"{lower_digit_regexp.pattern}+")
upper_digits_regexp: re.Pattern[str] = re.compile(rf"{upper_digit_regexp.pattern}+")
alpha_digits_regexp: re.Pattern[str] = re.compile(rf"{alpha_digit_regexp.pattern}+")
hex_digits_regexp: re.Pattern[str] = re.compile(rf"{hex_digit_regexp.pattern}+")
lower_identifier_regexp: re.Pattern[str] = re.compile(rf"{lower_regexp.pattern}{lower_digit_regexp.pattern}*")
upper_identifier_regexp: re.Pattern[str] = re.compile(rf"{upper_regexp.pattern}{upper_digit_regexp.pattern}*")
strict_chars_regexp: re.Pattern[str] = re.compile(rf"({alpha_digit_regexp.pattern}|[._-])+")

lower_element: pp.ParserElement = pp.Regex(lower_regexp.pattern)
upper_element: pp.ParserElement = pp.Regex(upper_regexp.pattern)
digit_element: pp.ParserElement = pp.Regex(digit_regexp.pattern)
lower_digit_element: pp.ParserElement = pp.Regex(lower_digit_regexp.pattern)
upper_digit_element: pp.ParserElement = pp.Regex(upper_digit_regexp.pattern)
alpha_digit_element: pp.ParserElement = pp.Regex(alpha_digit_regexp.pattern)
hex_digit_element: pp.ParserElement = pp.Regex(hex_digit_regexp.pattern)

lowers_element: pp.ParserElement = pp.Regex(lowers_regexp.pattern)
uppers_element: pp.ParserElement = pp.Regex(uppers_regexp.pattern)
digits_element: pp.ParserElement = pp.Regex(digits_regexp.pattern)
lower_digits_element: pp.ParserElement = pp.Regex(lower_digits_regexp.pattern)
upper_digits_element: pp.ParserElement = pp.Regex(upper_digits_regexp.pattern)
alpha_digits_element: pp.ParserElement = pp.Regex(alpha_digits_regexp.pattern)
hex_digits_element: pp.ParserElement = pp.Regex(hex_digits_regexp.pattern)
lower_identifier_element: pp.ParserElement = pp.Regex(lower_identifier_regexp.pattern)
upper_identifier_element: pp.ParserElement = pp.Regex(upper_identifier_regexp.pattern)
strict_chars_element: pp.ParserElement = pp.Regex(strict_chars_regexp.pattern)

basic_datetime_regexp: re.Pattern[str] = re.compile(r"\d{8}T\d{6}")
extended_datetime_regexp: re.Pattern[str] = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

basic_datetime_element: pp.ParserElement = pp.Regex(basic_datetime_regexp.pattern)
extended_datetime_element: pp.ParserElement = pp.Regex(extended_datetime_regexp.pattern)

positive_number_regexp: re.Pattern[str] = re.compile(rf"[1-9]{digit_regexp.pattern}*")
number_regexp: re.Pattern[str] = re.compile(rf"0|({positive_number_regexp.pattern})")

positive_number_element: pp.ParserElement = pp.Regex(positive_number_regexp.pattern)
number_element: pp.ParserElement = pp.Regex(number_regexp.pattern)

snake_case_regexp: re.Pattern[str] = re.compile(
    rf"{lower_digits_regexp.pattern}(?:_{lower_digits_regexp.pattern})*")
kebab_case_regexp: re.Pattern[str] = re.compile(
    rf"{lower_digits_regexp.pattern}(?:-{lower_digits_regexp.pattern})*")
dot_case_regexp: re.Pattern[str] = re.compile(
    rf"{lower_digits_regexp.pattern}(?:\.{lower_digits_regexp.pattern})*")

snake_case_element: pp.ParserElement = pp.Combine(
    lower_digits_element + (underscore_token + lower_digits_element)[...])
kebab_case_element: pp.ParserElement = pp.Combine(
    lower_digits_element + (hyphen_token + lower_digits_element)[...])
dot_case_element: pp.ParserElement = pp.Combine(
    lower_digits_element + (period_token + lower_digits_element)[...])

uuid_regexp: re.Pattern[str] = re.compile(
    rf"{hex_digit_regexp.pattern}{{8}}(-{hex_digit_regexp.pattern}{{4}}){{3}}-{hex_digit_regexp.pattern}{{12}}")
uuid_element: pp.ParserElement = pp.Regex(uuid_regexp.pattern)

strict_relpath_regexp: re.Pattern[str] = re.compile(
    rf"(?!.*(^|/)\.+($|/))(?:{strict_chars_regexp.pattern}/)*(?:{strict_chars_regexp.pattern})?")
strict_abspath_regexp: re.Pattern[str] = re.compile(
    rf"(?!.*(^|/)\.+($|/))/(?:{strict_chars_regexp.pattern}/)*(?:{strict_chars_regexp.pattern})?")
strict_archive_relpath_regexp: re.Pattern[str] = re.compile(
    rf"(?!.*(^|/)\.+($|/))(?:{strict_chars_regexp.pattern}/)*({strict_chars_regexp.pattern})(?:#({strict_relpath_regexp.pattern}))?")
strict_archive_abspath_regexp: re.Pattern[str] = re.compile(
    rf"(?!.*(^|/)\.+($|/))/(?:{strict_chars_regexp.pattern}/)*({strict_chars_regexp.pattern})(?:#({strict_relpath_regexp.pattern}))?")

strict_path_chars_element = strict_chars_element.copy()
strict_path_chars_element.add_condition(token_reparse(period_token[1, ...], negate=True),
                                        message="cannot be pure dots")

strict_relpath_element: pp.ParserElement = pp.Combine(
    (strict_path_chars_element + slash_token)[...] + strict_path_chars_element[0, 1])
strict_abspath_element: pp.ParserElement = pp.Combine(
    slash_token + (strict_path_chars_element + slash_token)[...] + strict_path_chars_element[0, 1])
strict_archive_relpath_element: pp.ParserElement = pp.Combine(
    (strict_path_chars_element + slash_token)[...] + strict_path_chars_element +
    (sharp_token + strict_relpath_element)[0, 1])
strict_archive_abspath_element: pp.ParserElement = pp.Combine(
    slash_token + (strict_path_chars_element + slash_token)[...] + strict_path_chars_element +
    (sharp_token + strict_relpath_element)[0, 1])

email_address_regexp: re.Pattern[str] = re.compile(
    rf"(({lower_digit_regexp.pattern}|[_-])+)(?:\.({lower_digit_regexp.pattern}|[_-])+)*@(?:{kebab_case_regexp.pattern}\.)+({lower_digit_regexp.pattern}{{2,63}})")
email_address_element: pp.ParserElement = pp.Regex(email_address_regexp.pattern)

semver_regexp: re.Pattern[str] = re.compile(
    rf"({number_regexp.pattern})\.({number_regexp.pattern})\.({number_regexp.pattern})"
    rf"(?:-{alpha_digits_regexp.pattern}(?:\.{alpha_digits_regexp.pattern})*)?"
    rf"(?:\+{alpha_digits_regexp.pattern}(?:\.{alpha_digits_regexp.pattern})*)?")
semver_element: pp.ParserElement = pp.Regex(semver_regexp.pattern)

colon_tag_regexp: re.Pattern[str] = re.compile(rf"{snake_case_regexp.pattern}(?::{snake_case_regexp.pattern})*")
colon_tag_element: pp.ParserElement = pp.Combine(snake_case_element + (colon_token + snake_case_element)[...])

slash_tag_regexp: re.Pattern[str] = re.compile(rf"{snake_case_regexp.pattern}(?:/{snake_case_regexp.pattern})*")
slash_tag_element: pp.ParserElement = pp.Combine(snake_case_element + (slash_token + snake_case_element)[...])

topic_regexp: re.Pattern[str] = re.compile(rf"(?:/{snake_case_regexp.pattern})+")
topic_element: pp.ParserElement = pp.Combine((slash_token + snake_case_element)[1, ...])

vin_code_chars: str = "0123456789ABCDEFGHJKLMNPRSTUVWXYZ"

vin_code_regexp: re.Pattern[str] = re.compile(rf"[{vin_code_chars}]{{17}}")
vin_code_element: pp.ParserElement = pp.Regex(vin_code_regexp.pattern)

hex_string_pattern = make_string_pattern(hex_digits_regexp)
hex_string_parser = make_string_parser(hex_digits_element)

snake_case_pattern = make_string_pattern(snake_case_regexp)
snake_case_parser = make_string_parser(snake_case_element)
kebab_case_pattern = make_string_pattern(kebab_case_regexp)
kebab_case_parser = make_string_parser(kebab_case_element)
dot_case_pattern = make_string_pattern(dot_case_regexp)
dot_case_parser = make_string_parser(dot_case_element)

uuid_pattern = make_string_pattern(uuid_regexp)
uuid_parser = make_string_parser(uuid_element)

strict_relpath_pattern = make_string_pattern(strict_relpath_regexp)
strict_relpath_parser = make_string_parser(strict_relpath_element)
strict_abspath_pattern = make_string_pattern(strict_abspath_regexp)
strict_abspath_parser = make_string_parser(strict_abspath_element)
strict_archive_relpath_pattern = make_string_pattern(strict_archive_relpath_regexp)
strict_archive_relpath_parser = make_string_parser(strict_archive_relpath_element)
strict_archive_abspath_pattern = make_string_pattern(strict_archive_abspath_regexp)
strict_archive_abspath_parser = make_string_parser(strict_archive_abspath_element)

email_address_pattern = make_string_pattern(email_address_regexp)
email_address_parser = make_string_parser(email_address_element)

semver_pattern = make_string_pattern(semver_regexp)
semver_parser = make_string_parser(semver_element)

colon_tag_pattern = make_string_pattern(colon_tag_regexp)
colon_tag_parser = make_string_parser(colon_tag_element)
slash_tag_pattern = make_string_pattern(slash_tag_regexp)
slash_tag_parser = make_string_parser(slash_tag_element)
topic_pattern = make_string_pattern(topic_regexp)
topic_parser = make_string_parser(topic_element)
vin_code_pattern = make_string_pattern(vin_code_regexp)
vin_code_parser = make_string_parser(vin_code_element)


def to_colon_tag(tag: str) -> str:
    return tag.replace("/", ":")


def to_slash_tag(tag: str) -> str:
    return tag.replace(":", "/")


@dataclasses.dataclass(frozen=True, eq=True)
class UserName(object):
    first_name: str
    last_name: str
    sn: int = 0

    def __str__(self) -> str:
        if self.sn == 0:
            return f"{self.first_name}.{self.last_name}"
        return f"{self.first_name}{self.sn}.{self.last_name}"


@dataclasses.dataclass(frozen=True, eq=True)
class UserEmail(object):
    user_name: UserName
    domain: str

    def __str__(self) -> str:
        return f"{str(self.user_name)}@{self.domain}"


@dataclasses.dataclass(frozen=True, eq=True)
class VehicleName(object):
    brand: str
    alias: str
    code: str | None = None
    vin: str | None = None

    def __str__(self) -> str:
        if self.code and self.vin:
            return f"{self.brand}_{self.alias}_{self.code}_V{self.vin}"
        if self.code:
            return f"{self.brand}_{self.alias}_{self.code}"
        if self.vin:
            return f"{self.brand}_{self.alias}_V{self.vin}"
        return f"{self.brand}_{self.alias}"


@dataclasses.dataclass(frozen=True, eq=True)
class BagName(object):
    vehicle_name: VehicleName
    record_dt: datetime.datetime
    record_sn: int

    def __str__(self) -> str:
        return f"{dt_format(self.record_dt, basic_format())}-{self.vehicle_name}-{self.record_sn}.bag"


@singleton
def get_user_name_element() -> pp.ParserElement:
    return pp.Combine(lowers_element("first_name") +
                      positive_number_element("sn")[0, 1] +
                      period_token +
                      lowers_element("last_name"))


@singleton
def get_user_name_parser() -> pp.ParserElement:
    return make_string_parser(get_user_name_element())


@singleton
def get_user_email_element() -> pp.ParserElement:
    return pp.Combine(get_user_name_element()("user_name") +
                      pp.Char("@") +
                      pp.Combine((kebab_case_element + period_token)[1, ...] + lowers_element)("domain"))


@singleton
def get_user_email_parser() -> pp.ParserElement:
    return make_string_parser(get_user_email_element())


@singleton
def get_vehicle_name_element() -> pp.ParserElement:
    return pp.Combine(lower_identifier_element("brand") +
                      (underscore_token +
                       pp.Combine(lower_identifier_element +
                                  (underscore_token + lower_identifier_element)[...])("alias")) +
                      (underscore_token + digits_element("code"))[0, 1] +
                      (underscore_token + pp.Char("V") + vin_code_element("vin"))[0, 1])


@singleton
def get_vehicle_name_parser() -> pp.ParserElement:
    return make_string_parser(get_vehicle_name_element())


@singleton
def get_bag_name_element() -> pp.ParserElement:
    return pp.Combine(basic_datetime_element("record_dt") +
                      (hyphen_token +
                       get_vehicle_name_element()("vehicle_name")) +
                      (hyphen_token + number_element("record_sn")) +
                      (period_token + pp.Literal("bag"))[0, 1])


@singleton
def get_bag_name_parser() -> pp.ParserElement:
    return make_string_parser(get_bag_name_element())


def parse_user_name(s: str) -> UserName | None:
    user_name_match = get_user_name_parser().parse_string(s, parse_all=True)

    return UserName(
        user_name_match.get("first_name"),
        user_name_match.get("last_name"),
        int(user_name_match.get("sn", 0)),
    )


def parse_user_email(s: str) -> UserEmail | None:
    user_email_match = get_user_email_parser().parse_string(s, parse_all=True)

    return UserEmail(
        UserName(
            user_email_match.get("user_name").get("first_name"),
            user_email_match.get("user_name").get("last_name"),
            int(user_email_match.get("user_name").get("sn", 0)),
        ),
        user_email_match.get("domain"),
    )


def parse_vehicle_name(s: str) -> VehicleName | None:
    vehicle_name_match = get_vehicle_name_parser().parse_string(s, parse_all=True)

    return VehicleName(
        vehicle_name_match.get("brand"),
        vehicle_name_match.get("alias"),
        vehicle_name_match.get("code"),
        vehicle_name_match.get("vin"),
    )


def parse_bag_name(s: str) -> BagName | None:
    bag_name_match = get_bag_name_parser().parse_string(s, parse_all=True)

    return BagName(
        VehicleName(
            bag_name_match.get("vehicle_name").get("brand"),
            bag_name_match.get("vehicle_name").get("alias"),
            bag_name_match.get("vehicle_name").get("code"),
            bag_name_match.get("vehicle_name").get("vin"),
        ),
        dt_parse(bag_name_match.get("record_dt"), basic_format()),
        int(bag_name_match.get("record_sn")),
    )
