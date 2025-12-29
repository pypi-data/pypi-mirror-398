from __future__ import annotations


__all__ = ('GetMainPage',)


from pydantic import BaseModel
from funpayparsers.parsers.page_parsers import MainPageParser

from funpaybotengine.types.enums import Language
from funpaybotengine.types.pages import MainPage
from funpaybotengine.methods.base import FunPayMethod
from funpaybotengine.client.session import HTTPMethod


class GetMainPage(FunPayMethod[MainPage], BaseModel):
    """
    Get the main page method (``https://funpay.com/``).

    Returns ``funpaybotengine.types.pages.MainPage`` obj.
    """

    change_locale: Language | None = None
    """
    Change locale to specified.
    
    Defaults to ``None``.
    """

    __model_to_build__ = MainPage

    def __init__(self, locale: Language | None = None, change_locale: Language | None = None):
        super().__init__(
            url='',
            method=HTTPMethod.GET,
            locale=locale,
            parser_cls=MainPageParser,
            allow_anonymous=True,
            allow_uninitialized=True,
            data={'setlocale': change_locale.value.appdata_alias}
            if change_locale is not None
            else {},
            change_locale=change_locale,
        )
