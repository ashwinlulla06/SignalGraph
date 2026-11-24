from datetime import datetime
from datetime import timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

from backend.ml.daily_features import (
    DAILY_FEATURE_NAMES,
)


DATA_FILE = Path(
    "data/training/daily_market_features.csv"
)

ARTIFACT_DIRECTORY = Path(
    "backend/ml/daily_artifacts"
)

TRAINING_RATIO = 0.80
CONTAMINATION = 0.01
RANDOM_STATE = 42


def train_symbol_model(
    symbol: str,
    symbol_frame: pd.DataFrame,
) -> None:
    symbol_frame = (
        symbol_frame
        .sort_values("start_time")
        .reset_index(drop=True)
    )

    if len(symbol_frame) < 100:
        raise ValueError(
            f"Not enough daily rows for {symbol}"
        )

    split_index = int(
        len(symbol_frame) * TRAINING_RATIO
    )

    training_frame = (
        symbol_frame.iloc[:split_index]
    )

    validation_frame = (
        symbol_frame.iloc[split_index:]
        .copy()
    )

    training_features = training_frame[
        DAILY_FEATURE_NAMES
    ]

    validation_features = validation_frame[
        DAILY_FEATURE_NAMES
    ]

    model = IsolationForest(
        n_estimators=300,
        contamination=CONTAMINATION,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    model.fit(training_features)

    validation_frame["prediction"] = (
        model.predict(validation_features)
    )

    validation_frame["decision_score"] = (
        model.decision_function(
            validation_features
        )
    )

    artifact = {
        "model_version": 1,
        "timeframe": "1day",
        "symbol": symbol,
        "feature_names": (
            DAILY_FEATURE_NAMES
        ),
        "trained_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "training_start": (
            training_frame[
                "start_time"
            ].min().isoformat()
        ),
        "training_end": (
            training_frame[
                "start_time"
            ].max().isoformat()
        ),
        "training_rows": (
            len(training_frame)
        ),
        "contamination": CONTAMINATION,
        "model": model,
    }

    artifact_file = (
        ARTIFACT_DIRECTORY
        / f"{symbol.lower()}_model.joblib"
    )

    joblib.dump(
        artifact,
        artifact_file,
    )

    anomaly_count = int(
        (
            validation_frame["prediction"]
            == -1
        ).sum()
    )

    print(f"\n--- {symbol} ---")
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
        anomaly_count,
    )
    print(
        "Model saved to:",
        artifact_file,
    )


def main() -> None:
    feature_frame = pd.read_csv(
        DATA_FILE,
        parse_dates=["start_time"],
    )

    missing_columns = [
        feature_name
        for feature_name
        in DAILY_FEATURE_NAMES
        if feature_name
        not in feature_frame.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing daily feature columns: "
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