"""
Load the generated CSV files into a SQLite database.

Output: data/teleq.db
Run from the project root:  python src/load_db.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("data/teleq.db")

SCHEMA = """
DROP TABLE IF EXISTS kpis;
DROP TABLE IF EXISTS cells;

CREATE TABLE cells (
    cell_id    TEXT PRIMARY KEY,
    region     TEXT NOT NULL,
    tower_type TEXT NOT NULL
);

CREATE TABLE kpis (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT NOT NULL,
    cell_id         TEXT NOT NULL,
    latency_ms      REAL,
    throughput_mbps REAL,
    signal_dbm      REAL,
    packet_loss_pct REAL,
    active_users    INTEGER,
    is_anomaly      INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (cell_id) REFERENCES cells (cell_id)
);

CREATE INDEX idx_kpis_cell_time ON kpis (cell_id, timestamp);
CREATE INDEX idx_kpis_time ON kpis (timestamp);
"""


def main() -> None:
    cells = pd.read_csv("data/cells.csv")
    kpis = pd.read_csv("data/network_kpis.csv")

    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        cells.to_sql("cells", conn, if_exists="append", index=False)
        kpis.to_sql("kpis", conn, if_exists="append", index=False)

        n_cells = conn.execute("SELECT COUNT(*) FROM cells").fetchone()[0]
        n_kpis = conn.execute("SELECT COUNT(*) FROM kpis").fetchone()[0]

    print(f"Loaded {n_cells} cells and {n_kpis} KPI rows into {DB_PATH}")


if __name__ == "__main__":
    main()
