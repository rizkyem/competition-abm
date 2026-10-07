# Product Requirements Document (PRD)

## 1. Project Overview

### Project Name
**Competition Agent-Based Model**

### Working Description
A Python-based Agent-Based Model (ABM) that simulates competition between brands within a geographically distributed artificial economy.

The simulation models individual agents — primarily **customers and brands** — and observes how their individual decisions create aggregate outcomes such as:

- Revenue
- Market share
- Customer distribution
- Brand cash balance
- Customer spending
- Money circulation
- Transaction volume
- Geographic market concentration

The model will initially simulate a finite amount of money within the environment. Money moves between agents through transactions rather than being automatically created.

The simulation will eventually be deployed as an interactive web application using **Streamlit**, allowing users to change assumptions and observe different outcomes.

---

# 2. Problem Statement

Traditional business analysis often evaluates competition using aggregate metrics such as revenue, market share, price, and location.

However, these metrics are the result of many individual decisions:

- Where customers live
- How much money customers have
- Which restaurant they choose
- How far they are willing to travel
- How price-sensitive they are
- Whether they have brand loyalty
- Where competitors establish outlets
- How competitors price their products

This project aims to demonstrate how these individual behaviors can generate emergent business and economic outcomes.

The key question is:

> **What happens to a market when competing brands enter, change location, price their products, and compete for customers within a finite money economy?**

---

# 3. Objectives

## Primary Objectives

1. Build an Agent-Based Model of competition.
2. Simulate customers making individual purchasing decisions.
3. Introduce geographic distance into customer decisions.
4. Simulate competition between multiple brands.
5. Model money as an actual transferable resource between agents.
6. Measure how brand entry and location affect market outcomes.
7. Create an interactive simulation that allows users to change assumptions.
8. Deploy the model as a publicly accessible web application.

## Secondary Objectives

- Demonstrate Python programming ability.
- Demonstrate financial and economic modeling.
- Demonstrate data analysis and visualization.
- Create a portfolio project relevant to FP&A, financial analysis, corporate finance, and business analytics.
- Create a foundation for future machine-learning or optimization experiments.

---

# 4. Scope

## In Scope — Version 1

The initial model will include:

### Agents

- Customers
- Brand A
- Brand B
- Brand C

### Environment

- Artificial geographic environment
- Customer coordinates
- Brand outlet coordinates
- Distance between customers and outlets

### Economy

- Initial money supply
- Customer cash balances
- Brand cash balances
- Customer purchases
- Brand revenue
- Money transfers

### Competition

- Brand entry
- Product price
- Brand preference
- Distance
- Customer switching
- Market share

### Outputs

- Revenue
- Market share
- Cash balance
- Customer distribution
- Transaction volume
- Money distribution
- Geographic customer concentration

---

# 5. Out of Scope — Initial Version

The following features will not be included initially:

- Real-world geographic maps
- Real company financial statements
- Real customer-level transaction data
- Banking system
- Loans and credit
- Interest rates
- Inflation
- Government monetary policy
- Complex supply chains
- Taxes
- Employee payroll
- Detailed accounting statements
- Real-time external data
- Machine learning optimization

These may be added in later versions.

---

# 6. Conceptual Model

The environment represents a simplified artificial economy.

There is a finite amount of money in the system.

For example:

**Initial money supply = Rp100,000,000**

This money is initially distributed among customers.

Customers use their money to purchase products from brands.

Example:

Customer 001:

> Cash = Rp500,000

Customer 001 purchases Rp50,000 from Brand A.

After the transaction:

> Customer 001 = Rp450,000  
> Brand A = Rp50,000

The total money remains:

> Rp500,000

The money has simply changed ownership.

---

# 7. Agents

## 7.1 Customer Agent

Each customer represents an individual consumer.

### Attributes

