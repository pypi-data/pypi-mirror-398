from __future__ import annotations


__all__ = ('Review',)


from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel

from funpaybotengine.types.enums import Language
from funpaybotengine.methods.base import FunPayMethod
from funpaybotengine.client.session.http_methods import HTTPMethod


if TYPE_CHECKING:
    from funpaybotengine.client.bot import Bot
    from funpaybotengine.client.session.base import RawResponse


class Review(FunPayMethod[bool], BaseModel):
    """
    Leave / Edit a review / reply to review (``https://funpay.com/orders/review``).

    Returns ``True``.
    """

    order_id: str
    """Reviewing order ID."""

    text: str
    """Review text."""

    rating: Literal[0, 1, 2, 3, 4, 5]
    """Review rating."""

    def __init__(
        self,
        order_id: str,
        text: str,
        rating: Literal[0, 1, 2, 3, 4, 5],
        locale: Language | None = None,
    ):
        super().__init__(
            method=HTTPMethod.POST,
            url='orders/review',
            locale=locale,
            data=make_data,
            headers={'X-Requested-With': 'XMLHttpRequest'},
            order_id=order_id,
            text=text,
            rating=rating,
        )

    async def parse_result(self, response: RawResponse[Any]) -> bool:
        return True

    async def transform_result(self, parsing_result: Any, response: RawResponse[Any]) -> bool:
        return True


async def make_data(method: Review, bot: Bot) -> dict[str, Any]:
    return {
        'orderId': method.order_id,
        'rating': method.rating or '',
        'text': method.text,
        'authorId': bot.userid,
    }
