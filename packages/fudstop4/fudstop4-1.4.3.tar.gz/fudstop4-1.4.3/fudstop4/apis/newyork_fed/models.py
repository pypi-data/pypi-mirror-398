import pandas as pd

MISSING_VALUES = (None, "", "--", "NA", "N/A")


def _sanitize_string(value: object) -> str:
    if value in MISSING_VALUES:
        return ""
    return str(value).strip()


def _strip_numeric(value: object) -> str:
    return str(value).replace(",", "").replace("%", "").strip()


def _to_float(value: object) -> float:
    if value in MISSING_VALUES:
        return 0.0
    try:
        return float(_strip_numeric(value))
    except (TypeError, ValueError):
        return 0.0


def _to_int(value: object) -> int:
    if value in MISSING_VALUES:
        return 0
    try:
        return int(float(_strip_numeric(value)))
    except (TypeError, ValueError):
        return 0


def _to_bool(value: object) -> bool:
    if value in MISSING_VALUES:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "t", "1", "yes", "y")


def _to_datetime(value: object):
    if value in MISSING_VALUES:
        return None
    try:
        dt = pd.to_datetime(value, errors="coerce")
    except (TypeError, ValueError):
        return None
    if pd.isna(dt):
        return None
    if getattr(dt, "tzinfo", None) is not None:
        dt = dt.tz_convert("US/Eastern").tz_localize(None)
    return dt.to_pydatetime()


class AmbsAuctions:
    def __init__(self, auctions: list[dict]):
        self.auction_status = [_sanitize_string(i.get("auctionStatus")) for i in auctions]
        self.operation_id = [_sanitize_string(i.get("operationId")) for i in auctions]
        self.operation_date = [_to_datetime(i.get("operationDate")) for i in auctions]
        self.operation_type = [_sanitize_string(i.get("operationType")) for i in auctions]
        self.operation_direction = [_sanitize_string(i.get("operationDirection")) for i in auctions]
        self.method = [_sanitize_string(i.get("method")) for i in auctions]
        self.release_time = [_sanitize_string(i.get("releaseTime")) for i in auctions]
        self.close_time = [_sanitize_string(i.get("closeTime")) for i in auctions]
        self.class_type = [_sanitize_string(i.get("classType")) for i in auctions]
        self.total_submitted_orig_face = [_to_float(i.get("totalSubmittedOrigFace")) for i in auctions]
        self.total_accepted_orig_face = [_to_float(i.get("totalAcceptedOrigFace")) for i in auctions]
        self.total_submitted_curr_face = [_to_float(i.get("totalSubmittedCurrFace")) for i in auctions]
        self.total_accepted_curr_face = [_to_float(i.get("totalAcceptedCurrFace")) for i in auctions]
        self.total_amt_submitted_par = [_to_float(i.get("totalAmtSubmittedPar")) for i in auctions]
        self.total_amt_accepted_par = [_to_float(i.get("totalAmtAcceptedPar")) for i in auctions]
        self.settlement_date = [_to_datetime(i.get("settlementDate")) for i in auctions]
        self.last_updated = [_to_datetime(i.get("lastUpdated")) for i in auctions]
        self.note = [_sanitize_string(i.get("note")) for i in auctions]

        self.data_dict = {
            "auction_status": self.auction_status,
            "operation_id": self.operation_id,
            "operation_date": self.operation_date,
            "operation_type": self.operation_type,
            "operation_direction": self.operation_direction,
            "method": self.method,
            "release_time": self.release_time,
            "close_time": self.close_time,
            "class_type": self.class_type,
            "total_submitted_orig_face": self.total_submitted_orig_face,
            "total_accepted_orig_face": self.total_accepted_orig_face,
            "total_submitted_curr_face": self.total_submitted_curr_face,
            "total_accepted_curr_face": self.total_accepted_curr_face,
            "total_amt_submitted_par": self.total_amt_submitted_par,
            "total_amt_accepted_par": self.total_amt_accepted_par,
            "settlement_date": self.settlement_date,
            "last_updated": self.last_updated,
            "note": self.note,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)
        self.df = self.as_dataframe


