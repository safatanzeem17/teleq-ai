"""
Train an Isolation Forest to detect anomalous network readings.

Key idea: latency and throughput depend on how many users are connected, so
raw values mislead (80 ms is normal at peak but suspicious at 3 AM). We first
learn the "expected" latency and throughput for a given load, then feed the
model the *residuals* (actual minus expected), which expose real faults.

Reads data/teleq.db, evaluates against the is_anomaly labels on held-out rows,
and saves the model to models/isolation_forest.joblib.

Run from the project root:  python src/anomaly_model.py
"""
import sqlite3
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DB_PATH = "data/teleq.db"
MODEL_PATH = Path("models/isolation_forest.joblib")
FEATURES = ["latency_resid", "throughput_resid", "signal_dbm", "packet_loss_pct"]


def load_data() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM kpis", conn)


class AnomalyDetector:
    """Load-adjusted Isolation Forest."""

    def __init__(self, contamination: float = 0.02):
        self.latency_lr = LinearRegression()
        self.throughput_lr = LinearRegression()
        self.scaler = StandardScaler()
        self.forest = IsolationForest(n_estimators=200, contamination=contamination, random_state=42)

    def _features(self, df: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame(index=df.index)
        users = df[["active_users"]]
        out["latency_resid"] = df["latency_ms"] - self.latency_lr.predict(users)
        out["throughput_resid"] = df["throughput_mbps"] - self.throughput_lr.predict(users)
        out["signal_dbm"] = df["signal_dbm"]
        out["packet_loss_pct"] = df["packet_loss_pct"]
        return out[FEATURES]

    def fit(self, df: pd.DataFrame) -> "AnomalyDetector":
        users = df[["active_users"]]
        self.latency_lr.fit(users, df["latency_ms"])
        self.throughput_lr.fit(users, df["throughput_mbps"])
        X = self._features(df)
        self.forest.fit(self.scaler.fit_transform(X))
        return self

    def predict(self, df: pd.DataFrame):
        """Return 1 for anomaly, 0 for normal."""
        X = self.scaler.transform(self._features(df))
        return (self.forest.predict(X) == -1).astype(int)


def main() -> None:
    df = load_data()

    # Hold out 25% of the data so we test on rows the model has never seen.
    train, test = train_test_split(df, test_size=0.25, random_state=42, stratify=df["is_anomaly"])

    detector = AnomalyDetector(contamination=0.02).fit(train)
    pred = detector.predict(test)

    print("Confusion matrix (rows = actual, cols = predicted):")
    print(confusion_matrix(test["is_anomaly"], pred))
    print("\nClassification report:")
    print(classification_report(test["is_anomaly"], pred, target_names=["normal", "anomaly"], digits=3))

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(detector, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    # Re-import ourselves so the saved model refers to "anomaly_model.AnomalyDetector"
    # instead of "__main__.AnomalyDetector", which lets other files load it later.
    import anomaly_model

    anomaly_model.main()
