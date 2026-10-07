"""NetLogo-style live dashboard for the Competition ABM.

Run with::

    ./run_dashboard.sh          # or: .venv/bin/streamlit run app.py

Design
------
* At day 0 only **Brand A** exists.
* Use **Add Brand** (in the running dashboard) to inject a new competitor at
  any day. It starts competing on the next tick and immediately changes how
  money flows between customers and brands.
* The **Brand editor** and **Global knobs** apply *during* play, on the next
  tick, just like dragging a NetLogo slider.
* The sidebar holds **setup** values, applied when you press Build & Run.
"""

from __future__ import annotations

from datetime import timedelta

import plotly.graph_objects as go
import streamlit as st

from agents import Brand
from model import BrandConfig, CompetitionModel, ModelConfig

BRAND_COLORS = {"A": "#1f77b4", "B": "#d62728", "C": "#2ca02c",
                "D": "#9467bd", "E": "#ff7f0e", "F": "#17becf",
                "G": "#8c564b", "H": "#e377c2"}
PALETTE = list(BRAND_COLORS.values())
WORLD = 10.0
GRAY = "#c9c9c9"
MAX_BRANDS = 8

st.set_page_config(page_title="Competition ABM", layout="wide")


def color_for(name: str, index: int = 0) -> str:
    return BRAND_COLORS.get(name, PALETTE[index % len(PALETTE)])


# ----------------------------------------------------------------------
# Sidebar: SETUP values (applied on Build & Run)
# ----------------------------------------------------------------------
with st.sidebar:
    st.title("Competition ABM")
    st.caption("Start with Brand A alone, then inject competitors live")

    with st.expander("Economy", expanded=True):
        n_customers = st.slider("Customers", 50, 1500, 500, 50)
        avg_cash = st.number_input("Average customer cash (Rp)", 100_000,
                                   20_000_000, 2_000_000, 100_000)
        purchase_frequency = st.slider("Purchase frequency (per day)", 0.01, 1.0,
                                       0.1, 0.01)

    with st.expander("Customer behaviour (setup)", expanded=False):
        loyalty = st.slider("Brand loyalty", 0.0, 1.0, 0.4, 0.05)
        distance_sensitivity = st.slider("Distance sensitivity", 0.0, 3.0, 1.0, 0.1)
        temperature = st.slider("Decision randomness", 0.05, 2.0, 0.6, 0.05)
        distribution = st.selectbox("Customer distribution",
                                    ["gaussian", "uniform"])

    with st.expander("Turtle movement (setup)", expanded=False):
        move_enabled = st.checkbox("Customers travel to buy (trip cycle)",
                                   value=True)
        travel_speed = st.slider("Travel speed (km/day)", 0.1, 2.0, 0.5, 0.1)
        purchase_radius = st.slider("Buy radius (km)", 0.05, 1.0, 0.3, 0.05)
        settle_distance = st.slider("Rest distance after buying (km)",
                                    0.5, 5.0, 2.0, 0.1)

    with st.expander("Brand A (setup)", expanded=True):
        a_x = st.slider("A x (km)", 0.0, WORLD, 2.5, 0.1)
        a_y = st.slider("A y (km)", 0.0, WORLD, 3.8, 0.1)
        a_price = st.number_input("A price (Rp)", 10_000, 200_000, 40_000, 1_000)
        a_strength = st.slider("A brand strength", 0.0, 1.0, 0.8, 0.05)

    include_b = st.checkbox("Schedule Brand B entry at setup", value=False)
    if include_b:
        with st.expander("Brand B (scheduled)", expanded=True):
            sched_b_x = st.slider("B x (km)", 0.0, WORLD, 7.0, 0.1)
            sched_b_y = st.slider("B y (km)", 0.0, WORLD, 7.5, 0.1)
            sched_b_price = st.number_input("B price (Rp)", 10_000, 200_000,
                                            40_000, 1_000)
            sched_b_strength = st.slider("B brand strength", 0.0, 1.0, 0.6, 0.05)
            sched_b_promo = st.slider("B promotion", 0.0, 1.0, 0.0, 0.05)
            entry_tick = st.number_input("B entry tick", 0, 730, 30, 1)
    else:
        sched_b_x, sched_b_y, sched_b_price = a_x, a_y, a_price
        sched_b_strength, sched_b_promo, entry_tick = 0.6, 0.0, 730

    ticks = st.slider("Days to simulate", 30, 730, 365, 10)
    seed = st.number_input("Random seed", 0, 10_000, 42, 1)
    build = st.button("Build & Run", type="primary", width="stretch")
    st.caption("At day 0 only Brand A exists. Add competitors from the running "
               "dashboard.")


