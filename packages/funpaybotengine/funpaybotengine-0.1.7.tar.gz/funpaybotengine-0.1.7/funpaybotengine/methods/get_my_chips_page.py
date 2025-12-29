from __future__ import annotations


__all__ = ('GetMyChipsPage',)

from funpayparsers.parsers.page_parsers import MyChipsPageParser

from funpaybotengine.types.pages import MyChipsPage
from funpaybotengine.methods.base import FunPayMethod
from funpaybotengine.client.session.http_methods import HTTPMethod


class GetMyChipsPage(FunPayMethod[MyChipsPage]):
    """
    Get personal chips page (``https://funpay.com/chips/<subcategory_id>/trade``).

    Returns ``funpaybotengine.types.pages.MyChipsPage``.
    """

    subcategory_id: int
    """Subcategory ID."""

    __model_to_build__ = MyChipsPage

    def __init__(self, subcategory_id: int):
        super().__init__(
            url=f'chips/{subcategory_id}/trade',
            method=HTTPMethod.GET,
            parser_cls=MyChipsPageParser,
            subcategory_id=subcategory_id,
        )
