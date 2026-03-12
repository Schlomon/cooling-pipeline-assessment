import os
import matplotlib.pyplot as plt
from utils import load_all_sources


def plot_timeseries(sources: dict) -> None:
    """Plot an overview of all three raw time-series and save to disk."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

    # Temperatures (1-min)
    temps = sources["chiller_temps"]
    axes[0].plot(temps.index, temps["supply_temp_c"], label="Supply temp", linewidth=0.5)
    axes[0].plot(temps.index, temps["return_temp_c"], label="Return temp", linewidth=0.5)
    axes[0].set_ylabel("Temperature (°C)")
    axes[0].set_title("Chiller Temperatures (1-min)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Pump flow rates (30-sec)
    flow = sources["pump_flow"]
    for col in flow.columns:
        axes[1].plot(flow.index, flow[col], label=col, linewidth=0.4)
    axes[1].set_ylabel("Flow (m³/h)")
    axes[1].set_title("Pump Flow Rates (30-sec)")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Chiller power (5-min)
    power = sources["chiller_power"]
    axes[2].plot(power.index, power["chiller1_power_kw"], label="Chiller 1", linewidth=0.6)
    axes[2].plot(power.index, power["chiller2_power_kw"], label="Chiller 2", linewidth=0.6)
    axes[2].set_ylabel("Power (kW)")
    axes[2].set_xlabel("Timestamp")
    axes[2].set_title("Chiller Power (5-min)")
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    fig.tight_layout()
    os.makedirs("data/processed", exist_ok=True)
    plt.savefig("data/processed/timeseries_overview.png", dpi=150)
    plt.show()


if __name__ == "__main__":
    sources = load_all_sources()
    plot_timeseries(sources)
