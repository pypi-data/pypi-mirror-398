import pytest

from ttutils.compress import (breaking_range, decode, decode_dict, decode_list,
                              encode, encode_dict, encode_list)


def test_encode_ok():
    assert encode(10) == 'a'
    assert encode(11232423) == 'GSiD'


def test_decode_ok():
    assert decode('a') == 10
    assert decode('GSi') == 175506


def test_encode_list_ok():
    assert encode_list([10, 15, 20]) == 'a-f-k'
    assert encode_list([10, 11, 12, 13, 14, 15, 20, 21, 23, 24, 25]) == 'a--f-k-l-n--p'
    assert encode_list([15, 20, 24, 25]) == 'f-k-o-p'
    assert encode_list([10, None, 15, 20]) == 'a--f-k'


def test_decode_list_ok():
    assert decode_list('A-Bc-Rf.') == [36, 2380, 218111]
    assert decode_list('A--F-Bc-Rf.') == [36, 37, 38, 39, 40, 41, 2380, 218111]
    assert decode_list('A--F-Bc-RfZ--Rf.') == [36, 37, 38, 39, 40, 41, 2380, 218109, 218110, 218111]
    assert decode_list('') == []


def test_decode_list_fail():
    with pytest.raises(ValueError):
        decode_list('1-2--QQQ')


def test_encode_dict_ok():
    assert encode_dict({12: [1, 2, 3, 4, 67], 234: [34, 76]}) == 'c-1--4-13/3G-y-1c'
    assert encode_dict({234: [34, 76]}) == '3G-y-1c'
    assert encode_dict({}) == ''  # noqa PLC1901


def test_decode_dict_ok():
    assert decode_dict('c-1--4-13/3G-y-1c') == {12: [1, 2, 3, 4, 67], 234: [34, 76]}
    assert decode_dict('3G-y-1c') == {234: [34, 76]}
    assert decode_dict('') == {}


def test_breaking_range_ok():
    assert list(breaking_range([1, 5, 10])) == [1, 5, 10]
    assert list(breaking_range([None, 1, 5, 10])) == [1, 5, 10]
    assert list(breaking_range([1, 5, 10, None])) == [1, 5, 10]
    assert list(breaking_range([1, 5, 10, None, None, None])) == [1, 5, 10]
    assert list(breaking_range([None, 1, 5, 10, None])) == [1, 5, 10]
    assert list(breaking_range([1, 5, None, 10])) == [1, 5, 6, 7, 8, 9, 10]
    assert list(breaking_range([1, 5, None, None, 10])) == [1, 5, 6, 7, 8, 9, 10]
    assert list(breaking_range([1, 5, None, None, None, None, 10])) == [1, 5, 6, 7, 8, 9, 10]
    assert list(breaking_range(list(range(10001)))) == list(range(10000))

    with pytest.raises(ValueError):
        assert list(breaking_range([1, None, 10002]))