- `customer_id`
- `x_coordinate`
- `y_coordinate`
- `cash_balance`
- `income`
- `price_sensitivity`
- `brand_preference`
- `quality_preference`
- `distance_sensitivity`
- `purchase_frequency`
- `loyalty`
- `last_purchase_brand`

### Behavior

Each simulation period, a customer may:

1. Decide whether to purchase.
2. Identify available brands.
3. Calculate attractiveness of each brand.
4. Select a brand.
5. Purchase if sufficient cash is available.
6. Transfer money to the selected brand.
7. Update brand preference / loyalty.

---

# 8. Brand Agent

Each brand represents a company or restaurant brand.

Example:

- Brand A
- Brand B
- Brand C

### Attributes

- `brand_id`
- `outlet_id`
- `x_coordinate`
- `y_coordinate`
- `cash_balance`
- `product_price`
- `quality_score`
- `promotion_score`
- `brand_strength`
- `operating_cost`
- `active_status`

### Behavior

Brands can:

- Sell products
- Receive customer payments
- Accumulate cash
- Change prices
- Run promotions
- Enter the market
- Open outlets
- Potentially close outlets in future versions

---

# 9. Geography

The simulation will initially use an artificial geographic environment.

Example:

**10 km × 10 km grid**

Customers and outlets have coordinates.

Example:

```text
Customer A → (2.1, 3.5)
Customer B → (7.2, 8.1)

Brand A → (2.5, 3.8)
Brand B → (7.0, 7.5)
```

Distance will influence customer decisions.

The initial distance calculation can use Euclidean distance:

> Distance = √((x₂ − x₁)² + (y₂ − y₁)²)

The model does not initially need real-world roads or GPS coordinates.

---

# 10. Customer Decision Model

Customers should not automatically choose the closest restaurant.

Instead, customers evaluate multiple factors.

A simplified attractiveness score can be represented as:

> **Utility = Brand Preference + Price Attractiveness + Quality + Promotion − Distance Cost**

For example:

| Factor | Brand A | Brand B |
|---|---:|---:|
| Brand preference | 8 | 5 |
| Price attractiveness | 6 | 8 |
| Quality | 8 | 7 |
| Promotion | 2 | 6 |
| Distance cost | -2 | -5 |
| **Total utility** | **22** | **21** |

The customer would therefore have a slightly higher preference for Brand A.

Future versions may convert utility into probabilities so that customers do not always make the same deterministic decision.

---

# 11. Competition Model

## Initial State

Initially:

> Brand A exists.

Brand A has an established customer base.

Example:

```text
Time 0

Brand A
████████████████████

Market Share
A = 100%
B = 0%
```

## Market Entry

At a specified simulation period:

> Brand B enters the market.

Example:

```text
Month 12

Brand A
██████████████

Brand B
██████
```

Customers can begin switching between brands.

The model then observes how the market changes over time.

---

# 12. Location Experiment

One of the primary experiments will examine the effect of Brand B's location.

### Scenario A — Brand B Opens Near Brand A

Example:

```text
Brand A ●
Brand B ●
```

Distance:

> 500 meters

### Scenario B — Brand B Opens Far From Brand A

Example:

```text
Brand A ●

        5 km

                 ● Brand B
```

The simulation compares:

- Revenue
- Market share
- Customer acquisition
- Customer switching
- Brand cash balance
- Geographic customer distribution

---

# 13. Important Economic Distinction

The model will track different types of monetary metrics.

## Money Supply

The total amount of money existing inside the modeled environment.

Example:

> Rp100 million

If no money is created or removed:

> Money supply remains Rp100 million.

## Cash Balance

The amount of money currently owned by each agent.

Example:

```text
Customers       Rp70m
Brand A         Rp15m
Brand B         Rp10m
Brand C         Rp5m
----------------------
Total           Rp100m
```

## Transaction Volume

The total value of transactions occurring during a period.

Example:

> January transaction volume = Rp20 million

This does **not** mean the economy contains Rp20 million of new money.

