from datetime import date, datetime, time, timedelta

import pytest

from validators import (
    validate_age,
    validate_availability,
    validate_cancellation,
    validate_confirm_password,
    validate_date,
    validate_doctor_id,
    validate_email,
    validate_name,
    validate_password,
    validate_phone,
    validate_time,
)


@pytest.mark.parametrize(
    "value",
    ["Juan Perez", "Ana", " Maria Lopez "],
)
def test_validate_name_valid(value):
    assert validate_name(value)


@pytest.mark.parametrize(
    "value",
    ["", "A", "Juan1", "Juan@", "J" * 51],
)
def test_validate_name_invalid(value):
    with pytest.raises(ValueError):
        validate_name(value)


@pytest.mark.parametrize(
    "value",
    ["test@example.com", "user.name@dominio.co"],
)
def test_validate_email_valid(value):
    assert validate_email(value) == value.lower()


@pytest.mark.parametrize(
    "value",
    ["testexample.com", "test@domain", "test@domain.", "test@.com"],
)
def test_validate_email_invalid(value):
    with pytest.raises(ValueError):
        validate_email(value)


def test_validate_email_length_limits():
    local = "a" * (100 - len("@example.com"))
    email = f"{local}@example.com"
    assert len(email) == 100
    assert validate_email(email) == email

    too_long = f"{local}b@example.com"
    with pytest.raises(ValueError):
        validate_email(too_long)


@pytest.mark.parametrize(
    "value,expected",
    [("18", 18), ("100", 100), ("19", 19)],
)
def test_validate_age_valid(value, expected):
    assert validate_age(value) == expected


@pytest.mark.parametrize(
    "value",
    ["17", "101", "18.5", "abc", ""],
)
def test_validate_age_invalid(value):
    with pytest.raises(ValueError):
        validate_age(value)


@pytest.mark.parametrize(
    "value",
    ["123456789", "123456789012345"],
)
def test_validate_phone_valid(value):
    assert validate_phone(value) == value


@pytest.mark.parametrize(
    "value",
    ["12345678", "1234567890123456", "123-456-789", "phone"],
)
def test_validate_phone_invalid(value):
    with pytest.raises(ValueError):
        validate_phone(value)


def test_validate_password_valid():
    assert validate_password("Test123!") == "Test123!"


@pytest.mark.parametrize(
    "value",
    ["short1!", "nouppercase1!", "NOLOWERCASE1!", "NoDigit!!", "NoSpecial1"],
)
def test_validate_password_invalid(value):
    with pytest.raises(ValueError):
        validate_password(value)


def test_validate_confirm_password():
    validate_confirm_password("Test123!", "Test123!")
    with pytest.raises(ValueError):
        validate_confirm_password("Test123!", "Test123")


def test_validate_doctor_id():
    valid_ids = {1, 2}
    assert validate_doctor_id("1", valid_ids) == 1
    with pytest.raises(ValueError):
        validate_doctor_id("3", valid_ids)
    with pytest.raises(ValueError):
        validate_doctor_id("abc", valid_ids)


def test_validate_date_limits():
    today = date(2026, 5, 18)
    valid_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    assert validate_date(valid_date, today=today)

    for offset in (-1, 0):
        with pytest.raises(ValueError):
            validate_date((today + timedelta(days=offset)).strftime("%Y-%m-%d"), today=today)

    saturday = today + timedelta(days=5)
    sunday = today + timedelta(days=6)
    with pytest.raises(ValueError):
        validate_date(saturday.strftime("%Y-%m-%d"), today=today)
    with pytest.raises(ValueError):
        validate_date(sunday.strftime("%Y-%m-%d"), today=today)


@pytest.mark.parametrize(
    "value,is_valid",
    [
        ("08:59", False),
        ("09:00", True),
        ("09:01", False),
        ("09:30", True),
        ("16:30", True),
        ("16:59", False),
        ("17:00", False),
        ("17:01", False),
    ],
)
def test_validate_time_blocks(value, is_valid):
    start = time(9, 0)
    end = time(17, 0)
    if is_valid:
        assert validate_time(value, start, end, 30)
    else:
        with pytest.raises(ValueError):
            validate_time(value, start, end, 30)


def test_validate_availability():
    validate_availability(False)
    with pytest.raises(ValueError):
        validate_availability(True)


def test_validate_cancellation_limits():
    now = datetime(2026, 5, 18, 12, 0, 0)
    validate_cancellation(now + timedelta(hours=2), now)
    with pytest.raises(ValueError):
        validate_cancellation(now + timedelta(hours=1, minutes=59), now)
    with pytest.raises(ValueError):
        validate_cancellation(now - timedelta(minutes=1), now)
