from __future__ import annotations


__all__ = ('SaveOfferFields',)

from typing import Any

from pydantic import BaseModel
from funpayparsers.types import Language
from funpayparsers.parsers import OfferFieldsParser

from funpaybotengine.methods.base import FunPayMethod
from funpaybotengine.types.offers import OfferFields
from funpaybotengine.client.session import HTTPMethod, RawResponse


class SaveOfferFields(FunPayMethod[bool], BaseModel):
    """
    Get offer fields method.

    Returns ``funpaybotengine.types.pages.OrderPage`` obj.
    """

    offer_fields: OfferFields

    def __init__(
        self,
        offer_fields: OfferFields,
        locale: Language | None = None,
    ):
        url = 'chips/saveOffers' if 'chip' in offer_fields.fields_dict else 'lots/offerSave'
        super().__init__(
            url=url,
            method=HTTPMethod.POST,
            data=offer_fields.fields_dict,
            parser_cls=OfferFieldsParser,
            locale=locale,
            offer_fields=offer_fields,
        )

    async def parse_result(self, response: RawResponse[Any]) -> bool:
        return True

    async def transform_result(self, parsing_result: Any, response: RawResponse[Any]) -> bool:
        return True
