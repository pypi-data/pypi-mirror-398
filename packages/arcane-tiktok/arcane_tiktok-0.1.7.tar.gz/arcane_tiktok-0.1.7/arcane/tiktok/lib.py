from datetime import date, timedelta
from typing import Optional

from arcane.datastore import Client as DatastoreClient
from arcane.core import BadRequestError, BaseAccount, ALL_CLIENTS_RIGHTS, UserRightsEnum, RightsLevelEnum
from arcane.requests import call_get_route

from .const import TIKTOK_OAUTH_CREDENTIALS_KIND

def get_tiktok_account(
    base_account: BaseAccount,
    clients_service_url: Optional[str] = None,
    firebase_api_key: Optional[str] = None,
    gcp_service_account: Optional[str] = None,
    auth_enabled: bool = True
) -> dict:
    """Fetch TikTok account details using the base account information.

    Args:
        base_account (BaseAccount): The base account object.
        clients_service_url (Optional[str]): URL of the clients service.
        firebase_api_key (Optional[str]): Firebase API key for authentication.
        gcp_service_account (Optional[str]): Path to the GCP service account file.
        auth_enabled (bool): Flag to enable or disable authentication.

    Raises:
        BadRequestError: Raised when required parameters are missing or invalid.

    Returns:
        dict: TikTok account.
    """

    if not (clients_service_url and firebase_api_key and gcp_service_account):
        raise BadRequestError('clients_service_url or firebase_api_key or gcp_service_account should not be None if tiktok account is not provided')

    url = f"{clients_service_url}/api/tiktok-account?account_id={base_account['id']}&client_id={base_account['client_id']}"
    accounts = call_get_route(
        url,
        firebase_api_key,
        claims={'features_rights': { UserRightsEnum.AMS_GTP: RightsLevelEnum.VIEWER }, 'authorized_clients': [ALL_CLIENTS_RIGHTS]},
        auth_enabled=auth_enabled,
        credentials_path=gcp_service_account
    )
    if len(accounts) == 0:
        raise BadRequestError(f'Error while getting tiktok account with: {base_account}. No account corresponding.')
    elif len(accounts) > 1:
        raise BadRequestError(f'Error while getting tiktok account with: {base_account}. Several account corresponding: {accounts}')

    return accounts[0]


def get_tikok_user_credentials(
    user_email: str,
    gcp_credentials_path: Optional[str],
    gcp_project: Optional[str],
    datastore_client: Optional[DatastoreClient]
    ):
    """Retrieve and decrypt TikTok user credentials.

    Args:
        user_email (str): Email of the user whose credentials are to be fetched.
        secret_key_file (str): Path to the secret key file for decryption.
        gcp_credentials_path (Optional[str]): Path to GCP credentials.
        gcp_project (Optional[str]): GCP project ID.
        datastore_client (Optional[DatastoreClient]): Datastore client instance.

    """

    if not datastore_client:
        if not gcp_credentials_path and not gcp_project:
            raise BadRequestError('gcp_credentials_path or gcp_project should not be None if datastore_client is not provided')
        datastore_client = DatastoreClient.from_service_account_json(gcp_credentials_path, project=gcp_project)

    query = datastore_client.query(kind=TIKTOK_OAUTH_CREDENTIALS_KIND).add_filter('email', '=', user_email)
    users_credential = list(query.fetch())
    if len(users_credential) == 0:
        raise BadRequestError(f'Error while getting tiktok user credentials with mail: {user_email}. No entity corresponding.')
    elif len(users_credential) > 1:
        raise BadRequestError(f'Error while getting tiktok user credentials with mail: {user_email}. Several entities corresponding: {users_credential}')

    return users_credential[0]


def get_period_list_of_thirty_days_max(start_date: date, end_date: date) -> list[tuple[date, date]]:
    """Split a date range into chunks of maximum 30 days.

    Args:
        start_date: Start date of the period
        end_date: End date of the period

    Returns:
        list of tuples (start_date, end_date) where each period is max 30 days

    Raises:
        ValueError: If end_date is before start_date
    """
    if end_date < start_date:
        raise ValueError('Incorrect Report Params: end_date must be greater than start_date')

    period_list: list[tuple[date, date]] = []
    current_start = start_date

    while current_start <= end_date:
        chunk_end = min(current_start + timedelta(days=29), end_date)
        period_list.append((current_start, chunk_end))
        current_start = chunk_end + timedelta(days=1)

    return period_list
