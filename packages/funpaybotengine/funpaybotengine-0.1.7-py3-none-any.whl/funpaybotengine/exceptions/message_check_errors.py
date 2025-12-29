from __future__ import annotations


__all__ = ('MessageTextTooLongError', 'MessageWordTooLongError', 'TooManyLinesError')


from funpaybotengine.exceptions.base import FunPayBotEngineError


class MessageTextError(FunPayBotEngineError, ValueError):
    def __init__(self, message_text: str):
        args = (
            f"Message text '{message_text}' does not meet FunPay rules.",
            message_text,
        )
        super().__init__(*args)

        self.message_text = message_text
        self.max_text_length = 2000
        self.max_word_length = 160
        self.max_lines_amount = 20


class MessageTextTooLongError(MessageTextError):
    def __str__(self) -> str:
        return f'Message text is too long ({len(self.message_text)} > {self.max_text_length}).'


class MessageWordTooLongError(MessageTextError):
    def __str__(self) -> str:
        big_words = [i for i in self.message_text.split() if len(i) > self.max_word_length]
        words_sizes = [f'{len(i)} > {self.max_word_length}' for i in big_words]
        return f'Words {big_words} are too long ({", ".join(words_sizes)}).'


class TooManyLinesError(MessageTextError):
    def __str__(self) -> str:
        return f'Too many lines ({len(self.message_text.splitlines())}).'
