# kelviq_sdk/client.py

import httpx
import json
import datetime
from typing import Optional, Dict, Any, Union, TYPE_CHECKING, Literal, TypeVar, Type

# Import the SDK's logger (assuming logger is defined in kelviq_sdk/__init__.py)
from . import logger

from .exceptions import APIError, AuthenticationError, InvalidRequestError, ServerError, NotFoundError
from .constants import (API_URLS, EDGE_API_URLS, API_BASE_PATH_PREFIX,
                        DEFAULT_API_VERSION, DEFAULT_API_URL, EDGE_API_URL)

# Import reporting operation classes
# TYPE_CHECKING is used to prevent circular imports at runtime
if TYPE_CHECKING:
    from .reporting import ReportingSyncOperations, ReportingAsyncOperations
    from .checkout import CheckoutSyncOperations, CheckoutAsyncOperations
    from .entitlements import EntitlementsSyncOperations, EntitlementsAsyncOperations
    from .subscription import SubscriptionSyncOperations, SubscriptionAsyncOperations
    from .customers import CustomersSyncOperations, CustomersAsyncOperations
else:
    # Allow runtime access for isinstance checks or dynamic access if ever needed.
    ReportingSyncOperations = None
    ReportingAsyncOperations = None
    CheckoutSyncOperations = None
    CheckoutAsyncOperations = None
    EntitlementsSyncOperations = None
    EntitlementsAsyncOperations = None
    SubscriptionSyncOperations = None
    SubscriptionAsyncOperations = None
    CustomersSyncOperations = None
    CustomersAsyncOperations = None

# Type variable for the Kelviq class itself, used in factory method return types
TKelviq = TypeVar("TKelviq", bound="Kelviq")


