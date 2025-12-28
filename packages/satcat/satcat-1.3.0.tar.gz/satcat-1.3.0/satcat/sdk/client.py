import json as jsonlib
import warnings
from datetime import datetime
from importlib.metadata import version as pkg_version
from typing import Any, Collection, Dict, List, Literal, Optional, Union
from urllib.error import HTTPError
from urllib.parse import urljoin

import requests
from packaging import version

from satcat.cli import utils as cli_utils
from satcat.sdk.events.event_client import EventClient
from satcat.sdk.od_client import ODClient
from satcat.sdk.propagation.propagation_client import PropagationClient
from satcat.sdk.screening.screening_client import ScreeningClient
from satcat.sdk.maneuvers.cola_maneuver_client import ColaManeuverClient
from satcat.sdk.settings import settings
from satcat.sdk.utils import SortDirection

# Get current installed version
CURRENT_VERSION = pkg_version("satcat")


# Get latest version from PyPI
def get_latest_version(package_name: str) -> str:
    url = f"https://pypi.org/pypi/{package_name}/json"
    res = requests.get(url, timeout=2)
    if res.status_code == 200:
        return res.json()["info"]["version"]
    return None


# Compare versions and print a warning if outdated
def check_version():
    package_name = "satcat"
    try:
        current = version.parse(CURRENT_VERSION)
        latest = version.parse(get_latest_version(package_name))
        if latest and current < latest:
            warnings.warn(
                f"⚠️ You are using {package_name} {current}, "
                f"but the latest version is {latest}. "
                f"Run `pip install -U {package_name}` to upgrade."
            )
    except Exception:
        # Silently fail if check fails
        pass


AUTH_TIMEOUT_MINUTES = 60


