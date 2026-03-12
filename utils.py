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
    """
    df = df.copy()

    # Setting implausible readings to NaN as they give no information -> handle them the same ways as missing values
    df.loc[~df["supply_temp_c"].between(4.0, 12.0), "supply_temp_c"] = np.nan
    df.loc[~df["return_temp_c"].between(8.0, 18.0), "return_temp_c"] = np.nan

    # Limit interpolation to 15 min. More would likely be a real outage / sensor failure
    # We choose linear for three resons:
    #   1. Temperature changes smoothely
    #   2. Data follows a sinusoidal pattern with a ~24 h period. At a 15 min scale, it is effectively linear.
    #   3. Simplicity
    df = df.interpolate(method="linear", limit=15)

    return df


def clean_flow_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean pump flow rate data.

    Normal operating range: 0 - 65 m³/h per pump
    Negative values are sensor errors.
    """
    df = df.copy()

    # Replace values outside of the valid operating range 0-65 m^3/h with NaN
    for col in df.columns:
        df.loc[~df[col].between(0.0, 65.0), col] = np.nan

    # Linear interpolation, limit 30 rows = 15 min at 30-sec resolution.
    # Same reasoning as for temperatures
    df = df.interpolate(method="linear", limit=30)

    return df


def clean_power(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean chiller power consumption data.

    Normal operating range when running: 80 - 320 kW
    IMPORTANT: 0.0 kW is valid — it means the chiller is offline. Do NOT treat
    it as missing or as an error.
    """
    df = df.copy()

    # Replace non-zero values outside the valid operating range 80-320 kW with NaN
    for col in df.columns:
        mask = (df[col] != 0) & ~df[col].between(80.0, 320.0)
        df.loc[mask, col] = np.nan

    # Forward-fill with limit to 15 min (3 rows at 5 min resolution).
    # Even though power also follows a sinusoidal pattern, to keep it simple,
    # we use forward fill to avoid generating values outside the valid range,
    # which can occur when e.g. using linear interpolation between a valid zero and a non-zero value.
    df = df.ffill(limit=3)

    return df


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
    target_index = pd.date_range(
        start="2024-03-01 00:00", end="2024-03-07 23:55", freq="5min"
    )

    # Temperatures 1 min -> aggregate using mean to 5 min
    # Mean best represents the window.
    # Max would overstate, sum is nonsensical.
    temps = dataframes["chiller_temps"].resample("5min").mean()

    # Pump flow rates 30 s -> aggregate using mean to 5 min
    # Mean gives the average flow rate, which is what we need COP.
    # Max would overstate, sum would give volume.
    flow = dataframes["pump_flow"].resample("5min").mean()

    # Power is already 5 min
    power = dataframes["chiller_power"]

    # Merge all three on the common 5-min index.
    # Reindex to the full target range to ensure no gaps. Not strictly required on the sample data but keep for code quality / reusability.
    merged = temps.join(flow, how="outer").join(power, how="outer")
    merged = merged.reindex(target_index)
    merged.index.name = "timestamp"

    return merged


def align_events(events_df: pd.DataFrame, time_index: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Make the event log joinable with the 5-minute time-series.

    For each 5-minute window, surface whether an active fault was present
    and which asset it affected. Design this however makes sense to you —
    there's no single right answer. Comment your approach.

    Returns:
        A dataframe indexed like time_index with event-derived columns.
    """
    # Approach: create one boolean column per asset that had a fault.
    # For each FAULT event, set True at that timestamp; for each FAULT_CLEAR,
    # set False. Forward-fill to mark the entire fault window, then reindex to the 5 min grid.

    faults = events_df[events_df["event_type"].isin(["FAULT", "FAULT_CLEAR"])]

    # Get unique assets that have faults
    fault_assets = faults["asset_id"].unique()

    result = pd.DataFrame(index=time_index)

    for asset in fault_assets:
        asset_events = faults[faults["asset_id"] == asset].copy()

        # Create a series: True at FAULT, False at FAULT_CLEAR
        fault_flag = asset_events["event_type"].map(
            {"FAULT": True, "FAULT_CLEAR": False}
        )
        fault_flag.index = asset_events.index

        # Reindex to the 5-min grid and forward-fill.
        # Fill timestamps before first event with False.
        fault_flag = fault_flag.reindex(time_index, method="ffill").fillna(False)

        col_name = f"{asset}_FAULT"
        result[col_name] = fault_flag

    return result


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
    df = df.copy()

    # Assumptions:
    # 1. Split flow 50/50. The draw about the same power i.e. seem to be of equal size.
    #    We could choose a weighted split basede on the per window power conspumtion,
    #    however that would be circular (user power to calculate flow then divide by power)
    # 2. power_kw == 0 => div by zero => COP undefined: return NaN
    # 3. Any required input is NaN: propagate NaN

    total_flow_m3h = (
        df["pump1_flow_m3h"] + df["pump2_flow_m3h"] + df["pump3_flow_m3h"]
    )
    flow_per_chiller_m3h = total_flow_m3h / 2.0

    # Convert m^3/h to kg/s
    mass_flow_kg_s = flow_per_chiller_m3h * WATER_DENSITY / 3600.0

    delta_t = df["return_temp_c"] - df["supply_temp_c"]

    # Cooling capacity = mass_flow * Cp * ΔT
    cooling_kw = mass_flow_kg_s * CP_WATER * delta_t

    for chiller_num in [1, 2]:
        power_col = f"chiller{chiller_num}_power_kw"
        power = df[power_col]

        # Replace 0 power with NaN so COP is undefined when offline
        cop = cooling_kw / power.replace(0.0, np.nan)

        df[f"cop_chiller{chiller_num}"] = cop

    return df
