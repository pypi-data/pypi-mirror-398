from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, NewType, TypedDict

from elemento_customers.types import Customer, CustomerId
from msgspec import Struct


__all__ = [
    "DATE_MAXVALUE",
    "ListId",
    "CustomerId",
    "ItemList",
    "ItemListType",
    "EventTypeId",
    "BalanceStatus",
    "Balance",
    "TransactionType",
    "TransactionId",
    "CustomerId",
    "Transaction",
    "EventTypeId",
    "Item",
    "RefundItem",
    "Cart",
    "BalanceAction",
    "Customer",
    "StoredTransaction",
    "OfferId",
    "GroupId",
    "OfferEventTypes",
    "ConditionId",
    "LifetimeId",
    "ActionId",
    "Points",
    "StoreId",
    "AppliedOffer",
    "PointType",
    "TransactionExtId",
    "PurchaseStats",
]

DATE_MAXVALUE = date.fromisoformat("3000-01-01")

TransactionExtId = NewType("TransactionExtId", str)
TransactionId = NewType("TransactionId", int)
EventTypeId = NewType("EventTypeId", str)
ListId = NewType("ListId", int)
StoreId = NewType("StoreId", int)
OfferId = NewType("OfferId", int)
LifetimeId = NewType("LifetimeId", str)
GroupId = NewType("GroupId", int)
ConditionId = NewType("ConditionId", int)
ActionId = NewType("ActionId", int)
Points = NewType("Points", int)


class OfferEventTypes(Enum):
    PointsAdd = "PointsAdd"
    PointsUse = "PointsUse"
    Purchase = "Purchase"
    Return = "Return"
    Birthday = "Birthday"
    RegistrationDone = "RegistrationDone"


class ItemListType(Enum):
    STORE = "STORE"
    PRODUCT = "PRODUCT"
    TERMINAL = "TERMINAL"


class ItemList(Struct):
    type: ItemListType
    id: ListId
    items: list[str]


class BalanceStatus(Enum):
    FUTURE = "FUTURE"
    HOLD = "HOLD"
    ACTIVE = "ACTIVE"


class Balance(Struct):
    customer_id: CustomerId
    active_from: date
    active_to: date
    status: BalanceStatus
    amount: int
    transaction_id: TransactionId | None = None


class TransactionType(Enum):
    ORDER = "ORDER"
    SCRIPT = "SCRIPT"


class _PointTypeData(TypedDict, total=False):
    func: str
    value: Any
    time_unit: str


class PointType(Struct):
    updated: datetime
    id: LifetimeId
    label: str
    activation: _PointTypeData
    expiration: _PointTypeData


class BalanceAction(Enum):
    CALC = "CALC"
    SUB = "SUB"
    ADD = "ADD"


class AppliedOffer(Struct):
    offer_id: int | None
    offer_name: str
    points_sub: Points
    points_sub_max: Points
    points_add: Points
    active_from: date
    active_to: date


class Item(Struct):
    pos: int
    product_id: str
    quantity: int
    total: Decimal
    price: Decimal
    initial_total: Decimal | None = None
    cashback: Points = 0
    discount: Decimal = Decimal("0.00")
    points_add: Points = 0
    points_sub: Points = 0
    points_sub_max: Points = 0
    params: dict[str, Any] = {}
    offers_add: list[AppliedOffer] = []
    offers_sub: list[AppliedOffer] = []


class RefundItem(TypedDict):
    pos: int
    quantity: int


class Cart(Struct):
    items: list[Item]
    total: Decimal = Decimal(0)
    initial_total: Decimal = Decimal(0)
    discount: Decimal = Decimal(0)
    points_add: Points = Points(0)
    points_sub: Points = Points(0)
    points_sub_max: Points = Points(0)
    points_available: Points = Points(0)
    cashier_message: str | None = None
    customer_message: str | None = None
    offers_add: list[AppliedOffer] = []


class StoredTransaction(Struct):
    id: TransactionId
    created: datetime
    customer_id: CustomerId
    total: int
    type: TransactionType
    balance: list[int]
    quantity: list[int]
    ext_id: TransactionExtId
    source: str
    # data: dict[str, Any] = None
    active: bool = True


class Transaction(Struct):
    ext_id: TransactionExtId
    id: TransactionId
    source: str
    order_id: str | None = None
    customer_id: CustomerId = None
    timestamp: datetime = None
    cart: Cart = None
    confirmed: bool = False
    payment_type: str | None = None


class PurchaseStats(Struct):
    total: int
    oldest_date: date | None
    latest_date: date | None
