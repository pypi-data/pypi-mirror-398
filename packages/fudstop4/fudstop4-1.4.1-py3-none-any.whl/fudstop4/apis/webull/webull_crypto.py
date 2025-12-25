from fudstop4.apis.helpers import generate_webull_headers
from fudstop4.apis.polygonio.polygon_options import PolygonOptions
import aiohttp
import asyncio
db = PolygonOptions()
from fudstop4.apis.webull.crypto_models.crypto_data import WebullCryptoData
from datetime import datetime, timezone
import pandas as pd
import time
from zoneinfo import ZoneInfo

class WebullCrypto:
    def __init__(self, headers=None):

        self.headers=headers

        self.timeframes = ['m1','m5', 'm10', 'm15', 'm20', 'm30', 'm60', 'm120', 'm240', 'd1']
        self.now_timestamp_int = int(datetime.now(timezone.utc).timestamp())
        self.day = int(86400)
        self.crypto_df = pd.read_csv('files/crypto_tickers.csv')
        self.coin_to_id_map = dict(zip(self.crypto_df['ticker'], self.crypto_df['id']))

    async def get_crypto_list(self):
        url = f"https://quotes-gw.webullfintech.com/api/bgw/crypto/list"

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url) as resp:
                data = await resp.json()
                data = WebullCryptoData(data)

                return data.as_dataframe
            
    async def get_webull_id(self, symbol):
        """Converts ticker name to ticker ID to be passed to other API endpoints from Webull."""
        ticker_id = self.coin_to_id_map.get(symbol)
        return ticker_id
    async def get_webull_ids(self, symbols):
        """Fetch ticker IDs for a list of symbols in one go."""
        return {symbol: self.coin_to_id_map.get(symbol) for symbol in symbols}
    async def get_crypto_chart_data(self, headers, ticker_id: str, timespan: str='d1', count: int=50):

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                "https://quotes-gw.webullfintech.com/api/quote/charts/query-mini"
                f"?type={timespan}&count={count}&restorationType=1&extendTrading=0&loadFactor=1"
                f"&tickerId={ticker_id}"
            ) as resp:
                data = await resp.json()

                # Extract first "data" array
                rows = [i.get("data") for i in data][0]

                est = ZoneInfo("America/New_York")
                parsed_rows = []

                for row in rows:
                    parts = row.split(",")

                    ts = int(parts[0])
                    dt_est = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(est)
                    timestamp_str = dt_est.strftime("%Y-%m-%d %H:%M:%S")

                    # Adjust OHLC mapping if your API differs
                    o = float(parts[1])
                    c = float(parts[2])
                    h = float(parts[3])
                    l = float(parts[4])

                    parsed_rows.append({
                        "unix_timestamp": ts,
                        "timestamp_et": timestamp_str,
                        "open": o,
                        "high": h,
                        "low": l,
                        "close": c,
                    })

                # Convert to DataFrame
                df = pd.DataFrame(parsed_rows)
                return df