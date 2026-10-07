# Competition Agent-Based Model

A Python Agent-Based Model that simulates competition between brands in a
finite-money artificial economy. Individual customers decide where to spend,
money changes hands through transactions, and aggregate outcomes (revenue,
market share, cash, geography) emerge from those decisions.

Implements the MVP and core experiments described in `Competition Agent-Based Model PRD.md`.

## Highlights

- **Customer agents** with cash, price/distance sensitivity, quality and
  promotion preference, purchase frequency and loyalty.
- **Mobile customers (turtle trips)** — customers alternate between resting and
  a shopping trip: they travel to their chosen brand, buy on arrival (within
  `purchase_radius`), then walk back out to `settle_distance` and rest before
  the next trip. Configurable via `move_enabled`, `travel_speed`,
  `purchase_radius` and `settle_distance`; set `move_enabled=False` for the
  original static, instant-purchase behaviour.
- **Brand agents** with location, price, quality, promotion, brand strength and
  a configurable market-entry tick.
- **Finite money economy** — money only moves between agents, so the internal
  money supply is conserved (verified by a test).
- **Geographic utility model** — brand attractiveness = preference + quality +
  promotion − price cost − distance cost, converted to choice probabilities
  with a softmax (logit) rule.
- **Reproducible** — same parameters + seed produce identical results.
- **Zero-dependency core** — the engine runs on a stock Python 3 installation.

## Requirements

- Python 3.9+ (tested on 3.14). The core needs **no third-party packages**.

Optional extras (charts / dashboard):

```bash
pip install -r requirements.txt
```

## Running the simulation

```bash
# Default scenario (500 customers, 365 days, Brand B enters on day 30)
python3 simulation.py

# Print a rough map of the market
python3 simulation.py --map

# Custom assumptions
python3 simulation.py --ticks 200 --customers 800 --seed 7 \
    --price-b 30000 --entry-tick 60 --loyalty 0.6

# Fixed total money supply instead of average cash
python3 simulation.py --money-supply 100000000 --map

# Save charts (needs matplotlib)
python3 simulation.py --plot
```

Results are written to `data/` as CSV. The summary printed to the console
includes revenue, market share, cash balances, transaction volume and a
money-conservation check.

## Experiments (PRD section 21)

```bash
python3 simulation.py --experiment entry       # Brand B entry timing
python3 simulation.py --experiment location    # B near vs far from A / customers
python3 simulation.py --experiment price       # B undercuts A
python3 simulation.py --experiment promotion   # B promotes
python3 simulation.py --experiment loyalty     # customer loyalty
python3 simulation.py --experiment geography   # customer concentration
python3 simulation.py --experiment all         # everything
```

Each experiment writes per-scenario histories plus a
`data/comparison_<experiment>.csv` summary table.

## Interactive dashboard (browser, NetLogo-style)

A virtual environment `.venv` with Streamlit already created. Start the app:

```bash
.venv/bin/streamlit run app.py
```

Your browser opens at `http://localhost:8501`. The model **steps tick-by-tick
in the browser**, so you can change assumptions *during* a run:

- **Starts with Brand A alone at day 0.** Use the **Market entry** panel to
  **Add Brand** at any day. A new competitor (B, C, D, ...) starts on the next
  tick and immediately changes how money flows between customers and brands.
  Optionally tick *Schedule Brand B entry at setup* to have B enter on a fixed
  day instead.
- **Brand to adjust live** - pick any brand and change its price, promotion and
  location on the fly.
- **Global knobs** - decision randomness, distance sensitivity, loyalty. These
  apply on the next tick.
- **Turtle movement** (sidebar *setup*) - toggle the travel-to-buy trip cycle
  and tune travel speed, buy radius and rest distance.
- **Play / Pause / Step / Reset**, speed slider and a day progress bar.
- Live KPIs plus geographic, market-share, revenue, **money-distribution** and
  volume charts (watch who accumulates cash after each entry).
- **Sidebar** = setup values (economy, customer population, Brand A, optional
  scheduled B). Click **Build & Run** to apply them and restart.



To set it up on another machine:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```


## Tests

```bash
python3 -m unittest discover -s tests -v
```

The tests encode the PRD validation logic: money conservation, reproducibility,
cheaper brands gaining share, distance sensitivity concentrating customers,
loyalty blocking entrants, empty-location underperformance, money transfer on
purchase and promotions helping entrants. They also cover the turtle movement:
customers relocate over time, stay inside the world grid, remain static when
`move_enabled=False`, and complete the idle → outbound → buy → retreat cycle.

## Project structure

```text
agents.py        Customer and Brand agent classes
model.py         Economy engine: setup, decisions, transactions, metrics
simulation.py    CLI runner + predefined experiments + CSV export
viz.py           Optional matplotlib charts (simulation.py --plot)
app.py           Optional Streamlit dashboard
tests/           Validation tests (unittest)
data/            Generated CSV output (created at runtime)
```

## Model notes

- `1 tick = 1 day`. Revenue is a **flow**; cash balance is a **stock**.
- Utility factors can be negative (e.g. distance cost); the softmax uses
  utility *differences*, so absolute scale does not matter.
- By default there is no money creation or destruction and no operating costs,
  so `customer cash + brand cash` is constant. Optional `income_per_tick` and
  `operating_cost_per_tick` (both default `0`) are tracked as `external_money`.
- The model is an artificial economy for exploring competition, not a forecast
  of real-world performance.
