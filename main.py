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



# ── 4. RESAMPLING & ALIGNMENT ─────────────────────────────────────────────────
# TODO: call resample_to_5min() with the cleaned time-series dataframes
# TODO: call align_events() and join the result onto the resampled dataframe


# ── 5. DERIVED SIGNALS ────────────────────────────────────────────────────────
# TODO: call compute_cop() and add COP columns to the dataframe


# ── 6. OUTPUT ─────────────────────────────────────────────────────────────────
# TODO: save the final dataframe to data/processed/dataset_clean.csv


if __name__ == "__main__":
    pass  # remove once you start implementing
