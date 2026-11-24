import asyncio
from pathlib import Path
import pandas as pd
from backend.providers.twelve_data_provider import TwelveDataProvider
from backend.ml.features import build_candle_features
from backend.config import TWELVE_DATA_API_KEY

SYMBOLS = [
    'NVDA',
    'AMD',
    'MSFT',
    'GOOGL',
    'META'
]

OUTPUT_SIZE = 5000

OUTPUT_DIRECTORY = Path('data/training')

OUTPUT_FILE = OUTPUT_DIRECTORY/"market_features.csv"

async def main():
    provider = TwelveDataProvider(api_key=TWELVE_DATA_API_KEY)

    all_feature_rows = []

    try:
        for symbol in SYMBOLS:
            print(f"Downloading {symbol}...")

            candles = await provider.get_recent_candles(symbol=symbol, output_size=OUTPUT_SIZE)

            feature_rows = build_candle_features(candles=candles)

            all_feature_rows.extend(feature_rows)

            print(
                f"{symbol}: "
                f"{len(candles)} candles, "
                f"{len(feature_rows)} "
                f"feature rows"
            )

    finally:
        await provider.close()

    feature_frame = pd.DataFrame(all_feature_rows)

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    feature_frame.to_csv(OUTPUT_FILE, index=False)

    print("Total feature rows: ", len(feature_frame))

    print("Saved to: ", OUTPUT_FILE)

asyncio.run(main())