class AmbsAuctionDetails:
    def __init__(self, auctions: list[dict]):
        pairs = [
            (auction, detail)
            for auction in auctions
            for detail in (auction.get("details") or [])
        ]
        self.operation_id = [_sanitize_string(a.get("operationId")) for a, _ in pairs]
        self.operation_date = [_to_datetime(a.get("operationDate")) for a, _ in pairs]
        self.operation_type = [_sanitize_string(a.get("operationType")) for a, _ in pairs]
        self.inclusion_flag = [_sanitize_string(d.get("inclusionExclusionFlag")) for _, d in pairs]
        self.security_description = [_sanitize_string(d.get("securityDescription")) for _, d in pairs]
        self.amt_accepted_par = [_to_float(d.get("amtAcceptedPar")) for _, d in pairs]

        self.data_dict = {
            "operation_id": self.operation_id,
            "operation_date": self.operation_date,
            "operation_type": self.operation_type,
            "inclusion_flag": self.inclusion_flag,
            "security_description": self.security_description,
            "amt_accepted_par": self.amt_accepted_par,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class TsyOperations:
    def __init__(self, auctions: list[dict]):
        self.operation_id = [_sanitize_string(i.get("operationId")) for i in auctions]
        self.auction_status = [_sanitize_string(i.get("auctionStatus")) for i in auctions]
        self.operation_type = [_sanitize_string(i.get("operationType")) for i in auctions]
        self.operation_date = [_to_datetime(i.get("operationDate")) for i in auctions]
        self.settlement_date = [_to_datetime(i.get("settlementDate") or i.get("settlementdate")) for i in auctions]
        self.maturity_range_start = [_to_datetime(i.get("maturityRangeStart")) for i in auctions]
        self.maturity_range_end = [_to_datetime(i.get("maturityRangeEnd")) for i in auctions]
        self.operation_direction = [_sanitize_string(i.get("operationDirection")) for i in auctions]
        self.auction_method = [_sanitize_string(i.get("auctionMethod")) for i in auctions]
        self.release_time = [_sanitize_string(i.get("releaseTime")) for i in auctions]
        self.close_time = [_sanitize_string(i.get("closeTime")) for i in auctions]
        self.total_par_amt_submitted = [_to_float(i.get("totalParAmtSubmitted")) for i in auctions]
        self.total_par_amt_accepted = [_to_float(i.get("totalParAmtAccepted")) for i in auctions]
        self.note = [_sanitize_string(i.get("note")) for i in auctions]
        self.last_updated = [_to_datetime(i.get("lastupdated") or i.get("lastUpdated")) for i in auctions]

        self.data_dict = {
            "operation_id": self.operation_id,
            "auction_status": self.auction_status,
            "operation_type": self.operation_type,
            "operation_date": self.operation_date,
            "settlement_date": self.settlement_date,
            "maturity_range_start": self.maturity_range_start,
            "maturity_range_end": self.maturity_range_end,
            "operation_direction": self.operation_direction,
            "auction_method": self.auction_method,
            "release_time": self.release_time,
            "close_time": self.close_time,
            "total_par_amt_submitted": self.total_par_amt_submitted,
            "total_par_amt_accepted": self.total_par_amt_accepted,
            "note": self.note,
            "last_updated": self.last_updated,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)
        self.df = self.as_dataframe


class TsyOperationDetails:
    def __init__(self, auctions: list[dict]):
        pairs = [
            (auction, detail)
            for auction in auctions
            for detail in (auction.get("details") or [])
        ]
        self.operation_id = [_sanitize_string(a.get("operationId")) for a, _ in pairs]
        self.operation_date = [_to_datetime(a.get("operationDate")) for a, _ in pairs]
        self.inclusion_indicator = [_sanitize_string(d.get("inclusionIndicator")) for _, d in pairs]
        self.cusip = [_sanitize_string(d.get("cusip")) for _, d in pairs]
        self.security_description = [_sanitize_string(d.get("securityDescription")) for _, d in pairs]
        self.par_amount_accepted = [_to_float(d.get("parAmountAccepted")) for _, d in pairs]
        self.weighted_avg_accept_price = [_sanitize_string(d.get("weightedAvgAccptPrice")) for _, d in pairs]
        self.least_favorite_accept_price = [_sanitize_string(d.get("leastFavoriteAccptPrice")) for _, d in pairs]
        self.percent_allotted_least_favorite_accept_price = [
            _sanitize_string(d.get("percentAllottedleastFavoriteAccptPrice")) for _, d in pairs
        ]

        self.data_dict = {
            "operation_id": self.operation_id,
            "operation_date": self.operation_date,
            "inclusion_indicator": self.inclusion_indicator,
            "cusip": self.cusip,
            "security_description": self.security_description,
            "par_amount_accepted": self.par_amount_accepted,
            "weighted_avg_accept_price": self.weighted_avg_accept_price,
            "least_favorite_accept_price": self.least_favorite_accept_price,
            "percent_allotted_least_favorite_accept_price": self.percent_allotted_least_favorite_accept_price,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class FxSwapsOperations:
    def __init__(self, operations: list[dict]):
        self.operation_type = [_sanitize_string(i.get("operationType")) for i in operations]
        self.counterparty = [_sanitize_string(i.get("counterparty")) for i in operations]
        self.currency = [_sanitize_string(i.get("currency")) for i in operations]
        self.trade_date = [_to_datetime(i.get("tradeDate")) for i in operations]
        self.settlement_date = [_to_datetime(i.get("settlementDate")) for i in operations]
        self.maturity_date = [_to_datetime(i.get("maturityDate")) for i in operations]
        self.term_in_days = [_to_int(i.get("termInDays")) for i in operations]
        self.amount = [_to_float(i.get("amount")) for i in operations]
        self.interest_rate = [_to_float(i.get("interestRate")) for i in operations]
        self.is_small_value = [_to_bool(i.get("isSmallValue")) for i in operations]
        self.last_updated = [_to_datetime(i.get("lastUpdated")) for i in operations]

        self.data_dict = {
            "operation_type": self.operation_type,
            "counterparty": self.counterparty,
            "currency": self.currency,
            "trade_date": self.trade_date,
            "settlement_date": self.settlement_date,
            "maturity_date": self.maturity_date,
            "term_in_days": self.term_in_days,
            "amount": self.amount,
            "interest_rate": self.interest_rate,
            "is_small_value": self.is_small_value,
            "last_updated": self.last_updated,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)
        self.df = self.as_dataframe


class FxSwapCounterparties:
    def __init__(self, counterparties: list[str]):
        self.counterparty = [_sanitize_string(i) for i in counterparties]
        self.data_dict = {"counterparty": self.counterparty}
        self.as_dataframe = pd.DataFrame(self.data_dict)


class GuideSheetSi:
    def __init__(self, data: dict):
        self.title = [_sanitize_string(data.get("title"))]
        self.guide_msg = [_sanitize_string(data.get("guideMsg"))]
        self.note = [_sanitize_string(data.get("note"))]
        self.report_weeks_from_date = [_to_datetime(data.get("reportWeeksFromDate"))]
        self.report_weeks_to_date = [_to_datetime(data.get("reportWeeksToDate"))]
        self.next_distribution_date = [_to_datetime(data.get("nextDistributionDate"))]

        self.data_dict = {
            "title": self.title,
            "guide_msg": self.guide_msg,
            "note": self.note,
            "report_weeks_from_date": self.report_weeks_from_date,
            "report_weeks_to_date": self.report_weeks_to_date,
            "next_distribution_date": self.next_distribution_date,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class GuideSheetSiDetails:
    def __init__(self, details: list[dict]):
        self.form_line = [_sanitize_string(i.get("formLine")) for i in details]
        self.sec_type = [_sanitize_string(i.get("secType")) for i in details]
        self.ny_fed_sec_id = [_sanitize_string(i.get("nyFedSecId")) for i in details]
        self.cusip = [_sanitize_string(i.get("cusip")) for i in details]
        self.issue_date = [_to_datetime(i.get("issueDate")) for i in details]
        self.maturity_date = [_to_datetime(i.get("maturityDate")) for i in details]
        self.percent_coupon_rate = [_to_float(i.get("percentCouponRate")) for i in details]

        self.data_dict = {
            "form_line": self.form_line,
            "sec_type": self.sec_type,
            "ny_fed_sec_id": self.ny_fed_sec_id,
            "cusip": self.cusip,
            "issue_date": self.issue_date,
            "maturity_date": self.maturity_date,
            "percent_coupon_rate": self.percent_coupon_rate,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class GuideSheetWi:
    def __init__(self, data: dict):
        self.title = [_sanitize_string(data.get("title"))]
        self.guide_msg = [_sanitize_string(data.get("guideMsg"))]
        self.note = [_sanitize_string(data.get("note"))]
        self.sec_dir_as_of_date = [_to_datetime(data.get("secDirAsOfDate"))]
        self.first_due_date = [_to_datetime(data.get("firstDueDate"))]
        self.first_as_of_date = [_to_datetime(data.get("firstAsOfDate"))]
        self.last_due_date = [_to_datetime(data.get("lastDueDate"))]
        self.last_as_of_date = [_to_datetime(data.get("lastAsOfDate"))]

        self.data_dict = {
            "title": self.title,
            "guide_msg": self.guide_msg,
            "note": self.note,
            "sec_dir_as_of_date": self.sec_dir_as_of_date,
            "first_due_date": self.first_due_date,
            "first_as_of_date": self.first_as_of_date,
            "last_due_date": self.last_due_date,
            "last_as_of_date": self.last_as_of_date,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class GuideSheetWiDetails:
    def __init__(self, details: list[dict]):
        self.sec_type = [_sanitize_string(i.get("secType")) for i in details]
        self.ny_fed_sec_id = [_sanitize_string(i.get("nyFedSecId")) for i in details]
        self.cusip = [_sanitize_string(i.get("cusip")) for i in details]
        self.announcement_date = [_to_datetime(i.get("announcementDate")) for i in details]
        self.auction_date = [_to_datetime(i.get("auctionDate")) for i in details]
        self.issue_date = [_to_datetime(i.get("issueDate")) for i in details]
        self.maturity_date = [_to_datetime(i.get("maturityDate")) for i in details]
        self.percent_coupon_rate = [_to_float(i.get("percentCouponRate")) for i in details]

        self.data_dict = {
            "sec_type": self.sec_type,
            "ny_fed_sec_id": self.ny_fed_sec_id,
            "cusip": self.cusip,
            "announcement_date": self.announcement_date,
            "auction_date": self.auction_date,
            "issue_date": self.issue_date,
            "maturity_date": self.maturity_date,
            "percent_coupon_rate": self.percent_coupon_rate,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class GuideSheetFs:
    def __init__(self, data: dict):
        self.title = [_sanitize_string(data.get("title"))]
        self.guide_msg = [_sanitize_string(data.get("guideMsg"))]
        self.note = [_sanitize_string(data.get("note"))]
        self.reports_for = [_to_datetime(data.get("reportsFor"))]
        self.next_distribution_date = [_to_datetime(data.get("nextDistributionDate"))]

        self.data_dict = {
            "title": self.title,
            "guide_msg": self.guide_msg,
            "note": self.note,
            "reports_for": self.reports_for,
            "next_distribution_date": self.next_distribution_date,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class GuideSheetFsDetails:
    def __init__(self, details: list[dict]):
        self.report_name = [_sanitize_string(i.get("reportName")) for i in details]
        self.as_of_class_settle_date = [_to_datetime(i.get("asOfClassSettleDate")) for i in details]
        self.report_due_date = [_to_datetime(i.get("reportDueDate")) for i in details]

        self.data_dict = {
            "report_name": self.report_name,
            "as_of_class_settle_date": self.as_of_class_settle_date,
            "report_due_date": self.report_due_date,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class PrimaryDealerTimeSeries:
    def __init__(self, timeseries: list[dict]):
        self.series_break = [_sanitize_string(i.get("seriesbreak")) for i in timeseries]
        self.key_id = [_sanitize_string(i.get("keyid")) for i in timeseries]
        self.description = [_sanitize_string(i.get("description")) for i in timeseries]

        self.data_dict = {
            "series_break": self.series_break,
            "key_id": self.key_id,
            "description": self.description,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)
        self.df = self.as_dataframe


class PrimaryDealerTimeSeriesSet:
    def __init__(self, timeseries: list[dict]):
        self.as_of_date = [_to_datetime(i.get("asofdate")) for i in timeseries]
        self.key_id = [_sanitize_string(i.get("keyid")) for i in timeseries]
        self.value = [_to_float(i.get("value")) for i in timeseries]

        self.data_dict = {
            "as_of_date": self.as_of_date,
            "key_id": self.key_id,
            "value": self.value,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)
        self.df = self.as_dataframe


class PrimaryDealerAsOfDates:
    def __init__(self, dates: list[dict]):
        self.series_break = [_sanitize_string(i.get("seriesbreak")) for i in dates]
        self.as_of = [_to_datetime(i.get("asof")) for i in dates]

        self.data_dict = {
            "series_break": self.series_break,
            "as_of": self.as_of,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)
        self.df = self.as_dataframe


class PrimaryDealerSeriesBreaks:
    def __init__(self, series_breaks: list[dict]):
        self.label = [_sanitize_string(i.get("label")) for i in series_breaks]
        self.series_break = [_sanitize_string(i.get("seriesbreak")) for i in series_breaks]
        self.start_date = [_to_datetime(i.get("startdate")) for i in series_breaks]
        self.end_date = [_to_datetime(i.get("enddate")) for i in series_breaks]

        self.data_dict = {
            "label": self.label,
            "series_break": self.series_break,
            "start_date": self.start_date,
            "end_date": self.end_date,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class PrimaryDealerMarketShareSummary:
    def __init__(self, record: dict):
        num_dealers = record.get("numDealers") or {}
        self.release_date = [_to_datetime(record.get("releaseDate"))]
        self.title = [_sanitize_string(record.get("title"))]
        self.num_dealers_first_quint = [_to_int(num_dealers.get("firstQuint"))]
        self.num_dealers_second_quint = [_to_int(num_dealers.get("secondQuint"))]
        self.num_dealers_third_quint = [_to_int(num_dealers.get("thirdQuint"))]
        self.num_dealers_fourth_quint = [_to_int(num_dealers.get("fourthQuint"))]
        self.num_dealers_fifth_quint = [_to_int(num_dealers.get("fifthQuint"))]

        self.data_dict = {
            "release_date": self.release_date,
            "title": self.title,
            "num_dealers_first_quint": self.num_dealers_first_quint,
            "num_dealers_second_quint": self.num_dealers_second_quint,
            "num_dealers_third_quint": self.num_dealers_third_quint,
            "num_dealers_fourth_quint": self.num_dealers_fourth_quint,
            "num_dealers_fifth_quint": self.num_dealers_fifth_quint,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class PrimaryDealerMarketShareDealers:
    def __init__(self, record: dict):
        release_date = _to_datetime(record.get("releaseDate"))
        title = _sanitize_string(record.get("title"))

        dealers = []
        for category, key in (
            ("inter_dealer_brokers", "interDealerBrokers"),
            ("others", "others"),
            ("totals", "totals"),
        ):
            for dealer in record.get(key) or []:
                dealers.append((category, dealer))

        self.release_date = [release_date for _ in dealers]
        self.title = [title for _ in dealers]
        self.category = [c for c, _ in dealers]
        self.security_type = [_sanitize_string(d.get("securityType")) for _, d in dealers]
        self.security = [_sanitize_string(d.get("security")) for _, d in dealers]
        self.percent_first_quint_range = [_sanitize_string(d.get("percentFirstQuintRange")) for _, d in dealers]
        self.percent_first_quint_mkt_share = [_to_float(d.get("percentFirstQuintMktShare")) for _, d in dealers]
        self.percent_second_quint_range = [_sanitize_string(d.get("percentSecondQuintRange")) for _, d in dealers]
        self.percent_second_quint_mkt_share = [_to_float(d.get("percentSecondQuintMktShare")) for _, d in dealers]
        self.percent_third_quint_range = [_sanitize_string(d.get("percentThirdQuintRange")) for _, d in dealers]
        self.percent_third_quint_mkt_share = [_to_float(d.get("percentThirdQuintMktShare")) for _, d in dealers]
        self.percent_fourth_quint_range = [_sanitize_string(d.get("percentFourthQuintRange")) for _, d in dealers]
        self.percent_fourth_quint_mkt_share = [_to_float(d.get("percentFourthQuintMktShare")) for _, d in dealers]
        self.percent_fifth_quint_range = [_sanitize_string(d.get("percentFifthQuintRange")) for _, d in dealers]
        self.percent_fifth_quint_mkt_share = [_to_float(d.get("percentFifthQuintMktShare")) for _, d in dealers]
        self.daily_avg_vol_in_millions = [_to_float(d.get("dailyAvgVolInMillions")) for _, d in dealers]

        self.data_dict = {
            "release_date": self.release_date,
            "title": self.title,
            "category": self.category,
            "security_type": self.security_type,
            "security": self.security,
            "percent_first_quint_range": self.percent_first_quint_range,
            "percent_first_quint_mkt_share": self.percent_first_quint_mkt_share,
            "percent_second_quint_range": self.percent_second_quint_range,
            "percent_second_quint_mkt_share": self.percent_second_quint_mkt_share,
            "percent_third_quint_range": self.percent_third_quint_range,
            "percent_third_quint_mkt_share": self.percent_third_quint_mkt_share,
            "percent_fourth_quint_range": self.percent_fourth_quint_range,
            "percent_fourth_quint_mkt_share": self.percent_fourth_quint_mkt_share,
            "percent_fifth_quint_range": self.percent_fifth_quint_range,
            "percent_fifth_quint_mkt_share": self.percent_fifth_quint_mkt_share,
            "daily_avg_vol_in_millions": self.daily_avg_vol_in_millions,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class ReferenceRates:
    def __init__(self, rates: list[dict]):
        self.effective_date = [_to_datetime(i.get("effectiveDate")) for i in rates]
        self.rate_type = [_sanitize_string(i.get("type")) for i in rates]
        self.percent = [_to_float(i.get("percent")) for i in rates]
        self.percent_percentile_1 = [_to_float(i.get("percentPercentile1")) for i in rates]
        self.percent_percentile_25 = [_to_float(i.get("percentPercentile25")) for i in rates]
        self.percent_percentile_75 = [_to_float(i.get("percentPercentile75")) for i in rates]
        self.percent_percentile_99 = [_to_float(i.get("percentPercentile99")) for i in rates]
        self.target_rate_from = [_to_float(i.get("targetRateFrom")) for i in rates]
        self.target_rate_to = [_to_float(i.get("targetRateTo")) for i in rates]
        self.volume_in_billions = [_to_float(i.get("volumeInBillions")) for i in rates]
        self.footnote_id = [_sanitize_string(i.get("footnoteId")) for i in rates]
        self.revision_indicator = [_sanitize_string(i.get("revisionIndicator")) for i in rates]
        self.target_range = [_sanitize_string(i.get("targetRange")) for i in rates]
        self.intra_day_low = [_to_float(i.get("intraDayLow")) for i in rates]
        self.intra_day_high = [_to_float(i.get("intraDayHigh")) for i in rates]
        self.std_deviation = [_to_float(i.get("stdDeviation")) for i in rates]
        self.average_30_day = [_to_float(i.get("average30day")) for i in rates]
        self.average_90_day = [_to_float(i.get("average90day")) for i in rates]
        self.average_180_day = [_to_float(i.get("average180day")) for i in rates]
        self.index = [_to_float(i.get("index")) for i in rates]

        self.data_dict = {
            "effective_date": self.effective_date,
            "rate_type": self.rate_type,
            "percent": self.percent,
            "percent_percentile_1": self.percent_percentile_1,
            "percent_percentile_25": self.percent_percentile_25,
            "percent_percentile_75": self.percent_percentile_75,
            "percent_percentile_99": self.percent_percentile_99,
            "target_rate_from": self.target_rate_from,
            "target_rate_to": self.target_rate_to,
            "volume_in_billions": self.volume_in_billions,
            "footnote_id": self.footnote_id,
            "revision_indicator": self.revision_indicator,
            "target_range": self.target_range,
            "intra_day_low": self.intra_day_low,
            "intra_day_high": self.intra_day_high,
            "std_deviation": self.std_deviation,
            "average_30_day": self.average_30_day,
            "average_90_day": self.average_90_day,
            "average_180_day": self.average_180_day,
            "index": self.index,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)
        self.df = self.as_dataframe


class RepoOperations:
    def __init__(self, operations: list[dict]):
        self.operation_id = [_sanitize_string(i.get("operationId")) for i in operations]
        self.operation_date = [_to_datetime(i.get("operationDate")) for i in operations]
        self.auction_status = [_sanitize_string(i.get("auctionStatus")) for i in operations]
        self.settlement_date = [_to_datetime(i.get("settlementDate")) for i in operations]
        self.maturity_date = [_to_datetime(i.get("maturityDate")) for i in operations]
        self.operation_type = [_sanitize_string(i.get("operationType")) for i in operations]
        self.operation_method = [_sanitize_string(i.get("operationMethod")) for i in operations]
        self.settlement_type = [_sanitize_string(i.get("settlementType")) for i in operations]
        self.term_calendar_days = [_to_int(i.get("termCalenderDays")) for i in operations]
        self.close_time = [_sanitize_string(i.get("closeTime")) for i in operations]
        self.total_amt_submitted = [_to_float(i.get("totalAmtSubmitted")) for i in operations]
        self.total_amt_accepted = [_to_float(i.get("totalAmtAccepted")) for i in operations]
        self.participating_cpty = [_to_int(i.get("participatingCpty")) for i in operations]
        self.accepted_cpty = [_to_int(i.get("acceptedCpty")) for i in operations]
        self.last_updated = [_to_datetime(i.get("lastUpdated")) for i in operations]
        self.note = [_sanitize_string(i.get("note")) for i in operations]

        self.data_dict = {
            "operation_id": self.operation_id,
            "operation_date": self.operation_date,
            "auction_status": self.auction_status,
            "settlement_date": self.settlement_date,
            "maturity_date": self.maturity_date,
            "operation_type": self.operation_type,
            "operation_method": self.operation_method,
            "settlement_type": self.settlement_type,
            "term_calendar_days": self.term_calendar_days,
            "close_time": self.close_time,
            "total_amt_submitted": self.total_amt_submitted,
            "total_amt_accepted": self.total_amt_accepted,
            "participating_cpty": self.participating_cpty,
            "accepted_cpty": self.accepted_cpty,
            "last_updated": self.last_updated,
            "note": self.note,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)
        self.df = self.as_dataframe


class RepoTrancheDetails:
    def __init__(self, operations: list[dict]):
        rows = [
            (operation, detail)
            for operation in operations
            for detail in (operation.get("details") or [])
        ]
        self.operation_id = [_sanitize_string(op.get("operationId")) for op, _ in rows]
        self.operation_date = [_to_datetime(op.get("operationDate")) for op, _ in rows]
        self.operation_method = [_sanitize_string(op.get("operationMethod")) for op, _ in rows]
        self.security_type = [_sanitize_string(d.get("securityType")) for _, d in rows]
        self.amt_submitted = [_to_float(d.get("amtSubmitted")) for _, d in rows]
        self.amt_accepted = [_to_float(d.get("amtAccepted")) for _, d in rows]
        self.minimum_bid_rate = [_to_float(d.get("minimumBidRate")) for _, d in rows]
        self.maximum_bid_rate = [_to_float(d.get("maximumBidRate")) for _, d in rows]
        self.percent_offering_rate = [_to_float(d.get("percentOfferingRate")) for _, d in rows]
        self.percent_award_rate = [_to_float(d.get("percentAwardRate")) for _, d in rows]
        self.percent_amt_at_stop_out = [_to_float(d.get("percentAmtAtStopOut")) for _, d in rows]
        self.percent_high_rate = [_to_float(d.get("percentHighRate")) for _, d in rows]
        self.percent_low_rate = [_to_float(d.get("percentLowRate")) for _, d in rows]
        self.percent_stop_out_rate = [_to_float(d.get("percentStopOutRate")) for _, d in rows]
        self.percent_weighted_average_rate = [_to_float(d.get("percentWeightedAverageRate")) for _, d in rows]

        self.data_dict = {
            "operation_id": self.operation_id,
            "operation_date": self.operation_date,
            "operation_method": self.operation_method,
            "security_type": self.security_type,
            "amt_submitted": self.amt_submitted,
            "amt_accepted": self.amt_accepted,
            "minimum_bid_rate": self.minimum_bid_rate,
            "maximum_bid_rate": self.maximum_bid_rate,
            "percent_offering_rate": self.percent_offering_rate,
            "percent_award_rate": self.percent_award_rate,
            "percent_amt_at_stop_out": self.percent_amt_at_stop_out,
            "percent_high_rate": self.percent_high_rate,
            "percent_low_rate": self.percent_low_rate,
            "percent_stop_out_rate": self.percent_stop_out_rate,
            "percent_weighted_average_rate": self.percent_weighted_average_rate,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class RepoSettlementAmounts:
    def __init__(self, operations: list[dict]):
        rows = [
            (operation, settlement)
            for operation in operations
            for settlement in (operation.get("settlementAmts") or [])
        ]
        self.operation_id = [_sanitize_string(op.get("operationId")) for op, _ in rows]
        self.operation_date = [_to_datetime(op.get("operationDate")) for op, _ in rows]
        self.counterparty_type = [_sanitize_string(s.get("counterpartyType")) for _, s in rows]
        self.security_type = [_sanitize_string(s.get("securityType")) for _, s in rows]
        self.amt_accepted = [_to_float(s.get("amtAccepted")) for _, s in rows]

        self.data_dict = {
            "operation_id": self.operation_id,
            "operation_date": self.operation_date,
            "counterparty_type": self.counterparty_type,
            "security_type": self.security_type,
            "amt_accepted": self.amt_accepted,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class RepoPropositions:
    def __init__(self, operations: list[dict]):
        rows = [
            (operation, prop)
            for operation in operations
            for prop in (operation.get("propositions") or [])
        ]
        self.operation_id = [_sanitize_string(op.get("operationId")) for op, _ in rows]
        self.operation_date = [_to_datetime(op.get("operationDate")) for op, _ in rows]
        self.counterparty_type = [_sanitize_string(p.get("counterpartyType")) for _, p in rows]
        self.amt_accepted = [_to_float(p.get("amtAccepted")) for _, p in rows]

        self.data_dict = {
            "operation_id": self.operation_id,
            "operation_date": self.operation_date,
            "counterparty_type": self.counterparty_type,
            "amt_accepted": self.amt_accepted,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class RepoPostOperations:
    def __init__(self, operations: list[dict]):
        self.operation_id = [_sanitize_string(i.get("operationId")) for i in operations]
        self.operation_date = [_to_datetime(i.get("operationDate")) for i in operations]
        self.operation_type = [_sanitize_string(i.get("operationType")) for i in operations]
        self.note = [_sanitize_string(i.get("note")) for i in operations]
        self.total_amt_accepted = [_to_float(i.get("totalAmtAccepted")) for i in operations]

        self.data_dict = {
            "operation_id": self.operation_id,
            "operation_date": self.operation_date,
            "operation_type": self.operation_type,
            "note": self.note,
            "total_amt_accepted": self.total_amt_accepted,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class SecuritiesLendingOperations:
    def __init__(self, operations: list[dict]):
        self.operation_id = [_sanitize_string(i.get("operationId")) for i in operations]
        self.auction_status = [_sanitize_string(i.get("auctionStatus")) for i in operations]
        self.operation_type = [_sanitize_string(i.get("operationType")) for i in operations]
        self.operation_date = [_to_datetime(i.get("operationDate")) for i in operations]
        self.settlement_date = [_to_datetime(i.get("settlementDate")) for i in operations]
        self.maturity_date = [_to_datetime(i.get("maturityDate")) for i in operations]
        self.release_time = [_sanitize_string(i.get("releaseTime")) for i in operations]
        self.close_time = [_sanitize_string(i.get("closeTime")) for i in operations]
        self.note = [_sanitize_string(i.get("note")) for i in operations]
        self.last_updated = [_to_datetime(i.get("lastUpdated")) for i in operations]
        self.total_par_amt_submitted = [_to_float(i.get("totalParAmtSubmitted")) for i in operations]
        self.total_par_amt_accepted = [_to_float(i.get("totalParAmtAccepted")) for i in operations]
        self.total_par_amt_extended = [_to_float(i.get("totalParAmtExtended")) for i in operations]

        self.data_dict = {
            "operation_id": self.operation_id,
            "auction_status": self.auction_status,
            "operation_type": self.operation_type,
            "operation_date": self.operation_date,
            "settlement_date": self.settlement_date,
            "maturity_date": self.maturity_date,
            "release_time": self.release_time,
            "close_time": self.close_time,
            "note": self.note,
            "last_updated": self.last_updated,
            "total_par_amt_submitted": self.total_par_amt_submitted,
            "total_par_amt_accepted": self.total_par_amt_accepted,
            "total_par_amt_extended": self.total_par_amt_extended,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)
        self.df = self.as_dataframe


class SecuritiesLendingDetails:
    def __init__(self, operations: list[dict]):
        rows = [
            (operation, detail)
            for operation in operations
            for detail in (operation.get("details") or [])
        ]
        self.operation_id = [_sanitize_string(op.get("operationId")) for op, _ in rows]
        self.operation_date = [_to_datetime(op.get("operationDate")) for op, _ in rows]
        self.cusip = [_sanitize_string(d.get("cusip")) for _, d in rows]
        self.security_description = [_sanitize_string(d.get("securityDescription")) for _, d in rows]
        self.par_amt_submitted = [_to_float(d.get("parAmtSubmitted")) for _, d in rows]
        self.par_amt_accepted = [_to_float(d.get("parAmtAccepted")) for _, d in rows]
        self.par_amt_extended = [_to_float(d.get("parAmtExtended")) for _, d in rows]
        self.weighted_average_rate = [_to_float(d.get("weightedAverageRate")) for _, d in rows]
        self.soma_holdings = [_to_float(d.get("somaHoldings")) for _, d in rows]
        self.theo_avail_to_borrow = [_to_float(d.get("theoAvailToBorrow")) for _, d in rows]
        self.actual_avail_to_borrow = [_to_float(d.get("actualAvailToBorrow")) for _, d in rows]
        self.outstanding_loans = [_to_float(d.get("outstandingLoans")) for _, d in rows]

        self.data_dict = {
            "operation_id": self.operation_id,
            "operation_date": self.operation_date,
            "cusip": self.cusip,
            "security_description": self.security_description,
            "par_amt_submitted": self.par_amt_submitted,
            "par_amt_accepted": self.par_amt_accepted,
            "par_amt_extended": self.par_amt_extended,
            "weighted_average_rate": self.weighted_average_rate,
            "soma_holdings": self.soma_holdings,
            "theo_avail_to_borrow": self.theo_avail_to_borrow,
            "actual_avail_to_borrow": self.actual_avail_to_borrow,
            "outstanding_loans": self.outstanding_loans,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class SecuritiesLendingCusipOperations:
    def __init__(self, operations: list[dict]):
        self.operation_id = [_sanitize_string(i.get("operationId")) for i in operations]
        self.operation_type = [_sanitize_string(i.get("operationType")) for i in operations]
        self.operation_date = [_to_datetime(i.get("operationDate")) for i in operations]
        self.settlement_date = [_to_datetime(i.get("settlementDate")) for i in operations]
        self.maturity_date = [_to_datetime(i.get("maturityDate")) for i in operations]
        self.cusip = [_sanitize_string(i.get("cusip")) for i in operations]
        self.security_description = [_sanitize_string(i.get("securityDescription")) for i in operations]
        self.par_amt_submitted = [_to_float(i.get("parAmtSubmitted")) for i in operations]
        self.par_amt_accepted = [_to_float(i.get("parAmtAccepted")) for i in operations]
        self.par_amt_extended = [_to_float(i.get("parAmtExtended")) for i in operations]
        self.weighted_average_rate = [_to_float(i.get("weightedAverageRate")) for i in operations]
        self.soma_holdings = [_to_float(i.get("somaHoldings")) for i in operations]
        self.theo_avail_to_borrow = [_to_float(i.get("theoAvailToBorrow")) for i in operations]
        self.actual_avail_to_borrow = [_to_float(i.get("actualAvailToBorrow")) for i in operations]
        self.outstanding_loans = [_to_float(i.get("outstandingLoans")) for i in operations]

        self.data_dict = {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "operation_date": self.operation_date,
            "settlement_date": self.settlement_date,
            "maturity_date": self.maturity_date,
            "cusip": self.cusip,
            "security_description": self.security_description,
            "par_amt_submitted": self.par_amt_submitted,
            "par_amt_accepted": self.par_amt_accepted,
            "par_amt_extended": self.par_amt_extended,
            "weighted_average_rate": self.weighted_average_rate,
            "soma_holdings": self.soma_holdings,
            "theo_avail_to_borrow": self.theo_avail_to_borrow,
            "actual_avail_to_borrow": self.actual_avail_to_borrow,
            "outstanding_loans": self.outstanding_loans,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class SomaSummary:
    def __init__(self, summary: list[dict]):
        self.as_of_date = [_to_datetime(i.get("asOfDate")) for i in summary]
        self.mbs = [_to_float(i.get("mbs")) for i in summary]
        self.cmbs = [_to_float(i.get("cmbs")) for i in summary]
        self.tips = [_to_float(i.get("tips")) for i in summary]
        self.frn = [_to_float(i.get("frn")) for i in summary]
        self.tips_inflation_compensation = [_to_float(i.get("tipsInflationCompensation")) for i in summary]
        self.notes_bonds = [_to_float(i.get("notesbonds")) for i in summary]
        self.bills = [_to_float(i.get("bills")) for i in summary]
        self.agencies = [_to_float(i.get("agencies")) for i in summary]
        self.total = [_to_float(i.get("total")) for i in summary]

        self.data_dict = {
            "as_of_date": self.as_of_date,
            "mbs": self.mbs,
            "cmbs": self.cmbs,
            "tips": self.tips,
            "frn": self.frn,
            "tips_inflation_compensation": self.tips_inflation_compensation,
            "notes_bonds": self.notes_bonds,
            "bills": self.bills,
            "agencies": self.agencies,
            "total": self.total,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class SomaAsOfDates:
    def __init__(self, dates: list[str]):
        self.as_of_date = [_to_datetime(i) for i in dates]
        self.data_dict = {"as_of_date": self.as_of_date}
        self.as_dataframe = pd.DataFrame(self.data_dict)


class SomaReleaseDates:
    def __init__(self, dates: list[dict]):
        self.release_date = [_to_datetime(i.get("releaseDate")) for i in dates]
        self.as_of_date = [_to_datetime(i.get("asOfDate")) for i in dates]

        self.data_dict = {
            "release_date": self.release_date,
            "as_of_date": self.as_of_date,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class SomaWam:
    def __init__(self, data: dict):
        self.as_of_date = [_to_datetime(data.get("asOfDate"))]
        self.wam = [_to_float(data.get("wam"))]
        security_types = data.get("securityTypes") or []
        self.security_types = [", ".join([_sanitize_string(i) for i in security_types])]

        self.data_dict = {
            "as_of_date": self.as_of_date,
            "wam": self.wam,
            "security_types": self.security_types,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class SomaAgencyHoldings:
    def __init__(self, holdings: list[dict]):
        self.as_of_date = [_to_datetime(i.get("asOfDate")) for i in holdings]
        self.cusip = [_sanitize_string(i.get("cusip")) for i in holdings]
        self.maturity_date = [_to_datetime(i.get("maturityDate")) for i in holdings]
        self.issuer = [_sanitize_string(i.get("issuer")) for i in holdings]
        self.spread = [_sanitize_string(i.get("spread")) for i in holdings]
        self.coupon = [_to_float(i.get("coupon")) for i in holdings]
        self.par_value = [_to_float(i.get("parValue")) for i in holdings]
        self.inflation_compensation = [_to_float(i.get("inflationCompensation")) for i in holdings]
        self.percent_outstanding = [_to_float(i.get("percentOutstanding")) for i in holdings]
        self.change_from_prior_week = [_to_float(i.get("changeFromPriorWeek")) for i in holdings]
        self.change_from_prior_year = [_to_float(i.get("changeFromPriorYear")) for i in holdings]
        self.security_type = [_sanitize_string(i.get("securityType")) for i in holdings]
        self.security_description = [_sanitize_string(i.get("securityDescription")) for i in holdings]
        self.term = [_sanitize_string(i.get("term")) for i in holdings]
        self.current_face_value = [_to_float(i.get("currentFaceValue")) for i in holdings]
        self.is_aggregated = [_sanitize_string(i.get("isAggregated")) for i in holdings]

        self.data_dict = {
            "as_of_date": self.as_of_date,
            "cusip": self.cusip,
            "maturity_date": self.maturity_date,
            "issuer": self.issuer,
            "spread": self.spread,
            "coupon": self.coupon,
            "par_value": self.par_value,
            "inflation_compensation": self.inflation_compensation,
            "percent_outstanding": self.percent_outstanding,
            "change_from_prior_week": self.change_from_prior_week,
            "change_from_prior_year": self.change_from_prior_year,
            "security_type": self.security_type,
            "security_description": self.security_description,
            "term": self.term,
            "current_face_value": self.current_face_value,
            "is_aggregated": self.is_aggregated,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


class SomaTreasuryHoldings:
    def __init__(self, holdings: list[dict]):
        self.as_of_date = [_to_datetime(i.get("asOfDate")) for i in holdings]
        self.cusip = [_sanitize_string(i.get("cusip")) for i in holdings]
        self.maturity_date = [_to_datetime(i.get("maturityDate")) for i in holdings]
        self.issuer = [_sanitize_string(i.get("issuer")) for i in holdings]
        self.spread = [_sanitize_string(i.get("spread")) for i in holdings]
        self.coupon = [_to_float(i.get("coupon")) for i in holdings]
        self.par_value = [_to_float(i.get("parValue")) for i in holdings]
        self.inflation_compensation = [_to_float(i.get("inflationCompensation")) for i in holdings]
        self.percent_outstanding = [_to_float(i.get("percentOutstanding")) for i in holdings]
        self.change_from_prior_week = [_to_float(i.get("changeFromPriorWeek")) for i in holdings]
        self.change_from_prior_year = [_to_float(i.get("changeFromPriorYear")) for i in holdings]
        self.security_type = [_sanitize_string(i.get("securityType")) for i in holdings]

        self.data_dict = {
            "as_of_date": self.as_of_date,
            "cusip": self.cusip,
            "maturity_date": self.maturity_date,
            "issuer": self.issuer,
            "spread": self.spread,
            "coupon": self.coupon,
            "par_value": self.par_value,
            "inflation_compensation": self.inflation_compensation,
            "percent_outstanding": self.percent_outstanding,
            "change_from_prior_week": self.change_from_prior_week,
            "change_from_prior_year": self.change_from_prior_year,
            "security_type": self.security_type,
        }
        self.as_dataframe = pd.DataFrame(self.data_dict)


# Backward-compatible aliases
AuctionResult = AmbsAuctions
FXSwaps = FxSwapsOperations
TimeSeries = PrimaryDealerTimeSeries
TimeSeriesData = PrimaryDealerTimeSeriesSet
AsOfDates = PrimaryDealerAsOfDates
SecuredReferenceRates = ReferenceRates
SecuritiesLending = SecuritiesLendingOperations
