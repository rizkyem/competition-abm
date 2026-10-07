# MODEL.md — F&B Competition Agent-Based Model

This document describes the mathematical model implemented in the code: the
agents, the state variables, the formulas, the tick algorithm, the parameters
and the metrics. Every formula lists where it lives in the source.

- Engine: [`model.py`](model.py)
- Agents: [`agents.py`](agents.py)
- Tunable parameters: `ModelConfig` ([`model.py:41`](model.py))
- Conceptual background: PRD section 10

---

## 1. Overview

An **artificial economy** with a **finite stock of money**. The only two agent
types are **Customers** and **Brands**. Each tick (= 1 day), every customer may
buy from one affordable brand. A purchase **transfers** money from the customer
to the brand — money is not created or destroyed, so the internal money supply
is conserved.

```
Customer decides → utility of each brand → softmax probability → pick brand
→ pay price (cash transfer) → brand revenue/cash rises → metrics recorded
```

---

## 2. Agents and state variables

### 2.1 Customer — `agents.py:22`

| Symbol | Attribute | Meaning |
|---|---|---|
| `x, y` | `x`, `y` | Location on a 10×10 km grid |
| `cash` | `cash_balance` | Money held (Rp) |
| `income` | `income` | Cash received per tick (external, default 0) |
| `P` | `price_sensitivity` | Sensitivity to price |
| `⍺` | `brand_preference` | Weight on brand strength |
| `Q` | `quality_preference` | Weight on quality |
| `M` | `promotion_sensitivity` | Weight on promotion |
| `D` | `distance_sensitivity` | Sensitivity to travel distance |
| `f` | `purchase_frequency` | Probability of shopping on a given day |
| `L` | `loyalty` | Strength of repeat-purchase habit |
| `last` | `last_purchase_brand` | Brand id bought last tick (for loyalty) |

### 2.2 Brand — `agents.py:52`

| Symbol | Attribute | Meaning |
|---|---|---|
| `x, y` | `x`, `y` | Outlet location (fixed unless changed live) |
| `cash` | `cash_balance` | Money accumulated (Rp) |
| `p` | `product_price` | Price per purchase (Rp) |
| `q` | `quality_score` | Quality, ~0–1 |
| `m` | `promotion_score` | Promotion intensity, ~0–1 |
| `S` | `brand_strength` | Brand equity / awareness |
| `entry_tick` | `entry_tick` | Day the outlet becomes active |
| `revenue_tick` / `revenue_total` | | Revenue this tick / cumulative (flow) |
| `customers_served_tick` / `_total` | | Purchases this tick / cumulative |

Revenue is a **flow**; cash is a **stock** (`agents.py:83` `sell`: `cash += price`,
`revenue += price`).

---

## 3. Geography — distance

Customer *c* to brand *b* (Euclidean, km) — `agents.py:42`:

```
dist(c, b) = sqrt( (x_c − x_b)² + (y_c − y_b)² )
```

---

## 4. Utility (brand attractiveness) — `model.py:190`

For a customer *c* and a brand *b*:

```
U(c, b) =  ⍺ · S_b                       brand preference × brand strength
        +  Q · q_b                        quality preference × quality
        +  M · m_b                        promotion sensitivity × promotion
        −  P · (p_b / PRICE_REF)          price cost
        −  D · (dist(c,b) / DIST_REF)     distance cost
        +  [ last_c = b ] · L · LOYALTY   loyalty bonus (only for last brand)
```

`PRICE_REF = 20,000`, `DIST_REF = 10`, `LOYALTY = 1.0` are scaling constants
(`ModelConfig.reference_price`, `distance_scale`, `loyalty_scale`). Absolute
utility does not matter — only **differences between brands**, because of the
softmax below.

---

## 5. Choice probability — softmax / logit — `model.py:202`

Customers are **not** fully deterministic. Utilities become probabilities:

```
Pr(c picks b) = exp( U(c,b) / τ ) / Σ_k exp( U(c,k) / τ )
```

- `τ` = `temperature` (decision randomness).
- Larger τ → choices approach uniform (more random).
- Smaller τ → choices approach “always pick the highest utility”.
- Implemented numerically stable (subtract the max utility before `exp`), then
  the winner is **sampled** with `random()`.

