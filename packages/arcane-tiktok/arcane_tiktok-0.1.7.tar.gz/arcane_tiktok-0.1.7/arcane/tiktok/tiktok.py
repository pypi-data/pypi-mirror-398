from datetime import date
import json
from typing import Optional, cast
import backoff
import requests

from arcane.core import BaseAccount, BadRequestError
from arcane.datastore import Client as DatastoreClient

from .const import TIKTOK_SERVER_URL
from .exceptions import TikTokAuthError, TikTokApiError
from .lib import get_tiktok_account, get_tikok_user_credentials, get_period_list_of_thirty_days_max

class TiktokClient:
    def __init__(
        self,
        gcp_service_account: str,
        base_account: Optional[BaseAccount] = None,
        user_email: Optional[str] = None,
        clients_service_url: Optional[str] = None,
        firebase_api_key: Optional[str] = None,
        gcp_credentials_path: Optional[str] = None,
        datastore_client: Optional[DatastoreClient] = None,
        gcp_project: Optional[str] = None,
        auth_enabled: bool = True
    ) -> None:

        creator_email = None

        if gcp_service_account and (base_account or user_email):
            if user_email:
                creator_email = user_email
            else:
                base_account = cast(BaseAccount, base_account)
                tiktok_account = get_tiktok_account(
                    base_account=base_account,
                    clients_service_url=clients_service_url,
                    firebase_api_key=firebase_api_key,
                    gcp_service_account=gcp_service_account,
                    auth_enabled=auth_enabled
                )

                creator_email = cast(str, tiktok_account['creator_email'])

            if creator_email is None:
                raise BadRequestError('creator_email should not be None while using user access protocol')

            credentials = get_tikok_user_credentials(
                user_email=creator_email,
                gcp_credentials_path=gcp_credentials_path,
                gcp_project=gcp_project,
                datastore_client=datastore_client
            )

            self._access_token = credentials['access_token']
        else:
            raise BadRequestError('gcp_service_account and (base_account or user_email) should be provided to initialize TiktokClient')


    @backoff.on_exception(backoff.expo, requests.exceptions.HTTPError, max_tries=5)
    def _make_request(self, endpoint: str, method: str, params: Optional[dict] = None, headers: Optional[dict] = None, **kwargs) -> dict:
        """Send a request to TikTok API"""

        default_headers = {"Access-Token": self._access_token}
        if headers:
            default_headers.update(headers)

        response = requests.request(method=method, url=f"{TIKTOK_SERVER_URL}{endpoint}", headers=default_headers, params=params, **kwargs)
        response.raise_for_status()

        response = response.json()
        # tiktok return error codes in 200 HTTP responses
        api_code = response.get('code')
        if api_code != 0:
            if api_code in [40104, 40105, 40106]:
                raise TikTokAuthError(f"{response.get('message')}")
            raise TikTokApiError(f"{response.get('message')}")

        return response.get('data', {})

    def get_advertiser_info(self, advertiser_ids: list[str]) -> dict:
        """Get advertiser info"""
        params = {"advertiser_ids": json.dumps(advertiser_ids)}

        response = self._make_request(
            endpoint="/advertiser/info/",
            method="GET",
            params=params
            )
        return response.get('list', {})

    def get_account_campaigns(self, advertiser_id: str) -> list[dict[str, str]]:
        """Get campaigns for an advertiser account"""
        page = 1
        campaigns = []
        while True:
            params = {
                "advertiser_id": advertiser_id,
                "page_size": 1000,
                "page": page,
                "fields": json.dumps(["campaign_id","campaign_name","operation_status"])
            }

            response = self._make_request(
                endpoint='/campaign/get/',
                method='GET',
                params=params
            )

            current_campaigns = response.get('list', [])
            total_page = response.get('page_info', {}).get('total_page', 1)

            if current_campaigns:
                campaigns.extend(current_campaigns)

            if page >= total_page:
                break
            page += 1

        return [{
            'id': campaign.get('campaign_id'),
            'name': campaign.get('campaign_name'),
            'status': campaign.get('operation_status')
        } for campaign in campaigns]


    def get_tiktok_report(self, advertiser_id: str, start_date: date, end_date: date, campaign_ids: Optional[list[str]] = None) -> list[dict[str, str]]:
        """Get TikTok report data. Automatically chunks date ranges into 30-day periods and campaign IDs into batches of 100.

        Args:
            advertiser_id: TikTok advertiser account ID
            start_date: Start date of the report period
            end_date: End date of the report period
            campaign_ids: Optional list of campaign IDs to filter by

        Returns:
            List of dictionaries, each containing:
            {
                'campaign_id': str,           # Campaign identifier
                'stat_time_day': str,          # Date in format 'YYYY-MM-DD HH:MM:SS'
                'campaign_name': str,          # Campaign name
                'currency': str,               # Currency code (e.g. 'EUR')
                'spend': str                   # Spend amount
            }

        Example:
            [
                {
                    'campaign_id': '1784548428904466',
                    'stat_time_day': '2024-02-03 00:00:00',
                    'campaign_name': 'My Campaign',
                    'currency': 'EUR',
                    'spend': '123.45'
                },
                ...
            ]
        """
        endpoint = "/report/integrated/get/"

        date_periods = get_period_list_of_thirty_days_max(start_date, end_date)
        all_data = []

        # Chunk campaign_ids into batches of 100 (TikTok API limit)
        campaign_id_batches = []
        if campaign_ids:
            for i in range(0, len(campaign_ids), 100):
                campaign_id_batches.append(campaign_ids[i:i + 100])
        else:
            campaign_id_batches = [None]  # No filter

        for campaign_id_batch in campaign_id_batches:
            for period_start, period_end in date_periods:
                page = 1
                while True:
                    params = {
                        "advertiser_id": advertiser_id,
                        "report_type": "BASIC",
                        "data_level": "AUCTION_CAMPAIGN",
                        "start_date": period_start.strftime("%Y-%m-%d"),
                        "end_date": period_end.strftime("%Y-%m-%d"),
                        "page": page,
                        "page_size": 1000,
                        "dimensions": json.dumps(["campaign_id","stat_time_day"]),
                        "metrics": json.dumps(["spend", "currency", "campaign_name"])
                    }

                    if campaign_id_batch:
                        filters = [
                            {
                                "field_name": "campaign_ids",
                                "filter_type": "IN",
                                "filter_value": json.dumps(campaign_id_batch)
                            }
                        ]
                        params["filtering"] = json.dumps(filters)

                    response = self._make_request(
                        endpoint=endpoint,
                        method="GET",
                        params=params
                    )

                    current_data = response.get('list', [])
                    total_page = response.get('page_info', {}).get('total_page', 1)

                    if current_data:
                        flattened_data = [
                            {**item.get('dimensions', {}), **item.get('metrics', {})}
                            for item in current_data
                        ]
                        all_data.extend(flattened_data)

                    if page >= total_page:
                        break
                    page += 1

        return all_data
