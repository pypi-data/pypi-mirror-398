import aiohttp

from fudstop4.apis.polygonio.polygon_options import PolygonOptions
from .prebid_models import PrebidCurrencyConversions


class PrebidSDK:
    def __init__(self, db: PolygonOptions | None = None):
        self.base_url = "https://cdn.jsdelivr.net/gh/prebid/currency-file@1/latest.json"
        self.db = db or PolygonOptions()

    async def get(self, url: str, params: dict | None = None):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def currency_conversions(
        self,
        date: str | None = None,
        insert: bool = True,
        as_dataframe: bool = True,
    ):
        params = {"date": date} if date else None
        data = await self.get(self.base_url, params=params)

        conversions = PrebidCurrencyConversions(data)
        df = conversions.as_dataframe

        if insert:
            await self.db.connect()
            await self.db.batch_upsert_dataframe(
                df,
                table_name="prebid_currency_rates",
                unique_columns=["base_currency", "quote_currency", "generated_at"],
            )

        return df if as_dataframe else conversions
