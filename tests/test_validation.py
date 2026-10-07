"""Logic-validation tests for the F&B Competition ABM (PRD section 30).

Run with::

    python3 -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import BrandConfig, FnBModel, ModelConfig  # noqa: E402


def base_brands(b_x=7.0, b_y=7.5, price_b=40_000.0, promo_b=0.0, entry_tick=30):
    return [
        BrandConfig(1, "A", x=2.5, y=3.8, brand_strength=0.8),
        BrandConfig(2, "B", x=b_x, y=b_y, brand_strength=0.6,
                    product_price=price_b, promotion_score=promo_b,
                    entry_tick=entry_tick),
    ]


def run_model(**kwargs):
    kwargs.setdefault("seed", 123)
    kwargs.setdefault("ticks", 365)
    kwargs.setdefault("n_customers", 500)
    model = FnBModel(ModelConfig(**kwargs))
    model.run()
    return model


class ValidationTests(unittest.TestCase):
    def test_money_is_conserved(self):
        """Test 5: total money before == total money after (no income/costs)."""
        model = run_model(brands=base_brands())
        self.assertAlmostEqual(model.initial_money_supply,
                               model.total_money, delta=1.0)
        self.assertEqual(model.external_money, 0.0)

    def test_reproducible_with_seed(self):
        """Same config + seed => identical results (PRD s.29)."""
        a = run_model(brands=base_brands()).summary()
        b = run_model(brands=base_brands()).summary()
        self.assertEqual(a["total_revenue"], b["total_revenue"])
        self.assertEqual(a["brands"]["B"]["customers_served"],
                         b["brands"]["B"]["customers_served"])

    def test_cheaper_brand_wins_more_share(self):
        """Test 1: a significantly cheaper entrant should gain share."""
        same = run_model(brands=base_brands(price_b=40_000)).summary()
        cheap = run_model(brands=base_brands(price_b=25_000)).summary()
        self.assertGreater(cheap["brands"]["B"]["revenue_share"],
                           same["brands"]["B"]["revenue_share"])

    def test_distance_sensitivity_concentrates_customers(self):
        """Test 2: higher distance sensitivity => shorter trips on average."""
        brands = base_brands()
        low = run_model(brands=brands, mean_distance_sensitivity=0.2)
        high = run_model(brands=base_brands(), mean_distance_sensitivity=3.0)

        def avg_trip(model):
            dists = []
            for c in model.customers:
                if c.last_purchase_brand is None:
                    continue
                for b in model.brands:
                    if b.brand_id == c.last_purchase_brand:
                        dists.append(c.distance_to(b))
            return sum(dists) / len(dists) if dists else 0.0

        self.assertLess(avg_trip(high), avg_trip(low))

    def test_loyalty_hurts_entrant(self):
        """Test 3: strong loyalty should make it harder for B to acquire."""
        low = run_model(brands=base_brands(), mean_loyalty=0.05).summary()
        high = run_model(brands=base_brands(), mean_loyalty=0.9).summary()
        self.assertGreater(low["brands"]["B"]["revenue_share"],
                           high["brands"]["B"]["revenue_share"])

    def test_empty_location_earns_less(self):
        """Test 4: an outlet far from customers earns less than a nearby one."""
        cluster = [(2.5, 3.8)]
        near = run_model(cluster_centers=cluster,
                         brands=base_brands(b_x=2.9, b_y=3.4)).summary()
        empty = run_model(cluster_centers=cluster,
                          brands=base_brands(b_x=8.5, b_y=8.5)).summary()
        self.assertGreater(near["brands"]["B"]["revenue_total"],
                           empty["brands"]["B"]["revenue_total"])

    def test_transaction_transfers_money(self):
        """A purchase should decrease customer cash and increase brand cash."""
        model = FnBModel(ModelConfig(seed=1, ticks=1, n_customers=50,
                                     move_enabled=False,
                                     brands=base_brands(entry_tick=0)))
        before = sum(c.cash for c in model.customers)
        model.step()
        after = sum(c.cash for c in model.customers)
        brand_cash = sum(b.cash for b in model.brands)
        self.assertLess(after, before)
        self.assertAlmostEqual(before - after, brand_cash, delta=1e-6)

    def test_promotion_increases_entrant_share(self):
        """PRD experiment 4: promotions should help the entrant."""
        none = run_model(brands=base_brands(promo_b=0.0)).summary()
        promo = run_model(brands=base_brands(promo_b=0.9)).summary()
        self.assertGreater(promo["brands"]["B"]["revenue_share"],
                           none["brands"]["B"]["revenue_share"])

    def test_customers_move_when_satisfied(self):
        """Satisfied customers relocate over time (turtle movement)."""
        model = FnBModel(ModelConfig(seed=123, ticks=365, n_customers=500,
                                     move_enabled=True,
                                     brands=base_brands(entry_tick=0)))
        start = [(c.x, c.y) for c in model.customers]
        model.run()
        self.assertTrue(
            any(c.x != x or c.y != y
                for c, (x, y) in zip(model.customers, start)))

    def test_movement_stays_in_bounds(self):
        """Customers never leave the world grid while moving."""
        model = run_model(brands=base_brands(entry_tick=0), move_enabled=True)
        world = model.cfg.world_size
        for c in model.customers:
            self.assertGreaterEqual(c.x, 0.0)
            self.assertLessEqual(c.x, world)
            self.assertGreaterEqual(c.y, 0.0)
            self.assertLessEqual(c.y, world)

    def test_movement_disabled_keeps_customers_static(self):
        """move_enabled=False reproduces the original static customers."""
        model = FnBModel(ModelConfig(seed=123, ticks=365, n_customers=500,
                                     move_enabled=False,
                                     brands=base_brands(entry_tick=0)))
        start = [(c.x, c.y) for c in model.customers]
        model.run()
        for c, (x, y) in zip(model.customers, start):
            self.assertEqual((c.x, c.y), (x, y))

    def test_trip_cycle_travels_buys_and_retreats(self):
        """A customer should travel to the brand, buy, then move away."""
        brands = [BrandConfig(1, "A", x=5.0, y=5.0, brand_strength=0.8,
                              entry_tick=0)]
        model = FnBModel(ModelConfig(
            seed=7, ticks=80, n_customers=1, move_enabled=True,
            travel_speed=0.5, purchase_radius=0.3, settle_distance=2.0,
            purchase_frequency=1.0, brands=brands))
        c = model.customers[0]
        c.x, c.y = 1.0, 5.0
        bought = False
        for _ in range(80):
            model.step()
            if c.last_purchase_brand is not None:
                bought = True
        self.assertTrue(bought, "customer never completed a purchase")
        # After buying, the customer never rests farther than settle_distance.
        self.assertLessEqual(c.distance_to(model.brands[0]),
                             model.cfg.settle_distance + model.cfg.travel_speed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
