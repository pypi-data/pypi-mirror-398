
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import requests

import re
import json
import csv
from io import StringIO

import pandas as pd
from .models import AuctionResult, FXSwaps, TimeSeries, AsOfDates, TimeSeriesData, SecuredReferenceRates, RepoOperations, SecuritiesLending
import aiohttp
import asyncio
from fudstop4.apis.polygonio.polygon_options import PolygonOptions
from . import models as nyfed_models
session = requests.session()
from datetime import datetime, timedelta
today_str = datetime.now().strftime('%Y-%m-%d')
thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
class FedNewyork:
    def __init__(self):
        self.base_url = "https://markets.newyorkfed.org/api/"
        self.thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        self.today = datetime.now().strftime('%Y-%m-%d')
    def agency_mbs_search(self, start_date=thirty_days_ago, end_date=today_str):
        """Search for AMBS operations out of the Federal Reserve of New York"""

        r = session.get(self.base_url + f"ambs/all/results/summary/search.json?startDate={start_date}&endDate={today_str}").json()
        ambs = r['ambs']
        auctions = ambs['auctions']
        if auctions is not None:
            data = AuctionResult(auctions)
            return data
        else:
            return None
    

    def agency_mbs_count(self, number=10):
        """Return AMBS transactions by count."""
        r = session.get(self.base_url + f"ambs/all/results/details/last/{number}.json").json()
        ambs = r['ambs']
        auctions = ambs['auctions']
        if auctions is not None:
            data = AuctionResult(auctions)
            return data
        else:
            return None
        

    def soma_holdings(self):
        url = f"https://markets.newyorkfed.org/api/soma/summary.json"
        r = requests.get(url).json()
        soma = r['soma']
        summary = soma['summary'] if 'summary' in soma else None
        if summary is not None:
            return summary
    def liquidity_swaps_latest(self):
        """Get the latest central bank liquidity swap data."""
        r = session.get(self.base_url + f"fxs/all/latest.json").json()
        fxSwaps = r['fxSwaps']
        operations = fxSwaps['operations']
        if operations is not None:
            data = FXSwaps(operations)
            return data
        else:
            return "No recent data found."
        
    def liquidity_swaps_count(self, number=50):
        """Get the latest central bank liquidity swap data."""
        r = session.get(self.base_url + f"fxs/usdollar/last/{number}.json").json()
        fxSwaps = r['fxSwaps']
        operations = fxSwaps['operations']
        if operations is not None:
            data = FXSwaps(operations)
            return data
        else:
            return "No recent data found."
        

    def liquidity_swaps_search(self, start_date = "2023-01-01", end_date = today_str, type="trade", counterparties='japan,europe'):
        """Search for liquidity swaps between a custom date range.
        
        Arguments:
          >>> start_date: a date in YYYY-MM-DD format to start from
          >>> end_date: a date in YYYY-MM-DD to end on. defaults to today.
          >>> type: type of information to return. trade or maturity.
          >>> counterparties: list of counterparties. default: europe, japan
        """

        

        r = session.get(self.base_url + f"fxs/all/search.json?startDate={start_date}&endDate={end_date}&dateType={type}&counterparties={counterparties}").json()
        fxSwaps = r['fxSwaps']
        operations = fxSwaps['operations']
        if operations is not None:
            data = FXSwaps(operations)
            return data
        else:
            return None
        

    def get_fed_counterparties(self):
        """Returns the current counterparties to the Federal Reserve."""
        r = session.get(self.base_url + "fxs/list/counterparties.json").json()
        fxSwaps = r['fxSwaps']
        counterparties = fxSwaps['counterparties']
        if counterparties is not None:
            return counterparties


    def get_as_of_dates(self):
        """Returns a list of dates to query the FED API with."""
        r = session.get("https://markets.newyorkfed.org/api/pd/list/asof.json").json()
        pdd = r['pd']
        as_of_dates = pdd['asofdates']
        if as_of_dates is not None:
            data = AsOfDates(as_of_dates)
            return data
        else:
            return None
        
    def get_timeseries(self):
        """Returns the timeseries data to query the FED API"""

        r = requests.get("https://markets.newyorkfed.org/api/pd/list/timeseries.json").json()
        pdd = r['pd']
        timeseries = pdd['timeseries']
        if timeseries is not None:
            data = TimeSeries(timeseries)

            
            return data
        else:
            return None


    def get_timeseries_data(self, timeseries):
        """Use timeseries codes to query the FED API."""
        
        timeseries_data = requests.get(f"https://markets.newyorkfed.org/api/pd/get/{timeseries}.json").json()
        pdd = timeseries_data['pd']
        timeseries = pdd['timeseries']
        if timeseries is not None:
            data = TimeSeriesData(timeseries)
            return data
        else:
            return None
    
    def reference_rates(self, type):
        """Returns all unsecured central bank rates globally.
        
        Arguments:
        >>> rate_type: secured or unsecured
        """
        r = session.get(f"https://markets.newyorkfed.org/api/rates/{type}/all/latest.json").json()
        refrates = r['refRates']

        if refrates is not None:
            data = SecuredReferenceRates(refrates)
            return data

        

    def rates_search(self, start_date:str=None, end_date:str=None):
        """Search reference rates between a given time range."""
        if start_date == None:
            start_date = self.thirty_days_ago
        if end_date == None:
            end_date = self.today
        r = session.get(self.base_url + f"rates/all/search.json?startDate={start_date}&endDate={end_date}").json()
        refrates = r['refRates']
        if refrates is not None:
            data = SecuredReferenceRates(refrates)
            return data
   
    def repo_operations_search(self, start_date=None, end_date=today_str):
        """Search by date for repo operations out of the FED."""
        if start_date == None:
            start_date = self.thirty_days_ago
        r = session.get(f"https://markets.newyorkfed.org/api/rp/results/search.json?startDate={start_date}&endDate={end_date}&securityType=mb").json()
        repo = r['repo']
        operations = repo['operations']
        if operations is not None:
            data = RepoOperations(operations)
            return data

        

    def repo_latest(self):
        """Get the latest repo operations from the FED's discount window."""

        r = session.get("https://markets.newyorkfed.org/api/rp/all/all/results/latest.json").json()

        repo = r['repo']
        operations = repo['operations']
        if operations is not None:
            data = RepoOperations(operations)

            return data
  

    def repo_propositions(self):
        """Check all repo & reverse repo operations out of the FED."""
        propositions = session.get("https://markets.newyorkfed.org/api/rp/reverserepo/propositions/search.json").json()

        repo = propositions['repo']
        operations = repo['operations']
        data = []
        for operation in operations:
            operation_id = operation['operationId']
            operation_date = operation['operationDate']
            operation_type = operation['operationType']
            note = operation['note']
            total_amt_accepted = operation['totalAmtAccepted']
            
            data.append({
                'Operation ID': operation_id,
                'Operation Date': operation_date,
                'Operation Type': operation_type,
                'Note': note,
                'Total Amount Accepted': total_amt_accepted
            })

        df = pd.DataFrame(data)
        return df


    def securities_lending_search(self, start_date=None, end_date=today_str):
        """Search securities lending operations out of the FED."""
        if start_date == None:
            start_date = self.thirty_days_ago
        sec_lending = session.get(f"https://markets.newyorkfed.org/api/seclending/all/results/summary/search.json?startDate={start_date}&endDate={end_date}").json()

        seclending = sec_lending.get('seclending')
        operations = seclending['operations']
        if operations is not None:
            data = SecuritiesLending(operations)
            return data





    def all_agency_mortgage_backed_securities(self):
        """Returns Agency Mortgage Backed Securities from the New York Fed API
        
        PARAMS:

        >>> operation:

            'all'
            'purchases'
            'sales'
            'roll'
            'swap'
        
        >>> status:


            'announcements'
            'results'
        
            
        >>> include:

            'summary'
            'details'

        >>> format:

            'json'
            'csv'
            'xml'
            'xlsx'
        
        """
        url = f"https://markets.newyorkfed.org/beta/api/ambs/all/results/details/search.json?startDate={self.thirty_days_ago}&endDate={today_str}"
        print(url)
        r = requests.get(url).json()
        ambs = r['ambs'] if 'ambs' in r else None

        all_data_dicts = []
        
        if ambs is None:
            return all_data_dicts
        
        auctions = ambs.get('auctions', [])
        
        for i in auctions:
            details = i.get('details', [])
            
            for detail in details:
                data_dict = {
                    'auction_status': i.get("auctionStatus"),
                    'operation_id': i.get('operationId'),
                    'operation_date': i.get('operationDate'),
                    'operation_type': i.get('operationType'),
                    'operation_direction': i.get('operationDirection'),
                    'method': i.get('method'),
                    'release_time': i.get('releaseTime'),
                    'close_time': i.get('closeTime'),
                    'class_type': i.get('classType'),
                    'total_submitted_orig_face': i.get('totalSubmittedOrigFace'),
                    'total_accepted_orig_face': i.get('totalAcceptedOrigFace'),
                    'total_submitted_curr_face': i.get('totalSubmittedCurrFace'),
                    'total_accepted_curr_face': i.get('totalAcceptedCurrFace'),
                    'total_submitted_par': i.get('totalAmtSubmittedPar'),
                    'total_accepted_par': i.get('totalAmtAcceptedPar'),
                    'settlement_date': i.get('settlementDate'),
                    'last_updated': i.get('lastUpdated'),
                    'note': i.get('note'),
                    'inclusion_flag': detail.get('inclusionExclusionFlag'),
                    'security_description': detail.get('securityDescription'),
                    'amt_accepted_par': detail.get('amtAcceptedPar')
                }
                all_data_dicts.append(data_dict)
        df = pd.DataFrame(all_data_dicts)
        return df



    def securities_lending_operations(self):
        url="https://markets.newyorkfed.org/api/seclending/all/results/summary/lastTwoWeeks.json"
        r = requests.get(url).json()

        seclending = r['seclending'] if 'seclending' in r else None
        if seclending is not None:
            operations = seclending['operations'] if 'operations' in seclending else None
            if operations is not None:
                df = pd.DataFrame(operations)

                return df

    def treasury_holdings(self):
        url = f"https://markets.newyorkfed.org/api/tsy/all/results/summary/last/10.json"
        r = requests.get(url).json()
        treasury = r['treasury']
        auctions = treasury['auctions'] if 'auctions' in treasury else None
        df = pd.DataFrame(auctions)
        return df
    def data_act_compliance(self):
        base_url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"
        url=base_url+f"/v2/debt/tror/data_act_compliance?filter=record_date:gte:{self.thirty_days_ago},record_date:lte:{today_str}&sort=-record_date,agency_nm,agency_bureau_indicator,bureau_nm"
        r = requests.get(url).json()
        data = r['data']
        df = pd.DataFrame(data)

        return df


    def soma_holdings(self):
        url = f"https://markets.newyorkfed.org/api/soma/summary.json"
        r = requests.get(url).json()
        soma = r['soma']
        summary = soma['summary'] if 'summary' in soma else None

        df = pd.DataFrame(summary)
        return df        

    def market_share(self):
        url="https://markets.newyorkfed.org/api/marketshare/qtrly/latest.json"
        r = requests.get(url).text


        securityType = re.compile(r'"securityType": "(.*?)"')
        security  = re.compile(r'"security": "(.*?)"')
        security_matches = security.findall(r)
        securityType_matches = securityType.findall(r)

        percentFirstQuintRange = re.compile(r'"percentFirstQuintRange": "(.*?)"')
        percentFirstQuintRange_matches = percentFirstQuintRange.findall(r)
        percentFirstQuintMktShare = re.compile(r'"percentFirstQuintMktShare": "(\d+\.\d+)"')
        percentFirstQuintMktShare_matches = percentFirstQuintMktShare.findall(r)


        percentSecondQuintRange = re.compile(r'"percentSecondQuintRange": "(.*?)"')
        percentSecondQuintRange_matches = percentSecondQuintRange.findall(r)
        percentSecondQuintMktShare= re.compile(r'"percentSecondQuintMktShare": "(\d+\.\d+)"')
        percentSecondQuintMktShare_matches = percentSecondQuintMktShare.findall(r)

        percentThirdQuintRange = re.compile(r'"percentThirdQuintRange": "(.*?)"')
        percentThirdQuintRange_matches = percentThirdQuintRange.findall(r)
        percentThirdQuintMktShare = re.compile(r'"percentThirdQuintMktShare": "(\d+\.\d+)"')
        percentThirdQuintMktShare_matches = percentThirdQuintMktShare.findall(r)


        percentFourthQuintRange  = re.compile(r'"percentFourthQuintRange": "(.*?)"')
        percentFourthQuintRange_matches = percentFourthQuintRange.findall(r)
        percentFourthQuintMktShare= re.compile(r'"percentFourthQuintMktShare": "(\d+\.\d+)"')
        percentFourthQuintMktShare_matches = percentFourthQuintMktShare.findall(r)

        percentFifthQuintRange =  re.compile(r'"percentFifthQuintRange": "(.*?)"')
        percentFifthQuintRange_matches = percentFifthQuintRange.findall(r)
        percentFifthQuintMktShare = re.compile(r'"percentFifthQuintMktShare": "(\d+\.\d+)"')
        percentFifthQuintMktShare_matches = percentFifthQuintMktShare.findall(r)



        dailyAvgVolInMillions = re.compile(r'"dailyAvgVolInMillions": (\d+\.\d+)')
        dailyAvgVolInMillions_matches = dailyAvgVolInMillions.findall(r)

        print(percentFirstQuintRange_matches)
        print(percentFirstQuintMktShare_matches)

        print(percentSecondQuintRange_matches)
        print(percentSecondQuintMktShare_matches)

        print(percentThirdQuintRange_matches)
        print(percentThirdQuintMktShare_matches)

        print(percentFourthQuintRange_matches)
        print(percentFourthQuintMktShare_matches)

        print(percentFifthQuintRange_matches)
        print(percentFifthQuintMktShare_matches)


        print(dailyAvgVolInMillions_matches)

        print(security_matches)
        print(securityType_matches)

        # Assuming all lists are of the same length

        # Create a list of dictionaries
        data_dicts = []
        print("Length of percentFirstQuintRange_matches:", len(percentFirstQuintRange_matches))
        print("Length of percentFirstQuintMktShare_matches:", len(percentFirstQuintMktShare_matches))
        print("Length of percentSecondQuintRange_matches:", len(percentSecondQuintRange_matches))
        print("Length of percentSecondQuintMktShare_matches:", len(percentSecondQuintMktShare_matches))
        print("Length of percentThirdQuintRange_matches:", len(percentThirdQuintRange_matches))
        print("Length of percentThirdQuintMktShare_matches:", len(percentThirdQuintMktShare_matches))
        # Assuming all lists are of the same length
        min_length = min(
            len(percentFirstQuintRange_matches),
            len(percentFirstQuintMktShare_matches),
            len(percentSecondQuintRange_matches),
            len(percentSecondQuintMktShare_matches),
            len(percentThirdQuintRange_matches),
            len(percentThirdQuintMktShare_matches),
            len(percentFourthQuintRange_matches),
            len(percentFourthQuintMktShare_matches),
            len(percentFifthQuintRange_matches),
            len(percentFifthQuintMktShare_matches),
            len(security_matches),
            len(securityType_matches))
        for i in range(min_length):
            data_dict = {
                'percentFirstQuintRange': percentFirstQuintRange_matches[i],
                'percentFirstQuintMktShare': percentFirstQuintMktShare_matches[i],
                'percentSecondQuintRange': percentSecondQuintRange_matches[i],
                'percentSecondQuintMktShare': percentSecondQuintMktShare_matches[i],
                'percentThirdQuintRange': percentThirdQuintRange_matches[i],
                'percentThirdQuintMktShare': percentThirdQuintMktShare_matches[i],
                'percentFourthQuintRange': percentFourthQuintRange_matches[i],
                'percentFourthQuintMktShare': percentFourthQuintMktShare_matches[i],
                'percentFifthQuintRange': percentFifthQuintRange_matches[i],  # Changed this line
                'percentFifthQuintMktShare': percentFifthQuintMktShare_matches[i],
                'dailyAvgVolInMillions': dailyAvgVolInMillions_matches[i],
                'security': security_matches[i],  # Changed this line
                'securityType': securityType_matches[i]  # Changed this line
            }
            data_dicts.append(data_dict)

        df = pd.DataFrame(data_dicts)
        return df


    def central_bank_liquidity_swaps(self):
        """Returns operations out of the fed for central bank liquidity swaps
        
        ARGS:

        >>> count:
                    the last n records
        
        default: 10
        
        """

        url = f"https://markets.newyorkfed.org/api/fxs/usdollar/last/100.json"

        r = requests.get(url).json()
        fxswaps = r["fxSwaps"]
        ops = fxswaps["operations"] if "operations" in fxswaps else None
        if ops is not None:
            return pd.DataFrame(ops)
    

    def primary_dealer_timeseries():


        metadata_url = "https://markets.newyorkfed.org/api/pd/list/timeseries.csv"
        metadata_response = requests.get(metadata_url)
        metadata_csv = StringIO(metadata_response.text)
        metadata_df = pd.read_csv(metadata_csv)

        # Download timeseries data in CSV format and load it into a DataFrame
        timeseries_url = "https://markets.newyorkfed.org/api/pd/get/all/timeseries.csv"
        timeseries_response = requests.get(timeseries_url)
        timeseries_csv = StringIO(timeseries_response.text)
        timeseries_df = pd.read_csv(timeseries_csv)

        # Merge the two DataFrames on the common column (assuming it's called 'keyid' in both DataFrames)
        #final_df = pd.merge(timeseries_df, metadata_df, on='keyid', how='left')


        # Merge the two DataFrames on the common columns
        final_df = pd.merge(timeseries_df, metadata_df, left_on='Time Series', right_on='Key Id', how='left')

        # Display the first few rows of the merged DataFrame
        print(final_df.head())

        return final_df



    def reverse_repo(self):
        url = f"https://markets.newyorkfed.org/api/rp/all/all/results/last/10.json"
        r = requests.get(url)
        r.raise_for_status()  # This will raise an exception if the request failed
        repo_data = r.json().get('repo', {})
        operations = repo_data.get('operations', [])

        all_operations = []
        for operation in operations:
            # Common operation data
            op_data_common = {
                'operationId': operation.get('operationId'),
                'auctionStatus': operation.get('auctionStatus'),
                'operationDate': operation.get('operationDate'),
                'settlementDate': operation.get('settlementDate'),
                'maturityDate': operation.get('maturityDate'),
                'operationType': operation.get('operationType'),
                'operationMethod': operation.get('operationMethod'),
                'settlementType': operation.get('settlementType'),
                'termCalenderDays': operation.get('termCalenderDays'),
                'term': operation.get('term'),
                'releaseTime': operation.get('releaseTime'),
                'closeTime': operation.get('closeTime'),
                'note': operation.get('note'),
                'lastUpdated': operation.get('lastUpdated'),
                'participatingCpty': operation.get('participatingCpty'),
                'acceptedCpty': operation.get('acceptedCpty'),
                'totalAmtSubmitted': operation.get('totalAmtSubmitted'),
                'totalAmtAccepted': operation.get('totalAmtAccepted'),
            }

            details = operation.get('details', [])
            for detail in details:
                # Combine common data with detail data for each entry in details
                op_data = {**op_data_common, **{
                    'securityType': detail.get('securityType'),
                    'amtSubmitted': detail.get('amtSubmitted'),
                    'amtAccepted': detail.get('amtAccepted'),
                    'minimumBidRate': detail.get('minimumBidRate'),
                    'percentHighRate': detail.get('percentHighRate'),
                    'percentLowRate': detail.get('percentLowRate'),
                    'percentStopOutRate': detail.get('percentStopOutRate'),
                    'percentWeightedAverageRate': detail.get('percentWeightedAverageRate')
                }}

                all_operations.append(op_data)
        df = pd.DataFrame(all_operations)
        return df, RepoOperations(all_operations)


