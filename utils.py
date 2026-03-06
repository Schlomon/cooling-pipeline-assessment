# utils.py
# ─────────────────────────────────────────────────────────────────────────────
# Helper functions for the data pipeline.
# load_all_sources() and summarize_dataset() are implemented for you.
# Implement the remaining functions. Add new helpers freely.
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from pathlib import Path

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")

CP_WATER = 4.18        # kJ / kg·°C
WATER_DENSITY = 1000.0 # kg / m³


# ── INGESTION (pre-implemented) ───────────────────────────────────────────────

def load_all_sources() -> dict[str, pd.DataFrame]:
    """Load all raw CSV files. Returns a dict keyed by short source name."""
    files = {
        "chiller_temps":  "chiller_temperatures_1min.csv",
        "pump_flow":      "pump_flow_rates_30sec.csv",
        "chiller_power":  "chiller_power_5min.csv",
        "events":         "equipment_events.csv",
    }
    loaded = {}
    for key, filename in files.items():
        path = RAW_DATA_DIR / filename
        df = pd.read_csv(path, parse_dates=["timestamp"])
        df = df.set_index("timestamp").sort_index()
        loaded[key] = df
    return loaded


def summarize_dataset(df: pd.DataFrame, name: str) -> None:
    """Print a summary for a single dataframe."""
    print(f"\n{'─' * 50}")
    print(f"  {name}  {df.shape}")
    print(f"  Time range: {df.index.min()}  →  {df.index.max()}")
    print(f"\n  Missing values:")
    print(df.isnull().sum().to_string(header=False))
    numeric = df.select_dtypes(include="number")
    if not numeric.empty:
        print(f"\n  Statistics:")
        print(numeric.agg(["min", "mean", "max"]).round(3).to_string())


# ── CLEANING ──────────────────────────────────────────────────────────────────

def clean_temperatures(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean chiller supply/return temperature data.

    Normal operating ranges:
        supply_temp_c:  4.0 - 12.0 °C
        return_temp_c:  8.0 - 18.0 °C

    TODO:
    - Handle missing values (choose a strategy and comment why)
    - Detect and handle physically implausible readings
    """
    # TODO: implement
    pass


def clean_flow_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean pump flow rate data.

    Normal operating range: 0 - 65 m³/h per pump
    Negative values are sensor errors.

    TODO:
    - Handle missing values
    - Handle out-of-range values
    """
    # TODO: implement
    pass


def clean_power(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean chiller power consumption data.

    Normal operating range when running: 80 - 320 kW
    IMPORTANT: 0.0 kW is valid — it means the chiller is offline. Do NOT treat
    it as missing or as an error.

    TODO:
    - Handle missing values
    - Handle implausible non-zero readings
    """
    # TODO: implement
    pass


# ── RESAMPLING & ALIGNMENT ────────────────────────────────────────────────────

def resample_to_5min(dataframes: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Resample all time-series signals to a common 5-minute frequency
    and merge into a single wide dataframe.

    Input dict keys: 'chiller_temps', 'pump_flow', 'chiller_power'
    (do not include 'events' here — handle that in align_events)

    Guidelines:
    - High-frequency signals (30-sec, 1-min): aggregate per 5-min window
    - chiller_power is already at 5-min — just align the index
    - Output must cover 2024-03-01 00:00 → 2024-03-07 23:55, no index gaps

    Comment your aggregation choices (mean vs. max vs. sum) and why.

    Returns:
        A single wide dataframe indexed at 5-min frequency.
    """
    # TODO: implement
    pass


def align_events(events_df: pd.DataFrame, time_index: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Make the event log joinable with the 5-minute time-series.

    For each 5-minute window, surface whether an active fault was present
    and which asset it affected. Design this however makes sense to you —
    there's no single right answer. Comment your approach.

    Returns:
        A dataframe indexed like time_index with event-derived columns.
    """
    # TODO: implement
    pass


# ── DERIVED SIGNALS ───────────────────────────────────────────────────────────

def compute_cop(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute COP for each chiller at each 5-minute timestep.

    Formula:
        COP = (mass_flow_kg_s * CP_WATER * delta_T) / power_kw

        mass_flow_kg_s = total_pump_flow_m3h * WATER_DENSITY / 3600
        delta_T        = return_temp_c - supply_temp_c
        power_kw       = chiller power consumption

    You need to make and document explicit assumptions:
        - How do you split total pump flow between the two chillers?
        - What do you return when power_kw == 0.0 (chiller offline)?
        - What do you return when any required input is NaN?

    Adds columns: cop_chiller1, cop_chiller2 (NaN where not computable).
    Returns the dataframe with those columns added.
    """
    # TODO: implement
    pass
