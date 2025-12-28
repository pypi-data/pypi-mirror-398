import base64
import html
import random


def random_code32(length: int = 6) -> str:
    ''' Генератор случайных кодов '''
    return str(base64.b32encode(random.randbytes(length))[:length], 'utf8')


random_code = random_code32


def random_code64(length: int = 6) -> str:
    ''' Генератор случайных кодов '''
    result = str(base64.b64encode(random.randbytes(2 * length)), 'utf8')
    return result.replace('/', '.').replace('+', '-')[:length]


def text_crop(text: str, length: int, postfix: str = ' …') -> str:
    ''' Crop text '''
    if len(text) > length:
        return text[:length - len(postfix)] + postfix

    return text


def safe_text(text: str) -> str:
    ''' Escape tags from text '''
    return html.escape(text, True).replace('\xa0', ' ') if text else text