class Client:
    """Base Client class which may be used to make requests to Satcat APIs.
    May be used as a context manager with the ``with`` keyword:

    .. code-block:: python

        with Client() as client:
            client.request(...)

    If not used with the ``with`` keyword, it is recommended to explicitly close
    the Client with ``client.close()`` after the application is finished making requests.
    """

    session: requests.Session

    def __init__(self, default_page_size: int = 32):
        """
        :param default_page_size: Default page size to use when sending repeated listing
            requests to a collection endpoint, defaults to 10
        :type page_size: int, optional
        """
        self.session = requests.Session()
        self.access_token = None
        self.authenticated = False
        self.authenticated_at = None
        self.default_page_size = default_page_size
        check_version()

    def __enter__(self):
        return self

    def __exit__(self, *exc_args):
        self.close()

    def close(self):
        """Close the client and any associated network connections."""
        self.session.close()

    def authenticate_session(self, timeout_s: Optional[int] = None):
        """Authenticate the HTTP session with the authentication provider using the
            authentication method determined by ``satcat.sdk.settings.auth_method`` .

        This is done automatically when using ``request_authenticated`` .
        """
        if settings.auth_method == "password":
            path = urljoin(settings.satcat_rest_api_url, "login")
            res = self.request(
                path,
                method="POST",
                data={
                    "username": settings.auth_username,
                    "password": settings.auth_password,
                    "grant_type": "password",
                },
            )
            try:
                token = res.json()["access_token"]
            except Exception:
                raise ValueError(
                    f"Authentication Error ({res.status_code}): {res.text}"
                ) from None
            self.access_token = token
            self.session.headers["Authorization"] = f"Bearer {token}"
        elif settings.auth_method == "client_credentials":
            payload = f"grant_type=client_credentials&client_id={settings.auth_client_id}&client_secret={settings.auth_client_secret}"
            headers = {"content-type": "application/x-www-form-urlencoded"}
            response = requests.post(
                urljoin(settings.satcat_rest_api_url, "/oauth/token/"),
                data=payload,
                headers=headers,
                timeout=timeout_s or settings.default_timeout,
            )

            if response.status_code == 200:
                token = response.json()["access_token"]
            else:
                raise ValueError(
                    "Failed to authenticate with client_credentials flow using provided credentials"
                )
            self.session.headers["Authorization"] = f"Bearer {token}"
            self.access_token = token
        self.authenticated = True
        self.authenticated_at = datetime.utcnow()

    def request(
        self,
        path: str,
        method: str = "GET",
        data: Optional[dict] = None,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
        files=None,
        api: Literal["rest", "web"] = "rest",
    ) -> requests.Response:
        """Make an HTTP request to a Satcat API.
        .. warning:: For most use cases, this function should only be called internally by
        high level functions inside the SDK, such as those inside ``client.screening`` .
        """
        if api == "rest":
            url = urljoin(settings.satcat_rest_api_url, path)
        elif api == "web":
            url = urljoin(settings.satcat_web_api_url, path)
        else:
            raise ValueError(f"Invalid api setting {api}")

        with cli_utils.FetchingSpinner():
            response = self.session.request(
                method,
                url,
                json=json,
                data=data,
                params=params,
                files=files,
                timeout=settings.default_timeout,
            )
        return response

    def request_authenticated(
        self,
        path: str,
        method: str = "GET",
        data: Optional[dict] = None,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
        ignore_failure: bool = False,
        files=None,
        api: Literal["rest", "web"] = "rest",
    ) -> requests.Response:
        """Ensure that the HTTP session is authorized and make an HTTP request to
            a Satcat API.

        .. warning:: For most use cases, this function should only be called internally by
            high level functions inside the SDK, such as those inside ``client.screening`` .
        """
        if not self.authenticated:
            with cli_utils.FetchingSpinner("Authenticating..."):
                self.authenticate_session()
        elif (
            self.authenticated_at
            and (datetime.utcnow() - self.authenticated_at).total_seconds()
            > AUTH_TIMEOUT_MINUTES * 60
        ):
            with cli_utils.FetchingSpinner("Authenticating..."):
                self.authenticate_session()
        res = self.request(
            path, method, data=data, json=json, params=params, files=files, api=api
        )
        if not str(res.status_code).startswith("2") and not ignore_failure:
            raise HTTPError(path, res.status_code, res.text, res.headers, None)
        return res

    def request_list(
        self,
        path: str,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        params: Optional[dict] = None,
        sort_direction: Union[SortDirection, str] = SortDirection.DESC,
        sort_field: str = "created_at",
        fields: Optional[List[str]] = None,
    ) -> Collection[Any]:
        """Request a list of resources from a Satcat API and automatically page through
            the results if necessary.

        .. warning:: For most use cases, this function should only be called internally by
            high level functions inside the SDK, such as those inside ``client.screening`` .
        """
        if params is None:
            params = {}
        params["sort_field"] = sort_field
        if fields is not None:
            params["fields"] = ",".join(fields)
        if isinstance(sort_direction, str):
            sort_direction = SortDirection(sort_direction)
        params["sort_direction"] = sort_direction.value.lower()
        result_items = []
        if filters is not None:
            params["filters"] = jsonlib.dumps(filters)
        if count is not None:
            params["count"] = count
            result_items = self.request_authenticated(
                path, "GET", params=params
            ).json()["items"]
        else:
            params["count"] = self.default_page_size
            result_items = []
            offset = 0
            total_count = None
            while total_count is None or offset <= total_count:
                params["offset"] = offset
                res = self.request_authenticated(path, "GET", params=params)
                data = res.json()
                items = data["items"]
                result_items.extend(items)
                offset += self.default_page_size
                total_count = data["total_count"]

        for item in result_items:
            item["client"] = self

        return result_items

    def ping_authenticated(self) -> bool:
        """Sends a request to Kayhan servers to confirm a healthy and authenticated session. Returns True if valid, raises an HTTPError if not."""
        try:
            self.request_authenticated("health_authenticated")
            return True
        except HTTPError as e:
            if e.code == 401:
                return False
            raise

    @property
    def propagation(self) -> "PropagationClient":
        """Library containing SDK functions for interacting with the
        Satcat Propagation API."""
        return PropagationClient(self)

    @property
    def screening(self) -> "ScreeningClient":
        """Library containing SDK functions for interacting with the
        Satcat Screening API."""
        return ScreeningClient(self)

    @property
    def events(self) -> "EventClient":
        """Library containing SDK functions for interacting with the
        Satcat Events API."""
        return EventClient(self)

    @property
    def od(self) -> "ODClient":
        """Library containing SDK functions for interacting with the
        Satcat OD API."""
        return ODClient(self)

    @property
    def cola_maneuvers(self) -> "ColaManeuverClient":
        """Library containing SDK functions for interacting with the
        Satcat COLA Maneuver Designer API."""
        return ColaManeuverClient(self)

    def create_ephemeris(self, *args, **kwargs):
        """Alias for ``client.screening.create_ephemeris``."""
        return self.screening.create_ephemeris(*args, **kwargs)

    def list_ephemerides(self, *args, **kwargs):
        """Alias for ``client.screening.list_ephemerides``."""
        return self.screening.list_ephemerides(*args, **kwargs)

    def get_ephemeris(self, *args, **kwargs):
        """Alias for ``client.screening.get_ephemeris``."""
        return self.screening.get_ephemeris(*args, **kwargs)

    def download_ephemeris(self, *args, **kwargs):
        """Alias for ``client.screening.download_ephemeris``."""
        return self.screening.download_ephemeris(*args, **kwargs)

    def operationalize_ephemeris(self, *args, **kwargs):
        """Alias for ``client.screening.operationalize_ephemeris``."""
        return self.screening.operationalize_ephemeris(*args, **kwargs)
