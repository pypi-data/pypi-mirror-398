"""RPC client services for customer app."""

from datetime import datetime
from typing import Any

from kaiju_tools.http import RPCClientService
from kaiju_tools.services import SERVICE_CLASS_REGISTRY
from msgspec import convert

from .types import *


class ElementoLoyaltyProcessingClient(RPCClientService):
    """Auto-generated ElementoCustomers RPC client."""

    async def lists_set_product_list(self, id: ListId, items: list, _max_timeout: int = None, _nowait: bool = False):
        """Call Lists.products.set."""
        return await self.call(
            method="Lists.products.set", params=dict(id=id, items=items), max_timeout=_max_timeout, nowait=_nowait
        )

    async def balance_history(
        self,
        customer_id: CustomerId,
        next_transaction_id: TransactionId | None = None,
        limit: int = 10,
        _max_timeout: int = None,
        _nowait: bool = False,
    ) -> list:
        return await self.call(
            method="Balance.history",
            params=dict(customer_id=customer_id, next_transaction_id=next_transaction_id, limit=limit),
            max_timeout=_max_timeout,
            nowait=_nowait,
        )

    async def balance_history_list(
        self,
        customer_id: CustomerId,
        page: int = 1,
        per_page: int = 24,
        _max_timeout: int = None,
    ) -> dict:
        return await self.call(
            method="Balance.history.list",
            params=dict(customer_id=customer_id, page=page, per_page=per_page),
            max_timeout=_max_timeout,
            nowait=False,
        )

    async def balance_history_expiring(
        self, customer_id: CustomerId, active_to: str, _max_timeout: int = None, _nowait: bool = False
    ) -> list:
        return await self.call(
            method="Balance.history.expiring",
            params=dict(customer_id=customer_id, active_to=active_to),
            max_timeout=_max_timeout,
            nowait=_nowait,
        )

    async def balance_history_expiring_list(
        self,
        customer_id: CustomerId,
        active_to: str,
        _max_timeout: int = None,
    ) -> list[Any]:
        return await self.call(
            method="Balance.history.expiring.list",
            params=dict(customer_id=customer_id, active_to=active_to),
            max_timeout=_max_timeout,
            nowait=False,
        )

    async def balance_get_balance(
        self, customer_id: CustomerId, _max_timeout: int = None, _nowait: bool = False
    ) -> Points:
        """Call Balance.get."""
        return await self.call(
            method="Balance.get", params=dict(customer_id=customer_id), max_timeout=_max_timeout, nowait=_nowait
        )

    async def balance_clear_balance(
        self, customer_id: CustomerId, _max_timeout: int = None, _nowait: bool = False
    ) -> None:
        """Call Balance.clear."""
        return await self.call(
            method="Balance.clear", params=dict(customer_id=customer_id), max_timeout=_max_timeout, nowait=_nowait
        )

    async def balance_calculate(
        self,
        customer: Customer.Fields | dict[str, Any],
        items: list[Item] | list[dict[str, Any]],
        store_id: StoreId,
        payment_type: str = None,
        points_sub: Points = 0,
        _max_timeout: int = None,
        _nowait: bool = False,
    ):
        data = await self.call(
            method="Balance.calculate",
            params=dict(
                customer=customer, store_id=store_id, items=items, payment_type=payment_type, points_sub=points_sub
            ),
            max_timeout=_max_timeout,
            nowait=_nowait,
        )
        return convert(data, Cart)

    async def balance_set_transaction(
        self,
        customer: Customer.Fields | dict[str, Any],
        items: list[Item] | list[dict[str, Any]],
        source: str,
        store_id: StoreId,
        payment_type: str,
        transaction_id: TransactionExtId,
        action: str = BalanceAction.CALC.value,
        points_sub: Points = 0,
        timestamp: datetime | str = None,
        _max_timeout: int = None,
        _nowait: bool = False,
    ) -> Transaction:
        """Call Balance.calculate_cart."""
        data = await self.call(
            method="Balance.transaction.set",
            params=dict(
                customer=customer,
                store_id=store_id,
                items=items,
                payment_type=payment_type,
                points_sub=points_sub,
                transaction_id=transaction_id,
                source=source,
                timestamp=timestamp,
                action=action,
            ),
            max_timeout=_max_timeout,
            nowait=_nowait,
        )
        return convert(data, Transaction)

    async def balance_confirm_transaction(
        self, transaction_id: TransactionExtId, _max_timeout: int = None, _nowait: bool = False
    ) -> Transaction | None:
        """Call Balance.transaction.confirm."""
        data = await self.call(
            method="Balance.transaction.confirm",
            params=dict(transaction_id=transaction_id),
            max_timeout=_max_timeout,
            nowait=_nowait,
        )
        if not data:
            return None
        return convert(data, Transaction)

    async def balance_revert_transaction(
        self, transaction_id: TransactionExtId, _max_timeout: int = None, _nowait: bool = False
    ) -> None:
        """Call Balance.transaction.revert."""
        return await self.call(
            method="Balance.transaction.revert",
            params=dict(transaction_id=transaction_id),
            max_timeout=_max_timeout,
            nowait=_nowait,
        )

    async def balance_commit_transaction(
        self, transaction_id: TransactionExtId, _max_timeout: int = None, _nowait: bool = False
    ) -> Transaction | None:
        """Call Balance.transaction.commit."""
        data = await self.call(
            method="Balance.transaction.commit",
            params=dict(transaction_id=transaction_id),
            max_timeout=_max_timeout,
            nowait=_nowait,
        )
        if not data:
            return None
        return convert(data, Transaction)

    async def balance_refund(
        self,
        customer_id: CustomerId,
        source: str,
        transaction_id: TransactionExtId,
        items: list[RefundItem],
        _max_timeout: int = None,
        _nowait: bool = False,
    ) -> Points:
        """Call Balance.refund."""
        data = await self.call(
            method="Balance.refund",
            params=dict(customer_id=customer_id, source=source, transaction_id=transaction_id, items=items),
            max_timeout=_max_timeout,
            nowait=_nowait,
        )
        return Points(data)

    async def balance_create_event(
        self,
        customer: dict[str, Any],
        event_type: EventTypeId,
        meta: dict[str, Any] = None,
        _max_timeout: int = None,
        _nowait: bool = False,
    ) -> bool:
        """Call Balance.create_event."""
        return await self.call(
            method="Balance.create_event",
            params=dict(customer=customer, event_type=event_type, meta=meta),
            max_timeout=_max_timeout,
            nowait=_nowait,
        )


SERVICE_CLASS_REGISTRY.register(ElementoLoyaltyProcessingClient)
