from __future__ import annotations


__all__ = ('ProfilePage',)


from typing import Annotated
from types import MappingProxyType
from collections.abc import Mapping

from pydantic import BaseModel, BeforeValidator

from funpaybotengine.types.chat import Chat
from funpaybotengine.types.enums import SubcategoryType
from funpaybotengine.types.common import UserBadge, UserRating, Achievement
from funpaybotengine.types.offers import OfferPreview
from funpaybotengine.types.reviews import ReviewsBatch
from funpaybotengine.types.pages.base import FunPayPage


class ProfilePage(FunPayPage, BaseModel):
    """Represents a user profile page (`https://funpay.com/users/<user_id>`)."""

    user_id: int
    """User id."""

    username: str
    """Username."""

    badge: UserBadge | None
    """User badge."""

    achievements: tuple[Achievement, ...]
    """User achievements."""

    avatar_url: str
    """User avatar url."""

    online: bool
    """Whether the user is online or not."""

    banned: bool
    """Whether the user is banned or not."""

    registration_date_text: str
    """User registration date text."""

    status_text: str | None
    """User status text."""

    rating: UserRating | None
    """User rating."""

    offers: Annotated[
        Mapping[SubcategoryType, Mapping[int, tuple[OfferPreview, ...]]] | None,
        BeforeValidator(ProfilePage._convert_to_immutable),
    ]
    """User offers."""

    chat: Chat | None
    """Chat with user."""

    reviews: ReviewsBatch | None
    """User reviews."""

    @staticmethod
    def _convert_to_immutable(
        value: dict[SubcategoryType, dict[int, list[OfferPreview]]],
    ) -> MappingProxyType[SubcategoryType, Mapping[int, tuple[OfferPreview, ...]]] | None:
        if value is None:
            return None

        result = {}
        for type_, offers in value.items():
            result[type_] = MappingProxyType(
                {id_: tuple(offers_list) for id_, offers_list in offers.items()},
            )
        return MappingProxyType(result)
