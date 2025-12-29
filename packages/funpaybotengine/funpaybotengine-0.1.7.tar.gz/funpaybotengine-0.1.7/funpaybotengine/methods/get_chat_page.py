from __future__ import annotations


__all__ = ('GetChatPage',)


from pydantic import BaseModel
from funpayparsers.parsers.page_parsers import ChatPageParser

from funpaybotengine.types.enums import Language
from funpaybotengine.methods.base import FunPayMethod
from funpaybotengine.client.session import HTTPMethod
from funpaybotengine.types.pages.chat_page import ChatPage


class GetChatPage(FunPayMethod[ChatPage], BaseModel):
    """
    Get chat method (``https://funpay.com/chat/history``).

    Returns max. 50 messages before ``before_message_id``.
    """

    chat_id: int | str
    """Chat ID."""

    __model_to_build__ = ChatPage

    def __init__(self, chat_id: int | str, locale: Language | None = None):
        """
        :param chat_id: Chat ID.
        :param locale: FunPay locale.
            If specified and ``ignore_locale`` is ``False``,
            it will override bots locale when making a request.
            Defaults to ``None``.
        """
        super().__init__(
            url='chat/',
            method=HTTPMethod.GET,
            locale=locale,
            data={'node': str(chat_id)},
            parser_cls=ChatPageParser,
            allow_anonymous=True,
            allow_uninitialized=True,
            chat_id=chat_id,
        )
