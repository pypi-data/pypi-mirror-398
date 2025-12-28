import sys
from logging import INFO, makeLogRecord
from unittest.mock import Mock

from ttutils.logging import ColourizedFormatter, colourize_text


def test_colourize_text_ok():
    assert '31m' in colourize_text('text', 'red')
    assert '32m' in colourize_text('text', 'green')
    assert '33m' in colourize_text('text', 'yellow')
    assert '34m' in colourize_text('text', 'blue')
    assert '35m' in colourize_text('text', 'magenta')
    assert '36m' in colourize_text('text', 'cyan')


def test_ColourizedFormatter_init_ok_use_colors(monkeypatch):
    monkeypatch.setattr(sys.stdout, 'isatty', Mock(return_value=True))
    formatter = ColourizedFormatter()
    assert formatter.use_colors


def test_ColourizedFormatter_init_ok_not_use_colors(monkeypatch):
    monkeypatch.setattr(sys.stdout, 'isatty', Mock(return_value=False))
    formatter = ColourizedFormatter()
    assert not formatter.use_colors


def test_ColourizedFormatter_formatMessage_ok(monkeypatch):
    monkeypatch.setattr(sys.stdout, 'isatty', Mock(return_value=True))
    formatter = ColourizedFormatter('%(levelprefix)s %(message)s')
    record = makeLogRecord({'message': 'text', 'levelno': INFO, 'levelname': 'INFO'})
    assert formatter.formatMessage(record) == '\x1b[32mINFO\x1b[0m:     text'


def test_ColourizedFormatter_formatMessage_ok_not_use_color(monkeypatch):
    monkeypatch.setattr(sys.stdout, 'isatty', Mock(return_value=False))
    formatter = ColourizedFormatter('%(levelprefix)s %(message)s')
    record = makeLogRecord({'message': 'text', 'levelno': INFO, 'levelname': 'INFO'})
    assert formatter.formatMessage(record) == 'INFO:     text'


def test_ColourizedFormatter_formatMessage_ok_unknown_log_level(monkeypatch):
    monkeypatch.setattr(sys.stdout, 'isatty', Mock(return_value=True))
    formatter = ColourizedFormatter('%(levelprefix)s %(message)s')
    record = makeLogRecord({'message': 'text', 'levelno': 6, 'levelname': 'TRACE'})
    assert formatter.formatMessage(record) == 'TRACE:    text'
