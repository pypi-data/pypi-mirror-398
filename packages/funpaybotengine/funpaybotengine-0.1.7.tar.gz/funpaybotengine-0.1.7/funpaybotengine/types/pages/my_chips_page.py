from __future__ import annotations


__all__ = ('MyChipsPage',)


from funpaybotengine.types.offers import OfferFields
from funpaybotengine.types.pages.base import FunPayPage


class MyChipsPage(FunPayPage):
    """Represents personal chips page (`/chips/<subcategory_id>/trade`)."""

    category_id: int | None
    """Category ID (hidden input `name="game"`)."""

    subcategory_id: int
    """Subcategory ID."""

    fields: OfferFields
    """All form fields for chips offers (editable values)."""
