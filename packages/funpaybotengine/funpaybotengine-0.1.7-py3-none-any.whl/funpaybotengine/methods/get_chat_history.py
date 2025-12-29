from __future__ import annotations


__all__ = ('GetChatHistory',)

import json
from typing import TYPE_CHECKING, Any, cast

from pydantic import BaseModel
from funpayparsers.types import Message as ParserMessage
from funpayparsers.parsers import MessagesParser

from funpaybotengine.types.enums import Language
from funpaybotengine.methods.base import FunPayMethod
from funpaybotengine.client.session import HTTPMethod
from funpaybotengine.types.messages import Message


if TYPE_CHECKING:
    from funpaybotengine.client.session.base import RawResponse


class GetChatHistory(FunPayMethod[list[Message]], BaseModel):
    """
    Get chat history method (``https://funpay.com/chat/history``).

    Returns max. 50 messages before ``before_message_id``.
    """

    chat_id: int | str
    """Chat ID."""

    before_message_id: int = 99999999999
    """
    Message ID to paginate history **backwards from** (exclusive).

    Messages with IDs **less than** this one will be returned,
    i.e. history will be fetched in reverse order *before* this message.
    
    Defaults to ``99999999999``
    """

    def __init__(
        self,
        chat_id: int | str,
        before_message_id: int = 99999999999,
        locale: Language | None = None,
    ):
        """
        :param chat_id: Chat ID.
        :param before_message_id: Message ID to paginate history **backwards from**
            (exclusive).
            Messages with IDs **less than** this one will be returned,
            i.e. history will be fetched in reverse order *before* this message.
        :param locale: FunPay locale.
            If specified and ``ignore_locale`` is ``False``,
            it will override bots locale when making a request.
            Defaults to ``None``.
        """
        super().__init__(
            url='chat/history',
            method=HTTPMethod.GET,
            locale=locale,
            data={'node': str(chat_id), 'last_message': str(before_message_id)},
            headers={'X-Requested-With': 'XMLHttpRequest'},
            allow_anonymous=True,
            allow_uninitialized=True,
            parser_cls=MessagesParser,
            context={'chat_id': chat_id} if isinstance(chat_id, int) else {'chat_name': chat_id},
            chat_id=chat_id,
            before_message_id=before_message_id,
        )

    async def parse_result(self, response: RawResponse[Any]) -> list[ParserMessage]:
        result = json.loads(response.raw_response)
        messages = result['chat']['messages']
        html = '\n'.join(i['html'] for i in messages)
        return cast(
            list[ParserMessage],
            self.parser_cls(html, options=self.parser_options).parse(),  # type: ignore[misc]
            # not None
        )

    async def transform_result(
        self,
        parsing_result: list[ParserMessage],
        response: RawResponse[Any],
    ) -> list[Message]:
        context = await self.get_full_context(response)
        return [Message.model_validate(i, context=context) for i in parsing_result]
