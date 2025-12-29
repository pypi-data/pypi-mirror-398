from __future__ import annotations


__all__ = (
    'RequestableObject',
    'OrdersCountersRequestObject',
    'ChatCounterRequestObject',
    'ChatBookmarksRequestObject',
    'CPURequestObject',
    'RequestNodeInfo',
    'NodeRequestObject',
    'Action',
    'SendingMessageData',
    'SendMessageAction',
)
from typing import TYPE_CHECKING, Any, Literal
from abc import ABC, abstractmethod

from pydantic import Field, BaseModel, AliasChoices, computed_field

from funpaybotengine.utils import random_runner_tag


if TYPE_CHECKING:
    from funpaybotengine.client.bot import Bot


class RequestableObject(ABC, BaseModel):
    """
    Base class for all objects that can be sent as runner requests.
    """

    @computed_field
    @abstractmethod
    def type(self) -> str: ...

    """Request type identifier."""

    async def as_data_dict(self, bot: Bot) -> dict[str, Any]:
        return self.model_dump(exclude_none=True, by_alias=True)


class OrdersCountersRequestObject(RequestableObject, BaseModel):
    """
    Request for retrieving order counters of a specific user.
    """

    runner_tag: str = Field(
        serialization_alias='tag',
        validation_alias=AliasChoices('runner_tag', 'tag'),
        default_factory=random_runner_tag,
    )
    """Runner tag used for request tracking."""

    @computed_field
    def type(self) -> str:
        return 'orders_counters'

    @computed_field
    def data(self) -> bool:
        return False

    async def as_data_dict(self, bot: Bot) -> dict[str, Any]:
        result = await super().as_data_dict(bot)
        return result | {'id': bot.userid}


class ChatCounterRequestObject(RequestableObject, BaseModel):
    """
    Request for retrieving chat counter for a user.
    """

    runner_tag: str = Field(
        serialization_alias='tag',
        validation_alias=AliasChoices('runner_tag', 'tag'),
        default_factory=random_runner_tag,
    )
    """Runner tag used for request tracking."""

    @computed_field
    def type(self) -> str:
        return 'chat_counter'

    @computed_field
    def data(self) -> bool:
        return False

    async def as_data_dict(self, bot: Bot) -> dict[str, Any]:
        result = await super().as_data_dict(bot)
        return result | {'id': bot.userid}


class CPURequestObject(RequestableObject, BaseModel):
    """
    Request for information about the offer currently being viewed by a user.
    """

    id: int
    """User ID whose currently viewed offer info is being requested."""

    runner_tag: str = Field(
        serialization_alias='tag',
        validation_alias=AliasChoices('runner_tag', 'tag'),
        default_factory=random_runner_tag,
    )
    """Runner tag used for request tracking."""

    @computed_field
    def type(self) -> str:
        return 'c-p-u'

    @computed_field
    def data(self) -> bool:
        return False


class ChatBookmarksRequestObject(RequestableObject, BaseModel):
    """
    Request for retrieving chat bookmarks for a user.
    """

    runner_tag: str = Field(
        serialization_alias='tag',
        validation_alias=AliasChoices('runner_tag', 'tag'),
        default_factory=random_runner_tag,
    )
    """Runner tag used for request tracking."""

    data: list[tuple[int, int]] | Literal[False] = False
    """
    Optional list of (chat ID, last message ID) pairs.

    If not provided, defaults to ``False`` (recommended).
    """

    @computed_field
    def type(self) -> str:
        return 'chat_bookmarks'

    async def as_data_dict(self, bot: Bot) -> dict[str, Any]:
        result = await super().as_data_dict(bot)
        return result | {'id': bot.userid}


class RequestNodeInfo(BaseModel):
    """
    Chat node metadata used in ``NodeRequestObject.data``.
    """

    chat_id: int | str = Field(
        serialization_alias='node',
        validation_alias=AliasChoices('chat_id', 'node'),
    )
    """Chat ID or name whose message history is being requested."""

    after_message_id: int = Field(
        default=0,
        serialization_alias='last_message',
        validation_alias=AliasChoices('after_message_id', 'last_message '),
    )
    """
    ID of the last message (start point for history retrieval).

    Fetches messages sent **after** this ID, typically in batches of 50.
    
    If you need to fetch last messages in a chat, set it to ``0``.
    """

    show_avatar: Literal[0, 1] = 1
    """
    Whether to include user avatars in the rendered HTML output.
    
    Avatars are only available for public chats.
    """

    @computed_field
    def content(self) -> str:
        return ''


class NodeRequestObject(RequestableObject, BaseModel):
    """
    Request for retrieving chat (node) message history.
    """

    chat_id: int | str = Field(
        serialization_alias='id',
        validation_alias=AliasChoices('chat_id', 'id'),
    )
    """Chat ID or name whose history is being requested."""

    runner_tag: str = Field(
        serialization_alias='tag',
        validation_alias=AliasChoices('runner_tag', 'tag'),
        default_factory=random_runner_tag,
    )
    """Runner tag used for request tracking."""

    data: RequestNodeInfo | Literal[False] = False
    """
    Chat metadata describing what history to fetch.
    
    Set to ``False`` to retrieve the latest 50 messages from the chat.
    
    Defaults to ``False``.
    """

    @computed_field
    def type(self) -> str:
        return 'chat_node'


class Action(ABC, BaseModel):
    """
    Base class for all runner actions.
    """

    @computed_field
    @abstractmethod
    def action(self) -> str: ...

    """Action type identifier."""


class SendingMessageData(BaseModel):
    """
    Chat node metadata used in ``SendMessageAction.message_data``.
    """

    chat_id: int | str = Field(
        serialization_alias='node',
        validation_alias=AliasChoices('chat_id', 'node'),
    )
    """Chat ID or name where the message should be sent."""

    after_message_id: int = Field(
        default=-1,
        serialization_alias='last_message',
        validation_alias=AliasChoices('after_message_id', 'last_message'),
    )
    """Unused field (currently has no effect)."""

    message_text: str = Field(
        default='',
        serialization_alias='content',
        validation_alias=AliasChoices('message_text', 'content'),
    )
    """
    Text content of the message.

    Leave empty when sending an image.
    """

    image_id: int | None = None
    """
    ID of the image to send.

    Leave as ``None`` if sending a text message.
    """


class SendMessageAction(Action, BaseModel):
    """
    Action that sends a message to a chat.
    """

    message_data: SendingMessageData = Field(
        serialization_alias='data',
        validation_alias=AliasChoices('message_data', 'data'),
    )
    """Message data."""

    @computed_field
    def action(self) -> str:
        return 'chat_message'
