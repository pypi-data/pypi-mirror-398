from __future__ import annotations


__all__ = (
    'random_runner_tag',
    'check_message_text',
    'enforce_message_text_whitespaces',
)

import re
import random
import string

from funpaybotengine.exceptions import (
    TooManyLinesError,
    MessageTextTooLongError,
    MessageWordTooLongError,
)


def random_runner_tag() -> str:
    """
    Generate a random lowercase string tag used to identify the first request
    in a pagination sequence.
    """
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(8))


def check_message_text(message_text: str, /) -> None:
    """
    Checks if a message text meets FunPay rules:
        - Max message length: 2000 characters.
        - Max word length: 160 characters.
        - Max lines amount: 20.

    If it doesn't, raises an exception.

    :param message_text: message text to check.
    """
    max_message_len = 2000
    max_word_len = 160
    max_lines = 20

    message_text = message_text.strip()
    message_text = re.sub(' {2,}', ' ', message_text)
    message_text = re.sub('\n{2,}', '\n', message_text)

    if len(message_text) > max_message_len:
        raise MessageTextTooLongError(message_text=message_text)

    big_words = [i for i in message_text.split() if len(i) > max_word_len]
    if big_words:
        raise MessageWordTooLongError(message_text=message_text)

    if len(message_text.splitlines()) > max_lines:
        raise TooManyLinesError(message_text=message_text)


def enforce_message_text_whitespaces(
    message_text: str,
    /,
    enforce_spaces: bool = True,
    enforce_line_breaks: bool = True,
) -> str:
    """
    By default, FunPay trims the message text and replaces multiple consecutive spaces
    or line breaks with a single space or line break.

    This function preserves the exact number of spaces and line breaks by appending
    an invisible tag ``[a][/a]`` after each one (except the last), preventing FunPay
    from collapsing them.

    :param message_text: The original message text.
    :param enforce_spaces: If ``True``, preserves multiple spaces using ``[a][/a]`` tags.
    :param enforce_line_breaks: If ``True``, preserves multiple line breaks using ``[a][/a]`` tags.
    :return: The modified message text with spacing and/or line breaks preserved.
    """
    if enforce_spaces:
        message_text = re.sub(r' {2,}', _replace_multiple_spaces, message_text)
        message_text = re.sub(r'^ |\n ', _replace_first_space, message_text)
        message_text = re.sub(r' $| \n', _replace_last_space, message_text)

    if enforce_line_breaks:
        message_text = re.sub('\n{2,}', _replace_line_breaks, message_text)
        message_text = re.sub('\n$', '\n[a][/a]', message_text)
        if message_text.startswith('\n'):
            message_text = '[a][/a]' + message_text

    return message_text


def _replace_multiple_spaces(match: re.Match[str]) -> str:
    spaces_amount = len(match.group())
    return ' [a][/a]' * (spaces_amount - 1) + ' '


def _replace_first_space(match: re.Match[str]) -> str:
    if match.group().startswith('\n'):
        return '\n[a][/a] '
    return '[a][/a] '


def _replace_last_space(match: re.Match[str]) -> str:
    if match.group().endswith('\n'):
        return ' [a][/a]\n'
    return ' [a][/a]'


def _replace_line_breaks(match: re.Match[str]) -> str:
    breaks_amount = len(match.group())
    return '\n[a][/a]' * (breaks_amount - 1) + '\n'
