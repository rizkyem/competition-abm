"""Core simulation engine for the F&B Competition Agent-Based Model.

The model holds a finite stock of money. Money only moves between agents
(customers <-> brands) through transactions, so the internal money supply is
conserved. Optional ``income_per_tick`` (money entering the economy) and
``operating_cost_per_tick`` (money leaving the economy) are tracked separately
as ``external_money`` so conservation can still be verified.

The customer choice model converts an additive utility into probabilities with
a softmax (logit) rule, so customers do not make fully deterministic choices.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

from agents import Brand, Customer


@dataclass
class BrandConfig:
    """Static configuration for a brand outlet."""

    brand_id: int
    name: str
    x: float
    y: float
    product_price: float = 40_000.0
    quality_score: float = 0.7
    promotion_score: float = 0.0
    brand_strength: float = 0.5
    entry_tick: int = 0
    operating_cost_per_tick: float = 0.0
    initial_cash: float = 0.0


@dataclass
class ModelConfig:
    """All tunable assumptions for a simulation run."""

    seed: int = 42
    ticks: int = 365

    # --- Economy ---------------------------------------------------------
    n_customers: int = 500
    total_money_supply: Optional[float] = None
    avg_cash: float = 2_000_000.0
    cash_cv: float = 0.4
    income_per_tick: float = 0.0

    # --- Geography -------------------------------------------------------
    world_size: float = 10.0  # km x km
    customer_distribution: str = "gaussian"  # "uniform" | "gaussian"
    cluster_centers: list = field(
        default_factory=lambda: [(2.5, 3.8), (7.0, 7.5)]
    )
    cluster_sigma: float = 1.2

    # --- Customer behaviour (population means) --------------------------
    purchase_frequency: float = 0.1
    mean_price_sensitivity: float = 1.0
    mean_distance_sensitivity: float = 1.0
    mean_brand_preference: float = 1.0
    mean_quality_preference: float = 1.0
    mean_promotion_sensitivity: float = 1.0
    mean_loyalty: float = 0.4
    sensitivity_sd: float = 0.3

    # --- Decision model scaling -----------------------------------------
    reference_price: float = 20_000.0
    distance_scale: float = 10.0
    loyalty_scale: float = 1.0
    temperature: float = 0.6

    # --- Customer movement (turtle trip behaviour) ----------------------
    # Each customer alternates between an idle base and a shopping trip:
    # it travels to its chosen brand, buys on arrival, then walks back out
    # to ``settle_distance`` from the brand and rests until its next trip.
    # With ``move_enabled = False`` customers stay static and purchase
    # instantly (the original behaviour).
    move_enabled: bool = True
    travel_speed: float = 0.5        # km travelled per tick
    purchase_radius: float = 0.3     # km - buys when this close to the outlet
    settle_distance: float = 2.0     # km - rests this far from the brand

    # Record per-customer served brand each tick (for animated dashboards).
    record_frames: bool = False

    brands: list = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.brands:
            self.brands = [
                BrandConfig(1, "A", x=2.5, y=3.8, brand_strength=0.8),
                BrandConfig(2, "B", x=7.0, y=7.5, entry_tick=30,
                            brand_strength=0.6),
            ]


class FnBModel:
    """The artificial F&B economy."""

    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        self.cfg = config or ModelConfig()
        self.rng = random.Random(self.cfg.seed)
        self.tick = 0
        self.external_money = 0.0
        self.history: list = []
        self.frames: list = []
        self.customers: list = []
        self.brands: list = []

        self._build_customers()
        self._build_brands()

        self.initial_money_supply = self.total_money

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def _pos(self) -> tuple:
        """Draw a customer position according to the configured distribution."""
        world = self.cfg.world_size
        if self.cfg.customer_distribution == "gaussian" and self.cfg.cluster_centers:
            cx, cy = self.rng.choice(self.cfg.cluster_centers)
            x = min(world, max(0.0, self.rng.gauss(cx, self.cfg.cluster_sigma)))
            y = min(world, max(0.0, self.rng.gauss(cy, self.cfg.cluster_sigma)))
            return x, y
        return self.rng.uniform(0, world), self.rng.uniform(0, world)

    def _draw_cash(self) -> float:
        mean = self.cfg.avg_cash
        return max(0.0, self.rng.gauss(mean, mean * self.cfg.cash_cv))

    def _build_customers(self) -> None:
        cfg = self.cfg
        n = cfg.n_customers
        if cfg.total_money_supply is not None:
            raw = [max(0.01, self.rng.gauss(1.0, cfg.cash_cv)) for _ in range(n)]
            scale = cfg.total_money_supply / sum(raw)
            cash_values = [r * scale for r in raw]
        else:
            cash_values = [self._draw_cash() for _ in range(n)]

        sd = cfg.sensitivity_sd
        for i in range(n):
            x, y = self._pos()
            self.customers.append(
                Customer(
                    customer_id=i,
                    x=x,
                    y=y,
                    cash=cash_values[i],
                    income=cfg.income_per_tick,
                    price_sensitivity=max(0.0, self.rng.gauss(cfg.mean_price_sensitivity, sd)),
                    brand_preference=max(0.0, self.rng.gauss(cfg.mean_brand_preference, sd)),
                    quality_preference=max(0.0, self.rng.gauss(cfg.mean_quality_preference, sd)),
                    promotion_sensitivity=max(0.0, self.rng.gauss(cfg.mean_promotion_sensitivity, sd)),
                    distance_sensitivity=max(0.0, self.rng.gauss(cfg.mean_distance_sensitivity, sd)),
                    purchase_frequency=min(1.0, max(0.0, self.rng.gauss(cfg.purchase_frequency, 0.1))),
                    loyalty=min(1.0, max(0.0, self.rng.gauss(cfg.mean_loyalty, 0.15))),
                    last_purchase_brand=None,
                )
            )

    def _build_brands(self) -> None:
        for bc in self.cfg.brands:
            brand = Brand(
                brand_id=bc.brand_id,
                name=bc.name,
                x=bc.x,
                y=bc.y,
                cash=bc.initial_cash,
                product_price=bc.product_price,
                quality_score=bc.quality_score,
                promotion_score=bc.promotion_score,
                brand_strength=bc.brand_strength,
                operating_cost_per_tick=bc.operating_cost_per_tick,
                entry_tick=bc.entry_tick,
                active=bc.entry_tick <= 0,
            )
            self.brands.append(brand)

    # ------------------------------------------------------------------
    # Decision model
    # ------------------------------------------------------------------
    def utility(self, customer: Customer, brand: Brand) -> float:
        """Additive attractiveness of a brand for a customer (see PRD s.10)."""
        cfg = self.cfg
        u = customer.brand_preference * brand.brand_strength
        u += customer.quality_preference * brand.quality_score
        u += customer.promotion_sensitivity * brand.promotion_score
        u -= customer.price_sensitivity * (brand.product_price / cfg.reference_price)
        u -= customer.distance_sensitivity * (customer.distance_to(brand) / cfg.distance_scale)
        if customer.last_purchase_brand == brand.brand_id:
            u += customer.loyalty * cfg.loyalty_scale
        return u

    def choose_brand(self, customer: Customer, brands: list) -> Optional[Brand]:
        """Pick a brand via softmax over utilities (logit choice)."""
        if not brands:
            return None
        temp = max(self.cfg.temperature, 1e-9)
        utils = [self.utility(customer, b) for b in brands]
        best = max(utils)
        weights = [math.exp((u - best) / temp) for u in utils]
        total = sum(weights)
        r = self.rng.random() * total
        upto = 0.0
        for brand, weight in zip(brands, weights):
            upto += weight
            if r <= upto:
                return brand
        return brands[-1]

    # ------------------------------------------------------------------
    # Customer behaviour - trips and purchases
    # ------------------------------------------------------------------
    def _brand_by_id(self, brand_id: Optional[int]) -> Optional[Brand]:
        for brand in self.brands:
            if brand.brand_id == brand_id:
                return brand
        return None

    def _execute_purchase(self, customer: Customer, brand: Brand) -> None:
        customer.cash -= brand.product_price
        brand.sell(brand.product_price)
        customer.last_purchase_brand = brand.brand_id

    def _step_toward(self, customer: Customer, tx: float, ty: float,
                     speed: float, world: float) -> None:
        """Move one tick toward (tx, ty), never overshooting or leaving the grid."""
        dx, dy = tx - customer.x, ty - customer.y
        dist = math.hypot(dx, dy)
        if dist == 0.0:
            return
        step = min(speed, dist)
        customer.x = min(world, max(0.0, customer.x + step * dx / dist))
        customer.y = min(world, max(0.0, customer.y + step * dy / dist))

    def _step_away(self, customer: Customer, brand: Brand,
                   speed: float, world: float) -> None:
        """Move one tick directly away from ``brand`` (with tiny jitter).

        Retries with a fresh heading if a world boundary blocks the escape,
        so customers never get stuck in a corner.
        """
        for _ in range(4):
            dx, dy = customer.x - brand.x, customer.y - brand.y
            dist = math.hypot(dx, dy)
            if dist == 0.0:
                heading = self.rng.uniform(0.0, 2.0 * math.pi)
            else:
                heading = math.atan2(dy, dx) + self.rng.uniform(-0.4, 0.4)
            nx = min(world, max(0.0, customer.x + speed * math.cos(heading)))
            ny = min(world, max(0.0, customer.y + speed * math.sin(heading)))
            moved_away = (math.hypot(nx - brand.x, ny - brand.y) > dist)
            customer.x, customer.y = nx, ny
            if moved_away:
                return

    def _update_customers(self, active_brands: list) -> tuple:
        """Run the per-customer trip machine. Returns (volume, transactions, purchasers).

        With ``move_enabled = False`` this degrades to the original static
        model: a customer buys instantly with probability ``purchase_frequency``.
        Otherwise a customer cycles idle -> outbound -> buy -> retreating -> idle.
        """
        cfg = self.cfg
        volume = 0.0
        transactions = 0
        purchasers = 0

        if not cfg.move_enabled:
            for customer in self.customers:
                if self.rng.random() >= customer.purchase_frequency:
                    continue
                affordable = [b for b in active_brands
                              if b.product_price <= customer.cash]
                if not affordable:
                    continue
                chosen = self.choose_brand(customer, affordable)
                if chosen is None:
                    continue
                self._execute_purchase(customer, chosen)
                volume += chosen.product_price
                transactions += 1
                purchasers += 1
            return volume, transactions, purchasers

        world = cfg.world_size
        for customer in self.customers:
            state = customer.trip_state
            target = self._brand_by_id(customer.target_brand_id)

            if state == "outbound":
                if (target is None or not target.active
                        or target.product_price > customer.cash):
                    customer.trip_state = "idle"
                    customer.target_brand_id = None
                    continue
                if customer.distance_to(target) > cfg.purchase_radius:
                    self._step_toward(customer, target.x, target.y,
                                      cfg.travel_speed, world)
                if customer.distance_to(target) <= cfg.purchase_radius:
                    self._execute_purchase(customer, target)
                    volume += target.product_price
                    transactions += 1
                    purchasers += 1
                    customer.trip_state = "retreating"
                continue

            if state == "retreating":
                if target is None or customer.distance_to(target) >= cfg.settle_distance:
                    customer.trip_state = "idle"
                    customer.target_brand_id = None
                    continue
                self._step_away(customer, target, cfg.travel_speed, world)
                if customer.distance_to(target) >= cfg.settle_distance:
                    customer.trip_state = "idle"
                    customer.target_brand_id = None
                continue

            # Idle: decide whether to start a shopping trip.
            if self.rng.random() < customer.purchase_frequency:
                affordable = [b for b in active_brands
                              if b.product_price <= customer.cash]
                if not affordable:
                    continue
                chosen = self.choose_brand(customer, affordable)
                if chosen is None:
                    continue
                customer.target_brand_id = chosen.brand_id
                customer.trip_state = "outbound"

        return volume, transactions, purchasers

    # ------------------------------------------------------------------
    # Simulation step
    # ------------------------------------------------------------------
    def step(self) -> dict:
        """Advance the simulation by one tick and record metrics."""
        self.tick += 1

        # Brand entry
        for brand in self.brands:
            if not brand.active and self.tick >= brand.entry_tick:
                brand.enter()

        active_brands = [b for b in self.brands if b.active]
        for brand in self.brands:
            brand.reset_tick()

        # External income enters the economy before decisions.
        if self.cfg.income_per_tick:
            for c in self.customers:
                c.cash += c.income
            self.external_money -= self.cfg.income_per_tick * len(self.customers)

        transaction_volume, transactions, purchasers = self._update_customers(
            active_brands)

        # Operating costs leave the internal economy.
        for brand in self.brands:
            if brand.active and brand.operating_cost_per_tick:
                brand.cash -= brand.operating_cost_per_tick
                self.external_money += brand.operating_cost_per_tick

        record = self._record(transaction_volume, transactions, purchasers)
        if self.cfg.record_frames:
            self.frames.append([c.last_purchase_brand for c in self.customers])
        self.history.append(record)
        return record

    def run(self, ticks: Optional[int] = None) -> list:
        ticks = self.cfg.ticks if ticks is None else ticks
        for _ in range(ticks):
            self.step()
        return self.history

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    @property
    def total_money(self) -> float:
        """Internal money = customers + brands. Excludes external leakage."""
        return sum(c.cash for c in self.customers) + sum(b.cash for b in self.brands)

    def _record(self, volume: float, transactions: int, purchasers: int) -> dict:
        customer_cash = sum(c.cash for c in self.customers)
        brand_cash = sum(b.cash for b in self.brands)
        cumulative_revenue = sum(b.revenue_total for b in self.brands)
        money = customer_cash + brand_cash

        rec = {
            "tick": self.tick,
            "transaction_volume": volume,
            "transactions": transactions,
            "purchasers": purchasers,
            "total_revenue": cumulative_revenue,
            "customer_cash": customer_cash,
            "brand_cash": brand_cash,
            "external_money": self.external_money,
            "total_money": money,
            "avg_customer_cash": customer_cash / len(self.customers) if self.customers else 0.0,
            "money_velocity": volume / money if money else 0.0,
        }
        for brand in self.brands:
            name = brand.name
            rec[f"revenue_{name}"] = brand.revenue_tick
            rec[f"cum_revenue_{name}"] = brand.revenue_total
            rec[f"cash_{name}"] = brand.cash
            rec[f"customers_{name}"] = brand.customers_served_tick
            rec[f"share_{name}"] = volume and brand.revenue_tick / volume or 0.0
            rec[f"cum_share_{name}"] = (
                cumulative_revenue and brand.revenue_total / cumulative_revenue or 0.0
            )
        return rec

    def summary(self) -> dict:
        """Final-period snapshot plus cumulative outcomes."""
        if not self.history:
            self.run()
        last = self.history[-1]
        out = {
            "ticks": self.tick,
            "total_money_supply": self.initial_money_supply,
            "ending_total_money": last["total_money"],
            "external_money": self.external_money,
            "total_revenue": last["total_revenue"],
            "total_transactions": sum(h["transactions"] for h in self.history),
            "total_transaction_volume": sum(h["transaction_volume"] for h in self.history),
        }
        out["brands"] = {
            b.name: {
                "revenue_total": b.revenue_total,
                "revenue_share": (b.revenue_total / last["total_revenue"]
                                  if last["total_revenue"] else 0.0),
                "cash": b.cash,
                "customers_served": b.customers_served_total,
                "active": b.active,
            }
            for b in self.brands
        }
        return out
