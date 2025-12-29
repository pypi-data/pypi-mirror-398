import pandas as pd
pd.options.display.float_format = '{:,.2f}'.format
from datetime import datetime, timezone
import json
def _to_float(vals):
    out = []
    for v in vals:
        if v in (None, '', '--'):
            out.append(None)
        else:
            try:
                out.append(float(v))
            except (TypeError, ValueError):
                out.append(None)
    return out

def _to_float_one(v):
    if v in (None, '', '--'):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
    return out
class CoinHolders:
    def __init__(self, data: dict):

        self.date = [
    pd.to_datetime(i.get('date'), unit='ms')
    for i in data
]
        self.holderCount = [int(i.get('holderCount')) for i in data]
        self.mcpUsd = [float(i.get('mcpUsd')) for i in data]


        self.data_dict = { 
            'date': self.date,
            'holders': self.holderCount,
            'market_cap': self.mcpUsd
        }


        self.as_dataframe = pd.DataFrame(self.data_dict)




class LiquidityPools:
    def __init__(self, data:dict):


        self.addr = [i.get('addr') for i in data]
        self.v24 = [
    float(i['v24']) if i.get('v24') is not None else None
    for i in data
]
        self.pubAt = [
            datetime.fromtimestamp(int(i.get('pubAt')) / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
            for i in data
        ]
        #self.t0 = [i.get('t0') for i in data]
        #self.t1 = [i.get('t1') for i in data]
        self.bidx = [i.get('bidx') for i in data]
        self.exid = [i.get('exid') for i in data]
        self.exn = [i.get('exn') for i in data]
        self.liqUsd = [i.get('liqUsd') for i in data]
        self.fa = [i.get('fa') for i in data]

        self.mi = [i.get('mi') for i in data]


        self.data_dict =  { 
            'address': self.addr,
            'volume_24h': self.v24,
            'published_at': self.pubAt,
            'bid': self.bidx,
            'exchange_id': self.exid,
            'exchange_name': self.exn,
            'liquidity_usd': self.liqUsd,
            'from_address': self.fa,
        }


        self.as_dataframe = pd.DataFrame(self.data_dict)




class LiquidityChanges:
    def __init__(self, data: dict):
        self.ts = [
            datetime.fromtimestamp(int(i.get('ts')) / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
            for i in data
        ]
        self.tp = [i.get('tp') for i in data]
        self.eid = [i.get('eid') for i in data]
        self.en = [i.get('en') for i in data]
        self.f = [i.get('f') for i in data]
        self.t0a = [i.get('t0a') for i in data]
        self.t1a = [i.get('t1a') for i in data]
        self.t0s = [i.get('t0s') for i in data]
        self.t1s = [i.get('t1s') for i in data]
        self.a0 = [float(i.get('a0')) if i.get('a0') is not None else None for i in data]
        self.a1 = [float(i.get('a1')) if i.get('a1') is not None else None for i in data]
        self.tu = [float(i.get('tu')) if i.get('tu') is not None else None for i in data]
        self.m = [i.get('m') for i in data]
        self.txn = [i.get('txn') for i in data]
        self.h = [i.get('h') for i in data]
        self.txId = [i.get('txId') for i in data]
        self.lgid = [i.get('lgid') for i in data]


        self.data_dict = { 
            'timestamp': self.ts,
            'type': self.tp,
            'exchange_id': self.eid,
            'exchange_name': self.en,
            'from_address': self.f,
            'token0_address': self.t0a,
            'token1_address': self.t1a,
            'token0_name': self.t0s,
            'token1_name': self.t1s,
            'token1_amount': self.t1s,
            'token0_amount': self.a0,
            'token1_amount': self.a1,
            'tu': self.tu,
            'm': self.m,
            'network_txn': self.txn,
            'hash': self.h,
            'tx_id': self.txId,
            'liquidity_change_id': self.lgid,


        }



        self.as_dataframe = pd.DataFrame(self.data_dict)



class TopCryptoTokens:
    def __init__(self, data:dict):

        self.unifiedTokenId = [i.get('unifiedTokenId') for i in data]
        self.type = [i.get('type') for i in data]
        self.cryptoId = [i.get('cryptoId') for i in data]
        self.slug = [i.get('slug') for i in data]
        self.tokenSymbol = [i.get('tokenSymbol') for i in data]
        self.tokenName = [i.get('tokenName') for i in data]
        self.priceUsd = [i.get('priceUsd') for i in data]
        self.volume24h = [i.get('volume24h') for i in data]
        self.pricePercentageChange24h = [i.get('pricePercentageChange24h') for i in data]
        self.marketCap = [i.get('marketCap') for i in data]
        self.selfReportedMarketCap = [i.get('selfReportedMarketCap') for i in data]


        self.data_dict = { 
            'token_id': self.unifiedTokenId,
            'type': self.type,
            'crypto_id': self.cryptoId,
            'slug': self.slug,
            'ticker': self.tokenSymbol,
            'name': self.tokenName,
            'price': self.priceUsd,
            'volume_24h': self.volume24h,
            'price_change_24h': self.pricePercentageChange24h,
            'market_cap': self.marketCap,
            'self_reported_market_cap': self.selfReportedMarketCap
        }


        self.as_dataframe = pd.DataFrame(self.data_dict)



class CryptoSentiment:
    def __init__(self, mostBullish):

        self.id = [i.get('id') for i in mostBullish]
        self.name = [i.get('name') for i in mostBullish]
        self.symbol = [i.get('symbol') for i in mostBullish]
        self.slug = [i.get('slug') for i in mostBullish]
        self.rank = [i.get('rank') for i in mostBullish]
        self.votable = [i.get('votable') for i in mostBullish]
        self.myVote = [i.get('myVote') for i in mostBullish]
        self.bullishVotes = [i.get('bullishVotes') for i in mostBullish]
        self.bearishVotes = [i.get('bearishVotes') for i in mostBullish]
        self.bullishRate = [float(i.get('bullishRate')) if i.get('bullishRate') is not None else None for i in mostBullish]
        self.bearishRate = [float(i.get('bearishRate')) if i.get('bearishRate') is not None else None for i in mostBullish]
        self.votes = [i.get('votes') for i in mostBullish]
        self.voteChange = [i.get('voteChange') for i in mostBullish]
        priceChange = [i.get('priceChange') for i in mostBullish]
        self.change = [float(i.get('change')) if i.get('change') is not None else None for i in priceChange]
        self.price = [float(i.get('price')) if i.get('price') is not None else None for i in priceChange]


        self.data_dict = { 
            'id': self.id,
            'name': self.name,
            'ticker': self.symbol,
            'slug': self.slug,
            'rank': self.rank,
            'votable': self.votable,
            'my_vote': self.myVote,
            'bullish_votes': self.bullishVotes,
            'bearish_votes': self.bearishVotes,
            'bullish_rate': self.bullishRate,
            'bearish_rate': self.bearishRate,
            'total_votes': self.votes,
            'vote_change': self.voteChange,
            'price_change': self.change,
            'price': self.price

        }


        self.as_dataframe = pd.DataFrame(self.data_dict)



class FearGreed:
    def __init__(self, dataList):

        self.score = [i.get('score') for i in dataList]
        self.name = [i.get('name') for i in dataList]
        self.timestamp = [i.get('timestamp') for i in dataList]
        self.btc_price = [float(i.get('btcPrice')) if i.get('btcPrice') is not None else None for i in dataList]
        self.btc_volume = [float(i.get('btcVolume')) if i.get('btcVolume') is not None else None for i in dataList]


        self.data_dict =  { 
            'name': self.name,
            'score': self.score,
            'timestamp': self.timestamp,
            'btc_price': self.btc_price,
            'btc_volume': self.btc_volume
        }


        self.as_dataframe = pd.DataFrame(self.data_dict)



class HistoricalFearAndGreed:
    def __init__(self, data, timeframe):
        
        self.score = data.get('score')
        self.name = data.get('name')
        self.timestamp =data.get('timestamp')


        self.data_dict = {  
            'score': self.score,
            'name': self.name,
            'timestamp': self.timestamp
        }


        self.as_dataframe = pd.DataFrame(self.data_dict, index=[0])
        self.as_dataframe['timeframe'] = timeframe




class DerivativePoints:
    def __init__(self, points):


        self.futures = [i.get('futures') for i in points]
        self.perpetuals= [i.get('perpetuals') for i in points]
        self.cex= [i.get('cex') for i in points]
        self.dex= [i.get('dex') for i in points]
        self.marketcap= [i.get('marketcap') for i in points]
        self.timestamp= [i.get('timestamp') for i in points]


        self.data_dict = { 
            'futures': self.futures,
            'perpetuals': self.perpetuals,
            'cex': self.cex,
            'dex': self.dex,
            'marketcap': self.marketcap,
            'timestamp': self.timestamp
        }


        self.as_dataframe = pd.DataFrame(self.data_dict)


class CryptoQuote:
    def __init__(self, data):

        self.id = [i.get('id') for i in data]
        self.name = [i.get('name') for i in data]
        self.symbol = [i.get('symbol') for i in data]
        self.slug = [i.get('slug') for i in data]
        self.lastUpdatedTime = [i.get('lastUpdatedTime') for i in data]
        self.quotes = [i.get('quotes') for i in data]
        self.rank = [i.get('rank') for i in data]
        self.dateAdded = [i.get('dateAdded') for i in data]
        self.maxSupply = [i.get('maxSupply') for i in data]
        self.totalSupply = [i.get('totalSupply') for i in data]
        self.selfReportedCirculatingSupply = [i.get('selfReportedCirculatingSupply') for i in data]
        self.circulatingSupply = [i.get('circulatingSupply') for i in data]
        self.marketCapPercentChange1h = [i.get('marketCapPercentChange1h') for i in data]
        self.marketCapPercentChange = [i.get('marketCapPercentChange') for i in data]
        self.marketCapPercentChange7d = [i.get('marketCapPercentChange7d') for i in data]
        self.marketCapPercentChange30d = [i.get('marketCapPercentChange30d') for i in data]
        self.marketCapPercentChange90d = [i.get('marketCapPercentChange90d') for i in data]
        self.marketCapPercentChange1y = [i.get('marketCapPercentChange1y') for i in data]
        self.marketCapPercentChange3y = [i.get('marketCapPercentChange3y') for i in data]
        self.marketCapPercentChangeAll = [i.get('marketCapPercentChangeAll') for i in data]
        self.percentChange1y = [i.get('percentChange1y') for i in data]
        self.percentChange3y = [i.get('percentChange3y') for i in data]
        self.percentChangeAll = [i.get('percentChangeAll') for i in data]
        self.price = [i.get('price') for i in self.quotes[0]]


        self.data_dict = {
            "id": [i.get("id") for i in data],
            "name": [i.get("name") for i in data],
            "symbol": [i.get("symbol") for i in data],
            "slug": [i.get("slug") for i in data],
            "last_updated": [i.get("lastUpdatedTime") for i in data],
            "rank": [i.get("rank") for i in data],
            "date_added": [i.get("dateAdded") for i in data],

            "max_supply": [i.get("maxSupply") for i in data],
            "total_supply": [i.get("totalSupply") for i in data],
            "circ_supply": [i.get("circulatingSupply") for i in data],
            "self_reported_circ_supply": [
                i.get("selfReportedCirculatingSupply") for i in data
            ],

            "mcap_chg_1h": [i.get("marketCapPercentChange1h") for i in data],
            "mcap_chg": [i.get("marketCapPercentChange") for i in data],
            "mcap_chg_7d": [i.get("marketCapPercentChange7d") for i in data],
            "mcap_chg_30d": [i.get("marketCapPercentChange30d") for i in data],
            "mcap_chg_90d": [i.get("marketCapPercentChange90d") for i in data],
            "mcap_chg_1y": [i.get("marketCapPercentChange1y") for i in data],
            "mcap_chg_3y": [i.get("marketCapPercentChange3y") for i in data],
            "mcap_chg_all": [i.get("marketCapPercentChangeAll") for i in data],

            "pct_chg_1y": [i.get("percentChange1y") for i in data],
            "pct_chg_3y": [i.get("percentChange3y") for i in data],
            "pct_chg_all": [i.get("percentChangeAll") for i in data],
            "price": self.price
        }


        self.as_dataframe = pd.DataFrame(self.data_dict)



class CryptoTreasuries:
    def __init__(self, data):

        self.company_name = [i.get('company_name') for i in data]
        self.country = [i.get('country') for i in data]
        self.ticker = [i.get('ticker') for i in data]
        self.coin = [i.get('coin') for i in data]
        self.company_type = [i.get('company_type') for i in data]
        self.holdings = [i.get('holdings') for i in data]
        self.data_as_of = [i.get('data_as_of') for i in data]
        self.doc = [
            float(str(v).replace('%', '').strip())
            if (v := i.get('doc')) not in (None, '--', '', '—')
            else 0.0
            for i in data
        ]
        self.data_dict = { 
            'company': self.company_name,
            'country': self.country,
            'ticker': self.ticker,
            'coin': self.coin,
            'company_type': self.company_type,
            'holdings': self.holdings,
            'doc': self.doc,
        }


        self.as_dataframe = pd.DataFrame(self.data_dict)

class CryptoSignals:
    def __init__(self, signals):
        self.tokenAddress = [i.get('tokenAddress') for i in signals]
        self.tokenSymbol = [i.get('tokenSymbol') for i in signals]
        self.tokenName = [i.get('tokenName') for i in signals]
        self.tokenImageUrl = [i.get('tokenImageUrl') for i in signals]
        self.pushCount = [i.get('pushCount') for i in signals]
        self.multiple = [i.get('multiple') for i in signals]
        self.highestPrice = [i.get('highestPrice') for i in signals]
        self.platformId = [i.get('platformId') for i in signals]
        self.platformName = [i.get('platformName') for i in signals]
        self.dexerPlatformName = [i.get('dexerPlatformName') for i in signals]
        self.platformCryptoId = [i.get('platformCryptoId') for i in signals]
        self.poolCreateTime = [i.get('poolCreateTime') for i in signals]
        self.publishAt = [i.get('publishAt') for i in signals]
        self.launchPad = [i.get('launchPad') for i in signals]
        self.priceUsd = [i.get('priceUsd') for i in signals]
        self.volume24h = [i.get('volume24h') for i in signals]
        self.priceChange24h = [i.get('priceChange24h') for i in signals]
        self.pinCard = [i.get('pinCard') for i in signals]
        self.marketCap = [i.get('marketCap') for i in signals]
        self.liquidity = [i.get('liquidity') for i in signals]
        self.smartBuyerCount = [i.get('smartBuyerCount') for i in signals]
        self.smartBuyerAmountUsd = [i.get('smartBuyerAmountUsd') for i in signals]
        self.latestSignalTime = [i.get('latestSignalTime') for i in signals]
        self.latestSignalMarketCap = [i.get('latestSignalMarketCap') for i in signals]
        self.latestSignalPrice = [i.get('latestSignalPrice') for i in signals]
        self.latestSignalLiquidityUsd = [i.get('latestSignalLiquidityUsd') for i in signals]
        self.firstSignalTime = [i.get('firstSignalTime') for i in signals]
        self.firstSignalMarketCap = [i.get('firstSignalMarketCap') for i in signals]
        self.twitter = [i.get('twitter') for i in signals]
        self.website = [i.get('website') for i in signals]
        self.securityLevel = [i.get('securityLevel') for i in signals]
        self.allTimeVolume = [i.get('allTimeVolume') for i in signals]
        self.allTimeBuyAmountUSD = [i.get('allTimeBuyAmountUSD') for i in signals]
        self.allTimeTraderCount = [i.get('allTimeTraderCount') for i in signals]
        self.updateTime = [i.get('updateTime') for i in signals]
        self.exclusive = [i.get('exclusive') for i in signals]
        self.tags = [i.get('tags') for i in signals]
        self.poolSource = [i.get('poolSource') for i in signals]
        self.type = [i.get('type') for i in signals]
        self.totalSupply = [i.get('totalSupply') for i in signals]

        # keep per-signal wallet lists aligned with root rows
        self.wallets = [(i.get('wallets') or []) for i in signals]

        # 1) TOKEN-LEVEL (normalized parent)
        self.data_dict = {
            'address': self.tokenAddress,
            'ticker': self.tokenSymbol,
            'name': self.tokenName,
            'image_url': self.tokenImageUrl,
            'platform_id': self.platformId,
            'platform': self.platformName,
            'dex_platform': self.dexerPlatformName,
            'platform_crypto_id': self.platformCryptoId,
            'launch_pad': self.launchPad,
            'pool_source': self.poolSource,
            'type': self.type,
            'exclusive': self.exclusive,

            'pool_created_at': self.poolCreateTime,
            'published_at': self.publishAt,
            'updated_at': self.updateTime,
            'first_signal_at': self.firstSignalTime,
            'latest_signal_at': self.latestSignalTime,

            'price_usd': _to_float(self.priceUsd),
            'high_price': _to_float(self.highestPrice),
            'market_cap': _to_float(self.marketCap),
            'liquidity_usd': _to_float(self.liquidity),
            'volume_24h': _to_float(self.volume24h),
            'price_change_24h': _to_float(self.priceChange24h),
            'multiple': _to_float(self.multiple),

            'push_count': _to_float(self.pushCount),
            'first_signal_mc': _to_float(self.firstSignalMarketCap),
            'latest_signal_mc': _to_float(self.latestSignalMarketCap),
            'latest_signal_price': _to_float(self.latestSignalPrice),
            'latest_signal_liquidity': _to_float(self.latestSignalLiquidityUsd),

            'smart_buyers': _to_float(self.smartBuyerCount),
            'smart_buy_usd': _to_float(self.smartBuyerAmountUsd),

            'all_time_volume': _to_float(self.allTimeVolume),
            'all_time_buy_usd': _to_float(self.allTimeBuyAmountUSD),
            'all_time_traders': _to_float(self.allTimeTraderCount),

            'total_supply': _to_float(self.totalSupply),
            'security_level': _to_float(self.securityLevel),

            'twitter': self.twitter,
            'website': self.website,
            'pin_card': self.pinCard,
        }

        self.as_dataframe = pd.DataFrame(self.data_dict)

        # 2) WALLET-LEVEL (normalized child)
        wallet_rows = []
        for addr, ticker, wallets in zip(self.tokenAddress, self.tokenSymbol, self.wallets):
            for w in wallets:
                wallet_rows.append({
                    'address': addr,
                    'ticker': ticker,
                    'wallet_label': w.get('walletLabel'),
                    'behavior': w.get('behavior'),
                    'updated_at': w.get('updateTime'),

                    'balance_usd': _to_float_one(w.get('balanceAmountUsd')),
                    'balance': _to_float_one(w.get('balanceAmount')),
                    'total_buy_usd': _to_float_one(w.get('totalBuyAmountUsd')),
                    'total_buy': _to_float_one(w.get('totalBuyAmount')),
                    'buy_txs_24h': _to_float_one(w.get('buyTxs24h')),
                    'sell_txs_24h': _to_float_one(w.get('sellTxs24h')),
                    'roi': _to_float_one(w.get('roi')),
                    'avg_buy_price': _to_float_one(w.get('avgBuyPrice')),
                    'age_ms': _to_float_one(w.get('age')),
                })

        self.wallets_dataframe = pd.DataFrame(wallet_rows)