class Kelviq:
    """
    Unified Python SDK Client for interacting with the Kelviq API.
    This client is initialized for either synchronous or asynchronous operations
    using the `create_sync_client` or `create_async_client` static factory methods.

    Synchronous usage:
        client = Kelviq.create_sync_client(access_token="YOUR_TOKEN")
        with client: # Or client.close() manually
            response = client.reporting.report_usage(...)
            checkout_session = client.checkout.create_session(...)

    Asynchronous usage:
        async_client = Kelviq.create_async_client(access_token="YOUR_TOKEN")
        async with async_client: # Or await async_client.aclose() manually
            response = await client.reporting.report_usage(...)
            checkout_session = await client.checkout.create_session(...)
    """
    _DEFAULT_TIMEOUT = 10.0  # seconds

    # Resource operation attributes will be populated based on the 'mode'
    reporting: Union['ReportingSyncOperations', 'ReportingAsyncOperations']
    checkout: Union['CheckoutSyncOperations', 'CheckoutAsyncOperations']
    entitlements: Union['EntitlementsSyncOperations', 'EntitlementsAsyncOperations']
    subscription: Union['SubscriptionSyncOperations', 'SubscriptionAsyncOperations']
    customers: Union['CustomersSyncOperations', 'CustomersAsyncOperations']

    edge_api_url_to_use: str

    # Users should use factory methods.
    def __init__(self,
                 access_token: str,
                 mode: Literal['sync', 'async'],  # Mode is crucial for internal setup
                 environment: Optional[str] = 'prod',
                 base_url: Optional[str] = None,  # Default handled by DEFAULT_API_URL constant
                 edge_api_url: Optional[str] = None,  # Default handled by EDGE_API_URL constant
                 api_version: Optional[str] = None,  # Default handled by DEFAULT_API_VERSION constant
                 timeout: float = _DEFAULT_TIMEOUT,
                 transport: Optional[Union[httpx.BaseTransport, httpx.AsyncBaseTransport]] = None):
        """
        Initializes the Kelviq API client.
        It's recommended to use `Kelviq.create_sync_client` or
        `Kelviq.create_async_client` factory methods for instantiation.

        Args:
            access_token (str): Your API access token (Bearer Token).
            mode (Literal['sync', 'async']): The operational mode of the client.
            base_url (Optional[str]): The base URL of the API.
                                      Defaults to value from constants.DEFAULT_API_URL.
            api_version (Optional[str]): The API version string (e.g., "v1").
                                         Defaults to value from constants.DEFAULT_API_VERSION.
            timeout (float): Request timeout in seconds.
            transport (Optional): For testing, an httpx transport can be injected.
        """
        # Ensure Resource Operation classes are loaded to avoid errors if this file is imported first
        global ReportingSyncOperations, ReportingAsyncOperations
        global CheckoutSyncOperations, CheckoutAsyncOperations
        global EntitlementsSyncOperations, EntitlementsAsyncOperations
        global SubscriptionSyncOperations, SubscriptionAsyncOperations
        global CustomersSyncOperations, CustomersAsyncOperations
        if ReportingSyncOperations is None or ReportingAsyncOperations is None:
            from .reporting import ReportingSyncOperations as ReportingSyncOps, \
                ReportingAsyncOperations as ReportingAsyncOps
            ReportingSyncOperations = ReportingSyncOps
            ReportingAsyncOperations = ReportingAsyncOps
        if CheckoutSyncOperations is None or CheckoutAsyncOperations is None:
            from .checkout import CheckoutSyncOperations as CheckoutSyncOps, CheckoutAsyncOperations as CheckoutAsyncOps
            CheckoutSyncOperations = CheckoutSyncOps
            CheckoutAsyncOperations = CheckoutAsyncOps
        if EntitlementsSyncOperations is None or EntitlementsAsyncOperations is None:
            from .entitlements import EntitlementsSyncOperations as EntitlementsSyncOps, \
                EntitlementsAsyncOperations as EntitlementsAsyncOps
            EntitlementsSyncOperations = EntitlementsSyncOps
            EntitlementsAsyncOperations = EntitlementsAsyncOps
        if SubscriptionSyncOperations is None or SubscriptionAsyncOperations is None:
            from .subscription import SubscriptionSyncOperations as SubscriptionSyncOps, \
                SubscriptionAsyncOperations as SubscriptionAsyncOps
            SubscriptionSyncOperations = SubscriptionSyncOps
            SubscriptionAsyncOperations = SubscriptionAsyncOps
        if CustomersSyncOperations is None or CustomersAsyncOperations is None:
            from .customers import CustomersSyncOperations as CustomersSyncOps, \
                CustomersAsyncOperations as CustomersAsyncOps
            CustomersSyncOperations = CustomersSyncOps
            CustomersAsyncOperations = CustomersAsyncOps

        actual_base_url = base_url if base_url is not None else API_URLS.get(environment, DEFAULT_API_URL)
        self.edge_api_url_to_use = edge_api_url if edge_api_url is not None else EDGE_API_URLS.get(environment, EDGE_API_URL)

        if actual_base_url.endswith('/'):
            actual_base_url = actual_base_url[:-1]
        if self.edge_api_url_to_use.endswith('/'):  # Ensure edge URL is also clean
            self.edge_api_url_to_use = self.edge_api_url_to_use[:-1]

        if actual_base_url.endswith('/'):
            actual_base_url = actual_base_url[:-1]
        self.base_url = actual_base_url
        self.access_token = access_token
        self.api_version = api_version if api_version is not None else DEFAULT_API_VERSION  # This is the client's default API version
        self.timeout = timeout
        self._mode = mode
        self.logger = logger
        logger.info(
            f"Kelviq client initialized. Environment: {environment}, Mode: {self._mode}, Base URL: {self.base_url}, API Version: {self.api_version}"
        )

        self._http_client: Union[httpx.Client, httpx.AsyncClient]

        if self._mode == 'sync':
            if transport and not isinstance(transport, httpx.BaseTransport):
                logger.error("Invalid transport type for synchronous client.")
                raise TypeError("For synchronous client, transport must be an instance of httpx.BaseTransport or None.")
            self._http_client = httpx.Client(
                headers=self._get_headers(),
                timeout=self.timeout,
                transport=transport  # type: ignore
            )
            assert ReportingSyncOperations is not None
            self.reporting = ReportingSyncOperations(self)
            assert CheckoutSyncOperations is not None
            self.checkout = CheckoutSyncOperations(self)
            assert EntitlementsSyncOperations is not None
            self.entitlements = EntitlementsSyncOperations(self)
            assert SubscriptionSyncOperations is not None
            self.subscription = SubscriptionSyncOperations(self)
            assert CustomersSyncOperations is not None
            self.customers = CustomersSyncOperations(self)
            logger.debug("Synchronous HTTP client and resource operations initialized.")
        elif self._mode == 'async':
            if transport and not isinstance(transport, httpx.AsyncBaseTransport):
                logger.error("Invalid transport type for asynchronous client.")
                raise TypeError(
                    "For asynchronous client, transport must be an instance of httpx.AsyncBaseTransport or None.")
            self._http_client = httpx.AsyncClient(
                headers=self._get_headers(),
                timeout=self.timeout,
                transport=transport  # type: ignore
            )
            assert ReportingAsyncOperations is not None
            self.reporting = ReportingAsyncOperations(self)
            assert CheckoutAsyncOperations is not None
            self.checkout = CheckoutAsyncOperations(self)
            assert EntitlementsAsyncOperations is not None
            self.entitlements = EntitlementsAsyncOperations(self)
            assert SubscriptionAsyncOperations is not None
            self.subscription = SubscriptionAsyncOperations(self)
            assert CustomersAsyncOperations is not None
            self.customers = CustomersAsyncOperations(self)
        else:
            # This case should not be reachable if using factory methods
            logger.critical(f"Invalid mode provided during client initialization: {self._mode}")
            raise ValueError(f"Invalid mode: {self._mode}. Must be 'sync' or 'async'.")

    @classmethod
    def create_sync_client(
            cls: Type[TKelviq],
            access_token: str,
            environment: Optional[str] = 'prod',
            base_url: Optional[str] = None,
            edge_api_url: Optional[str] = None,
            api_version: Optional[str] = None,
            timeout: float = _DEFAULT_TIMEOUT,
            transport: Optional[httpx.BaseTransport] = None
    ) -> TKelviq:
        """
        Factory method to create a Kelviq client configured for synchronous operations.
        """
        logger.debug(f"Creating synchronous Kelviq client via factory for '{environment}' environment.")
        return cls(
            access_token=access_token,
            mode='sync',
            environment=environment,
            base_url=base_url,
            edge_api_url=edge_api_url,
            api_version=api_version,  # Pass along to __init__
            timeout=timeout,
            transport=transport
        )

    @classmethod
    def create_async_client(
            cls: Type[TKelviq],
            access_token: str,
            environment: Optional[str] = 'prod',
            base_url: Optional[str] = None,
            edge_api_url: Optional[str] = None,
            api_version: Optional[str] = None,
            timeout: float = _DEFAULT_TIMEOUT,
            transport: Optional[httpx.AsyncBaseTransport] = None
    ) -> TKelviq:
        """
        Factory method to create a Kelviq client configured for asynchronous operations.
        """
        logger.debug("Creating asynchronous Kelviq client via factory.")
        return cls(
            access_token=access_token,
            mode='async',
            environment=environment,
            base_url=base_url,
            edge_api_url=edge_api_url,
            api_version=api_version,
            timeout=timeout,
            transport=transport
        )

    def _get_headers(self) -> Dict[str, str]:
        """Constructs standard request headers including Bearer token authorization."""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

    def _prepare_url(self, endpoint_module_path: str,
                     api_version_override: Optional[str] = None,
                     base_url_override: Optional[str] = None) -> str:
        """
        Prepares the full URL for an API endpoint.
        Uses api_version_override if provided, otherwise uses the client's default api_version.
        """
        # Determine which API version to use for this specific call
        effective_api_version = api_version_override if api_version_override is not None else self.api_version

        current_base_url = base_url_override if base_url_override is not None else self.base_url
        if current_base_url.endswith('/'):  # Ensure no double slashes
            current_base_url = current_base_url[:-1]

        if not endpoint_module_path.startswith('/'):
            endpoint_module_path = '/' + endpoint_module_path
        return f"{current_base_url}{API_BASE_PATH_PREFIX}/{effective_api_version}{endpoint_module_path}"

    def _process_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Processes the HTTP response, parsing JSON and handling errors."""
        logger.debug(f"Processing response. Status: {response.status_code}, URL: {response.url}")
        response_details: Optional[Any] = None
        try:
            if response.content:
                response_details = response.json()
                # Be cautious logging full response details if they might contain sensitive info
                logger.debug(f"Response JSON content (first 200 chars): {str(response_details)[:200]}")
        except json.JSONDecodeError:
            response_details = response.text if response.status_code >= 500 else "Invalid JSON response"

        if 200 <= response.status_code < 300:
            return response_details if isinstance(response_details, dict) else {} if response.content else {}
        elif response.status_code == 400:
            raise InvalidRequestError("Bad Request", status_code=response.status_code, details=response_details)
        elif response.status_code == 401:
            raise AuthenticationError("Unauthorized: Access token is invalid, missing, or expired.",
                                      status_code=response.status_code, details=response_details)
        elif response.status_code == 403:
            raise AuthenticationError("Forbidden: Access token does not grant permission for this action.",
                                      status_code=response.status_code, details=response_details)
        elif response.status_code == 404:
            raise NotFoundError(f"Not Found: The resource at {response.url} was not found.",
                                status_code=response.status_code, details=response_details)
        elif response.status_code >= 500:
            raise ServerError("Server Error", status_code=response.status_code, details=response_details)
        else:
            raise APIError(f"HTTP Error {response.status_code}: {response.reason_phrase}",
                           status_code=response.status_code, details=response_details)

    # --- Synchronous operations ---
    def _request(self,
                 method: str,
                 endpoint_module_path: str,
                 data: Optional[Dict[str, Any]] = None,
                 params: Optional[Dict[str, Any]] = None,
                 api_version_override: Optional[str] = None,
                 base_url_override: Optional[str] = None
                 ) -> Dict[str, Any]:
        """Internal method for making synchronous HTTP requests."""
        if self._mode != 'sync' or not isinstance(self._http_client, httpx.Client):
            logger.critical("Attempted synchronous request with non-sync client configuration.")
            raise RuntimeError(
                "Client not in 'sync' mode or HTTP client not initialized correctly for sync operations.")

        url = self._prepare_url(endpoint_module_path,
                                api_version_override=api_version_override,
                                base_url_override=base_url_override)
        try:
            response = self._http_client.request(method, url, json=data, params=params)
            return self._process_response(response)
        except httpx.TimeoutException:
            raise APIError(f"Request timed out for {method} {url}.")
        except httpx.ConnectError:
            raise APIError(f"Could not connect to {url}.")
        except httpx.RequestError as e:
            raise APIError(f"Request error for {method} {url}: {e}")

    def close(self):
        """Closes the synchronous HTTP client. Call this if not using a context manager."""
        if self._mode == 'sync' and isinstance(self._http_client, httpx.Client):
            if not self._http_client.is_closed:
                logger.info("Closing synchronous Kelviq client.")
                self._http_client.close()
            else:
                logger.debug("Synchronous client was already closed.")
        elif self._mode == 'async':
            logger.warning(
                "close() called on an async-mode client. Use aclose() instead for async clients or use the async context manager.")

    # --- Asynchronous operations ---
    async def _async_request(self,
                             method: str,
                             endpoint_module_path: str,
                             data: Optional[Dict[str, Any]] = None,
                             params: Optional[Dict[str, Any]] = None,
                             api_version_override: Optional[str] = None,
                             base_url_override: Optional[str] = None
                             ) -> Dict[str, Any]:
        """Internal method for making asynchronous HTTP requests."""
        if self._mode != 'async' or not isinstance(self._http_client, httpx.AsyncClient):
            logger.critical("Attempted asynchronous request with non-async client configuration.")
            raise RuntimeError(
                "Client not in 'async' mode or HTTP client not initialized correctly for async operations.")

        url = self._prepare_url(endpoint_module_path,
                                api_version_override=api_version_override,
                                base_url_override=base_url_override)
        try:
            response = await self._http_client.request(method, url, json=data, params=params)
            return self._process_response(response)
        except httpx.TimeoutException:
            raise APIError(f"Async request timed out for {method} {url}.")
        except httpx.ConnectError:
            raise APIError(f"Async could not connect to {url}.")
        except httpx.RequestError as e:
            raise APIError(f"Async request error for {method} {url}: {e}")

    async def aclose(self):
        """Closes the asynchronous HTTP client. Call this if not using an async context manager."""
        if self._mode == 'async' and isinstance(self._http_client, httpx.AsyncClient):
            if not self._http_client.is_closed:
                logger.info("Closing asynchronous Kelviq client.")
                await self._http_client.aclose()
            else:
                logger.debug("Asynchronous client was already closed.")
        elif self._mode == 'sync':
            logger.warning(
                "aclose() called on a sync-mode client. Use close() instead for sync clients or use the sync context manager.")

    # --- Context Management ---
    def __enter__(self: TKelviq) -> TKelviq:
        if self._mode != 'sync':
            logger.error("Attempted to use sync context manager with async-mode client.")
            raise TypeError(
                "Client must be initialized with mode='sync' (e.g., via create_sync_client) to use synchronous 'with' statement.")
        logger.debug("Entering synchronous client context.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug(f"Exiting synchronous client context. exc_type: {exc_type}")
        self.close()

    async def __aenter__(self: TKelviq) -> TKelviq:
        if self._mode != 'async':
            logger.error("Attempted to use async context manager with sync-mode client.")
            raise TypeError(
                "Client must be initialized with mode='async' (e.g., via create_async_client) to use 'async with' statement.")
        logger.debug("Entering asynchronous client context.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.debug(f"Exiting asynchronous client context. exc_type: {exc_type}")
        await self.aclose()
