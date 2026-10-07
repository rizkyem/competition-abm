"""Command-line runner for the Competition Agent-Based Model.

Examples
--------
Run a single default simulation and print a summary::

    python3 simulation.py

Run a custom scenario::

    python3 simulation.py --ticks 200 --customers 800 --price-b 30000 --plot

Run one of the PRD experiments (entry, location, price, promotion, loyalty,
geography)::

    python3 simulation.py --experiment location --plot

Run every experiment::

    python3 simulation.py --experiment all
"""

from __future__ import annotations

import argparse
import csv
import os
from typing import Optional

from model import BrandConfig, CompetitionModel, ModelConfig

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def rp(value: float) -> str:
    """Format a number as an Indonesian Rupiah string."""
    return f"Rp{value:,.0f}"


def scenario_config(**overrides) -> ModelConfig:
    """Build a ModelConfig, allowing brand overrides through ``overrides``."""
    brand_overrides = overrides.pop("brands", None)
    cfg = ModelConfig(**overrides)
    if brand_overrides:
        cfg.brands = brand_overrides
    return cfg


def default_brands(b_x: float = 7.0, b_y: float = 7.5, price_b: float = 40_000.0,
                   entry_tick: int = 30, promo_b: float = 0.0,
                   strength_b: float = 0.6) -> list:
    return [
        BrandConfig(1, "A", x=2.5, y=3.8, brand_strength=0.8, product_price=40_000.0),
        BrandConfig(2, "B", x=b_x, y=b_y, brand_strength=strength_b,
                    product_price=price_b, entry_tick=entry_tick,
                    promotion_score=promo_b),
    ]


def save_csv(rows: list, path: str) -> None:
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fields = list(rows[0].keys())
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(title: str, model: CompetitionModel) -> None:
    s = model.summary()
    print(f"\n=== {title} ===")
    print(f"Ticks simulated:        {s['ticks']}")
    print(f"Initial money supply:   {rp(s['total_money_supply'])}")
    print(f"Ending internal money:  {rp(s['ending_total_money'])}")
    print(f"External money (net):   {rp(s['external_money'])}")
    print(f"Total revenue:          {rp(s['total_revenue'])}")
    print(f"Total transactions:     {s['total_transactions']:,}")
    print(f"Total transaction vol:  {rp(s['total_transaction_volume'])}")
    print("-" * 60)
    print(f"{'Brand':<6}{'Revenue':>18}{'Rev share':>12}{'Cash':>18}{'Served':>10}")
    for name, d in s["brands"].items():
        print(f"{name:<6}{rp(d['revenue_total']):>18}{d['revenue_share']*100:>11.1f}%"
              f"{rp(d['cash']):>18}{d['customers_served']:>10,}")
    conserved = abs(s["ending_total_money"] - s["total_money_supply"]) < 1.0
    print("-" * 60)
    print(f"Money conserved:        {'YES' if conserved else 'NO'}")


def ascii_map(model: CompetitionModel, size: int = 20) -> str:
    """Render a rough ASCII map of customers and brand outlets."""
    grid = [["." for _ in range(size)] for _ in range(size)]
    world = model.cfg.world_size

    def cell(x, y):
        col = min(size - 1, int(x / world * size))
        row = min(size - 1, int(y / world * size))
        return row, col

    for c in model.customers:
        r, col = cell(c.x, c.y)
        if grid[r][col] == ".":
            grid[r][col] = "o"
    for b in model.brands:
        if b.active:
            r, col = cell(b.x, b.y)
            grid[r][col] = b.name
    return "\n".join("".join(row) for row in grid)


# ----------------------------------------------------------------------
# Experiments (PRD section 21)
# ----------------------------------------------------------------------
def experiment_entry() -> list:
    return [
        ("no_entry", scenario_config(brands=default_brands(entry_tick=10_000))),
        ("B_enters_t30", scenario_config(brands=default_brands(entry_tick=30))),
        ("B_enters_t0", scenario_config(brands=default_brands(entry_tick=0))),
    ]


def experiment_location() -> list:
    single_cluster = [(2.5, 3.8)]
    return [
        ("near", scenario_config(cluster_centers=single_cluster,
                                 brands=default_brands(b_x=2.9, b_y=3.4))),
        ("mid", scenario_config(cluster_centers=single_cluster,
                                brands=default_brands(b_x=4.5, b_y=4.5))),
        ("far", scenario_config(cluster_centers=single_cluster,
                                brands=default_brands(b_x=7.5, b_y=7.5))),
    ]


def experiment_price() -> list:
    return [
        ("same_price", scenario_config(brands=default_brands(price_b=40_000))),
        ("B_cheaper", scenario_config(brands=default_brands(price_b=30_000))),
        ("B_much_cheaper", scenario_config(brands=default_brands(price_b=25_000))),
    ]


def experiment_promotion() -> list:
    return [
        ("no_promo", scenario_config(brands=default_brands(promo_b=0.0))),
        ("moderate_promo", scenario_config(brands=default_brands(promo_b=0.4))),
        ("aggressive_promo", scenario_config(brands=default_brands(promo_b=0.9))),
    ]