Only **affordable** brands (`p_b ≤ cash_c`) are offered to the softmax
(`model.py:281`, `model.py:329`).

---

## 6. Purchase and money transfer — `model.py` `_execute_purchase`

The transaction itself is a simple money transfer, applied either on arrival
(trip mode, Section 6.1) or instantly when `move_enabled = False`:

```
for each customer c:
    if random() < f_c:                     # does c shop today? (purchase_frequency)
        affordable = { b active : p_b ≤ cash_c }
        if affordable is empty: skip
        b* = choose_brand(c, affordable)   # softmax sample
        cash_c      -= p_b*                # customer pays
        cash_b*     += p_b*                # brand receives (sell)
        last_c       = b*                  # remember for loyalty
        transaction_volume += p_b*
```

At most **one purchase per customer per tick**.

---

## 6.1 Customer movement (turtle trip cycle) — `model.py` `_update_customers`

Customers are not static. Each customer is a small state machine that
alternates between resting and a shopping trip:

| State | Behaviour |
|---|---|
| `idle` | Roll `purchase_frequency`; on success choose an affordable brand (softmax) and switch to `outbound`. |
| `outbound` | Step `travel_speed` km toward the chosen brand each tick. On reaching `purchase_radius` km, **buy**, then switch to `retreating`. |
| `retreating` | Step `travel_speed` km directly away from the brand until `settle_distance` km away, then switch back to `idle`. |

```
outbound:    move toward brand; if dist <= purchase_radius -> buy -> retreating
retreating:  move away from brand; if dist >= settle_distance -> idle
idle:        if rand() < purchase_frequency -> outbound
```

* A trip aborts (back to `idle`) if the target becomes inactive or unaffordable.
* The purchase happens only **on arrival**, so money still only changes hands
  through transactions and is conserved.
* Positions are clamped to `[0, world_size]`; `_step_away` retries with a fresh
  heading if a boundary blocks the escape, so customers never get stuck.
* With `move_enabled = False` the trip machine is off: customers stay put and
  purchase instantly (the original one-tick behaviour).

Movement does not move money, so conservation is unaffected.

---

## 7. Tick algorithm — `model.py` (`step`)

```
1. tick += 1
2. Activate any brand whose entry_tick ≤ tick          (market entry)
3. Reset per-tick brand counters (revenue_tick, customers_served_tick)
4. If income_per_tick > 0: add income to customers     (external money in)
5. For each customer: run the trip machine (Section 6.1)  (movement + transactions)
6. Apply operating_cost_per_tick to active brands      (external money out)
7. Record metrics for this tick (Section 8)
8. Append per-customer brand frame if record_frames     (for animation)
```

---

## 8. Metrics — `model.py:392` (`_record`)

| Metric | Formula |
|---|---|
| Transaction volume (tick) | `Σ price` over transactions this tick |
| Total revenue (cumulative) | `Σ_b revenue_total_b` |
| Revenue market share | `revenue_b / total_revenue` (cumulative) |
| Share (this tick) | `revenue_tick_b / transaction_volume` |
| Customer cash | `Σ_c cash_c` |
| Brand cash | `Σ_b cash_b` |
| Total money | `customer_cash + brand_cash` |
| Average customer cash | `customer_cash / n_customers` |
| Money velocity | `transaction_volume / total_money` |

`summary()` ([`model.py:423`](model.py)) returns the final snapshot plus
cumulative revenue share, ending cash and customers served per brand.

---

## 9. Money conservation

Total internal money is invariant:

```
Σ_c cash_c  +  Σ_b cash_b  =  constant          (model.py:388 total_money)
```

Money is only *transferred*. `income_per_tick` and `operating_cost_per_tick`
(default 0) move money across the boundary and are tracked in `external_money`:

```
internal_money + external_money = constant
```

This is asserted by `test_money_is_conserved` and printed by the CLI.

---

## 10. Parameters and defaults (`ModelConfig`, `model.py:41`)

### Economy
| Parameter | Default | Meaning |
|---|---:|---|
| `seed` | 42 | Random seed (reproducibility) |
| `ticks` | 365 | Simulated days |
| `n_customers` | 500 | Number of customers |
| `avg_cash` | 2,000,000 | Mean starting cash (Rp) |
| `total_money_supply` | `None` | If set, fixes the total money supply |
| `cash_cv` | 0.4 | Cash dispersion (coefficient of variation) |
| `income_per_tick` | 0 | External income per customer per tick |

