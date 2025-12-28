from ttutils.safe_types import (as_bool, int_list, int_set, to_bytes,
                                to_string, try_float, try_int)


def test_try_int_ok():
    assert try_int('123') == 123
    assert try_int('asd') is None


def test_try_float_ok():
    assert try_float('123') == 123.0
    assert try_float('123.45') == 123.45
    assert try_float('asd') is None


def test_as_bool_ok():
    assert as_bool('t') is True
    assert as_bool(1) is True
    assert as_bool('false') is False


def test_to_string_ok():
    assert to_string(try_int)
    assert to_string('text') == 'text'
    assert to_string(b'text') == 'text'


def test_to_bytes_ok():
    assert to_bytes('textтекст') == b'text\xd1\x82\xd0\xb5\xd0\xba\xd1\x81\xd1\x82'
    assert to_bytes(b'text\xd1\x82') == b'text\xd1\x82'
    assert to_bytes(1234567890) == b'I\x96\x02\xd2'


def test_iter_ok():
    assert int_list(['1', '2', 'a', 'b', None]) == [1, 2]
    assert int_set(['1', '2', 'a', 'b', None]) == {1, 2}
