import re
import unicodedata
from functools import partial


def slugify(text: str) -> str:
    """
    Converts a given text to a slugified version, replacing spaces and special characters with a hyphen.

    Args:
        text (str): The text to slugify.

    Returns:
        str: The slugified version of the text.
    """
    return _transform(text, '-')


def to_camel_case(text: str, *, upper: bool = True) -> str:
    """
    Converts a given text to camel case.

    Args:
        text (str): The text to convert.
        upper (bool, optional): If True, the first letter of the result will be uppercase. Defaults to True.

    Returns:
        str: The camel case version of the text.
    """
    words = [word.capitalize() for word in _transform(text, '_').split('_')]

    if not upper and words:
        words[0] = words[0].lower()

    return ''.join(words)


classify = partial(to_camel_case, upper=True)


def to_snake_case(text: str) -> str:
    """
    Converts a given text to snake case.

    Args:
        text (str): The text to convert.

    Returns:
        str: The snake case version of the text.
    """
    return _transform(text, '_')


def _transform(text: str, separator: str) -> str:
    text = ' '.join(' '.join(_split_on_uppercase(text)).split('_'))
    value = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())

    return re.sub(r'[-\s]+', separator, value).strip('-_')


def _split_on_uppercase(text: str) -> list[str]:
    string_length = len(text)
    start = 0
    parts: list[str] = []

    def _is_lower_around(index: int) -> bool:
        return text[index - 1].islower() or (string_length > (index + 1) and text[index + 1].islower())

    for i in range(1, string_length):
        if text[i].isupper() and _is_lower_around(i):
            parts.append(text[start:i])
            start = i

    parts.append(text[start:])

    return parts
