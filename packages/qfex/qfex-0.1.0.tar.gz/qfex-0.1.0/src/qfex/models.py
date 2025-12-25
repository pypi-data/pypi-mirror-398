from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from enum import Enum


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class TimeInForce(str, Enum):
    IOC = "IOC"
    GTC = "GTC"
    FOK = "FOK"


@dataclass
class BalanceState:
    deposit: Decimal = Decimal("0")
    realised_pnl: Decimal = Decimal("0")
    unrealised_pnl: Decimal = Decimal("0")
    net_funding: Decimal = Decimal("0")
    order_margin: Decimal = Decimal("0")
    position_margin: Decimal = Decimal("0")
    available_balance: Decimal = Decimal("0")


@dataclass
class PositionState:
    symbol: str
    position: Decimal = Decimal("0")
    margin_alloc: Decimal = Decimal("0")
    realised_pnl: Decimal = Decimal("0")
    unrealised_pnl: Decimal = Decimal("0")
    net_funding: Decimal = Decimal("0")
    open_orders: Decimal = Decimal("0")
    open_quantity: Decimal = Decimal("0")
    leverage: Decimal = Decimal("0")
    initial_margin: Decimal = Decimal("0")
    maintenance_margin: Decimal = Decimal("0")
    average_price: Decimal = Decimal("0")


@dataclass
class BBO:
    symbol: str
    bid_px: Optional[Decimal] = None
    bid_qty: Optional[Decimal] = None
    ask_px: Optional[Decimal] = None
    ask_qty: Optional[Decimal] = None
    sequence: Optional[int] = None
    ts: Optional[str] = None
