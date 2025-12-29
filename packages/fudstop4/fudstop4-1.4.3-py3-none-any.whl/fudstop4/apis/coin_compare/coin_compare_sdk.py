import pandas as pd
import aiohttp
import asyncio
from fudstop4.apis.polygonio.polygon_options import PolygonOptions
from .cc_models import CCCryptoData, CryptoChartData, TickerSearch # CryptoExchanges
import time

db = PolygonOptions()



class CoinCompareSDK:
    def __init__(self):
        pass

    async def search_for_ticker(self, search_query:str, limit:str='100'):
        url = f"https://data-api.cryptocompare.com/asset/v1/search?search_string={search_query}&limit={limit}&response_format=JSON"
        await db.connect()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()

                    data = data['Data']
                    list = data['LIST']
                    list = TickerSearch(list)

                    df = list.as_dataframe
                    df = df.rename(columns={'symbol': 'ticker'})
                    await db.batch_upsert_dataframe(df, table_name='crypto_tickers', unique_columns=['ticker'])
                    return list
        except Exception as e:
            print(e)
        finally:

            await db.close()
    async def get_crypto_data(self, ticker:str='BTC'):
        await db.connect()
        url = f"https://data-api.cryptocompare.com/spot/v1/latest/tick/asset?base_asset={ticker}&groups=ID%2CMAPPING%2CVALUE%2CMOVING_24_HOUR&page=1&page_size=10&sort_by=MARKET_BENCHMARK_TIER_AND_MOVING_24_HOUR_VOLUME&sort_direction=DESC&apply_mapping=true"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:

                data = await resp.json()

                data = data['Data'] if 'Data' in data else None
                list = data['LIST'] if 'LIST' in data else None
                print(list)

                list = CCCryptoData(LIST=list)

                await db.batch_upsert_dataframe(list.as_dataframe, table_name='cc', unique_columns=['instrument'])

                return list
            

    async def crypto_chart_data(self, market:str='cadli', instrument:str='BTC-USD', limit:str='100', aggregate:str='1'):
        await db.connect()
        now = int(time.time())               # current timestamp in seconds
        cache_bust = now                     # good for cache bust
        to_ts = now - 60                     # example: 1 minute earlier
        url = f"https://data-api.cryptocompare.com/index/cc/v1/historical/minutes?market=cadli&instrument={instrument}&limit={limit}&aggregate={aggregate}&fill=true&apply_mapping=true&response_format=JSON&cache_bust_ts={cache_bust}&to_ts={to_ts}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()
                    data = data['Data']

                    data = CryptoChartData(data)
                    df = data.as_dataframe
                    df = df[::-1]
                    df = df.rename(columns={'instrument': 'ticker', 'unit': 'timespan'})
                    
                    await db.batch_upsert_dataframe(df, table_name='crypto_candles', unique_columns=['ticker', 'timespan', 'timestamp'])

                    return df
        except Exception as e:
            print(e)

        finally:
            await db.close()