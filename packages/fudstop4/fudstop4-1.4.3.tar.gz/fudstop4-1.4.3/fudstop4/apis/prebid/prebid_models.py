import pandas as pd

MISSING_VALUES = (None, "", "--")


def _sanitize_float(value):
    if value in MISSING_VALUES:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _to_et_datetime(value):
    if value in MISSING_VALUES:
        return None
    try:
        dt = pd.to_datetime(value, utc=True)
    except (TypeError, ValueError):
        return None
    dt = dt.tz_convert("US/Eastern").tz_localize(None)
    return dt.to_pydatetime()


class PrebidCurrencyConversions:
    def __init__(self, data: dict):
        conversions = data.get("conversions") or {}
        pairs = [
            (base, quote, rate)
            for base, quotes in conversions.items()
            for quote, rate in (quotes or {}).items()
        ]

        generated_at = _to_et_datetime(data.get("generatedAt"))
        self.base_currency = [
            str(base) if base not in MISSING_VALUES else ""
            for base, _, _ in pairs
        ]
        self.quote_currency = [
            str(quote) if quote not in MISSING_VALUES else ""
            for _, quote, _ in pairs
        ]
        self.rate = [_sanitize_float(rate) for _, _, rate in pairs]
        self.generated_at = [generated_at for _ in pairs]

        self.data_dict = {
            "base_currency": self.base_currency,
            "quote_currency": self.quote_currency,
            "rate": self.rate,
            "generated_at": self.generated_at,
        }

        self.as_dataframe = pd.DataFrame(self.data_dict)