The same money can be transacted multiple times.

## Money Velocity

A future metric can estimate how frequently money changes hands.

A simplified measure can be:

> Transaction Volume / Money Supply

---

# 14. Revenue

Brand revenue is the value of customer purchases.

Example:

Customer purchases:

> Rp50,000

Brand A revenue increases by:

> Rp50,000

Brand revenue is therefore a **flow**.

Cash balance is a **stock**.

This distinction should be maintained throughout the model.

---

# 15. Market Share

Market share will initially be based on customer purchases.

Possible calculation:

> Brand Market Share = Brand Transactions / Total Transactions

A second metric may be introduced:

> Revenue Market Share = Brand Revenue / Total Market Revenue

This allows the model to distinguish:

- Customer market share
- Transaction market share
- Revenue market share

---

# 16. Simulation Time

The simulation will operate in discrete time periods.

Initial implementation:

> 1 tick = 1 day

A simulation may run for:

> 365 ticks = 1 year

Future versions may allow:

- Daily
- Weekly
- Monthly

aggregation.

---

# 17. Simulation Flow

Each simulation tick follows approximately:

```text
START
  ↓
Update customer conditions
  ↓
Determine customers who want to purchase
  ↓
Find available brands
  ↓
Calculate brand attractiveness
  ↓
Customer selects brand
  ↓
Check customer cash balance
  ↓
Execute transaction
  ↓
Transfer money
  ↓
Update brand revenue
  ↓
Update customer loyalty
  ↓
Update brand financial position
  ↓
Record simulation metrics
  ↓
Next tick
```

---

# 18. Dashboard

The Streamlit application should provide an interactive dashboard.

## Main Controls

Users should be able to change:

### Economy

- Initial money supply
- Number of customers
- Average customer cash
- Purchase frequency

### Brand

- Number of brands
- Brand entry timing
- Product price
- Quality
- Promotion
- Brand strength

### Geography

- Brand A location
- Brand B location
- Brand C location
- Customer geographic distribution

### Customer Behavior

- Price sensitivity
- Distance sensitivity
- Brand loyalty
- Quality sensitivity

### Simulation

- Number of simulation periods
- Random seed
- Simulation speed

---

# 19. Dashboard Outputs

## KPI Cards

Display:

- Total Market Revenue
- Brand A Revenue
- Brand B Revenue
- Brand C Revenue
- Brand A Market Share
- Brand B Market Share
- Brand C Market Share
- Total Transaction Volume
- Total Money Supply

---

# 20. Visualizations

## 20.1 Geographic Market

A 2D visualization showing:

- Customer locations
- Brand locations
- Customer-brand relationships
- Geographic concentration

Example concept:

```text
       Customer ●
                 ● Customer

          🅰 Brand A

    Customer ●

                         🅱 Brand B
                 ● Customer
```

---

## 20.2 Market Share Over Time

Line chart:

```text
Market
Share

100% | A ───────╲
 80% |            ╲
 60% |             ╲
 40% |              ╲── B
 20% |
  0% |________________________
       Time →
```

---

## 20.3 Revenue Over Time

Track revenue by brand.

---

## 20.4 Money Distribution

Show how money is distributed between:

- Customers
- Brand A
- Brand B
- Brand C

---

## 20.5 Transaction Volume

Show total transactions per period.

---

# 21. Core Experiments

The application should allow users to perform controlled experiments.

## Experiment 1 — Brand Entry

Question:

> What happens when Brand B enters an existing market?

Compare:

- Market share
- Revenue
- Customer switching
- Brand cash

---

## Experiment 2 — Location

Question:

> Is it better for Brand B to open near or far from Brand A?

Compare different distances.

---

## Experiment 3 — Price Competition

Question:

> What happens when Brand B enters with a lower price?

Example:

```text
Brand A = Rp40,000
Brand B = Rp30,000
```

Measure:

