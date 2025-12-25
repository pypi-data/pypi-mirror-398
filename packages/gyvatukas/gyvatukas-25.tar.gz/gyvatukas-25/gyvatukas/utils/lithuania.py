import re
from gyvatukas.utils.string_ import str_remove_except
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Literal


class LtIdValidationError(Exception):
    """Base exception for Lithuanian ID validation errors."""

    pass


class InvalidFormatError(LtIdValidationError):
    """Invalid format of the ID (length, digits, etc.)"""

    pass


class InvalidGenderNumberError(LtIdValidationError):
    """Invalid gender number in the ID."""

    pass


class InvalidBirthDateError(LtIdValidationError):
    """Invalid birth date in the ID."""

    pass


class InvalidChecksumError(LtIdValidationError):
    """Invalid checksum in the ID."""

    pass


class InvalidIdentifierError(LtIdValidationError):
    """Invalid identifier number in the ID."""

    pass


class FutureBirthDateError(LtIdValidationError):
    """Birth date is in the future."""

    pass


class GenderNumber(Enum):
    """Enumeration of possible gender numbers and their meaning."""

    MALE_1800 = 1
    FEMALE_1800 = 2
    MALE_1900 = 3
    FEMALE_1900 = 4
    MALE_2000 = 5
    FEMALE_2000 = 6
    SPECIAL_CASE = 9


@dataclass
class LithuanianPersonalCode:
    gender: Literal["male", "female"] | None
    birth_year: int
    birth_month: int | None
    birth_day: int | None
    identifier_number: str
    is_edge_case: bool
    checksum: int | None = None

    @property
    def birth_date(self) -> date | None:
        """Return birthdate as dt object if is not an edge case (has no 0 in month/day)."""
        if not self.is_edge_case:
            return date(self.birth_year, self.birth_month, self.birth_day)  # type: ignore
        return None


def calculate_lt_id_checksum(pid: str) -> int:
    """Calculate Lithuanian personal identification code checksum."""
    weights_a = [1, 2, 3, 4, 5, 6, 7, 8, 9, 1]
    weights_b = [3, 4, 5, 6, 7, 8, 9, 1, 2, 3]

    checksum_a = sum([int(pid[i]) * weights_a[i] for i in range(10)])
    checksum_a = checksum_a % 11
    if checksum_a != 10:
        return checksum_a

    checksum_b = sum([int(pid[i]) * weights_b[i] for i in range(10)])
    checksum_b = checksum_b % 11
    if checksum_b != 10:
        return checksum_b

    return 0


def validate_format(pid: str) -> None:
    """Validate basic format of the ID."""
    if len(pid) != 11:
        raise InvalidFormatError(
            f"PID must be exactly 11 digits long, got {len(pid)} digits"
        )
    if not pid.isdigit():
        raise InvalidFormatError("PID must contain only digits")


def validate_gender_number(number: int) -> tuple[str | None, int]:
    """Validate gender number and return gender and birth year base."""
    try:
        gender_num = GenderNumber(number)
    except ValueError:
        raise InvalidGenderNumberError(
            f"Invalid first number {number}, must be one of {[g.value for g in GenderNumber]}"
        )

    gender_map = {
        GenderNumber.MALE_1800: ("male", 1800),
        GenderNumber.MALE_1900: ("male", 1900),
        GenderNumber.MALE_2000: ("male", 2000),
        GenderNumber.FEMALE_1800: ("female", 1800),
        GenderNumber.FEMALE_1900: ("female", 1900),
        GenderNumber.FEMALE_2000: ("female", 2000),
        GenderNumber.SPECIAL_CASE: (None, 1900),
    }

    return gender_map[gender_num]


def validate_identifier(identifier: str) -> None:
    """Validate the identifier number portion."""
    if len(identifier) != 3:
        raise InvalidIdentifierError("Identifier number must be exactly 3 digits")

    identifier_num = int(identifier)
    if identifier_num == 0:
        raise InvalidIdentifierError("Identifier number cannot be 000")


def validate_birth_date(
    year: int, month: int | None, day: int | None, is_edge_case: bool
) -> None:
    """Validate birth date."""
    if is_edge_case:
        return

    try:
        birth_date = date(year, month, day)  # type: ignore
    except ValueError as e:
        raise InvalidBirthDateError(f"Invalid birth date: {e}")

    if birth_date > date.today():
        raise FutureBirthDateError(f"Birth date {birth_date} is in the future")


def validate_lt_id(pid: str) -> LithuanianPersonalCode:
    """Validate Lithuanian personal identification code."""
    is_edge_case = False

    # 1. Basic format validation first
    validate_format(pid)

    # Parse components
    gender_number = int(pid[0])
    birth_year = int(pid[1:3])
    birth_month = int(pid[3:5])
    birth_day = int(pid[5:7])
    identifier_number = pid[7:10]
    control_number = int(pid[10])

    # 2. Gender validation
    gender, birth_base = validate_gender_number(gender_number)
    if gender is None:
        is_edge_case = True

    # Handle edge cases
    if birth_month == 0:
        is_edge_case = True
        birth_month = None
    if birth_day == 0:
        is_edge_case = True
        birth_day = None

    # Calculate full birth year
    birth_year = birth_base + birth_year

    # 3. Birth date validation (including future dates)
    validate_birth_date(birth_year, birth_month, birth_day, is_edge_case)

    # 4. Identifier validation
    validate_identifier(identifier_number)

    # 5. Checksum validation last (for non-edge cases)
    if not is_edge_case:
        calculated_checksum = calculate_lt_id_checksum(pid)
        if calculated_checksum != control_number:
            raise InvalidChecksumError(
                f"Invalid checksum! Expected {calculated_checksum}, got {control_number}"
            )

    return LithuanianPersonalCode(
        gender=gender,
        birth_year=birth_year,
        birth_month=birth_month,
        birth_day=birth_day,
        identifier_number=identifier_number,
        is_edge_case=is_edge_case,
        checksum=control_number if not is_edge_case else None,
    )


def validate_lt_tel_nr(tel_nr: str, format_370: bool = True) -> tuple[bool, str]:
    """Validate Lithuanian phone number. Return if is valid and formatted number.

    Lithuanian number may start with +370, 8 or 0, followed by 8 digits.

    🚨 Does not check if it exists lol.
    ❗ Does not validate short numbers like 112, 1848, etc.
    """
    is_valid = False
    # Remove all symbols except + and 0-9
    clean_tel_nr = str_remove_except(
        tel_nr, ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "+"]
    )

    # Check if valid
    regex = r"^(?:\+370|8|0)\d{8}$"
    if re.match(regex, clean_tel_nr):
        is_valid = True
        # If starts with 0 or 8, make it +370
        if format_370 and (
            clean_tel_nr.startswith("8") or clean_tel_nr.startswith("0")
        ):
            clean_tel_nr = f"+370{clean_tel_nr[1:]}"

    return is_valid, clean_tel_nr if is_valid else tel_nr


def get_clean_tel_nr(tel_nr: str) -> str | None:
    """Return mobile phone number with +370 prefix. Return None if invalid."""
    is_valid, clean_tel_nr = validate_lt_tel_nr(tel_nr=tel_nr, format_370=True)
    if not is_valid:
        return None
    return clean_tel_nr
