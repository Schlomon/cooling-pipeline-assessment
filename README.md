# Technical Assignment – Data Pipeline
## Sensor Data Cleaning, Resampling & Derived Signals · Chilled-Water Cooling System

> **Estimated time: 2 hours.**  
> Read this README fully before starting.

---

## How to Submit

1. **Fork** this repository to your personal GitHub account
2. Create a branch named `submission/<your-name>`
3. Complete your work in `main.py` and `utils.py`
4. Save your output to `data/processed/dataset_clean.csv`
5. Open a **Pull Request** back to this repository when you're done — add a short description of your approach and any key decisions

---

## Project Structure

```
option-b-data-pipeline/
│
├── README.md                        ← You are here
│
├── data/
│   ├── raw/                         ← Input data — DO NOT MODIFY
│   │   ├── chiller_temperatures_1min.csv
│   │   ├── pump_flow_rates_30sec.csv
│   │   ├── chiller_power_5min.csv
│   │   └── equipment_events.csv
│   │
│   └── processed/                   ← Write your output here
│
├── main.py                          ← Entry point — orchestrates the pipeline
└── utils.py                         ← Your implementation goes here
```

---

## The Dataset

One week of sensor data (2024-03-01 to 2024-03-07) from a chilled-water cooling loop. Three time-series files at different sampling rates, plus an event log.

| File | Signals | Sample Rate |
|------|---------|-------------|
| `chiller_temperatures_1min.csv` | `supply_temp_c`, `return_temp_c` | 1 min |
| `pump_flow_rates_30sec.csv` | `pump1_flow_m3h`, `pump2_flow_m3h`, `pump3_flow_m3h` | 30 sec |
| `chiller_power_5min.csv` | `chiller1_power_kw`, `chiller2_power_kw` | 5 min |
| `equipment_events.csv` | Fault codes, status changes (event-driven) | On change |

### Known Data Issues

- **Missing values**: ~2% of readings are blank across the time-series files
- **Outlier spikes**: A small number of temperature readings are physically implausible
- **Chiller-02 outage**: On 2024-03-03, CHILLER-02 was offline from ~08:00 to ~14:00. Power reads `0.0` during this window — this is a **legitimate shutdown**, not a sensor error
- **Equipment events**: Timestamps are irregular and do not align to any fixed interval

---

## Your Tasks

### Task 1 — Cleaning  *(implement in `utils.py`)*

**`clean_temperatures(df)`**  
Clean `chiller_temperatures_1min.csv`:
- Handle missing values — choose an appropriate strategy and comment why
- Detect and remove physically implausible readings  
  - `supply_temp_c`: valid range 4–12 °C  
  - `return_temp_c`: valid range 8–18 °C

**`clean_power(df)`**  
Clean `chiller_power_5min.csv`:
- Handle missing values
- `0.0 kW` is a **valid value** (chiller offline) — do not treat it as missing or an error
- Valid operating range when running: 80–320 kW

**`clean_flow_rates(df)`**  
Clean `pump_flow_rates_30sec.csv`:
- Handle missing values
- Negative values are sensor errors; valid range: 0–65 m³/h

---

### Task 2 — Resampling & Alignment  *(implement in `utils.py`)*

**`resample_to_5min(dataframes)`**  
Resample all three time-series to a **common 5-minute frequency** and merge into a single dataframe:
- High-frequency signals (30-sec, 1-min): aggregate to 5-min windows — choose mean, max, or sum and comment your reasoning
- The output should cover `2024-03-01 00:00` → `2024-03-07 23:55` with no gaps in the index

**`align_events(events_df, time_index)`**  
Make the event log joinable with the 5-minute time-series. For each 5-minute window, surface whether an active fault was present and which asset it affected. The design is up to you — comment your approach.

---

### Task 3 — Derived Signal  *(implement in `utils.py`)*

**`compute_cop(df)`**  
Compute **Coefficient of Performance (COP)** for each chiller at each 5-minute timestep:

```
COP = (mass_flow_kg_s × Cp × ΔT) / power_kw

where:
  mass_flow_kg_s = total_pump_flow_m3h × 1000 / 3600
  Cp             = 4.18  kJ/kg·°C
  ΔT             = return_temp_c − supply_temp_c
  power_kw       = chiller power consumption
```

You'll need to make explicit assumptions — comment them in your code:
- How do you split total pump flow between the two chillers?
- What do you return when `power_kw == 0` (chiller offline)?
- What do you return when any required signal is missing?

Add columns `cop_chiller1` and `cop_chiller2` to the dataframe. Use `NaN` where COP cannot be computed.

---

### Task 4 — Output  *(implement in `main.py`)*

Save the final aligned dataset to `data/processed/dataset_clean.csv`.

---

## Getting Started

```bash
pip install pandas numpy
python main.py
```

`load_all_sources()` and `summarize_dataset()` are already implemented for you in `utils.py` — run `main.py` straight away to see the data summary before you start.

---

## Evaluation

| Criteria | Weight |
|----------|--------|
| Code quality & structure | 25% |
| Cleaning decisions & inline reasoning | 30% |
| Resampling & alignment correctness | 20% |
| COP computation & edge case handling | 25% |

We value **readable, well-commented code** over clever one-liners. Your comments are part of your answer — use them to show your thinking, not just describe what the code does.

---

*Questions? Open a GitHub issue in this repo.*
