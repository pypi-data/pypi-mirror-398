from __future__ import annotations

from typing import Any


__all__ = ('FunPayBotEngineError',)


class FunPayBotEngineError(Exception):
    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
