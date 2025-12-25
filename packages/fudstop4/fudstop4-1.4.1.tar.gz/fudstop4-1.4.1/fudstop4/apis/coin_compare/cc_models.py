import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def convert_ts_to_et(sec, ns):
    full_ts = sec + ns / 1_000_000_000
    dt = datetime.fromtimestamp(full_ts, tz=timezone.utc)
    dt_et = dt.astimezone(ZoneInfo("America/New_York"))
    return dt_et.strftime("%Y-%m-%d %H:%M:%S")

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def convert_ts(ts):
    if ts is None:
        return None
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    dt_et = dt.astimezone(ZoneInfo("America/New_York"))
    return dt_et.strftime("%Y-%m-%d %H:%M:%S")  # no timezone info

class CCCryptoData:
    def __init__(self, LIST):

        self.TYPE = [i.get('TYPE') for i in LIST]
        self.MARKET = [i.get('MARKET') for i in LIST]
        self.INSTRUMENT = [i.get('INSTRUMENT') for i in LIST]
        self.MAPPED_INSTRUMENT = [i.get('MAPPED_INSTRUMENT') for i in LIST]
        self.BASE = [i.get('BASE') for i in LIST]
        self.QUOTE = [i.get('QUOTE') for i in LIST]
        self.CCSEQ = [i.get('CCSEQ') for i in LIST]
        self.PRICE = [i.get('PRICE') for i in LIST]
        self.PRICE_FLAG = [i.get('PRICE_FLAG') for i in LIST]
        self.PRICE_LAST_UPDATE_TS = [i.get('PRICE_LAST_UPDATE_TS') for i in LIST]
        self.PRICE_LAST_UPDATE_TS_NS = [i.get('PRICE_LAST_UPDATE_TS_NS') for i in LIST]
        self.PRICE_LAST_UPDATE_DT_ET = [
            convert_ts_to_et(i.get("PRICE_LAST_UPDATE_TS"), i.get("PRICE_LAST_UPDATE_TS_NS"))
            for i in LIST
        ]
        self.MOVING_24_HOUR_VOLUME = [i.get('MOVING_24_HOUR_VOLUME') for i in LIST]
        self.MOVING_24_HOUR_VOLUME_BUY = [i.get('MOVING_24_HOUR_VOLUME_BUY') for i in LIST]
        self.MOVING_24_HOUR_VOLUME_SELL = [i.get('MOVING_24_HOUR_VOLUME_SELL') for i in LIST]
        self.MOVING_24_HOUR_VOLUME_UNKNOWN = [i.get('MOVING_24_HOUR_VOLUME_UNKNOWN') for i in LIST]
        self.MOVING_24_HOUR_QUOTE_VOLUME = [i.get('MOVING_24_HOUR_QUOTE_VOLUME') for i in LIST]
        self.MOVING_24_HOUR_QUOTE_VOLUME_BUY = [i.get('MOVING_24_HOUR_QUOTE_VOLUME_BUY') for i in LIST]
        self.MOVING_24_HOUR_QUOTE_VOLUME_SELL = [i.get('MOVING_24_HOUR_QUOTE_VOLUME_SELL') for i in LIST]
        self.MOVING_24_HOUR_QUOTE_VOLUME_UNKNOWN = [i.get('MOVING_24_HOUR_QUOTE_VOLUME_UNKNOWN') for i in LIST]
        self.MOVING_24_HOUR_OPEN = [i.get('MOVING_24_HOUR_OPEN') for i in LIST]
        self.MOVING_24_HOUR_HIGH = [i.get('MOVING_24_HOUR_HIGH') for i in LIST]
        self.MOVING_24_HOUR_LOW = [i.get('MOVING_24_HOUR_LOW') for i in LIST]
        self.MOVING_24_HOUR_TOTAL_TRADES = [i.get('MOVING_24_HOUR_TOTAL_TRADES') for i in LIST]
        self.MOVING_24_HOUR_TOTAL_TRADES_BUY = [i.get('MOVING_24_HOUR_TOTAL_TRADES_BUY') for i in LIST]
        self.MOVING_24_HOUR_TOTAL_TRADES_SELL = [i.get('MOVING_24_HOUR_TOTAL_TRADES_SELL') for i in LIST]
        self.MOVING_24_HOUR_TOTAL_TRADES_UNKNOWN = [i.get('MOVING_24_HOUR_TOTAL_TRADES_UNKNOWN') for i in LIST]
        self.MOVING_24_HOUR_CHANGE = [i.get('MOVING_24_HOUR_CHANGE') for i in LIST]
        self.MOVING_24_HOUR_CHANGE_PERCENTAGE = [i.get('MOVING_24_HOUR_CHANGE_PERCENTAGE') for i in LIST]


        self.data_dict = {
            'type': self.TYPE,
            'market': self.MARKET,
            'instrument': self.INSTRUMENT,
            'mapped_instrument': self.MAPPED_INSTRUMENT,
            'base': self.BASE,
            'quote': self.QUOTE,
            'ccseq': self.CCSEQ,
            'price': self.PRICE,
            'price_flag': self.PRICE_FLAG,
            'price_last_update_ts': self.PRICE_LAST_UPDATE_DT_ET,
            'price_last_update_ts_ns': self.PRICE_LAST_UPDATE_TS_NS,

            # Renamed 24h fields
            '24h_volume': self.MOVING_24_HOUR_VOLUME,
            '24h_volume_buy': self.MOVING_24_HOUR_VOLUME_BUY,
            '24h_volume_sell': self.MOVING_24_HOUR_VOLUME_SELL,
            '24h_volume_unknown': self.MOVING_24_HOUR_VOLUME_UNKNOWN,

            '24h_quote_volume': self.MOVING_24_HOUR_QUOTE_VOLUME,
            '24h_quote_volume_buy': self.MOVING_24_HOUR_QUOTE_VOLUME_BUY,
            '24h_quote_volume_sell': self.MOVING_24_HOUR_QUOTE_VOLUME_SELL,
            '24h_quote_volume_unknown': self.MOVING_24_HOUR_QUOTE_VOLUME_UNKNOWN,

            '24h_open': self.MOVING_24_HOUR_OPEN,
            '24h_high': self.MOVING_24_HOUR_HIGH,
            '24h_low': self.MOVING_24_HOUR_LOW,

            '24h_total_trades': self.MOVING_24_HOUR_TOTAL_TRADES,
            '24h_total_trades_buy': self.MOVING_24_HOUR_TOTAL_TRADES_BUY,
            '24h_total_trades_sell': self.MOVING_24_HOUR_TOTAL_TRADES_SELL,
            '24h_total_trades_unknown': self.MOVING_24_HOUR_TOTAL_TRADES_UNKNOWN,

            '24h_change': self.MOVING_24_HOUR_CHANGE,
            '24h_change_percentage': self.MOVING_24_HOUR_CHANGE_PERCENTAGE,
        }

        self.as_dataframe = pd.DataFrame(self.data_dict)
        self.as_dataframe = self.as_dataframe[::-1]



