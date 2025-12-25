import pandas as pd





class AssetBySlug:
    def __init__(self, data: dict):

        self.name = data.get('name', '')
        self.platformName = data.get('platformName', '')
        self.slug = data.get('slug', '')
        self.coinGeckoId = data.get('coinGeckoId', '')
        self.coinMarketCapId = data.get('coinMarketCapId', '')
        self.uuid = data.get('uuid', '')
        self.supportedContextsForLocation = data.get('supportedContextsForLocation', '')
        self.stakingStats = data.get('stakingStats', {})
        self.id = data.get('id', '')
        self.displaySymbol = data.get('displaySymbol', '')
        self.circulatingSupply = data.get('circulatingSupply', '')
        self.imageUrl = data.get('imageUrl', '')
        self.allTimeHigh = data.get('allTimeHigh', '')
        self.latestPrice = data.get('latestPrice', '')
        self.marketCapV2 = data.get('marketCapV2', '')
        self.volume24hV2 = data.get('volume24hV2', '')
        self.description = data.get('description', '')
        self.officialWebsite = data.get('officialWebsite', '')
        self.whitePaper = data.get('whitePaper', '')
        self.micaDisclosure = data.get('micaDisclosure', '')
        self.tradingInsight = data.get('tradingInsight', '')
        self.cgMarketCapChangePercentage24H = data.get('cgMarketCapChangePercentage24H', '')
        self.fullyDilutedMarketCap = data.get('fullyDilutedMarketCap', '')
        self.maxSupply = data.get('maxSupply', '')
        self.totalSupply = data.get('totalSupply', '')
        self.dominance = data.get('dominance', '')
        self.signals = data.get('signals', {})
        self.volumePercentChange24hV2 = data.get('volumePercentChange24hV2', '')
        self.cmcVolume7D = data.get('cmcVolume7D', '')
        self.cmcVolume30D = data.get('cmcVolume30D', '')
        self.allTimeHighV4 = data.get('allTimeHighV4', '')
        self.cmcTvl = data.get('cmcTvl', '')
        self.cgFullyDilutedValuation = data.get('cgFullyDilutedValuation', '')
        self.priceDataForYearV2 = data.get('priceDataForYearV2', '')
        self.buyerSellerRatio24h = data.get('buyerSellerRatio24h', '')
        self.uniqueBuyers24h = data.get('uniqueBuyers24h', '')
        self.uniqueTraders24h = data.get('uniqueTraders24h', '')
        self.uniqueBuyersPercentChange24h = data.get('uniqueBuyersPercentChange24h', '')
        self.uniqueTradersPercentChange24h = data.get('uniqueTradersPercentChange24h', '')
        self.uniqueSellers24h = data.get('uniqueSellers24h', '')
        self.uniqueSellersPercentChange24h = data.get('uniqueSellersPercentChange24h', '')
        self.searchStats = data.get('searchStats', {})
        self.marketCap = data.get('marketCap', '')
        self.volume24H = data.get('volume24H', '')
        self.assetsWithSimilarMarketCap = data.get('assetsWithSimilarMarketCap', [])
        self.usdQuote = data.get('usdQuote', {})
        self.cadQuote = data.get('cadQuote', {})
        self.gbpQuote    = data.get('gbpQuote', {})
        self.audQuote    = data.get('audQuote', {})
        self.jpyQuote    = data.get('jpyQuote', {})
        self.inrQuote    = data.get('inrQuote', {})
        self.brlQuote    = data.get('brlQuote', {})
        self.eurQuote    = data.get('eurQuote', {})
        self.ngnQuote    = data.get('ngnQuote', {})
        self.krwQuote    = data.get('krwQuote', {})
        self.sgdQuote    = data.get('sgdQuote', {})
        self.color       = data.get('color', '')
        self.priceDataForWeekV2 = data.get('priceDataForWeekV2', '')
        self.newsArticles = data.get('newsArticles', [])
        self.socialMediaMetrics = data.get('socialMediaMetrics', {})
        self.listed = data.get('listed', False)
        self.priceDataForDayV2 = data.get('priceDataForDayV2', '')
        self.priceDataForHourV2 = data.get('priceDataForHourV2', '')
        self.priceDataForMonthV2 = data.get('priceDataForMonthV2', '')
        self.cmcTags = data.get('cmcTags', [])
        self.priceDataForHour = data.get('priceDataForHour', '')
        self.priceDataForWeek = data.get('priceDataForWeek', '')
        self.priceDataForDay = data.get('priceDataForDay', '')
        self.volume24h = data.get('volume24h', '')
        trading_activity = self.signals.get('tradingActivity')
        self.trading_activity = trading_activity.get('value')
        percent_holding = self.signals.get('percentHolding')
        self.percent_holding = percent_holding.get('value')
        self.tradableMarketCapRank = self.signals.get('tradableMarketCapRank', '')

        self.scalar_dict = { 
            'name': self.name,
            'platform_name': self.platformName,
            'slug': self.slug,
            'coingecko_id': self.coinGeckoId,
            'coinmarketcap_id': self.coinMarketCapId,
            'uuid': self.uuid,
            'supported_contexts_for_location': self.supportedContextsForLocation,
            'id': self.id,
            'ticker': self.displaySymbol,
            'circulating_supply': self.circulatingSupply,
            'image_url': self.imageUrl,
            'all_time_high': self.allTimeHigh,
            'latest_price': self.latestPrice,
            'market_cap_v2': self.marketCapV2,
            'volume_24h_v2': self.volume24hV2,
            'description': self.description,
            'official_website': self.officialWebsite,
            'white_paper': self.whitePaper,
            'max_supply': self.maxSupply,
            'total_supply': self.totalSupply,
            'dominance': self.dominance,
            'listed': self.listed,
            'volume_24h': self.volume24h,
            'buyer_seller_ratio_24h': self.buyerSellerRatio24h,
            'unique_buyers_24h': self.uniqueBuyers24h,
            'unique_traders_24h': self.uniqueTraders24h,
            'unique_sellers_24h': self.uniqueSellers24h,
            'percent_holding': self.percent_holding,
            'trading_activity': self.trading_activity,
            'tradable_market_cap_rank': self.tradableMarketCapRank
      
            
        }


        self.as_dataframe = pd.DataFrame(self.scalar_dict)


        