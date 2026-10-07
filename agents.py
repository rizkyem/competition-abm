"""Agent definitions for the Competition Agent-Based Model.

Two agent types are modelled:

* :class:`Customer` - an individual consumer with limited cash that decides
  whether and where to purchase each tick.
* :class:`Brand` - a brand operating one outlet that sells to customers,
  accumulates cash and may enter the market at a configured tick.

The classes are intentionally plain dataclasses with no external dependencies
so the core simulation runs with a stock Python installation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Customer:
    """An individual consumer agent."""

    customer_id: int
    x: float
    y: float
    cash: float
    income: float = 0.0
    price_sensitivity: float = 1.0
    brand_preference: float = 1.0
    quality_preference: float = 1.0
    promotion_sensitivity: float = 1.0
    distance_sensitivity: float = 1.0
    purchase_frequency: float = 0.3
    loyalty: float = 0.5
    last_purchase_brand: Optional[int] = None
    # Turtle trip-machine state (see model.CompetitionModel._update_customers).
    trip_state: str = "idle"          # "idle" | "outbound" | "retreating"
    target_brand_id: Optional[int] = None

    def distance_to(self, brand: "Brand") -> float:
        """Euclidean distance (in km) from this customer to a brand outlet."""
        return math.hypot(self.x - brand.x, self.y - brand.y)

    @property
    def has_money(self) -> bool:
        return self.cash > 0


@dataclass
class Brand:
    """A brand agent operating a single outlet (MVP)."""

    brand_id: int
    name: str
    x: float
    y: float
    cash: float = 0.0
    product_price: float = 40_000.0
    quality_score: float = 0.7
    promotion_score: float = 0.0
    brand_strength: float = 0.5
    operating_cost_per_tick: float = 0.0
    entry_tick: int = 0
    active: bool = False

    # Cumulative / per-tick trackers (reset each tick by the model).
    revenue_total: float = 0.0
    revenue_tick: float = 0.0
    customers_served_total: int = 0
    customers_served_tick: int = 0

    def enter(self) -> None:
        """Activate the brand outlet."""
        self.active = True

    def reset_tick(self) -> None:
        """Reset the per-tick counters. Called at the start of every tick."""
        self.revenue_tick = 0.0
        self.customers_served_tick = 0

    def sell(self, amount: float) -> None:
        """Record a sale: receive cash and increase revenue."""
        self.cash += amount
        self.revenue_tick += amount
        self.revenue_total += amount
        self.customers_served_tick += 1
        self.customers_served_total += 1