### Geography
| Parameter | Default |
|---|---:|
| `world_size` | 10 km × 10 km |
| `customer_distribution` | `gaussian` (`uniform` alternative) |
| `cluster_centers` | `[(2.5, 3.8), (7.0, 7.5)]` |
| `cluster_sigma` | 1.2 km |

### Customer population (drawn as clipped Normal(mean, `sensitivity_sd`))
| Parameter | Default |
|---|---:|
| `purchase_frequency` | 0.1 |
| `mean_price_sensitivity` | 1.0 |
| `mean_distance_sensitivity` | 1.0 |
| `mean_brand_preference` | 1.0 |
| `mean_quality_preference` | 1.0 |
| `mean_promotion_sensitivity` | 1.0 |
| `mean_loyalty` | 0.4 |
| `sensitivity_sd` | 0.3 |

### Decision scaling
| Parameter | Default |
|---|---:|
| `reference_price` | 20,000 |
| `distance_scale` | 10 |
| `loyalty_scale` | 1.0 |
| `temperature` | 0.6 |

### Customer movement (turtle trip behaviour)
| Parameter | Default | Meaning |
|---|---:|---|
| `move_enabled` | `True` | Enable the travel-to-buy trip cycle |
| `travel_speed` | 0.5 | km travelled per tick |
| `purchase_radius` | 0.3 | km — buys when this close to the outlet |
| `settle_distance` | 2.0 | km — rests this far from the brand after buying |

### Default brands (`model.py:94`)
| Brand | x, y | Price | Quality | Strength | Entry |
|---|---:|---:|---:|---:|---:|
| A | 2.5, 3.8 | 40,000 | 0.7 | 0.8 | day 0 |
| B | 7.0, 7.5 | 40,000 | 0.7 | 0.6 | day 30 |

> The dashboard starts with **only Brand A**; new brands are injected live.

---

## 11. Randomness and reproducibility

- All randomness uses one `random.Random(seed)` (`model.py:108`).
- Same `ModelConfig` + `seed` → identical results (`test_reproducible_with_seed`).
- Initial draws:
  - cash `~ max(0, Normal(avg_cash, avg_cash·cash_cv))`
  - each sensitivity `~ max(0, Normal(mean, sensitivity_sd))`
  - `purchase_frequency ~ clip(Normal(0.1, 0.1), 0, 1)`
  - `loyalty ~ clip(Normal(0.4, 0.15), 0, 1)`
  - location: uniform, or cluster-center + `Normal(0, cluster_sigma)`

---

## 12. Validation tests (PRD section 30) — `tests/test_validation.py`

| Test | Expectation |
|---|---|
| `test_money_is_conserved` | internal money constant |
| `test_reproducible_with_seed` | same seed ⇒ same results |
| `test_cheaper_brand_wins_more_share` | lower price ⇒ more share |
| `test_distance_sensitivity_concentrates_customers` | higher `D` ⇒ shorter trips |
| `test_loyalty_hurts_entrant` | higher loyalty ⇒ entrant weaker |
| `test_empty_location_earns_less` | far from customers ⇒ less revenue |
| `test_transaction_transfers_money` | purchase moves cash customer→brand |
| `test_promotion_increases_entrant_share` | higher promotion ⇒ more share |
| `test_customers_move_when_satisfied` | movement relocates customers over time |
| `test_movement_stays_in_bounds` | customers never leave `[0, world_size]` |
| `test_movement_disabled_keeps_customers_static` | `move_enabled=False` reproduces static model |
| `test_trip_cycle_travels_buys_and_retreats` | idle → outbound → buy → retreat cycle |

---

## 13. Code map

| Concept | Location |
|---|---|
| Distance | `agents.py:42` |
| Utility `U(c,b)` | `model.py:190` |
| Softmax choice | `model.py:202` |
| Customer movement | `model.py:265` (`_update_customers`) |
| Purchase / transfer | `model.py:228` |
| Tick loop | `model.py:344` |
| Metrics | `model.py:392` |
| Summary | `model.py:423` |
| Parameters | `model.py:41` |
| Money conservation check | `model.py:388` |
