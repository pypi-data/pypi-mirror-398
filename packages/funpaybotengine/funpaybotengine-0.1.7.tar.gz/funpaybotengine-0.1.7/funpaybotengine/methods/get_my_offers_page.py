from __future__ import annotations


__all__ = ('GetMyOffersPage',)

from funpayparsers.parsers.page_parsers import MyOffersPageParser

from funpaybotengine.types.pages import MyOffersPage
from funpaybotengine.methods.base import FunPayMethod
from funpaybotengine.client.session.http_methods import HTTPMethod


class GetMyOffersPage(FunPayMethod[MyOffersPage]):
    """
    Get personal lots page (``https://funpay.com/lots/<subcategory_id>/trade``).

    Returns ``funpaybotengine.types.pages.MyOffersPage``.
    """

    subcategory_id: int
    """Subcategory ID."""

    __model_to_build__ = MyOffersPage

    def __init__(self, subcategory_id: int):
        super().__init__(
            url=f'lots/{subcategory_id}/trade',
            method=HTTPMethod.GET,
            parser_cls=MyOffersPageParser,
            subcategory_id=subcategory_id,
        )
