from __future__ import annotations


__all__ = ('Category', 'Subcategory')

from pydantic import BaseModel

from funpaybotengine.types.base import FunPayObject
from funpaybotengine.types.enums import SubcategoryType


class Category(FunPayObject, BaseModel):
    """Represents a category from FunPay main page."""

    id: int
    """Category ID."""

    name: str
    """Category name."""

    subcategories: tuple['Subcategory', ...]
    """List of subcategories."""

    location: str | None = None

    @property
    def full_name(self) -> str:
        if self.location is None:
            return self.name
        return f'{self.name} ({self.location})'


class Subcategory(FunPayObject, BaseModel):
    """Represents a subcategory from FunPay main page."""

    id: int
    """
    Subcategory ID.

    .. warning:: 
        Subcategory ID is not always unique. 
        IDs are unique per subcategory type but may repeat across types.
        That means, that some common category (``CategoryType.COMMON``) 
        can have same ID as some currency category (``CategoryType.CURRENCY``).

    Example:
        Common category `Lineage 2 Items (RU)` (category ID: ``1``): 
        https://funpay.com/lots/1/

        Currency category `Lineage 2 Adena (RU)` (category ID: ``1``): 
        https://funpay.com/chips/1/
    """

    name: str
    """Subcategory name."""

    type: SubcategoryType
    """Subcategory type."""

    offers_amount: int | None
    """
    Subcategory offers amount.
    Available only when parsing Subcategory offers list page.
    """
