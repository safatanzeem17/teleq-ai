"""
Generate a synthetic telecom network KPI dataset with injected anomalies.

Output: data/network_kpis.csv
Run from the project root:  python src/generate_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_CELLS = 20
DAYS = 30
ANOMALY_RATE = 0.02  # about 2% of rows will be anomalous

rng = np.random.default_rng(SEED)

REGIONS = ["North", "South", "East", "West", "Central"]


def build_cells() -> pd.DataFrame:
    """One row per cell tower."""
    cell_ids = [f"CELL_{i:03d}" for i in range(1, N_CELLS + 1)]
    return pd.DataFrame(
        {
            "cell_id": cell_ids,
            "region": rng.choice(REGIONS, size=N_CELLS),
            "tower_type": rng.choice(["Macro", "Micro", "Small"], size=N_CELLS, p=[0.5, 0.3, 0.2]),
        }
    )


def build_kpis(cells: pd.DataFrame) -> pd.DataFrame:
    """Hourly KPIs per cell for DAYS days."""
    timestamps = pd.date_range("2026-09-01", periods=DAYS * 24, freq="h")
    frames = []

    for cell_id in cells["cell_id"]:
        hours = timestamps.hour.to_numpy()

        # Users follow a daily pattern: low at night, peak in the evening.
        base_users = 40 + 60 * np.exp(-((hours - 20) ** 2) / 18)
        active_users = np.clip(rng.normal(base_users, 8), 1, None).round().astype(int)

        # More users -> more latency, less throughput per user.
        latency_ms = 20 + 0.25 * active_users + rng.normal(0, 3, len(hours))
        throughput_mbps = np.clip(120 - 0.5 * active_users + rng.normal(0, 8, len(hours)), 5, None)
        signal_dbm = rng.normal(-80, 4, len(hours))
        packet_loss_pct = np.clip(rng.normal(0.5, 0.2, len(hours)), 0, None)

        frames.append(
            pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "cell_id": cell_id,
                    "latency_ms": latency_ms,
                    "throughput_mbps": throughput_mbps,
                    "signal_dbm": signal_dbm,
                    "packet_loss_pct": packet_loss_pct,
                    "active_users": active_users,
                }
            )
        )

    df = pd.concat(frames, ignore_index=True)
    return inject_anomalies(df)


def inject_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Corrupt a random ~2% of rows with realistic fault patterns and label them."""
    df["is_anomaly"] = 0
    n_anomalies = int(len(df) * ANOMALY_RATE)
    idx = rng.choice(df.index, size=n_anomalies, replace=False)
    kinds = rng.choice(["latency_spike", "throughput_drop", "packet_loss", "signal_fade"], size=n_anomalies)

    for i, kind in zip(idx, kinds):
        if kind == "latency_spike":
            df.at[i, "latency_ms"] *= rng.uniform(3, 6)
        elif kind == "throughput_drop":
            df.at[i, "throughput_mbps"] *= rng.uniform(0.05, 0.25)
        elif kind == "packet_loss":
            df.at[i, "packet_loss_pct"] = rng.uniform(5, 15)
        elif kind == "signal_fade":
            df.at[i, "signal_dbm"] = rng.uniform(-115, -100)
        df.at[i, "is_anomaly"] = 1

    num_cols = ["latency_ms", "throughput_mbps", "signal_dbm", "packet_loss_pct"]
    df[num_cols] = df[num_cols].round(2)
    return df


def main() -> None:
    cells = build_cells()
    kpis = build_kpis(cells)

    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    cells.to_csv(out_dir / "cells.csv", index=False)
    kpis.to_csv(out_dir / "network_kpis.csv", index=False)

    print(f"cells.csv: {len(cells)} rows")
    print(f"network_kpis.csv: {len(kpis)} rows, {kpis['is_anomaly'].sum()} anomalies")


if __name__ == "__main__":
    main()