# ----------------------------------------------------------------------
# Build / reset the model
# ----------------------------------------------------------------------
def build_model() -> None:
    brands = [
        BrandConfig(1, "A", x=a_x, y=a_y, brand_strength=a_strength,
                    product_price=a_price),
    ]
    if include_b:
        brands.append(BrandConfig(2, "B", x=sched_b_x, y=sched_b_y,
                                  brand_strength=sched_b_strength,
                                  product_price=sched_b_price,
                                  entry_tick=int(entry_tick),
                                  promotion_score=sched_b_promo))
    cfg = ModelConfig(
        seed=int(seed), ticks=int(ticks), n_customers=n_customers,
        avg_cash=avg_cash, purchase_frequency=purchase_frequency,
        mean_loyalty=loyalty, mean_distance_sensitivity=distance_sensitivity,
        temperature=temperature, customer_distribution=distribution,
        move_enabled=move_enabled, travel_speed=travel_speed,
        purchase_radius=purchase_radius, settle_distance=settle_distance,
        cluster_centers=[(a_x, a_y), (sched_b_x, sched_b_y)], brands=brands,
    )
    st.session_state.model = CompetitionModel(cfg)
    st.session_state.playing = False
    st.session_state.live = {"temp": temperature, "dist": distance_sensitivity,
                             "loyal": loyalty}
    st.session_state.live_prev = {"dist": distance_sensitivity, "loyal": loyalty}


if build or "model" not in st.session_state:
    build_model()


# ----------------------------------------------------------------------
# Live actions
# ----------------------------------------------------------------------
def add_brand(model: CompetitionModel, x, y, price, strength, promo, quality=0.7):
    """Inject a new competitor immediately (affects the very next tick)."""
    used = {b.name for b in model.brands}
    name = next((n for n in "BCDEFGH" if n not in used), None)
    if name is None:
        return None
    bid = max((b.brand_id for b in model.brands), default=0) + 1
    brand = Brand(brand_id=bid, name=name, x=x, y=y, cash=0.0,
                  product_price=price, quality_score=quality,
                  promotion_score=promo, brand_strength=strength,
                  entry_tick=model.tick, active=True)
    model.brands.append(brand)
    return brand


def apply_globals(model: CompetitionModel, live: dict) -> None:
    """Apply global knobs; scale per-customer values to keep heterogeneity."""
    model.cfg.temperature = live["temp"]
    prev = st.session_state.get("live_prev", {})
    pd = prev.get("dist")
    if pd and live["dist"] != pd:
        ratio = live["dist"] / pd
        for c in model.customers:
            c.distance_sensitivity *= ratio
    pl = prev.get("loyal")
    if pl is not None and live["loyal"] != pl:
        ratio = (live["loyal"] / pl) if pl > 0 else 1.0
        for c in model.customers:
            c.loyalty = min(1.0, max(0.0, c.loyalty * ratio))
    st.session_state.live_prev = {"dist": live["dist"], "loyal": live["loyal"]}


