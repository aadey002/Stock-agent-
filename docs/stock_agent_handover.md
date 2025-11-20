# Stock Agent Build Handover – Project Brief

## 1. Current State

### 1.1 Existing Agent Architecture

The current system is a **rules-based research agent** with Gann/Elliott overlays, not yet RL-based.

Core logic lives in:

- `agent.py`

Key behavior:

- Pulls daily OHLCV for `SPY` from Tiingo using `TIINGO_TOKEN`.
- Writes raw and enriched price history to:
  - `data/SPY.csv` (enriched OHLCV + indicators)
  - `data/SPY_confluence.csv` (similar, confluence-focused view)
- Computes:
  - ATR(14)
  - Fast/slow SMAs (10/20)
  - Geometric ladder levels (swing low → swing high)
  - Φ (phi) levels based on golden ratio
  - Fib-based time windows off last major swing
  - Confluence flags: `PriceConfluence`, `TimeConfluence`
- Generates **base confluence trades** when:
  - Bias (SMA fast vs slow) = `CALL` or `PUT`
  - AND price and time confluence are both true
- For each trade, builds a **playbook**:
  - Entry band: `EntryLow`, `EntryHigh`
  - Guard-rail stop: `Stop`
  - 2R / 3R targets: `Target1`, `Target2`
  - Time stop (HOLD_DAYS)
- Runs an additional **Gann–Elliott strategy** (within `agent.py`, previously split out as `gann_elliott.py`):
  - Detects simplified Elliott 1–5 structure via ZigZag pivots
  - Computes Gann Square-of-9 support/resistance from current price
  - Applies Gann time cycles (11, 22, 34, 45, 56, 67, 78, 90 days)
  - Filters by trend/vol regime (SMA50/200 + realized vs historical volatility)
  - When conditions align, proposes a directional `CALL` or `PUT` idea

A **hybrid “UNIFIED” mode** exists conceptually:

- Base confluence agent generates trades.
- Gann–Elliott engine produces its own directional suggestion.
- **Super-Confluence** = only when both agree on direction.

### 1.2 Current Outputs & Performance Artifacts

Outputs currently written by `agent.py`:

- Raw/enriched data:
  - `data/SPY.csv`
  - `data/SPY_confluence.csv`
  - `data/performance_confluence.json`
  - `data/tuning_confluence.json`
- Trade logs:
  - `reports/portfolio_confluence.csv`
  - `reports/portfolio_gann_elliott.csv`
  - `reports/portfolio_super_confluence.csv` (base + Gann/Elliott agree; may be header-only if no overlap yet)

Performance JSONs include:

- Basic performance summary (win rate, avg PnL, avg R, max drawdown, etc.)
- Parameter tuning grid (entry band, stop ATR, hold days, price tolerance) and their resulting win rate / avg R.

There is **no RL/DQN agent** implemented yet. All logic is rule-based and deterministic.

---

## 2. Repository Links

### 2.1 GitHub URL

- **Repo (source):**  
  `https://github.com/aadey002/Stock-agent-`
- **Deployed GitHub Pages site:**  
  `https://aadey002.github.io/Stock-agent-/`

### 2.2 Branch Names

- Default branch: `main` (no separate `dev` or feature branches at this time).

### 2.3 Key File Locations

- Core agent logic:
  - `agent.py`
- Supporting logic (older/auxiliary):
  - `gann_elliott.py`
- Data and reports:
  - `data/SPY.csv`
  - `data/SPY_confluence.csv`
  - `reports/portfolio_confluence.csv`
  - `reports/portfolio_gann_elliott.csv`
  - `reports/portfolio_super_confluence.csv`
- Web/dashboard:
  - `web/` (HTML/JS dashboard reading CSVs from `web/data/`)
- Environment and config:
  - `environment.yml`
  - `.github/workflows/...` (confluence_agent GitHub Actions workflow)

---

## 3. Existing Code & Data Structures

### 3.1 Agent Output Format (Base Confluence)

Current **trade output schema** (`reports/portfolio_confluence.csv`):

```text
Symbol,Signal,EntryDate,ExitDate,EntryPrice,ExitPrice,PNL,EntryLow,EntryHigh,Stop,Target1,Target2,ExpiryDate,Status
