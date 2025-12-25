from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..usables.item import Item


@dataclass
class TradingItem:
    item: Item
    count: int = 1
    factor: float = 1.0
    available: int = 1
    tid: int = 0
    price: int = 0
    trading_price: int = 0
    stackable: bool = False
    stackable_merchant: bool = False

    def __eq__(self, other):
        return self.tid == other.tid
