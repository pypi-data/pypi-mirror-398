from ttutils.helpers import (random_code, random_code32, random_code64,
                             safe_text, text_crop)


def test_safe_text_ok():
    assert safe_text('<b>text</b>') == '&lt;b&gt;text&lt;/b&gt;'
    assert safe_text('text') == 'text'


def test_text_crop_ok():
    assert text_crop('text', 5) == 'text'
    assert text_crop('sometext', 6) == 'some …'


def test_random_code_ok():
    assert len(random_code(6)) == 6
    assert isinstance(random_code(), str)


def test_random_code32_ok():
    assert len(random_code32(6)) == 6
    assert isinstance(random_code32(), str)


def test_random_code64_ok():
    assert len(random_code64(100)) == 100
    assert len(random_code64(1)) == 1
    assert isinstance(random_code64(), str)
