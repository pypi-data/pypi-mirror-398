import pandas as pd




class CallPutProfile:
    def __init__(self, call_put_profiles):
        self.strikes = [i.get('strikes') if 'strikes' in i else None for i in call_put_profiles]
        self.calls = [i.get('calls') if 'calls' in i else None for i in call_put_profiles]
        self.callsRatio = [i.get('callsRatio') if 'callsRatio' in i else None for i in call_put_profiles]
        self.puts = [i.get('puts') if 'puts' in i else None for i in call_put_profiles]
        self.putsRatio = [i.get('putsRatio') if 'putsRatio' in i else None for i in call_put_profiles]
        self.totalVolume = [i.get('totalVolume') if 'totalVolume' in i else None for i in call_put_profiles]

        self.data_dict = { 
            'strikes': self.strikes,
            'calls': self.calls,
            'callsRatio': self.callsRatio,
            'puts': self.puts,
            'putsRatio': self.putsRatio,
            'totalVolume': self.totalVolume
        }


        self.as_dataframe = pd.DataFrame(self.data_dict)




class CallPutFlow:
    def __init__(self, data):
            
        self.totalVolume = data.get('totalVolume') if 'totalVolume' in data else None
        self.totalOpenInterest = data.get('totalOpenInterest') if 'totalOpenInterest' in data else None
        self.callAsk = data.get('callAsk') if 'callAsk' in data else None
        self.putAsk = data.get('putAsk') if 'putAsk' in data else None
        self.callBid = data.get('callBid') if 'callBid' in data else None
        self.putBid = data.get('putBid') if 'putBid' in data else None
        self.callNeutral = data.get('callNeutral') if 'callNeutral' in data else None
        self.putNeutral = data.get('putNeutral') if 'putNeutral' in data else None
        self.callTotalVolume = data.get('callTotalVolume') if 'callTotalVolume' in data else None
        self.putTotalVolume = data.get('putTotalVolume') if 'putTotalVolume' in data else None
        self.callAskRatio = data.get('callAskRatio') if 'callAskRatio' in data else None
        self.putAskRatio = data.get('putAskRatio') if 'putAskRatio' in data else None
        self.callBidRatio = data.get('callBidRatio') if 'callBidRatio' in data else None
        self.putBidRatio = data.get('putBidRatio') if 'putBidRatio' in data else None
        self.callNeutralRatio = data.get('callNeutralRatio') if 'callNeutralRatio' in data else None
        self.putNeutralRatio = data.get('putNeutralRatio') if 'putNeutralRatio' in data else None
                

        self.data_dict = { 
            'total_volume': self.totalVolume,
            'total_oi': self.totalOpenInterest,
            'call_ask': self.callAsk,
            'put_ask': self.putAsk,
            'call_bid': self.callBid,
            'put_bid': self.putBid,
            'call_neutral': self.callNeutral,
            'put_neutral': self.putNeutral,
            'call_total_volume': self.callTotalVolume,
            'put_total_volume': self.putTotalVolume,
            'call_ask_ratio': self.callAskRatio,
            'put_ask_ratio': self.putAskRatio,
            'call_bid_ratio': self.callBidRatio,
            'put_bid_ratio': self.putBidRatio,
            'call_neutral_ratio': self.callNeutralRatio,
            'put_neutral_ratio': self.putNeutralRatio,
        }


        self.as_dataframe = pd.DataFrame(self.data_dict, index=[0])