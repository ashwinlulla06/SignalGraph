from datetime import date
from datetime import datetime
from datetime import timezone
from pathlib import Path

import joblib
import pandas as pd

from backend.ml.daily_features import (
    DAILY_FEATURE_NAMES,
)
from backend.ml.daily_features import (
    build_daily_features,
)
from backend.models import DailyAnomalyResult
from backend.models import MarketCandle


class DailyAnomalyDetector:
    def __init__(
        self,
        artifact_directory: Path,
    ):
        self._artifact_directory = (
            artifact_directory
        )

        self._artifacts: dict[
            str,
            dict,
        ] = {}

        self._load_artifacts()

    @property
    def model_symbols(self) -> list[str]:
        return sorted(self._artifacts)

    def _load_artifacts(self) -> None:
        if not self._artifact_directory.exists():
            print(
                "Daily model directory does not "
                "exist:",
                self._artifact_directory,
            )
            return

        for artifact_file in (
            self._artifact_directory.glob(
                "*_model.joblib"
            )
        ):
            artifact = joblib.load(
                artifact_file
            )

            symbol = str(
                artifact["symbol"]
            ).upper()

            if (
                artifact["feature_names"]
                != DAILY_FEATURE_NAMES
            ):
                raise ValueError(
                    "Daily model features do not "
                    "match daily feature code"
                )

            self._artifacts[symbol] = (
                artifact
            )

        print(
            "Daily anomaly models loaded:",
            len(self._artifacts),
            self.model_symbols,
        )

    def analyze_day(
        self,
        symbol: str,
        trading_date: date,
        candles: list[MarketCandle],
    ) -> DailyAnomalyResult | None:
        normalized_symbol = symbol.upper()

        artifact = self._artifacts.get(
            normalized_symbol
        )

        if artifact is None:
            return None

        feature_rows = build_daily_features(
            candles
        )

        target_row = next(
            (
                row
                for row in feature_rows
                if row["start_time"].date()
                == trading_date
            ),
            None,
        )

        if target_row is None:
            return None

        feature_values = {
            feature_name: float(
                target_row[feature_name]
            )
            for feature_name
            in DAILY_FEATURE_NAMES
        }

        feature_frame = pd.DataFrame(
            [feature_values],
            columns=DAILY_FEATURE_NAMES,
        )

        model = artifact["model"]

        prediction = int(
            model.predict(
                feature_frame
            )[0]
        )

        decision_score = float(
            model.decision_function(
                feature_frame
            )[0]
        )

        return DailyAnomalyResult(
            symbol=normalized_symbol,
            trading_date=trading_date,
            analyzed_at=datetime.now(
                timezone.utc
            ),
            is_anomaly=(prediction == -1),
            decision_score=decision_score,
            model_version=int(
                artifact["model_version"]
            ),
            features=feature_values,
        )