- Market share
- Revenue
- Customer behavior
- Cash accumulation

---

## Experiment 4 — Promotion

Question:

> Can promotions allow a new entrant to compete with an established brand?

Compare:

```text
No Promotion
vs.
Moderate Promotion
vs.
Aggressive Promotion
```

---

## Experiment 5 — Brand Loyalty

Question:

> How difficult is it for a new entrant to acquire customers when existing customers have high loyalty?

---

## Experiment 6 — Customer Geography

Question:

> How does customer concentration affect the optimal location of a new outlet?

---

# 22. Future Strategic Location Model

A future version should allow Brand B to choose its own location.

Instead of:

> User manually chooses location.

The model could evaluate:

```text
Candidate Location 1
Candidate Location 2
Candidate Location 3
Candidate Location 4
...
```

For each location, estimate:

- Nearby population
- Expected customers
- Expected revenue
- Competitor proximity
- Rental cost
- Expected profit

Example:

| Location | Revenue | Rent | Expected Profit |
|---|---:|---:|---:|
| Near A | Rp800m | Rp300m | Rp500m |
| 2 km from A | Rp700m | Rp150m | Rp550m |
| 5 km from A | Rp550m | Rp80m | Rp470m |

The model can then demonstrate that **the location generating the highest revenue is not necessarily the location generating the highest profit**.

---

# 23. Future Financial Model

Later versions can expand the brand agent into a simplified business entity.

### Revenue

Customer purchases.

### Costs

- Employee wages
- Rent
- Utilities
- Ingredients
- Marketing
- Maintenance

### Profit

> Profit = Revenue − Costs

### Cash

> Ending Cash = Beginning Cash + Cash Inflows − Cash Outflows

This will allow the simulation to move beyond market share into **business financial sustainability**.

---

# 24. Future Agents

Potential additional agents:

### Employees

Receive wages from brands and spend money with businesses.

### Suppliers

Receive payments from brands.

### Landlords

Receive rent.

### Government

Collects taxes and spends money.

### Banks

Provide loans and receive repayments/interest.

This would transform the model into a larger artificial economic system.

---

# 25. Accounting Perspective

The model should eventually demonstrate a simplified flow of funds.

Example:

```text
Customer
   │
   │ Purchase
   ↓
Brand
   │
   ├── Wages ─────→ Employees
   │
   ├── Rent ──────→ Landlord
   │
   └── Inventory ─→ Supplier
```

The project should distinguish:

- Revenue
- Expense
- Profit
- Cash
- Assets
- Liabilities

when accounting features are introduced.

---

# 26. Technology

## Primary Language

**Python**

Reason:

- Strong fit with data analysis
- Financial modeling capabilities
- Easy integration with pandas/numpy
- Future ML capability
- Easier portfolio integration
- Can be deployed through Streamlit

## Potential Libraries

### ABM

**Mesa**

### Data Analysis

- pandas
- NumPy

### Visualization

- Plotly
- Matplotlib

### Web Application

**Streamlit**

### Version Control

**Git + GitHub**

---

# 27. Deployment

The application should eventually be deployed as a public web application.

Target architecture:

```text
Python ABM
     ↓
Streamlit
     ↓
GitHub Repository
     ↓
Streamlit Community Cloud
     ↓
Public Web Application
```

Users should be able to access and operate the simulation through a browser without installing Python.

---

# 28. Proposed Repository Structure

```text
competition-abm/
│
├── app.py
├── model.py
├── agents.py
├── simulation.py
│
├── requirements.txt
├── README.md
├── PRD.md
│
├── data/
│
├── notebooks/
│
└── tests/
```

The exact structure may change as the project develops.

---

# 29. Randomness and Reproducibility

Because agent behavior contains randomness, the model should support a random seed.

Example:

> Seed = 42

Running the simulation with the same parameters and seed should produce the same results.

This allows controlled experimentation and comparison between scenarios.

---