# class CryptoExchanges:
#     def __init__(self, data):
# your actual exchange dict

#         self.gemini = ex.get("gemini")
#         self.binance = ex.get("binance")
#         self.gateio = ex.get("gateio")
#         self.bybit = ex.get("bybit")
#         self.cryptodotcom = ex.get("cryptodotcom")
#         self.coinbase = ex.get("coinbase")
#         self.bitget = ex.get("bitget")


#         for i in self.gemini:
#             print(i)



class CryptoChartData:
    def __init__(self, data):
        self.data = data

        self.UNIT = [i.get('UNIT') for i in data]

        # Convert all timestamps
        self.TIMESTAMP = [convert_ts(i.get('TIMESTAMP')) for i in data]
        self.FIRST_MESSAGE_TIMESTAMP = [convert_ts(i.get('FIRST_MESSAGE_TIMESTAMP')) for i in data]
        self.LAST_MESSAGE_TIMESTAMP = [convert_ts(i.get('LAST_MESSAGE_TIMESTAMP')) for i in data]
        self.HIGH_MESSAGE_TIMESTAMP = [convert_ts(i.get('HIGH_MESSAGE_TIMESTAMP')) for i in data]
        self.LOW_MESSAGE_TIMESTAMP = [convert_ts(i.get('LOW_MESSAGE_TIMESTAMP')) for i in data]

        # Non-timestamp fields
        self.TYPE = [i.get('TYPE') for i in data]
        self.MARKET = [i.get('MARKET') for i in data]
        self.INSTRUMENT = [i.get('INSTRUMENT') for i in data]
        self.OPEN = [i.get('OPEN') for i in data]
        self.HIGH = [i.get('HIGH') for i in data]
        self.LOW = [i.get('LOW') for i in data]
        self.CLOSE = [i.get('CLOSE') for i in data]
        self.FIRST_MESSAGE_VALUE = [i.get('FIRST_MESSAGE_VALUE') for i in data]
        self.HIGH_MESSAGE_VALUE = [i.get('HIGH_MESSAGE_VALUE') for i in data]
        self.LOW_MESSAGE_VALUE = [i.get('LOW_MESSAGE_VALUE') for i in data]
        self.LAST_MESSAGE_VALUE = [i.get('LAST_MESSAGE_VALUE') for i in data]
        self.TOTAL_INDEX_UPDATES = [i.get('TOTAL_INDEX_UPDATES') for i in data]
        self.VOLUME = [i.get('VOLUME') for i in data]
        self.QUOTE_VOLUME = [i.get('QUOTE_VOLUME') for i in data]
        self.VOLUME_TOP_TIER = [i.get('VOLUME_TOP_TIER') for i in data]
        self.QUOTE_VOLUME_TOP_TIER = [i.get('QUOTE_VOLUME_TOP_TIER') for i in data]
        self.VOLUME_DIRECT = [i.get('VOLUME_DIRECT') for i in data]
        self.QUOTE_VOLUME_DIRECT = [i.get('QUOTE_VOLUME_DIRECT') for i in data]
        self.VOLUME_TOP_TIER_DIRECT = [i.get('VOLUME_TOP_TIER_DIRECT') for i in data]
        self.QUOTE_VOLUME_TOP_TIER_DIRECT = [i.get('QUOTE_VOLUME_TOP_TIER_DIRECT') for i in data]

        # Build dict
        self.data_dict = {
            'unit': self.UNIT,
            'timestamp': self.TIMESTAMP,
            'type': self.TYPE,
            'market': self.MARKET,
            'instrument': self.INSTRUMENT,
            'open': self.OPEN,
            'high': self.HIGH,
            'low': self.LOW,
            'close': self.CLOSE,
            'first_message_timestamp': self.FIRST_MESSAGE_TIMESTAMP,
            'last_message_timestamp': self.LAST_MESSAGE_TIMESTAMP,
            'first_message_value': self.FIRST_MESSAGE_VALUE,
            'high_message_value': self.HIGH_MESSAGE_VALUE,
            'high_message_timestamp': self.HIGH_MESSAGE_TIMESTAMP,
            'low_message_value': self.LOW_MESSAGE_VALUE,
            'low_message_timestamp': self.LOW_MESSAGE_TIMESTAMP,
            'last_message_value': self.LAST_MESSAGE_VALUE,
            'total_index_updates': self.TOTAL_INDEX_UPDATES,
            'volume': self.VOLUME,
            'quote_volume': self.QUOTE_VOLUME,
            'volume_top_tier': self.VOLUME_TOP_TIER,
            'quote_volume_top_tier': self.QUOTE_VOLUME_TOP_TIER,
            'volume_direct': self.VOLUME_DIRECT,
            'quote_volume_direct': self.QUOTE_VOLUME_DIRECT,
            'volume_top_tier_direct': self.VOLUME_TOP_TIER_DIRECT,
            'quote_volume_top_tier_direct': self.QUOTE_VOLUME_TOP_TIER_DIRECT,
        }


        self.as_dataframe = pd.DataFrame(self.data_dict)



