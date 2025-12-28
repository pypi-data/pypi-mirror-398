import logging
import sys
from copy import copy
from typing import Literal

LOG_COLLORS = {
    '': '\x1b[0m',  # сброс цвета
    'red': '\x1b[31m',
    'green': '\x1b[32m',
    'yellow': '\x1b[33m',
    'blue': '\x1b[34m',
    'magenta': '\x1b[35m',
    'cyan': '\x1b[36m',
}

LOG_LEVEL_COLLORS: dict[int, str] = {
    logging.DEBUG: 'blue',
    logging.INFO: 'green',
    logging.WARNING: 'yellow',
    logging.ERROR: 'red',
    logging.CRITICAL: 'magenta',
}


def colourize_text(text: str, color: str) -> str:
    return f'{LOG_COLLORS[color]}{text}{LOG_COLLORS[""]}'


class ColourizedFormatter(logging.Formatter):
    '''
        Collored log level (if supported by the system)

        Example:

        'formatters': {
            'default': {
                '()': 'ttutils.logging.ColourizedFormatter',
                'fmt': '%(levelprefix)s %(asctime)s %(name)s %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        }
    '''
    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal['%', '{', '$'] = '%',
    ) -> None:
        self.use_colors = sys.stdout.isatty()
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def formatMessage(self, record: logging.LogRecord) -> str:  # noqa
        recordcopy = copy(record)
        separator = ' ' * (8 - len(record.levelname))
        levelname = record.levelname

        if self.use_colors and (color := LOG_LEVEL_COLLORS.get(record.levelno)):
            levelname = colourize_text(levelname, color)

        recordcopy.__dict__['levelprefix'] = levelname + ':' + separator

        return super().formatMessage(recordcopy)
