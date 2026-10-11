"""
Run example SQL queries against the database and print the results.

Run from the project root:  python src/explore_queries.py
"""
import sqlite3

import pandas as pd

QUERIES = {
    "1. Average KPIs per region": """
        SELECT c.region,
               ROUND(AVG(k.latency_ms), 2)      AS avg_latency_ms,
               ROUND(AVG(k.throughput_mbps), 2) AS avg_throughput_mbps,
               ROUND(AVG(k.packet_loss_pct), 2) AS avg_packet_loss_pct
        FROM kpis k
        JOIN cells c ON c.cell_id = k.cell_id
        GROUP BY c.region
        ORDER BY avg_latency_ms DESC;
    """,
    "2. Top 5 cells by average latency": """
        SELECT cell_id, ROUND(AVG(latency_ms), 2) AS avg_latency_ms
        FROM kpis
        GROUP BY cell_id
        ORDER BY avg_latency_ms DESC
        LIMIT 5;
    """,
    "3. Busiest hour of the day (average users)": """
        SELECT CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
               ROUND(AVG(active_users), 1) AS avg_users
        FROM kpis
        GROUP BY hour
        ORDER BY avg_users DESC
        LIMIT 5;
    """,
    "4. Cells with the most flagged anomalies": """
        SELECT cell_id, SUM(is_anomaly) AS anomaly_count
        FROM kpis
        GROUP BY cell_id
        ORDER BY anomaly_count DESC
        LIMIT 5;
    """,
    "5. Worst latency reading per tower type": """
        SELECT c.tower_type, MAX(k.latency_ms) AS worst_latency_ms
        FROM kpis k
        JOIN cells c ON c.cell_id = k.cell_id
        GROUP BY c.tower_type;
    """,
    "6. Daily average latency (first 7 days)": """
        SELECT DATE(timestamp) AS day, ROUND(AVG(latency_ms), 2) AS avg_latency_ms
        FROM kpis
        GROUP BY day
        ORDER BY day
        LIMIT 7;
    """,
}


def main() -> None:
    with sqlite3.connect("data/teleq.db") as conn:
        for title, sql in QUERIES.items():
            print(f"\n=== {title} ===")
            print(pd.read_sql_query(sql, conn).to_string(index=False))


if __name__ == "__main__":
    main()
