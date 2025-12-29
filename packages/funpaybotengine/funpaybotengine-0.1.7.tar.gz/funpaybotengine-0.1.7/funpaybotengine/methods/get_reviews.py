from __future__ import annotations


__all__ = ('GetReviews',)


from pydantic import BaseModel
from funpayparsers.types import Language
from funpayparsers.parsers import ReviewsParser

from funpaybotengine.types import ReviewsBatch
from funpaybotengine.types.enums import OrderStatus
from funpaybotengine.methods.base import FunPayMethod
from funpaybotengine.client.session.http_methods import HTTPMethod


STATE_FILTERS = {
    OrderStatus.COMPLETED: 'closed',
    OrderStatus.PAID: 'paid',
    OrderStatus.REFUNDED: 'refunded',
}


class GetReviews(FunPayMethod[ReviewsBatch], BaseModel):
    """
    Get a sales list (``https://funpay.com/orders/trade``).

    Returns ``funpaybotengine.types.OrderPreviewsBatch`` obj.
    """

    user_id: int
    from_review_id: str
    filter: str

    __model_to_build__ = ReviewsBatch

    def __init__(
        self,
        user_id: int,
        from_review_id: str = '',
        filter: str = '',
        locale: Language | None = None,
    ):
        super().__init__(
            url='users/reviews',
            method=HTTPMethod.POST,
            parser_cls=ReviewsParser,
            data={'user_id': user_id, 'continue': from_review_id, 'filter': filter},
            locale=locale,
            user_id=user_id,
            from_review_id=from_review_id,
            filter=filter,
        )
