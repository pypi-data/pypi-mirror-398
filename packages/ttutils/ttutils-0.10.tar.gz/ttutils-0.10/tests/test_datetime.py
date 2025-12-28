from datetime import date, datetime, timezone

import pytest

from ttutils.datetime import (isoformat, parsedt, parsedt_ms, parsedt_sec,
                              try_isoformat, try_parsedt, utcnow, utcnow_ms,
                              utcnow_sec)


def test_utcnow_ok():
    result = utcnow()

    assert isinstance(result, datetime)
    assert result.tzinfo is timezone.utc


def test_utcnow_ms_ok():
    result = utcnow_ms()

    assert isinstance(result, datetime)
    assert result.microsecond % 1_000 == 0


def test_utcnow_sec_ok():
    result = utcnow_sec()

    assert isinstance(result, datetime)
    assert result.microsecond == 0


@pytest.mark.parametrize('param, expected_isoformat', [
    ('2022-01-23T11:22:33.123456', '2022-01-23T11:22:33.123456+00:00'),
    ('2022-01-23T11:22:33.123456Z', '2022-01-23T11:22:33.123456+00:00'),
    ('2022-01-23T11:22:33.123456+00:00', '2022-01-23T11:22:33.123456+00:00'),
    ('2022-01-23T11:22:33.123456+05:00', '2022-01-23T06:22:33.123456+00:00'),
])
def test_parsedt_ok_complex(param, expected_isoformat):
    expected_dt = datetime.fromisoformat(expected_isoformat)
    result = parsedt(param)

    assert isinstance(result, datetime)
    assert result == expected_dt


def test_parsedt_ms_ok():
    result = parsedt_ms('2022-01-23T11:22:33.123456Z')
    expected = datetime.fromisoformat('2022-01-23T11:22:33.123000+00:00')

    assert isinstance(result, datetime)
    assert result == expected


def test_parsedt_sec_ok():
    result = parsedt_sec('2022-01-23T11:22:33.123456Z')
    expected = datetime.fromisoformat('2022-01-23T11:22:33+00:00')

    assert isinstance(result, datetime)
    assert result == expected


def test_try_parsedt_ok_complex():
    dt = utcnow()

    assert try_parsedt(dt.isoformat()) == dt
    assert try_parsedt('2022-01-23T99:22:33.123456Z') is None
    assert try_parsedt(None) is None
    assert try_parsedt(123) is None
    assert try_parsedt(dt) is None


@pytest.mark.parametrize('param, expected', [
    (datetime.fromisoformat('2022-01-23T11:22:33.123456'), '2022-01-23T11:22:33.123456Z'),
    (datetime.fromisoformat('2022-01-23T11:22:33.123456+00:00'), '2022-01-23T11:22:33.123456Z'),
    (datetime.fromisoformat('2022-01-23T11:22:33.123456+05:00'), '2022-01-23T06:22:33.123456Z'),
    (date.fromisoformat('2022-01-23'), '2022-01-23T00:00:00Z'),
])
def test_isoformat_ok_complex(param, expected):
    assert isoformat(param) == expected


@pytest.mark.parametrize('param, expected', [
    (None, None),
    (0, None),
    ('', None),
    ([], None),
    (date.fromisoformat('2022-01-23'), '2022-01-23T00:00:00Z'),
    (datetime.fromisoformat('2022-01-23T11:22:33.123456'), '2022-01-23T11:22:33.123456Z'),
    ('2022-01-23T11:22:33.123456', '2022-01-23T11:22:33.123456'),
    ('datetime', 'datetime'),
    (b'2022-01-23T11:22:33.123456', '2022-01-23T11:22:33.123456'),
    (..., None),
])
def test_try_isoformat_ok_complex(param, expected):
    assert try_isoformat(param) == expected
