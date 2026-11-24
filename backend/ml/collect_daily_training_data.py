import asyncio
from pathlib import Path

import pandas as pd

from backend.config import TWELVE_DATA_API_KEY
from backend.ml.daily_features import (
    build_daily_features,
)
from backend.providers.twelve_data_provider import (
    TwelveDataProvider,
)


SYMBOLS = [
    "NVDA",
    "AMD",
    "MSFT",
    "GOOGL",
    "META",
]

OUTPUT_SIZE = 2500

OUTPUT_DIRECTORY = Path(
    "data/training"
)

OUTPUT_FILE = (
    OUTPUT_DIRECTORY
    / "daily_market_features.csv"
)


async def main():
    provider = TwelveDataProvider(
        api_key=TWELVE_DATA_API_KEY
    )

    all_feature_rows = []

    try:
        for symbol in SYMBOLS:
            print(
                f"Downloading daily candles "
                f"for {symbol}..."
            )

            candles = (
                await provider.get_daily_candles(
                    symbol=symbol,
                    output_size=OUTPUT_SIZE,
                )
            )

            feature_rows = (
                build_daily_features(candles)
            )

            all_feature_rows.extend(
                feature_rows
            )

            print(
                f"{symbol}: "
                f"{len(candles)} candles, "
                f"{len(feature_rows)} feature rows"
            )

    finally:
        await provider.close()

    feature_frame = pd.DataFrame(
        all_feature_rows
    )

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    feature_frame.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "Total daily feature rows:",
        len(feature_frame),
    )

    print(
        "Saved to:",
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    asyncio.run(main())