from __future__ import annotations

from dataclasses import dataclass, field

from .json_io import JsonDataclass


@dataclass
class ShopJson(JsonDataclass):
    """Shop record matching ``schemas/shop.schema.json``."""

    keeper: int
    buy_types: list[str] = field(default_factory=list)
    profit_buy: int = 100
    profit_sell: int = 100
    open_hour: int = 0
    close_hour: int = 23
