from __future__ import annotations


__all__ = ('FunPayPage',)


from pydantic import BaseModel

from funpaybotengine.types.base import FunPayObject
from funpaybotengine.types.common_page_elements import AppData, PageHeader


class FunPayPage(FunPayObject, BaseModel):
    """Base class for FunPay pages."""

    header: PageHeader
    """Page header."""

    app_data: AppData
    """App data."""
