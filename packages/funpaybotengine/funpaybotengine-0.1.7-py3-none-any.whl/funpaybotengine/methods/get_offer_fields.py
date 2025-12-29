from __future__ import annotations


__all__ = ('GetOfferFields',)


from pydantic import BaseModel
from funpayparsers.types import Language
from funpayparsers.parsers import OfferFieldsParser

from funpaybotengine.types.enums import SubcategoryType
from funpaybotengine.methods.base import FunPayMethod
from funpaybotengine.types.offers import OfferFields
from funpaybotengine.client.session import HTTPMethod


class GetOfferFields(FunPayMethod[OfferFields], BaseModel):
    """
    Get offer fields method.

    Returns ``funpaybotengine.types.pages.OrderPage`` obj.
    """

    subcategory_type: SubcategoryType
    subcategory_id: int
    offer_id: int | None = None

    __model_to_build__ = OfferFields

    def __init__(
        self,
        subcategory_type: SubcategoryType,
        subcategory_id: int,
        offer_id: int | None = None,
        locale: Language | None = None,
    ):
        if subcategory_type is SubcategoryType.COMMON:
            url = 'lots/offerEdit'
            data = {'offer': offer_id} if offer_id is not None else {'node': subcategory_id}
        else:
            url = f'chips/{subcategory_id}/trade'
            data = {}

        super().__init__(
            url=url,
            method=HTTPMethod.GET,
            data=data,
            parser_cls=OfferFieldsParser,
            locale=locale,
            subcategory_type=subcategory_type,
            subcategory_id=subcategory_id,
            offer_id=offer_id,
        )