class TickerSearch:
    def __init__(self, list):
        self.list = list

        self.TYPE = [i.get('TYPE') for i in list]
        self.ID = [i.get('ID') for i in list]
        self.SYMBOL = [i.get('SYMBOL') for i in list]
        self.URI = [i.get('URI') for i in list]
        self.IS_PUBLIC = [i.get('IS_PUBLIC') for i in list]
        self.NAME = [i.get('NAME') for i in list]
        self.LOGO_URL = [i.get('LOGO_URL') for i in list]
        self.ASSET_TYPE = [i.get('ASSET_TYPE') for i in list]
        self.HAS_SMART_CONTRACT_CAPABILITIES = [i.get('HAS_SMART_CONTRACT_CAPABILITIES') for i in list]
        self.MARKET_NAME = [i.get('MARKET_NAME') for i in list]
        self.CIRCULATING_MKT_CAP_USD = [i.get('CIRCULATING_MKT_CAP_USD') for i in list]
        self.ID_PARENT_ASSET = [i.get('ID_PARENT_ASSET') for i in list]
        self.PARENT_ASSET_SYMBOL = [i.get('PARENT_ASSET_SYMBOL') for i in list]
        self.ROOT_ASSET_ID = [i.get('ROOT_ASSET_ID') for i in list]
        self.ROOT_ASSET_SYMBOL = [i.get('ROOT_ASSET_SYMBOL') for i in list]
        self.ROOT_ASSET_TYPE = [i.get('ROOT_ASSET_TYPE') for i in list]

        # -------------------------------
        # Lowercase + proper data dict
        # -------------------------------
        self.data_dict = {
            'type': self.TYPE,
            'id': self.ID,
            'symbol': self.SYMBOL,
            'uri': self.URI,
            'is_public': self.IS_PUBLIC,
            'name': self.NAME,
            'logo_url': self.LOGO_URL,
            'asset_type': self.ASSET_TYPE,
            'has_smart_contract_capabilities': self.HAS_SMART_CONTRACT_CAPABILITIES,
            'market_name': self.MARKET_NAME,
            'circulating_mkt_cap_usd': self.CIRCULATING_MKT_CAP_USD,
            'id_parent_asset': self.ID_PARENT_ASSET,
            'parent_asset_symbol': self.PARENT_ASSET_SYMBOL,
            'root_asset_id': self.ROOT_ASSET_ID,
            'root_asset_symbol': self.ROOT_ASSET_SYMBOL,
            'root_asset_type': self.ROOT_ASSET_TYPE
        }


        self.as_dataframe = pd.DataFrame(self.data_dict)