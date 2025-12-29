from __future__ import annotations


__all__ = ('MyOffersPage',)


from funpaybotengine.types.offers import OfferPreview
from funpaybotengine.types.pages.base import FunPayPage


class MyOffersPage(FunPayPage):
    """Represents personal lots page (`/lots/<subcategory_id>/trade`)."""

    category_id: int | None
    """Category ID (from raise button data-game, if present)."""

    subcategory_id: int
    """Subcategory ID."""

    offers: dict[int | str, OfferPreview]
    """Owned offers mapped by offer ID."""
