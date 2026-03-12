# main.py
# ─────────────────────────────────────────────────────────────────────────────
# Entry point for the data pipeline.
# Orchestrates: ingestion → cleaning → alignment → COP → output.
#
# Run:
#   python main.py
#
# Output:
#   data/processed/dataset_clean.csv
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
from pathlib import Path
from utils import (
    load_all_sources,
    summarize_dataset,
    clean_temperatures,
    clean_flow_rates,
    clean_power,
    resample_to_5min,
    align_events,
    compute_cop,
)


# ── 1. INGESTION ──────────────────────────────────────────────────────────────
sources = load_all_sources()


# ── 2. EXPLORATION ────────────────────────────────────────────────────────────
for name, df in sources.items():
    summarize_dataset(df, name)


# ── 3. CLEANING ───────────────────────────────────────────────────────────────
sources["chiller_temps"] = clean_temperatures(sources["chiller_temps"])
sources["chiller_power"] = clean_power(sources["chiller_power"])
sources["pump_flow"] = clean_flow_rates(sources["pump_flow"])


# ── 4. RESAMPLING & ALIGNMENT ─────────────────────────────────────────────────
df = resample_to_5min({
    "chiller_temps": sources["chiller_temps"],
    "pump_flow": sources["pump_flow"],
    "chiller_power": sources["chiller_power"],
})
events = align_events(sources["events"], pd.DatetimeIndex(df.index))
df = df.join(events)


# ── 5. DERIVED SIGNALS ────────────────────────────────────────────────────────
df = compute_cop(df)


# ── 6. OUTPUT ─────────────────────────────────────────────────────────────────
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
df.to_csv(PROCESSED_DIR / "dataset_clean.csv")
print(f"\nSaved {len(df)} rows to {PROCESSED_DIR / 'dataset_clean.csv'}")