class NewYorkFedAPI:
    def __init__(self, db: PolygonOptions | None = None):
        self.base_url = "https://markets.newyorkfed.org"
        self.api_base = f"{self.base_url}/api"
        self.db = db or PolygonOptions()

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if path.startswith("/"):
            return f"{self.base_url}{path}"
        return f"{self.api_base}/{path}"

    async def fetch_json(self, path: str, params: dict | None = None) -> dict:
        url = self._build_url(path)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                text = await response.text()
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    sanitized = re.sub(r":\s*\*", ": null", text)
                    return json.loads(sanitized)

    async def _upsert(self, df: pd.DataFrame, table_name: str, unique_columns: list[str]) -> int:
        if df.empty:
            return 0
        await self.db.batch_upsert_dataframe(
            df,
            table_name=table_name,
            unique_columns=unique_columns,
        )
        return len(df)

    async def ambs_last(
        self,
        operation: str = "all",
        include: str = "details",
        number: int = 10,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/ambs/{operation}/results/{include}/last/{number}.json"
        data = await self.fetch_json(path)
        auctions = (data.get("ambs") or {}).get("auctions") or []
        auctions_model = nyfed_models.AmbsAuctions(auctions)
        details_model = nyfed_models.AmbsAuctionDetails(auctions)

        if insert:
            await self.db.connect()
            await self._upsert(
                auctions_model.as_dataframe,
                table_name="nyfed_ambs_auctions",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_ambs_details",
                unique_columns=["operation_id", "security_description", "inclusion_flag"],
            )

        if as_dataframe:
            return auctions_model.as_dataframe, details_model.as_dataframe
        return auctions_model, details_model

    async def ambs_latest(
        self,
        operation: str = "all",
        status: str = "results",
        include: str = "details",
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/ambs/{operation}/{status}/{include}/latest.json"
        data = await self.fetch_json(path)
        auctions = (data.get("ambs") or {}).get("auctions") or []
        auctions_model = nyfed_models.AmbsAuctions(auctions)
        details_model = nyfed_models.AmbsAuctionDetails(auctions)

        if insert:
            await self.db.connect()
            await self._upsert(
                auctions_model.as_dataframe,
                table_name="nyfed_ambs_auctions",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_ambs_details",
                unique_columns=["operation_id", "security_description", "inclusion_flag"],
            )

        if as_dataframe:
            return auctions_model.as_dataframe, details_model.as_dataframe
        return auctions_model, details_model

    async def ambs_last_two_weeks(
        self,
        operation: str = "all",
        include: str = "details",
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/ambs/{operation}/results/{include}/lastTwoWeeks.json"
        data = await self.fetch_json(path)
        auctions = (data.get("ambs") or {}).get("auctions") or []
        auctions_model = nyfed_models.AmbsAuctions(auctions)
        details_model = nyfed_models.AmbsAuctionDetails(auctions)

        if insert:
            await self.db.connect()
            await self._upsert(
                auctions_model.as_dataframe,
                table_name="nyfed_ambs_auctions",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_ambs_details",
                unique_columns=["operation_id", "security_description", "inclusion_flag"],
            )

        if as_dataframe:
            return auctions_model.as_dataframe, details_model.as_dataframe
        return auctions_model, details_model

    async def ambs_search(
        self,
        operation: str = "all",
        include: str = "details",
        start_date: str | None = None,
        end_date: str | None = None,
        securities: str | list[str] | None = None,
        cusip: str | list[str] | None = None,
        description: str | list[str] | None = None,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        params: dict[str, str] = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if securities:
            params["securities"] = (
                ",".join(securities) if isinstance(securities, (list, tuple, set)) else str(securities)
            )
        if cusip:
            params["cusip"] = ",".join(cusip) if isinstance(cusip, (list, tuple, set)) else str(cusip)
        if description:
            params["desc"] = (
                ",".join(description) if isinstance(description, (list, tuple, set)) else str(description)
            )

        path = f"/api/ambs/{operation}/results/{include}/search.json"
        data = await self.fetch_json(path, params=params)
        auctions = (data.get("ambs") or {}).get("auctions") or []
        auctions_model = nyfed_models.AmbsAuctions(auctions)
        details_model = nyfed_models.AmbsAuctionDetails(auctions)

        if insert:
            await self.db.connect()
            await self._upsert(
                auctions_model.as_dataframe,
                table_name="nyfed_ambs_auctions",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_ambs_details",
                unique_columns=["operation_id", "security_description", "inclusion_flag"],
            )

        if as_dataframe:
            return auctions_model.as_dataframe, details_model.as_dataframe
        return auctions_model, details_model

    async def tsy_last(
        self,
        operation: str = "all",
        include: str = "details",
        number: int = 10,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/tsy/{operation}/results/{include}/last/{number}.json"
        data = await self.fetch_json(path)
        auctions = (data.get("treasury") or {}).get("auctions") or []
        auctions_model = nyfed_models.TsyOperations(auctions)
        details_model = nyfed_models.TsyOperationDetails(auctions)

        if insert:
            await self.db.connect()
            await self._upsert(
                auctions_model.as_dataframe,
                table_name="nyfed_tsy_auctions",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_tsy_details",
                unique_columns=["operation_id", "cusip", "inclusion_indicator"],
            )

        if as_dataframe:
            return auctions_model.as_dataframe, details_model.as_dataframe
        return auctions_model, details_model

    async def tsy_latest(
        self,
        operation: str = "all",
        status: str = "results",
        include: str = "details",
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/tsy/{operation}/{status}/{include}/latest.json"
        data = await self.fetch_json(path)
        auctions = (data.get("treasury") or {}).get("auctions") or []
        auctions_model = nyfed_models.TsyOperations(auctions)
        details_model = nyfed_models.TsyOperationDetails(auctions)

        if insert:
            await self.db.connect()
            await self._upsert(
                auctions_model.as_dataframe,
                table_name="nyfed_tsy_auctions",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_tsy_details",
                unique_columns=["operation_id", "cusip", "inclusion_indicator"],
            )

        if as_dataframe:
            return auctions_model.as_dataframe, details_model.as_dataframe
        return auctions_model, details_model

    async def tsy_last_two_weeks(
        self,
        operation: str = "all",
        include: str = "details",
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/tsy/{operation}/results/{include}/lastTwoWeeks.json"
        data = await self.fetch_json(path)
        auctions = (data.get("treasury") or {}).get("auctions") or []
        auctions_model = nyfed_models.TsyOperations(auctions)
        details_model = nyfed_models.TsyOperationDetails(auctions)

        if insert:
            await self.db.connect()
            await self._upsert(
                auctions_model.as_dataframe,
                table_name="nyfed_tsy_auctions",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_tsy_details",
                unique_columns=["operation_id", "cusip", "inclusion_indicator"],
            )

        if as_dataframe:
            return auctions_model.as_dataframe, details_model.as_dataframe
        return auctions_model, details_model

    async def tsy_search(
        self,
        operation: str = "all",
        include: str = "details",
        start_date: str | None = None,
        end_date: str | None = None,
        security_type: str | list[str] | None = None,
        cusip: str | list[str] | None = None,
        description: str | list[str] | None = None,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        params: dict[str, str] = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if security_type:
            params["securityType"] = (
                ",".join(security_type)
                if isinstance(security_type, (list, tuple, set))
                else str(security_type)
            )
        if cusip:
            params["cusip"] = ",".join(cusip) if isinstance(cusip, (list, tuple, set)) else str(cusip)
        if description:
            params["desc"] = (
                ",".join(description) if isinstance(description, (list, tuple, set)) else str(description)
            )

        path = f"/api/tsy/{operation}/results/{include}/search.json"
        data = await self.fetch_json(path, params=params)
        auctions = (data.get("treasury") or {}).get("auctions") or []
        auctions_model = nyfed_models.TsyOperations(auctions)
        details_model = nyfed_models.TsyOperationDetails(auctions)

        if insert:
            await self.db.connect()
            await self._upsert(
                auctions_model.as_dataframe,
                table_name="nyfed_tsy_auctions",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_tsy_details",
                unique_columns=["operation_id", "cusip", "inclusion_indicator"],
            )

        if as_dataframe:
            return auctions_model.as_dataframe, details_model.as_dataframe
        return auctions_model, details_model

    async def fxs_latest(
        self,
        operation_type: str = "all",
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/fxs/{operation_type}/latest.json"
        data = await self.fetch_json(path)
        operations = (data.get("fxSwaps") or {}).get("operations") or []
        model = nyfed_models.FxSwapsOperations(operations)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_fx_swaps",
                unique_columns=["operation_type", "counterparty", "trade_date", "maturity_date"],
            )

        return model.as_dataframe if as_dataframe else model

    async def fxs_last(
        self,
        operation_type: str = "usdollar",
        number: int = 10,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/fxs/{operation_type}/last/{number}.json"
        data = await self.fetch_json(path)
        operations = (data.get("fxSwaps") or {}).get("operations") or []
        model = nyfed_models.FxSwapsOperations(operations)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_fx_swaps",
                unique_columns=["operation_type", "counterparty", "trade_date", "maturity_date"],
            )

        return model.as_dataframe if as_dataframe else model

    async def fxs_search(
        self,
        operation_type: str = "all",
        start_date: str | None = None,
        end_date: str | None = None,
        date_type: str | None = None,
        counterparties: str | list[str] | None = None,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        params: dict[str, str] = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if date_type:
            params["dateType"] = date_type
        if counterparties:
            params["counterparties"] = (
                ",".join(counterparties)
                if isinstance(counterparties, (list, tuple, set))
                else str(counterparties)
            )

        path = f"/api/fxs/{operation_type}/search.json"
        data = await self.fetch_json(path, params=params)
        operations = (data.get("fxSwaps") or {}).get("operations") or []
        model = nyfed_models.FxSwapsOperations(operations)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_fx_swaps",
                unique_columns=["operation_type", "counterparty", "trade_date", "maturity_date"],
            )

        return model.as_dataframe if as_dataframe else model

    async def fxs_counterparties(self, insert: bool = False, as_dataframe: bool = True):
        path = "/api/fxs/list/counterparties.json"
        data = await self.fetch_json(path)
        counterparties = (data.get("fxSwaps") or {}).get("counterparties") or []
        model = nyfed_models.FxSwapCounterparties(counterparties)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_fx_counterparties",
                unique_columns=["counterparty"],
            )

        return model.as_dataframe if as_dataframe else model

    async def reference_rates_latest(
        self,
        scope: str = "all",
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        if scope == "secured":
            path = "/api/rates/secured/all/latest.json"
        elif scope == "unsecured":
            path = "/api/rates/unsecured/all/latest.json"
        else:
            path = "/api/rates/all/latest.json"

        data = await self.fetch_json(path)
        rates = data.get("refRates") or []
        model = nyfed_models.ReferenceRates(rates)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_reference_rates",
                unique_columns=["effective_date", "rate_type"],
            )

        return model.as_dataframe if as_dataframe else model

    async def reference_rates_search(
        self,
        scope: str = "all",
        ratetype: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        rate_type: str | None = None,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        if scope == "secured":
            ratetype = ratetype or "sofr"
            path = f"/api/rates/secured/{ratetype}/search.json"
        elif scope == "unsecured":
            ratetype = ratetype or "effr"
            path = f"/api/rates/unsecured/{ratetype}/search.json"
        else:
            path = "/api/rates/all/search.json"

        params: dict[str, str] = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if rate_type:
            params["type"] = rate_type

        data = await self.fetch_json(path, params=params)
        rates = data.get("refRates") or []
        model = nyfed_models.ReferenceRates(rates)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_reference_rates",
                unique_columns=["effective_date", "rate_type"],
            )

        return model.as_dataframe if as_dataframe else model

    async def reference_rates_last(
        self,
        scope: str = "secured",
        ratetype: str | None = None,
        number: int = 10,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        if scope == "unsecured":
            ratetype = ratetype or "effr"
            path = f"/api/rates/unsecured/{ratetype}/last/{number}.json"
        else:
            ratetype = ratetype or "sofr"
            path = f"/api/rates/secured/{ratetype}/last/{number}.json"

        data = await self.fetch_json(path)
        rates = data.get("refRates") or []
        model = nyfed_models.ReferenceRates(rates)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_reference_rates",
                unique_columns=["effective_date", "rate_type"],
            )

        return model.as_dataframe if as_dataframe else model

    async def repo_latest(
        self,
        operation_type: str = "all",
        method: str = "all",
        status: str = "results",
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/rp/{operation_type}/{method}/{status}/latest.json"
        data = await self.fetch_json(path)
        operations = (data.get("repo") or {}).get("operations") or []

        ops_model = nyfed_models.RepoOperations(operations)
        details_model = nyfed_models.RepoTrancheDetails(operations)
        settlement_model = nyfed_models.RepoSettlementAmounts(operations)
        propositions_model = nyfed_models.RepoPropositions(operations)

        if insert:
            await self.db.connect()
            await self._upsert(
                ops_model.as_dataframe,
                table_name="nyfed_repo_operations",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_repo_tranche_details",
                unique_columns=["operation_id", "security_type", "operation_method"],
            )
            await self._upsert(
                settlement_model.as_dataframe,
                table_name="nyfed_repo_settlement_amounts",
                unique_columns=["operation_id", "counterparty_type", "security_type"],
            )
            await self._upsert(
                propositions_model.as_dataframe,
                table_name="nyfed_repo_propositions",
                unique_columns=["operation_id", "counterparty_type"],
            )

        if as_dataframe:
            return (
                ops_model.as_dataframe,
                details_model.as_dataframe,
                settlement_model.as_dataframe,
                propositions_model.as_dataframe,
            )
        return ops_model, details_model, settlement_model, propositions_model

    async def repo_last(
        self,
        operation_type: str = "all",
        method: str = "all",
        number: int = 10,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/rp/{operation_type}/{method}/results/last/{number}.json"
        data = await self.fetch_json(path)
        operations = (data.get("repo") or {}).get("operations") or []

        ops_model = nyfed_models.RepoOperations(operations)
        details_model = nyfed_models.RepoTrancheDetails(operations)
        settlement_model = nyfed_models.RepoSettlementAmounts(operations)
        propositions_model = nyfed_models.RepoPropositions(operations)

        if insert:
            await self.db.connect()
            await self._upsert(
                ops_model.as_dataframe,
                table_name="nyfed_repo_operations",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_repo_tranche_details",
                unique_columns=["operation_id", "security_type", "operation_method"],
            )
            await self._upsert(
                settlement_model.as_dataframe,
                table_name="nyfed_repo_settlement_amounts",
                unique_columns=["operation_id", "counterparty_type", "security_type"],
            )
            await self._upsert(
                propositions_model.as_dataframe,
                table_name="nyfed_repo_propositions",
                unique_columns=["operation_id", "counterparty_type"],
            )

        if as_dataframe:
            return (
                ops_model.as_dataframe,
                details_model.as_dataframe,
                settlement_model.as_dataframe,
                propositions_model.as_dataframe,
            )
        return ops_model, details_model, settlement_model, propositions_model

    async def repo_last_two_weeks(
        self,
        operation_type: str = "all",
        method: str = "all",
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/rp/{operation_type}/{method}/results/lastTwoWeeks.json"
        data = await self.fetch_json(path)
        operations = (data.get("repo") or {}).get("operations") or []

        ops_model = nyfed_models.RepoOperations(operations)
        details_model = nyfed_models.RepoTrancheDetails(operations)
        settlement_model = nyfed_models.RepoSettlementAmounts(operations)
        propositions_model = nyfed_models.RepoPropositions(operations)

        if insert:
            await self.db.connect()
            await self._upsert(
                ops_model.as_dataframe,
                table_name="nyfed_repo_operations",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_repo_tranche_details",
                unique_columns=["operation_id", "security_type", "operation_method"],
            )
            await self._upsert(
                settlement_model.as_dataframe,
                table_name="nyfed_repo_settlement_amounts",
                unique_columns=["operation_id", "counterparty_type", "security_type"],
            )
            await self._upsert(
                propositions_model.as_dataframe,
                table_name="nyfed_repo_propositions",
                unique_columns=["operation_id", "counterparty_type"],
            )

        if as_dataframe:
            return (
                ops_model.as_dataframe,
                details_model.as_dataframe,
                settlement_model.as_dataframe,
                propositions_model.as_dataframe,
            )
        return ops_model, details_model, settlement_model, propositions_model

    async def repo_search(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        operation_types: str | list[str] | None = None,
        method: str | None = None,
        security_type: str | None = None,
        term: str | None = None,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        params: dict[str, str] = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if operation_types:
            params["operationTypes"] = (
                ",".join(operation_types)
                if isinstance(operation_types, (list, tuple, set))
                else str(operation_types)
            )
        if method:
            params["method"] = method
        if security_type:
            params["securityType"] = security_type
        if term:
            params["term"] = term

        path = "/api/rp/results/search.json"
        data = await self.fetch_json(path, params=params)
        operations = (data.get("repo") or {}).get("operations") or []

        ops_model = nyfed_models.RepoOperations(operations)
        details_model = nyfed_models.RepoTrancheDetails(operations)
        settlement_model = nyfed_models.RepoSettlementAmounts(operations)
        propositions_model = nyfed_models.RepoPropositions(operations)

        if insert:
            await self.db.connect()
            await self._upsert(
                ops_model.as_dataframe,
                table_name="nyfed_repo_operations",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_repo_tranche_details",
                unique_columns=["operation_id", "security_type", "operation_method"],
            )
            await self._upsert(
                settlement_model.as_dataframe,
                table_name="nyfed_repo_settlement_amounts",
                unique_columns=["operation_id", "counterparty_type", "security_type"],
            )
            await self._upsert(
                propositions_model.as_dataframe,
                table_name="nyfed_repo_propositions",
                unique_columns=["operation_id", "counterparty_type"],
            )

        if as_dataframe:
            return (
                ops_model.as_dataframe,
                details_model.as_dataframe,
                settlement_model.as_dataframe,
                propositions_model.as_dataframe,
            )
        return ops_model, details_model, settlement_model, propositions_model

    async def reverse_repo_propositions(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        path = "/api/rp/reverserepo/propositions/search.json"
        data = await self.fetch_json(path, params=params)
        operations = (data.get("repo") or {}).get("operations") or []

        ops_model = nyfed_models.RepoPostOperations(operations)
        propositions_model = nyfed_models.RepoPropositions(operations)

        if insert:
            await self.db.connect()
            await self._upsert(
                ops_model.as_dataframe,
                table_name="nyfed_repo_post_operations",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                propositions_model.as_dataframe,
                table_name="nyfed_repo_propositions",
                unique_columns=["operation_id", "counterparty_type"],
            )

        if as_dataframe:
            return ops_model.as_dataframe, propositions_model.as_dataframe
        return ops_model, propositions_model

    async def seclending_latest(
        self,
        operation: str = "all",
        include: str = "details",
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/seclending/{operation}/results/{include}/latest.json"
        data = await self.fetch_json(path)
        operations = (data.get("seclending") or {}).get("operations") or []

        ops_model = nyfed_models.SecuritiesLendingOperations(operations)
        details_model = nyfed_models.SecuritiesLendingDetails(operations)

        if insert:
            await self.db.connect()
            await self._upsert(
                ops_model.as_dataframe,
                table_name="nyfed_seclending_operations",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_seclending_details",
                unique_columns=["operation_id", "cusip"],
            )

        if as_dataframe:
            return ops_model.as_dataframe, details_model.as_dataframe
        return ops_model, details_model

    async def seclending_last(
        self,
        operation: str = "all",
        include: str = "details",
        number: int = 10,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/seclending/{operation}/results/{include}/last/{number}.json"
        data = await self.fetch_json(path)
        operations = (data.get("seclending") or {}).get("operations") or []

        ops_model = nyfed_models.SecuritiesLendingOperations(operations)
        details_model = nyfed_models.SecuritiesLendingDetails(operations)

        if insert:
            await self.db.connect()
            await self._upsert(
                ops_model.as_dataframe,
                table_name="nyfed_seclending_operations",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_seclending_details",
                unique_columns=["operation_id", "cusip"],
            )

        if as_dataframe:
            return ops_model.as_dataframe, details_model.as_dataframe
        return ops_model, details_model

    async def seclending_last_two_weeks(
        self,
        operation: str = "all",
        include: str = "details",
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/seclending/{operation}/results/{include}/lastTwoWeeks.json"
        data = await self.fetch_json(path)
        operations = (data.get("seclending") or {}).get("operations") or []

        ops_model = nyfed_models.SecuritiesLendingOperations(operations)
        details_model = nyfed_models.SecuritiesLendingDetails(operations)

        if insert:
            await self.db.connect()
            await self._upsert(
                ops_model.as_dataframe,
                table_name="nyfed_seclending_operations",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_seclending_details",
                unique_columns=["operation_id", "cusip"],
            )

        if as_dataframe:
            return ops_model.as_dataframe, details_model.as_dataframe
        return ops_model, details_model

    async def seclending_search(
        self,
        operation: str = "all",
        include: str = "details",
        start_date: str | None = None,
        end_date: str | None = None,
        cusips: str | list[str] | None = None,
        descriptions: str | list[str] | None = None,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        params: dict[str, str] = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if cusips:
            params["cusips"] = ",".join(cusips) if isinstance(cusips, (list, tuple, set)) else str(cusips)
        if descriptions:
            params["descriptions"] = (
                ",".join(descriptions) if isinstance(descriptions, (list, tuple, set)) else str(descriptions)
            )

        path = f"/api/seclending/{operation}/results/{include}/search.json"
        data = await self.fetch_json(path, params=params)
        operations = (data.get("seclending") or {}).get("operations") or []

        ops_model = nyfed_models.SecuritiesLendingOperations(operations)
        details_model = nyfed_models.SecuritiesLendingDetails(operations)

        if insert:
            await self.db.connect()
            await self._upsert(
                ops_model.as_dataframe,
                table_name="nyfed_seclending_operations",
                unique_columns=["operation_id"],
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name="nyfed_seclending_details",
                unique_columns=["operation_id", "cusip"],
            )

        if as_dataframe:
            return ops_model.as_dataframe, details_model.as_dataframe
        return ops_model, details_model

    async def soma_summary(self, insert: bool = False, as_dataframe: bool = True):
        data = await self.fetch_json("/api/soma/summary.json")
        summary = (data.get("soma") or {}).get("summary") or []
        model = nyfed_models.SomaSummary(summary)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_soma_summary",
                unique_columns=["as_of_date"],
            )

        return model.as_dataframe if as_dataframe else model

    async def soma_asof_dates(self, latest: bool = False, insert: bool = False, as_dataframe: bool = True):
        path = "/api/soma/asofdates/latest.json" if latest else "/api/soma/asofdates/list.json"
        data = await self.fetch_json(path)
        soma = data.get("soma") or {}
        dates = soma.get("asOfDates") or soma.get("asofdates") or []
        model = nyfed_models.SomaAsOfDates(dates)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_soma_asof_dates",
                unique_columns=["as_of_date"],
            )

        return model.as_dataframe if as_dataframe else model

    async def soma_release_log_agency(self, insert: bool = False, as_dataframe: bool = True):
        data = await self.fetch_json("/api/soma/agency/get/release_log.json")
        dates = (data.get("soma") or {}).get("dates") or []
        model = nyfed_models.SomaReleaseDates(dates)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_soma_agency_release_dates",
                unique_columns=["release_date", "as_of_date"],
            )

        return model.as_dataframe if as_dataframe else model

    async def soma_release_log_tsy(self, insert: bool = False, as_dataframe: bool = True):
        data = await self.fetch_json("/api/soma/tsy/get/release_log.json")
        dates = (data.get("soma") or {}).get("dates") or []
        model = nyfed_models.SomaReleaseDates(dates)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_soma_tsy_release_dates",
                unique_columns=["release_date", "as_of_date"],
            )

        return model.as_dataframe if as_dataframe else model

    async def soma_agency_asof(self, date: str, insert: bool = False, as_dataframe: bool = True):
        path = f"/api/soma/agency/get/asof/{date}.json"
        data = await self.fetch_json(path)
        holdings = (data.get("soma") or {}).get("holdings") or []
        model = nyfed_models.SomaAgencyHoldings(holdings)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_soma_agency_holdings",
                unique_columns=["as_of_date", "cusip", "security_type"],
            )

        return model.as_dataframe if as_dataframe else model

    async def soma_tsy_asof(self, date: str, insert: bool = False, as_dataframe: bool = True):
        path = f"/api/soma/tsy/get/asof/{date}.json"
        data = await self.fetch_json(path)
        holdings = (data.get("soma") or {}).get("holdings") or []
        model = nyfed_models.SomaTreasuryHoldings(holdings)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_soma_tsy_holdings",
                unique_columns=["as_of_date", "cusip", "security_type"],
            )

        return model.as_dataframe if as_dataframe else model

    async def soma_agency_cusip(self, cusip: str, insert: bool = False, as_dataframe: bool = True):
        path = f"/api/soma/agency/get/cusip/{cusip}.json"
        data = await self.fetch_json(path)
        holdings = (data.get("soma") or {}).get("holdings") or []
        model = nyfed_models.SomaAgencyHoldings(holdings)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_soma_agency_holdings",
                unique_columns=["as_of_date", "cusip", "security_type"],
            )

        return model.as_dataframe if as_dataframe else model

    async def soma_agency_holding_asof(
        self,
        holding_type: str,
        date: str,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        holding = holding_type.replace(" ", "%20")
        path = f"/api/soma/agency/get/{holding}/asof/{date}.json"
        data = await self.fetch_json(path)
        holdings = (data.get("soma") or {}).get("holdings") or []
        model = nyfed_models.SomaAgencyHoldings(holdings)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_soma_agency_holdings",
                unique_columns=["as_of_date", "cusip", "security_type"],
            )

        return model.as_dataframe if as_dataframe else model

    async def soma_tsy_cusip(self, cusip: str, insert: bool = False, as_dataframe: bool = True):
        path = f"/api/soma/tsy/get/cusip/{cusip}.json"
        data = await self.fetch_json(path)
        holdings = (data.get("soma") or {}).get("holdings") or []
        model = nyfed_models.SomaTreasuryHoldings(holdings)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_soma_tsy_holdings",
                unique_columns=["as_of_date", "cusip", "security_type"],
            )

        return model.as_dataframe if as_dataframe else model

    async def soma_tsy_holding_asof(
        self,
        holding_type: str,
        date: str,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        holding = holding_type.replace(" ", "%20")
        path = f"/api/soma/tsy/get/{holding}/asof/{date}.json"
        data = await self.fetch_json(path)
        holdings = (data.get("soma") or {}).get("holdings") or []
        model = nyfed_models.SomaTreasuryHoldings(holdings)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_soma_tsy_holdings",
                unique_columns=["as_of_date", "cusip", "security_type"],
            )

        return model.as_dataframe if as_dataframe else model

    async def soma_tsy_monthly(
        self,
        limit: int | None = None,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        data = await self.fetch_json("/api/soma/tsy/get/monthly.json")
        holdings = (data.get("soma") or {}).get("holdings") or []
        if limit is not None:
            holdings = holdings[:limit]
        model = nyfed_models.SomaTreasuryHoldings(holdings)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_soma_tsy_holdings",
                unique_columns=["as_of_date", "cusip", "security_type"],
            )

        return model.as_dataframe if as_dataframe else model

    async def soma_wam_agency_debts(self, date: str, insert: bool = False, as_dataframe: bool = True):
        path = f"/api/soma/agency/wam/agency%20debts/asof/{date}.json"
        data = await self.fetch_json(path)
        soma = data.get("soma") or {}
        model = nyfed_models.SomaWam(soma)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_soma_wam",
                unique_columns=["as_of_date"],
            )

        return model.as_dataframe if as_dataframe else model

    async def soma_wam_tsy(
        self,
        holding_type: str,
        date: str,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/soma/tsy/wam/{holding_type}/asof/{date}.json"
        data = await self.fetch_json(path)
        soma = data.get("soma") or {}
        model = nyfed_models.SomaWam(soma)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_soma_wam",
                unique_columns=["as_of_date"],
            )

        return model.as_dataframe if as_dataframe else model

    async def pd_list_timeseries(self, insert: bool = False, as_dataframe: bool = True):
        data = await self.fetch_json("/api/pd/list/timeseries.json")
        timeseries = (data.get("pd") or {}).get("timeseries") or []
        model = nyfed_models.PrimaryDealerTimeSeries(timeseries)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_pd_timeseries",
                unique_columns=["key_id"],
            )

        return model.as_dataframe if as_dataframe else model

    async def pd_list_asof_dates(self, insert: bool = False, as_dataframe: bool = True):
        data = await self.fetch_json("/api/pd/list/asof.json")
        dates = (data.get("pd") or {}).get("asofdates") or []
        model = nyfed_models.PrimaryDealerAsOfDates(dates)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_pd_asof_dates",
                unique_columns=["as_of"],
            )

        return model.as_dataframe if as_dataframe else model

    async def pd_list_seriesbreaks(self, insert: bool = False, as_dataframe: bool = True):
        data = await self.fetch_json("/api/pd/list/seriesbreaks.json")
        seriesbreaks = (data.get("pd") or {}).get("seriesbreaks") or []
        model = nyfed_models.PrimaryDealerSeriesBreaks(seriesbreaks)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_pd_series_breaks",
                unique_columns=["series_break"],
            )

        return model.as_dataframe if as_dataframe else model

    async def pd_timeseries_data(
        self,
        timeseries: str,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/pd/get/{timeseries}.json"
        data = await self.fetch_json(path)
        series = (data.get("pd") or {}).get("timeseries") or []
        model = nyfed_models.PrimaryDealerTimeSeriesSet(series)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_pd_timeseries_data",
                unique_columns=["as_of_date", "key_id"],
            )

        return model.as_dataframe if as_dataframe else model

    async def pd_timeseries_asof(
        self,
        date: str,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/pd/get/asof/{date}.json"
        data = await self.fetch_json(path)
        series = (data.get("pd") or {}).get("timeseries") or []
        model = nyfed_models.PrimaryDealerTimeSeriesSet(series)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_pd_timeseries_data",
                unique_columns=["as_of_date", "key_id"],
            )

        return model.as_dataframe if as_dataframe else model

    async def pd_timeseries_by_seriesbreak(
        self,
        seriesbreak: str,
        timeseries: str,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/pd/get/{seriesbreak}/timeseries/{timeseries}.json"
        data = await self.fetch_json(path)
        series = (data.get("pd") or {}).get("timeseries") or []
        model = nyfed_models.PrimaryDealerTimeSeriesSet(series)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_pd_timeseries_data",
                unique_columns=["as_of_date", "key_id"],
            )

        return model.as_dataframe if as_dataframe else model

    async def pd_latest_seriesbreak(
        self,
        seriesbreak: str,
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/pd/latest/{seriesbreak}.json"
        data = await self.fetch_json(path)
        series = (data.get("pd") or {}).get("timeseries") or []
        model = nyfed_models.PrimaryDealerTimeSeriesSet(series)

        if insert:
            await self.db.connect()
            await self._upsert(
                model.as_dataframe,
                table_name="nyfed_pd_timeseries_data",
                unique_columns=["as_of_date", "key_id"],
            )

        return model.as_dataframe if as_dataframe else model

    async def pd_all_timeseries_csv(
        self,
        insert: bool = False,
        as_dataframe: bool = True,
        chunk_size: int = 5000,
        max_rows: int | None = None,
    ):
        url = self._build_url("/api/pd/get/all/timeseries.csv")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                text = await response.text()

        rows: list[dict[str, str]] = []
        frames: list[pd.DataFrame] = []
        models: list[nyfed_models.PrimaryDealerTimeSeriesSet] = []
        total = 0

        if insert:
            await self.db.connect()

        reader = csv.DictReader(StringIO(text))
        for row in reader:
            rows.append(
                {
                    "asofdate": row.get("As Of Date"),
                    "keyid": row.get("Time Series"),
                    "value": row.get("Value (millions)"),
                }
            )
            total += 1
            reached_limit = max_rows is not None and total >= max_rows
            if len(rows) >= chunk_size or reached_limit:
                model = nyfed_models.PrimaryDealerTimeSeriesSet(rows)
                if insert:
                    await self._upsert(
                        model.as_dataframe,
                        table_name="nyfed_pd_timeseries_data",
                        unique_columns=["as_of_date", "key_id"],
                    )
                if as_dataframe:
                    frames.append(model.as_dataframe)
                else:
                    models.append(model)
                rows = []
                if reached_limit:
                    break

        if rows:
            model = nyfed_models.PrimaryDealerTimeSeriesSet(rows)
            if insert:
                await self._upsert(
                    model.as_dataframe,
                    table_name="nyfed_pd_timeseries_data",
                    unique_columns=["as_of_date", "key_id"],
                )
            if as_dataframe:
                frames.append(model.as_dataframe)
            else:
                models.append(model)

        if as_dataframe:
            return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        return models

    async def pd_marketshare_latest(
        self,
        period: str = "quarterly",
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        if period == "ytd":
            path = "/api/marketshare/ytd/latest.json"
        else:
            path = "/api/marketshare/qtrly/latest.json"
        data = await self.fetch_json(path)
        pd_block = data.get("pd") or {}
        market_share = pd_block.get("marketShare") or pd_block.get("marketshare") or {}
        record = market_share.get("ytd" if period == "ytd" else "quarterly") or {}

        summary_model = nyfed_models.PrimaryDealerMarketShareSummary(record)
        dealers_model = nyfed_models.PrimaryDealerMarketShareDealers(record)

        if insert:
            await self.db.connect()
            summary_df = summary_model.as_dataframe.copy()
            dealers_df = dealers_model.as_dataframe.copy()
            summary_df["period"] = period
            dealers_df["period"] = period
            await self._upsert(
                summary_df,
                table_name="nyfed_pd_marketshare_summary",
                unique_columns=["release_date", "title", "period"],
            )
            await self._upsert(
                dealers_df,
                table_name="nyfed_pd_marketshare_dealers",
                unique_columns=["release_date", "period", "security_type", "security", "category"],
            )
            if as_dataframe:
                return summary_df, dealers_df
            return summary_model, dealers_model

        if as_dataframe:
            return summary_model.as_dataframe, dealers_model.as_dataframe
        return summary_model, dealers_model

    async def guidesheets_latest(
        self,
        guidesheet_type: str = "si",
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/guidesheets/{guidesheet_type}/latest.json"
        data = await self.fetch_json(path)
        guide = (data.get("guidesheet") or {}).get(guidesheet_type) or {}
        details = guide.get("details") or []

        if guidesheet_type == "wi":
            summary_model = nyfed_models.GuideSheetWi(guide)
            details_model = nyfed_models.GuideSheetWiDetails(details)
            summary_table = "nyfed_guidesheet_wi"
            details_table = "nyfed_guidesheet_wi_details"
            summary_unique = ["title", "sec_dir_as_of_date", "first_due_date", "last_due_date"]
            details_unique = ["cusip", "maturity_date"]
        elif guidesheet_type == "fs":
            summary_model = nyfed_models.GuideSheetFs(guide)
            details_model = nyfed_models.GuideSheetFsDetails(details)
            summary_table = "nyfed_guidesheet_fs"
            details_table = "nyfed_guidesheet_fs_details"
            summary_unique = ["title", "reports_for", "next_distribution_date"]
            details_unique = ["report_name", "report_due_date"]
        else:
            summary_model = nyfed_models.GuideSheetSi(guide)
            details_model = nyfed_models.GuideSheetSiDetails(details)
            summary_table = "nyfed_guidesheet_si"
            details_table = "nyfed_guidesheet_si_details"
            summary_unique = ["title", "report_weeks_from_date", "report_weeks_to_date"]
            details_unique = ["cusip", "maturity_date"]

        if insert:
            await self.db.connect()
            await self._upsert(
                summary_model.as_dataframe,
                table_name=summary_table,
                unique_columns=summary_unique,
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name=details_table,
                unique_columns=details_unique,
            )

        if as_dataframe:
            return summary_model.as_dataframe, details_model.as_dataframe
        return summary_model, details_model

    async def guidesheets_previous(
        self,
        guidesheet_type: str = "si",
        insert: bool = False,
        as_dataframe: bool = True,
    ):
        path = f"/api/guidesheets/{guidesheet_type}/previous.json"
        data = await self.fetch_json(path)
        guide = (data.get("guidesheet") or {}).get(guidesheet_type) or {}
        details = guide.get("details") or []

        if guidesheet_type == "wi":
            summary_model = nyfed_models.GuideSheetWi(guide)
            details_model = nyfed_models.GuideSheetWiDetails(details)
            summary_table = "nyfed_guidesheet_wi"
            details_table = "nyfed_guidesheet_wi_details"
            summary_unique = ["title", "sec_dir_as_of_date", "first_due_date", "last_due_date"]
            details_unique = ["cusip", "maturity_date"]
        elif guidesheet_type == "fs":
            summary_model = nyfed_models.GuideSheetFs(guide)
            details_model = nyfed_models.GuideSheetFsDetails(details)
            summary_table = "nyfed_guidesheet_fs"
            details_table = "nyfed_guidesheet_fs_details"
            summary_unique = ["title", "reports_for", "next_distribution_date"]
            details_unique = ["report_name", "report_due_date"]
        else:
            summary_model = nyfed_models.GuideSheetSi(guide)
            details_model = nyfed_models.GuideSheetSiDetails(details)
            summary_table = "nyfed_guidesheet_si"
            details_table = "nyfed_guidesheet_si_details"
            summary_unique = ["title", "report_weeks_from_date", "report_weeks_to_date"]
            details_unique = ["cusip", "maturity_date"]

        if insert:
            await self.db.connect()
            await self._upsert(
                summary_model.as_dataframe,
                table_name=summary_table,
                unique_columns=summary_unique,
            )
            await self._upsert(
                details_model.as_dataframe,
                table_name=details_table,
                unique_columns=details_unique,
            )

        if as_dataframe:
            return summary_model.as_dataframe, details_model.as_dataframe
        return summary_model, details_model
