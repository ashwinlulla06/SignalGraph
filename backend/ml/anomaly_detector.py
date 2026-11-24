from collections import deque
from datetime import datetime
from datetime import timezone
from pathlib import Path

import joblib
import pandas as pd

from backend.ml.features import FEATURE_NAMES
from backend.ml.features import build_candle_features
from backend.models import MarketAnomalyResult
from backend.models import MarketCandle


MAX_CONTEXT_CANDLES = 120


class AnomalyDetector:
    def __init__(
        self,
        artifact_directory: Path,
    ):
        self._artifact_directory = (
            artifact_directory
        )

        self._artifacts: dict[str, dict] = {}

        self._candles_by_symbol: dict[
            str,
            deque[MarketCandle],
        ] = {}

        self._last_analyzed_time: dict[
            str,
            datetime,
        ] = {}

        self._load_artifacts()

    @property
    def model_symbols(self) -> list[str]:
        return sorted(self._artifacts)

    def _load_artifacts(self) -> None:
        if not self._artifact_directory.exists():
            print(
                "Anomaly model directory does "
                "not exist: "
                f"{self._artifact_directory}"
            )
            return

        artifact_files = (
            self._artifact_directory.glob(
                "*_model.joblib"
            )
        )

        for artifact_file in artifact_files:
            try:
                artifact = joblib.load(
                    artifact_file
                )

                symbol = str(
                    artifact["symbol"]
                ).upper()

                feature_names = artifact[
                    "feature_names"
                ]

                if feature_names != FEATURE_NAMES:
                    raise ValueError(
                        "Model features do not match "
                        "the current feature code"
                    )

                if "model" not in artifact:
                    raise ValueError(
                        "Artifact contains no model"
                    )

                self._artifacts[symbol] = (
                    artifact
                )

            except Exception as error:
                print(
                    "Could not load anomaly model "
                    f"{artifact_file.name}: "
                    f"{type(error).__name__}: "
                    f"{error}"
                )

        print(
            "Anomaly models loaded:",
            len(self._artifacts),
            self.model_symbols,
        )

    def seed_candles(
        self,
        symbol: str,
        candles: list[MarketCandle],
    ) -> None:
        normalized_symbol = symbol.upper()

        if normalized_symbol not in self._artifacts:
            return

        candles_by_time = {
            candle.start_time: candle
            for candle in candles
        }

        ordered_candles = sorted(
            candles_by_time.values(),
            key=lambda candle: candle.start_time,
        )

        self._candles_by_symbol[
            normalized_symbol
        ] = deque(
            ordered_candles[
                -MAX_CONTEXT_CANDLES:
            ],
            maxlen=MAX_CONTEXT_CANDLES,
        )

    def analyze_finalized_candle(
        self,
        candle: MarketCandle,
    ) -> MarketAnomalyResult | None:
        symbol = candle.symbol.upper()

        artifact = self._artifacts.get(symbol)

        if artifact is None:
            return None

        last_analyzed_time = (
            self._last_analyzed_time.get(symbol)
        )

        if (
            last_analyzed_time is not None
            and candle.start_time
            <= last_analyzed_time
        ):
            return None

        candle_context = (
            self._candles_by_symbol.setdefault(
                symbol,
                deque(
                    maxlen=MAX_CONTEXT_CANDLES
                ),
            )
        )

        if candle_context:
            latest_context_time = (
                candle_context[-1].start_time
            )

            if candle.start_time < latest_context_time:
                return None

            if candle.start_time == latest_context_time:
                candle_context[-1] = candle
            else:
                candle_context.append(candle)
        else:
            candle_context.append(candle)

        feature_rows = build_candle_features(
            list(candle_context)
        )

        if not feature_rows:
            return None

        latest_feature_row = feature_rows[-1]

        if (
            latest_feature_row["start_time"]
            != candle.start_time
        ):
            return None

        feature_names = artifact[
            "feature_names"
        ]

        feature_values = {
            feature_name: float(
                latest_feature_row[
                    feature_name
                ]
            )
            for feature_name in feature_names
        }

        feature_frame = pd.DataFrame(
            [feature_values],
            columns=feature_names,
        )

        model = artifact["model"]

        prediction = int(
            model.predict(feature_frame)[0]
        )

        decision_score = float(
            model.decision_function(
                feature_frame
            )[0]
        )

        self._last_analyzed_time[
            symbol
        ] = candle.start_time

        return MarketAnomalyResult(
            symbol=symbol,
            start_time=candle.start_time,
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
