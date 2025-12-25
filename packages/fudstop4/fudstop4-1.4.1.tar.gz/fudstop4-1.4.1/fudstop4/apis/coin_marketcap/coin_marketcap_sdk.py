import pandas as pd
import asyncio
import aiohttp
from .coin_marketcap_models import CoinHolders, LiquidityPools, LiquidityChanges, TopCryptoTokens, CryptoSentiment,FearGreed, HistoricalFearAndGreed, DerivativePoints, CryptoQuote, CryptoTreasuries, CryptoSignals
from fudstop4.apis.polygonio.polygon_options import PolygonOptions
from fudstop4.apis.helpers import ymd_to_unix

db = PolygonOptions()




class CoinMarketCapSDK:
    def __init__(self):
        self.crypto_id_map = {'1INCH': 8104, 'AAVE': 7278, 'ACH': 39048, 'ALCX': 8613, 'ALICE': 8766, 'ANKR': 3783, 'API3': 7737, 'ARPA': 4039, 'AVAX': 9462, 'AVT': 1948, 'AXS': 6783, 'BADGER': 7859, 'BNT': 34033, 'BOBA': 14556, 'BTC': 32994, 'BTRST': 11584, 'C98': 10903, 'CHZ': 33469, 'CLV': 8384, 'COMP': 5692, 'COTI': 3992, 'CRO': 37166, 'CRV': 6538, 'CTSI': 5444, 'DAI': 4943, 'DNT': 21106, 'DOGE': 74, 'DYDX': 11156, 'EGLD': 16817, 'ETH': 2396, 'FET': 3773, 'FIS': 19534, 'FORTH': 9421, 'FOX': 8200, 'FTM': 10240, 'GHST': 7046, 'GLM': 1455, 'GNO': 1659, 'GRT': 6719, 'GTC': 38989, 'HBAR': 24399, 'HNT': 5665, 'ICP': 8916, 'ILV': 8719, 'IMX': 10603, 'IOTX': 19081, 'JASMY': 8425, 'JTO': 28541, 'KAVA': 4846, 'KRL': 2949, 'LCX': 8613, 'LINK': 1975,'LQTY': 7429, 'LRC': 1934, 'MAGIC': 14783, 'MANA': 39088, 'MASK': 36819, 'MATIC': 3890, 'METIS': 9640, 'MKR': 1518, 'MLN': 1552,'OCEAN': 3911, 'OGN': 35621, 'OXT': 5026, 'PAXG': 4705, 'PERP': 6950, 'QNT': 3155, 'REN': 35766, 'REQ': 2071, 'RLC': 1637, 'SAND': 6210, 'SEI': 31773, 'SHIB': 5994, 'SKL': 5691, 'SNX': 2586, 'SOL': 16116, 'SPELL': 11289, 'STORJ': 1772, 'SUSHI': 6758, 'SWFTC': 2341, 'TRAC': 2467, 'TRB': 21400, 'TRU': 35336, 'TRX': 18579, 'UMA': 36576, 'C': 3408, 'VET': 37298, 'WBTC': 3717, 'XRD': 7692, 'XTZ': 35930, 'XYO': 2765, 'ZEN': 1698, 'ZRX': 1896, 'ZRO': 26997, 'CBETH': 21535}

    async def get(self, url: str, params: dict | None = None, headers: dict | None = None):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                return await response.json()
            

    async def post(self, url: str, data: dict | None = None, headers: dict | None = None):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                return await response.json()
    

    async def get_id(self, search_term: str):

        url = f"https://dapi.coinmarketcap.com/dex/v1/search?q={search_term}"

        data = await self.get(url)
        data = data['data']
        tks = data['tks']
        cid = [i.get('cid') for i in tks][0]
        return cid


    async def get_holders(self, crypto_id:str = '8425', range:str = '30d'):
        await db.connect()
        url = f"https://dapi.coinmarketcap.com/dex-stats/v3/dexer/cdp-holder/total-holder-historical?cryptoId={crypto_id}&range={range}"

        data = await self.get(url)

        data = data['data']

        points = data['points']

        data = CoinHolders(points)
        df = data.as_dataframe
        df['ticker'] = self.crypto_id_map.get(crypto_id, 'unknown')

        await db.batch_upsert_dataframe(df, table_name='crypto_holders', unique_columns=['date', 'ticker'])

        return data

    
    async def get_liquidity(self, address:str='0x7420b4b9a0110cdc71fb720908340c03f9bc03ec'):

        await db.connect()
        url = f"https://dapi.coinmarketcap.com/dex/v1/token/pools?platform=ethereum&address={address}"

        data = await self.get(url)

        data = data['data']
        pools = LiquidityPools(data)

        await db.batch_upsert_dataframe(pools.as_dataframe, table_name='crypto_liquidity', unique_columns=['published_at', 'address'])
        return pools
    

    async def get_liquidity_changes(self, address:str='0x7420b4b9a0110cdc71fb720908340c03f9bc03ec', platform:str='ethereum', sort_by:str='ts', sort_type:str='desc', limit:int=100):

        await db.connect()
        url = f"https://dapi.coinmarketcap.com/dex/v1/liquidity-change/list?platform={platform}&address={address}&limit={limit}&sortBy={sort_by}&sortType={sort_type}"


        data = await self.get(url)

        data = data['data']
        lcs = data['lcs']

        changes = LiquidityChanges(lcs)

        await db.batch_upsert_dataframe(changes.as_dataframe, table_name='crypto_liquidity_changes', unique_columns=['ts', 'liquidity_change_id', 't0s', 't1s'])

        return changes
    

    async def top_crypto_tokens(self, limit:str='10'):
        await db.connect()
        url = f"https://api.coinmarketcap.com/data-api/v3/unified-trending/top-boost/listing?size={limit}"

        data = await self.get(url)

        data = data['data']
        list = data['list']

        tokens = TopCryptoTokens(list)
        df = tokens.as_dataframe

        await db.batch_upsert_dataframe(df, table_name='top_crypto_tokens', unique_columns=['ticker'])

        return tokens


    async def get_crypto_sentiment(self):
        """Returns most bullish, most bearish, top gainers, top losers, and most voted coins based on sentiment analysis from CoinMarketCap Gravity API."""
        await db.connect()
        url = f"https://api.coinmarketcap.com/gravity/v3/gravity/vote/get-sentiment-leaderboard"

        data = await self.post(url, data={'timeframe': '24h', 'coinsTopN': 0})


        data = data['data']

        mostBullish = data['mostBullish']
        mostBullish = CryptoSentiment(mostBullish)

        await db.batch_upsert_dataframe(mostBullish.as_dataframe, table_name='crypto_sentiment_most_bullish', unique_columns=['ticker'])

        mostBearish = data['mostBearish']
        mostBearish = CryptoSentiment(mostBearish)
        await db.batch_upsert_dataframe(mostBearish.as_dataframe, table_name='crypto_sentiment_most_bearish', unique_columns=['ticker'])

        topGainersBullish = data['topGainerInBullishVotes']
        topGainersBullish = CryptoSentiment(topGainersBullish)
        await db.batch_upsert_dataframe(topGainersBullish.as_dataframe, table_name='crypto_sentiment_top_gainers_bullish', unique_columns=['ticker'])

        topGainersBearish = data['topGainerInBearishVotes']
        topGainersBearish = CryptoSentiment(topGainersBearish)
        await db.batch_upsert_dataframe(topGainersBearish.as_dataframe, table_name='crypto_sentiment_top_gainers_bearish', unique_columns=['ticker'])
        mostVotes = data['mostVotes']
        mostVotes = CryptoSentiment(mostVotes)
        await db.batch_upsert_dataframe(mostVotes.as_dataframe, table_name='crypto_sentiment_most_votes', unique_columns=['ticker'])


        return mostBullish, mostBearish, topGainersBullish, topGainersBearish, mostVotes

    async def fetch_fear_greed(
        self,
        start_date: str,
        end_date: str,
        session: aiohttp.ClientSession | None = None
    ):
        start_ts = ymd_to_unix(start_date)
        end_ts = ymd_to_unix(end_date, end_of_day=True)



        url = f"https://api.coinmarketcap.com/data-api/v3/fear-greed/chart?start={start_ts}&end={end_ts}"


        data = await self.get(url)

        data = data['data']
        dataList = data['dataList']

        historical = data['historicalValues']

       
        yesterday = historical['yesterday']
        lastWeek = historical['lastWeek']
        lastMonth = historical['lastMonth']
        yearlyHigh = historical['yearlyHigh']
        yearlyLow = historical['yearlyLow']

        yesterday_df = HistoricalFearAndGreed(yesterday, timeframe='yesterday')
        lastWeek_df = HistoricalFearAndGreed(lastWeek, timeframe='lastWeek')
        lastMonth_df = HistoricalFearAndGreed(lastMonth, timeframe='lastMonth')
        yearlyHigh_df = HistoricalFearAndGreed(yearlyHigh, timeframe='yearlyHigh')
        yearlyLow_df = HistoricalFearAndGreed(yearlyLow, timeframe='yearlyLow')
        fear_greed_df = pd.concat([yesterday_df.as_dataframe, lastWeek_df.as_dataframe, lastMonth_df.as_dataframe, yearlyHigh_df.as_dataframe, yearlyLow_df.as_dataframe], ignore_index=True)

       
        score = FearGreed(dataList)


        return score, fear_greed_df
    


    async def get_derivatives(self, crypto_ticker:str):
        await db.connect()
        id = self.crypto_id_map.get(crypto_ticker)


        url = f"https://api.coinmarketcap.com/data-api/v4/derivatives/chart?range=ALL&convertId={id}"


        data = await self.get(url)
        data = data['data']

        overview = data['overview']
        points = data['points']

        futures = overview['futures']
        perpetuals = overview['perpetuals']
        marketcap = overview['marketcap']
        cex = overview['cex']
        dex = overview['dex']


        futures = [{
            "chg": futures.get("chg"),
            "value": futures.get("value"),
            "percentage": None
        }]
        perpetuals = [
            {
                "chg": perpetuals.get("chg"),
                "value": perpetuals.get("value"),
                "percentage": None}

        ]

        marketcap = [
            {
                "chg": marketcap.get("chg"),
                "value": marketcap.get("value"),
                "percentage": None
            }

        ]

        cex = [
            {
                "chg": cex.get("chg"),
                "value": cex.get("value"),
                "percentage": cex.get("percentage")
            }

        ]

        dex = [
            {
                "chg": dex.get("chg"),
                "value": dex.get("value"),
                "percentage": dex.get("percentage")
            }
        ]
        df_futures     = pd.DataFrame(futures)
        df_futures['ticker'] = crypto_ticker
        df_perpetuals  = pd.DataFrame(perpetuals)
        df_perpetuals['ticker'] = crypto_ticker
        df_marketcap  = pd.DataFrame(marketcap)
        df_marketcap['ticker'] = crypto_ticker
        df_cex         = pd.DataFrame(cex)
        df_cex['ticker'] = crypto_ticker
        df_dex         = pd.DataFrame(dex)
        df_dex['ticker'] = crypto_ticker


        await db.batch_upsert_dataframe(df_futures, table_name='crypto_futures', unique_columns=['ticker'])
        await db.batch_upsert_dataframe(df_perpetuals, table_name='crypto_perpetuals', unique_columns=['ticker'])
        await db.batch_upsert_dataframe(df_marketcap, table_name='crypto_marketcap', unique_columns=['ticker'])
        await db.batch_upsert_dataframe(df_cex, table_name='crypto_cex', unique_columns=['ticker'])
        await db.batch_upsert_dataframe(df_dex, table_name='crypto_dex', unique_columns=['ticker'])


        points = DerivativePoints(points)

        points_df = points.as_dataframe
        points_df['ticker'] = crypto_ticker 


        await db.batch_upsert_dataframe(points_df, table_name='crypto_points', unique_columns=['ticker'])


        return points
    

    async def get_crypto_quote(self, crypto_ticker:str):

        await db.connect()
        crypto_id= self.crypto_id_map.get(crypto_ticker)
        url = f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/quote/latest?id={crypto_id}"

        data = await self.get(url)
        data = data['data']
        
        data=  CryptoQuote(data)
        df = data.as_dataframe

        df['ticker'] = crypto_ticker


        await db.batch_upsert_dataframe(df, table_name='crypto_quote', unique_columns=['ticker'])

        return data
    

    async def crypto_treasuries(self):
        await db.connect()
        url = f"https://s3.coinmarketcap.com/treasuries/crypto_treasuries.json"


        data = await self.get(url)


        data = CryptoTreasuries(data)


        await db.batch_upsert_dataframe(data.as_dataframe, table_name='crypto_treasuries', unique_columns=['ticker', 'coin'])

        return data
    

    async def crypto_signals(self):

        await db.connect()
        payload = {"limit":100,"walletLimit":4,"type":"all"}
        url = f"https://dapi.coinmarketcap.com/dex/v3/dexer/signal/latest"


        data = await self.post(url, data=payload)
        data = data['data']
        signals = data['signals']
        signals = CryptoSignals(signals)

        await db.batch_upsert_dataframe(signals.wallets_dataframe, table_name='crypto_signals', unique_columns=['address'])
        print(f"Crypto signals inserted.")
        return signals