from __future__ import annotations


__all__ = ('DeleteReview',)


from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from funpaybotengine.types.enums import Language
from funpaybotengine.methods.base import FunPayMethod
from funpaybotengine.client.session.http_methods import HTTPMethod


if TYPE_CHECKING:
    from funpaybotengine.client.bot import Bot
    from funpaybotengine.client.session.base import RawResponse


class DeleteReview(FunPayMethod[bool], BaseModel):
    """
    Delete a review / reply to review (``https://funpay.com/orders/reviewDelete``).

    Returns ``True``.
    """

    order_id: str
    """Reviewing order ID."""

    def __init__(self, order_id: str, locale: Language | None = None):
        super().__init__(
            url='orders/review',
            method=HTTPMethod.POST,
            locale=locale,
            data=make_data,
            headers={'X-Requested-With': 'XMLHttpRequest'},
            order_id=order_id,
        )

    async def parse_result(self, response: RawResponse[Any]) -> bool:
        return True

    async def transform_result(self, parsing_result: Any, response: RawResponse[Any]) -> bool:
        return True


async def make_data(method: DeleteReview, bot: Bot) -> dict[str, Any]:
    return {
        'orderId': method.order_id,
        'authorId': bot.userid,
    }
