import pandas as pd
import re
import re

def clean_text(raw: str) -> str:
    if not isinstance(raw, str):
        return ""

    # Remove ALL <A|numbers> style tags anywhere in the text
    cleaned = re.sub(r'<A\|\d+>', '', raw)

    # Remove null bytes if present
    cleaned = cleaned.replace('\x00', '')

    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned



class Community:
    def __init__(self, subjects):
        self.subjects = subjects

        self.rankId     = [s.get('rankId') for s in self.subjects]
        counters        = [s.get('counter', {}) for s in self.subjects]
        self.views      = [c.get('views') for c in counters]
        self.joiners    = [c.get('joiners') for c in counters]
        self.comments   = [c.get('comments') for c in counters]
        # note: JSON uses thumbUps / thumbDowns, not thumbsUp / thumbsDown
        self.thumbs_up   = [c.get('thumbUps') for c in counters]
        self.thumbs_down = [c.get('thumbDowns') for c in counters]

        self.observer   = [s.get('observer') for s in self.subjects]
        self.uuid       = [s.get('uuid') for s in self.subjects]
        self.createTime = [s.get('createTime') for s in self.subjects]

        contents  = [s.get('content', {}) for s in self.subjects]
        self.text = [clean_text(c.get('txt', '')) for c in contents]

        self.publisher = [s.get('publisher') for s in self.subjects]

        links = [s.get('link', {}) for s in self.subjects]

        # one ticker per subject (first ticker, or None if missing)
        self.ticker    = []
        self.name      = []
        self.ticker_id = []

        for link in links:
            tickers = link.get('tickers') or []
            if tickers:
                t0 = tickers[0]
                self.ticker.append(t0.get('symbol'))
                self.name.append(t0.get('name'))
                self.ticker_id.append(t0.get('tickerId'))
            else:
                self.ticker.append(None)
                self.name.append(None)
                self.ticker_id.append(None)

        self.data_dict = {
            'rank_id':     self.rankId,
            'uuid':        self.uuid,
            'create_time': self.createTime,
            'text':        self.text,
            'views':       self.views,
            'joiners':     self.joiners,
            'thumbs_up':   self.thumbs_up,
            'thumbs_down': self.thumbs_down,
            'comments':    self.comments,
            'ticker':      self.ticker,
            'name':        self.name,
            'ticker_id':   self.ticker_id,
        }

        self.as_dataframe = pd.DataFrame(self.data_dict)