# ----------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------
def geography_figure(model: CompetitionModel) -> go.Figure:
    fig = go.Figure()
    for i, brand in enumerate(model.brands):
        pts = [c for c in model.customers if c.last_purchase_brand == brand.brand_id]
        fig.add_trace(go.Scatter(
            x=[c.x for c in pts], y=[c.y for c in pts], mode="markers",
            name=f"served by {brand.name}",
            marker=dict(size=7, color=color_for(brand.name, i)), opacity=0.7))
    unserved = [c for c in model.customers if c.last_purchase_brand is None]
    if unserved:
        fig.add_trace(go.Scatter(
            x=[c.x for c in unserved], y=[c.y for c in unserved],
            mode="markers", name="unserved",
            marker=dict(size=6, color=GRAY), opacity=0.5))
    for i, brand in enumerate(model.brands):
        if brand.active:
            fig.add_trace(go.Scatter(
                x=[brand.x], y=[brand.y], mode="markers+text",
                marker=dict(symbol="star", size=24,
                            color=color_for(brand.name, i),
                            line=dict(width=1, color="black")),
                text=[f"Brand {brand.name}"], textposition="top center",
                showlegend=False))
    fig.update_layout(
        title=f"Geographic market - day {model.tick}",
        xaxis=dict(range=[0, WORLD], title="x (km)"),
        yaxis=dict(range=[0, WORLD], title="y (km)", scaleanchor="x"),
        height=560, margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    return fig


def _brand_lines(model: CompetitionModel, key_fn, title, ytitle) -> go.Figure:
    fig = go.Figure()
    for i, brand in enumerate(model.brands):
        fig.add_trace(go.Scatter(
            x=[h["tick"] for h in model.history],
            y=[key_fn(h, brand.name) for h in model.history],
            mode="lines", name=f"Brand {brand.name}",
            line=dict(color=color_for(brand.name, i))))
    fig.update_layout(title=title, yaxis_title=ytitle, xaxis_title="Day",
                      height=270, margin=dict(l=10, r=10, t=40, b=10))
    return fig


# ----------------------------------------------------------------------
# Live playback fragment
# ----------------------------------------------------------------------
@st.fragment(run_every=timedelta(seconds=0.25))
def playback() -> None:
    model = st.session_state.model
    total = model.cfg.ticks

    c1, c2, c3, c4 = st.columns([1, 1, 1, 4])
    if c1.button("Play" if not st.session_state.playing else "Pause",
                 width="stretch"):
        st.session_state.playing = not st.session_state.playing
    if c2.button("Step", width="stretch"):
        st.session_state.playing = False
        if model.tick < total:
            model.step()
    if c3.button("Reset", width="stretch"):
        build_model()
        return
    speed = c4.slider("Speed (days/sec)", 1, 60, 8, key="speed")

    # --- market entry: inject a new competitor at the current day ----------
    with st.expander("Market entry - add a competitor mid-run", expanded=True):
        me = st.columns([1, 1, 1, 1, 1, 1.2])
        nx = me[0].slider("New x (km)", 0.0, WORLD, 5.0, 0.1, key="nx")
        ny = me[1].slider("New y (km)", 0.0, WORLD, 7.5, 0.1, key="ny")
        nprice = me[2].number_input("New price (Rp)", 10_000, 200_000, 40_000,
                                    1_000, key="nprice")
        nstrength = me[3].slider("New strength", 0.0, 1.0, 0.6, 0.05, key="nstr")
        npromo = me[4].slider("New promotion", 0.0, 1.0, 0.0, 0.05, key="npromo")
        can_add = len(model.brands) < MAX_BRANDS
        if me[5].button("Add Brand", type="primary", width="stretch",
                        disabled=not can_add):
            added = add_brand(model, nx, ny, nprice, nstrength, npromo)
            if added is None:
                st.warning("Max brands reached.")
            else:
                st.toast(f"Brand {added.name} entered on day {model.tick}")
        if not can_add:
            st.caption("Maximum of 8 brands reached.")

    # --- live editor for an existing brand --------------------------------
    names = [b.name for b in model.brands]
    if st.session_state.get("edit_brand") not in names:
        st.session_state.edit_brand = names[0]
    sel = st.selectbox("Brand to adjust live", names, key="edit_brand")
    brand = next(b for b in model.brands if b.name == sel)
    ec = st.columns(4)
    brand.product_price = ec[0].number_input(
        "Price (Rp)", 10_000, 200_000, int(brand.product_price), 1_000,
        key=f"lp_{sel}")
    brand.promotion_score = ec[1].slider(
        "Promotion", 0.0, 1.0, float(brand.promotion_score), 0.05, key=f"lpr_{sel}")
    brand.x = ec[2].slider("x (km)", 0.0, WORLD, float(brand.x), 0.1,
                           key=f"lx_{sel}")
    brand.y = ec[3].slider("y (km)", 0.0, WORLD, float(brand.y), 0.1,
                           key=f"ly_{sel}")

    # --- global knobs ------------------------------------------------------
    gc = st.columns(3)
    L = st.session_state.live
    L["temp"] = gc[0].slider("Decision randomness", 0.05, 2.0, float(L["temp"]), 0.05)
    L["dist"] = gc[1].slider("Distance sensitivity", 0.0, 3.0, float(L["dist"]), 0.1)
    L["loyal"] = gc[2].slider("Brand loyalty", 0.0, 1.0, float(L["loyal"]), 0.05)
    apply_globals(model, L)

    # --- advance the clock -------------------------------------------------
    if st.session_state.playing:
        if model.tick >= total:
            st.session_state.playing = False
        else:
            for _ in range(max(1, int(round(speed * 0.25)))):
                if model.tick < total:
                    model.step()
                else:
                    st.session_state.playing = False
                    break

    st.progress(min(1.0, model.tick / total),
                text=f"Day {model.tick} / {total}"
                + ("  - complete" if model.tick >= total else ""))

    # --- KPIs and charts ---------------------------------------------------
    if model.history:
        rec = model.history[-1]
        k = st.columns(3 + len(model.brands))
        k[0].metric("Customer cash", f"Rp{rec['customer_cash']:,.0f}")
        k[1].metric("Transacted today", f"Rp{rec['transaction_volume']:,.0f}")
        k[2].metric("Total money", f"Rp{rec['total_money']:,.0f}")
        for j, b in enumerate(model.brands):
            k[3 + j].metric(f"Brand {b.name} share",
                            f"{rec.get(f'share_{b.name}', 0.0)*100:.1f}%",
                            f"Rp{rec.get(f'cash_{b.name}', 0.0):,.0f}")

    left, right = st.columns([1.25, 1])
    with left:
        st.plotly_chart(geography_figure(model), width="stretch")
    with right:
        if model.history:
            st.plotly_chart(
                _brand_lines(model, lambda h, n: h.get(f"share_{n}", 0.0) * 100,
                             "Revenue market share", "%"), width="stretch")
            st.plotly_chart(
                _brand_lines(model, lambda h, n: h.get(f"cum_revenue_{n}", 0.0),
                             "Cumulative revenue", "Rp"), width="stretch")

    bl, br = st.columns(2)
    with bl:
        if model.history:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[h["tick"] for h in model.history],
                y=[h["customer_cash"] for h in model.history],
                mode="lines", name="Customers", line=dict(color="#555555")))
            for i, b in enumerate(model.brands):
                fig.add_trace(go.Scatter(
                    x=[h["tick"] for h in model.history],
                    y=[h.get(f"cash_{b.name}", 0.0) for h in model.history],
                    mode="lines", name=f"Brand {b.name}",
                    line=dict(color=color_for(b.name, i))))
            fig.update_layout(title="Money distribution (who holds the money)",
                              yaxis_title="Rp", xaxis_title="Day", height=270,
                              margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, width="stretch")
    with br:
        if model.history:
            fig = go.Figure(go.Bar(
                x=[h["tick"] for h in model.history],
                y=[h["transaction_volume"] for h in model.history],
                marker_color="#1f77b4"))
            fig.update_layout(title="Transaction volume per day",
                              yaxis_title="Rp", xaxis_title="Day", height=270,
                              margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, width="stretch")


playback()

st.caption("Money is conserved (customer cash + brand cash = constant) unless "
           "income or operating costs are enabled. 1 tick = 1 day.")
