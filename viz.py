"""Static charts for the F&B Competition ABM (optional - requires matplotlib).

``simulation.py --plot`` calls :func:`plot_all`. If matplotlib is not
installed this module raises ``ImportError`` on import, which the runner
catches gracefully.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")  # headless / file output
import matplotlib.pyplot as plt  # noqa: E402

BRAND_COLORS = {"A": "#1f77b4", "B": "#d62728", "C": "#2ca02c",
                "D": "#9467bd", "E": "#ff7f0e"}


def _color(name: str) -> str:
    return BRAND_COLORS.get(name, "#7f7f7f")


def _ticks(history: list) -> list:
    return [h["tick"] for h in history]


def plot_market_share(history: list, names: list, out: str) -> None:
    plt.figure(figsize=(9, 5))
    for name in names:
        key = f"share_{name}"
        # 7-tick moving average to smooth daily noise
        series = [h[key] * 100 for h in history]
        smoothed = _rolling_mean(series, 7)
        plt.plot(_ticks(history), smoothed, label=f"Brand {name}", color=_color(name))
    plt.title("Revenue Market Share Over Time")
    plt.xlabel("Tick (days)")
    plt.ylabel("Market share (%)")
    plt.ylim(0, 100)
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()


def plot_revenue(history: list, names: list, out: str) -> None:
    plt.figure(figsize=(9, 5))
    for name in names:
        key = f"cum_revenue_{name}"
        plt.plot(_ticks(history), [h[key] for h in history],
                 label=f"Brand {name}", color=_color(name))
    plt.title("Cumulative Revenue by Brand")
    plt.xlabel("Tick (days)")
    plt.ylabel("Revenue (Rp)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()


def plot_money_distribution(history: list, names: list, out: str) -> None:
    plt.figure(figsize=(9, 5))
    plt.plot(_ticks(history), [h["customer_cash"] for h in history],
             label="Customers", color="#555555")
    for name in names:
        key = f"cash_{name}"
        plt.plot(_ticks(history), [h[key] for h in history],
                 label=f"Brand {name}", color=_color(name))
    plt.title("Money Distribution (Cash Balances)")
    plt.xlabel("Tick (days)")
    plt.ylabel("Cash (Rp)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()


def plot_transaction_volume(history: list, out: str) -> None:
    plt.figure(figsize=(9, 5))
    plt.plot(_ticks(history), [h["transaction_volume"] for h in history],
             color="#1f77b4")
    plt.title("Transaction Volume per Tick")
    plt.xlabel("Tick (days)")
    plt.ylabel("Value transacted (Rp)")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()


def plot_geography(model, out: str) -> None:
    plt.figure(figsize=(7, 7))
    groups = {}
    for c in model.customers:
        groups.setdefault(c.last_purchase_brand, []).append(c)
    for brand_id, customers in groups.items():
        color = "#999999" if brand_id is None else _color(
            _name_of(model, brand_id))
        plt.scatter([c.x for c in customers], [c.y for c in customers],
                    s=12, alpha=0.6, color=color,
                    label="unserved" if brand_id is None
                    else f"served by {_name_of(model, brand_id)}")
    for b in model.brands:
        if b.active:
            plt.scatter([b.x], [b.y], marker="*", s=420,
                        color=_color(b.name), edgecolor="black", zorder=5)
            plt.annotate(f"Brand {b.name}", (b.x, b.y),
                         textcoords="offset points", xytext=(8, 8))
    world = getattr(model.cfg, "world_size", 10.0)
    plt.xlim(0, world)
    plt.ylim(0, world)
    plt.title("Geographic Market: Customers by Last Brand Purchased")
    plt.xlabel("x (km)")
    plt.ylabel("y (km)")
    plt.legend(loc="upper left", fontsize=8)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()


def _name_of(model, brand_id: int) -> str:
    for b in model.brands:
        if b.brand_id == brand_id:
            return b.name
    return str(brand_id)


def _rolling_mean(values: list, window: int) -> list:
    out = []
    acc = 0.0
    for i, v in enumerate(values):
        acc += v
        if i >= window:
            acc -= values[i - window]
        out.append(acc / min(i + 1, window))
    return out


def plot_all(model, prefix: str) -> str:
    """Generate every chart for ``model`` under ``prefix_*.png``."""
    os.makedirs(os.path.dirname(prefix) or ".", exist_ok=True)
    names = [b.name for b in model.brands]
    history = model.history
    plot_market_share(history, names, f"{prefix}_market_share.png")
    plot_revenue(history, names, f"{prefix}_revenue.png")
    plot_money_distribution(history, names, f"{prefix}_money.png")
    plot_transaction_volume(history, f"{prefix}_transactions.png")
    plot_geography(model, f"{prefix}_geography.png")
    return os.path.dirname(prefix) or "."
