import asyncio
import aiohttp
from fudstop4.apis.polygonio.polygon_options import PolygonOptions
from .coinbase_models import AssetBySlug

db = PolygonOptions()




class CoinbaseSDK:
    def __init__(self):

        pass




    async def monitor_traders(self):
        """Monitor unique traders on coinbase."""

        headers =  {
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            url = 'https://www.coinbase.com/graphql/query?&operationName=AssetPageContentV2Query&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22ed786c49102672b1d27c8279a6b7f160f042264ec5947f4dc1107f23edc4ca1b%22%7D%7D&variables=%7B%22assetSlug%22%3A%22jasmy%22%2C%22locale%22%3A%22en%22%2C%22currency%22%3A%22USD%22%2C%22targetSymbol%22%3A%22USD%22%2C%22country%22%3A%22US%22%2C%22countryCode%22%3A%22US%22%2C%22skipFrames%22%3Atrue%2C%22internalLinksLimit%22%3A12%2C%22pageKey%22%3A%22asset_logged_out%22%2C%22skipNewsArticles%22%3Afalse%2C%22isLoggedOutDexExperiment%22%3Atrue%2C%22isUKUser%22%3Afalse%2C%22url%22%3A%22https%3A%2F%2Fwww.coinbase.com%2Fprice%2Fjasmy%22%7D'

            async with session.get(url) as resp:
                data = await resp.json()
                data = data['data']
                assetBySlug = data['assetBySlug']
                
                assetBySlug = AssetBySlug(assetBySlug)
                

                return assetBySlug
            
