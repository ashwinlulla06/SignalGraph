from datetime import datetime, timezone
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

from backend.ml.features import FEATURE_NAMES

DATA_FILE = Path("data/training/market_features.csv")

ARTIFACT_DIRECTORY = Path("backend/ml/artifacts")

TRAINING_RATIO = 0.80
CONTAMINATION = 0.01
RANDOM_STATE = 42

def train_symbol_model(symbol: str, symbol_frame: pd.DataFrame) -> None:
    symbol_frame = symbol_frame.sort_values("start_time").reset_index(drop=True)

    split_index = int(len(symbol_frame) * TRAINING_RATIO)

    training_frame = symbol_frame.iloc[:split_index]

    validation_frame = symbol_frame.iloc[split_index:].copy()

    training_features = training_frame[FEATURE_NAMES]

    validation_features = validation_frame[FEATURE_NAMES]

    model = IsolationForest(
        n_estimators=300,
        contamination=CONTAMINATION,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    model.fit(training_features)

    validation_frame['prediction'] = model.predict(validation_features)

    validation_frame['decision_score'] = model.decision_function(validation_features)

    anomalies = validation_frame[validation_frame["prediction"] == -1].sort_values('decision_score')

    artifact = {
        "model_version" : 1,
        "symbol" : symbol,
        "feature_names": FEATURE_NAMES,
        "trained_at" : datetime.now(timezone.utc).isoformat(),
        "training_start": training_frame['start_time'].min().isoformat(),
        "training_end": training_frame['start_time'].max().isoformat(),
        "training_rows": len(training_frame),
        "contamination": CONTAMINATION,
        "model": model
    }

    artifact_file = ARTIFACT_DIRECTORY / f"{symbol.lower()}_model.joblib"

    joblib.dump(artifact, artifact_file)

    anomaly_rate = len(anomalies) / len(validation_frame)

    print(
        f"--- {symbol} ---"
    )

    print(
        "Training rows:",
        len(training_frame),
    )

    print(
        "Validation rows:",
        len(validation_frame),
    )

    print(
        "Validation anomalies:",
        len(anomalies),
    )

    print(
        "Validation anomaly rate:",
        f"{anomaly_rate:.2%}",
    )

    print(
        "Model saved to:",
        artifact_file,
    )

    if anomalies.empty:
        print(
            "No validation anomalies found."
        )

        return

    report_columns = [
        "start_time",
        "open",
        "high",
        "low",
        "close",
        "return_1",
        "range_percent",
        "rolling_volatility",
        "decision_score",
    ]

    print()
    print(
        "Strongest validation anomalies:"
    )

    print(anomalies[report_columns].head(10).to_string(index=False))


def main() -> None:
    feature_frame = pd.read_csv(
        DATA_FILE,
        parse_dates=[
            "start_time"
        ],
    )

    missing_columns = [
        feature_name
        for feature_name
        in FEATURE_NAMES
        if feature_name
        not in feature_frame.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing feature columns: "
            f"{missing_columns}"
        )

    ARTIFACT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    for symbol, symbol_frame in (
        feature_frame.groupby("symbol")
    ):
        train_symbol_model(
            symbol=symbol,
            symbol_frame=symbol_frame,
        )


if __name__ == "__main__":
    main()

