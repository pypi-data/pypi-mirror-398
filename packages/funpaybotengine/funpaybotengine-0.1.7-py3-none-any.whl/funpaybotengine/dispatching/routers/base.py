from __future__ import annotations


__all__ = ['Router']


from eventry.asyncio.router import Router as BaseRouter

import funpaybotengine.dispatching.events.builtin_events as events
from funpaybotengine.dispatching.events.base import ExceptionEvent
from funpaybotengine.dispatching.handlers.handler_manager import HandlerManager


_events = {
    'chat_changed': events.ChatChangedEvent,
    'new_message': events.NewMessageEvent,
    'new_sale': events.NewSaleEvent,
    'sale_closed_by_admin': events.SaleClosedByAdminEvent,
    'sale_closed': events.SaleClosedEvent,
    'sale_partially_refunded': events.SalePartiallyRefundedEvent,
    'sale_refunded': events.SaleRefundedEvent,
    'sale_reopened': events.SaleReopenedEvent,
    'sale_status_changed': events.SaleStatusChangedEvent,
    'new_purchase': events.NewPurchaseEvent,
    'purchase_closed_by_admin': events.PurchaseClosedByAdminEvent,
    'purchase_closed': events.PurchaseClosedEvent,
    'purchase_partially_refunded': events.PurchasePartiallyRefundedEvent,
    'purchase_refunded': events.PurchaseRefundedEvent,
    'purchase_reopened': events.PurchaseReopenedEvent,
    'purchase_status_changed': events.PurchaseStatusChangedEvent,
    'new_review': events.NewReviewEvent,
    'review_changed': events.ReviewChangedEvent,
    'review_deleted': events.ReviewDeletedEvent,
    'new_review_response': events.NewReviewResponseEvent,
    'review_response_changed': events.ReviewResponseChangedEvent,
    'review_response_deleted': events.ReviewResponseDeletedEvent,
    'error': ExceptionEvent,
}


class Router(BaseRouter):
    on_chat_changed: HandlerManager
    on_new_message: HandlerManager
    on_new_sale: HandlerManager
    on_sale_status_changed: HandlerManager
    on_sale_closed: HandlerManager
    on_sale_closed_by_admin: HandlerManager
    on_sale_refunded: HandlerManager
    on_sale_partially_refunded: HandlerManager
    on_sale_reopened: HandlerManager
    on_new_purchase: HandlerManager
    on_purchase_status_changed: HandlerManager
    on_purchase_closed: HandlerManager
    on_purchase_closed_by_admin: HandlerManager
    on_purchase_refunded: HandlerManager
    on_purchase_partially_refunded: HandlerManager
    on_purchase_reopened: HandlerManager
    on_new_review: HandlerManager
    on_review_changed: HandlerManager
    on_review_deleted: HandlerManager
    on_new_review_response: HandlerManager
    on_review_response_changed: HandlerManager
    on_review_response_deleted: HandlerManager
    on_error: HandlerManager

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name=name or f'Router{id(self)}')
        self._default_handler_manager = HandlerManager(self, 'default', None)

        for name, event in _events.items():
            manager = self._add_handler_manager(HandlerManager(self, name, event))  # type: ignore
            setattr(self, f'on_{name}', manager)

    @property
    def on_event(self) -> HandlerManager:
        return self._default_handler_manager