# 30. Validation

The model is not intended to perfectly predict real markets.

Instead, validation should focus on whether the model behaves logically.

Examples:

### Test 1

If Brand B becomes significantly cheaper, its customer acquisition should generally increase.

### Test 2

If distance sensitivity increases, customers should generally become more concentrated around nearby outlets.

### Test 3

If Brand A has extremely strong loyalty, Brand B should generally have greater difficulty acquiring customers.

### Test 4

If Brand B opens in an area with no customers, expected revenue should generally be lower.

### Test 5

If no external money is created or removed:

> Total money before simulation = Total money after simulation

---

# 31. Key Assumptions

The initial model assumes:

1. Customers have limited money.
2. Customers cannot spend money they do not have.
3. Transactions transfer money between agents.
4. Money is conserved unless explicitly introduced/removed.
5. Customers make decisions independently.
6. Distance affects customer utility.
7. Customers have heterogeneous preferences.
8. Brands compete for the same customer population.
9. Market outcomes emerge from individual decisions.
10. The simulation is an artificial economy, not a forecast of real-world performance.

---

# 32. Success Metrics

The project will be considered successful when:

### Technical

- ABM runs successfully.
- Multiple agents interact.
- Transactions transfer money correctly.
- Geographic distance affects decisions.
- Simulation can run for multiple periods.
- Results are reproducible using a random seed.

### Analytical

The model can answer questions such as:

> What happens when Brand B enters?

> Does location near Brand A help or hurt?

> How does price affect market share?

> How does customer loyalty affect competition?

> How does money move through the economy?

> Which brand accumulates the most cash?

### Product

- Users can change assumptions.
- Users can run simulations.
- Results are visualized.
- Application works through a web browser.
- Project is documented on GitHub.

---

# 33. Minimum Viable Product (MVP)

The first working version should contain only:

### Agents

- Customers
- Brand A
- Brand B

### Environment

- 2D geographic grid

### Customer

- Location
- Cash
- Brand preference
- Price sensitivity
- Distance sensitivity

### Brands

- Location
- Price
- Cash

### Transactions

Customer:

> Cash ↓

Brand:

> Cash ↑

### Outputs

- Revenue
- Market share
- Customer count
- Cash balance
- Total money
- Transaction volume
- Geographic visualization

### Experiment

> Brand B enters at different distances from Brand A.

This is the **minimum version that already demonstrates the core idea**.

---

# 34. Development Roadmap

## Phase 1 — Economic Core

Build:

- Customers
- Brands
- Money
- Transactions
- Revenue
- Cash balances

---

## Phase 2 — Geography

Add:

- Coordinates
- Distance
- Customer spatial distribution
- Distance-based decision making

---

## Phase 3 — Competition

Add:

- Brand B entry
- Customer switching
- Market share
- Brand loyalty

---

## Phase 4 — Business Strategy

Add:

- Pricing
- Promotion
- Quality
- Location experiments
- Outlet expansion

---

## Phase 5 — Financial Model

Add:

- Costs
- Profit
- Employees
- Suppliers
- Rent
- Cash flow

---

## Phase 6 — Web Application

Add:

- Streamlit interface
- User controls
- Interactive visualizations
- Scenario comparison

---

## Phase 7 — Advanced Model

Potential additions:

- Automated location selection
- Optimization
- Machine learning
- Credit
- Banking
- Government
- Investment
- External economy

---

# 35. Final Product Concept

The final project should allow a user to ask:

> **"If Brand B enters this market, where should it open, how should it price its product, and what will happen to Brand A?"**

The user can then manipulate:

**Location → Price → Promotion → Customer behavior → Competition**

and observe the resulting:

**Customers → Transactions → Revenue → Cash → Market Share → Business Outcome**

The central concept is:

> **Individual agent decisions → Money transactions → Emergent market behavior**

This makes the project both a **competition simulation** and a simplified **artificial economy**.