def experiment_loyalty() -> list:
    return [
        ("low_loyalty", scenario_config(mean_loyalty=0.1, brands=default_brands())),
        ("medium_loyalty", scenario_config(mean_loyalty=0.4, brands=default_brands())),
        ("high_loyalty", scenario_config(mean_loyalty=0.8, brands=default_brands())),
    ]


def experiment_geography() -> list:
    return [
        ("uniform_customers", scenario_config(customer_distribution="uniform",
                                              brands=default_brands(b_x=7.5, b_y=7.5))),
        ("concentrated_customers", scenario_config(
            customer_distribution="gaussian", cluster_centers=[(2.5, 3.8)],
            brands=default_brands(b_x=7.5, b_y=7.5))),
        ("dispersed_clusters", scenario_config(
            customer_distribution="gaussian",
            cluster_centers=[(2.5, 3.8), (7.0, 7.5)], cluster_sigma=1.8,
            brands=default_brands(b_x=7.5, b_y=7.5))),
    ]


EXPERIMENTS = {
    "entry": experiment_entry,
    "location": experiment_location,
    "price": experiment_price,
    "promotion": experiment_promotion,
    "loyalty": experiment_loyalty,
    "geography": experiment_geography,
}


def run_experiment(name: str, make_plots: bool) -> None:
    scenarios = EXPERIMENTS[name]()
    rows = []
    print(f"\n########## Experiment: {name} ##########")
    for label, cfg in scenarios:
        model = CompetitionModel(cfg)
        model.run()
        print_summary(f"{name} / {label}", model)
        save_csv(model.history, os.path.join(DATA_DIR, name, f"{label}.csv"))

        s = model.summary()
        row = {"scenario": label, "total_revenue": round(s["total_revenue"], 2),
               "total_transactions": s["total_transactions"],
               "ending_internal_money": round(s["ending_total_money"], 2)}
        for brand_name, bd in s["brands"].items():
            row[f"revenue_share_{brand_name}"] = round(bd["revenue_share"], 4)
            row[f"cash_{brand_name}"] = round(bd["cash"], 2)
            row[f"served_{brand_name}"] = bd["customers_served"]
        rows.append(row)

        if make_plots:
            try:
                import viz

                viz.plot_all(model, os.path.join(DATA_DIR, name, label))
            except ImportError:
                print("  (matplotlib not installed - skipping plots)")

    save_csv(rows, os.path.join(DATA_DIR, f"comparison_{name}.csv"))
    print(f"\nComparison saved to {os.path.join(DATA_DIR, f'comparison_{name}.csv')}")


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Competition Agent-Based Model")
    p.add_argument("--experiment", choices=list(EXPERIMENTS) + ["all"],
                   help="run a predefined PRD experiment (or 'all')")
    p.add_argument("--ticks", type=int, default=365)
    p.add_argument("--customers", type=int, default=500)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--cash", type=float, default=2_000_000.0,
                   help="average customer starting cash (Rp)")
    p.add_argument("--money-supply", type=float, default=None,
                   help="fix total money supply (Rp); overrides average cash")
    p.add_argument("--entry-tick", type=int, default=30,
                   help="tick at which Brand B enters")
    p.add_argument("--b-x", type=float, default=7.0)
    p.add_argument("--b-y", type=float, default=7.5)
    p.add_argument("--price-b", type=float, default=40_000.0)
    p.add_argument("--promo-b", type=float, default=0.0)
    p.add_argument("--loyalty", type=float, default=0.4)
    p.add_argument("--temperature", type=float, default=0.6)
    p.add_argument("--distribution", choices=["uniform", "gaussian"],
                   default="gaussian")
    p.add_argument("--plot", action="store_true", help="save matplotlib charts")
    p.add_argument("--map", action="store_true", help="print an ASCII map")
    return p


def main() -> None:
    args = build_parser().parse_args()
    os.makedirs(DATA_DIR, exist_ok=True)

    if args.experiment:
        names = list(EXPERIMENTS) if args.experiment == "all" else [args.experiment]
        for name in names:
            run_experiment(name, args.plot)
        return

    cfg = scenario_config(
        seed=args.seed,
        ticks=args.ticks,
        n_customers=args.customers,
        avg_cash=args.cash,
        total_money_supply=args.money_supply,
        mean_loyalty=args.loyalty,
        temperature=args.temperature,
        customer_distribution=args.distribution,
        brands=default_brands(b_x=args.b_x, b_y=args.b_y, price_b=args.price_b,
                              entry_tick=args.entry_tick, promo_b=args.promo_b),
    )
    model = CompetitionModel(cfg)
    model.run()
    print_summary("Custom scenario", model)

    if args.map:
        print("\nGeographic map (o = customer, A/B = outlet):\n")
        print(ascii_map(model))

    path = os.path.join(DATA_DIR, "custom_history.csv")
    save_csv(model.history, path)
    print(f"\nHistory saved to {path}")

    if args.plot:
        try:
            import viz

            out = viz.plot_all(model, os.path.join(DATA_DIR, "custom"))
            print(f"Charts saved to {out}")
        except ImportError:
            print("(matplotlib not installed - run: pip install matplotlib)")


if __name__ == "__main__":
    main()
