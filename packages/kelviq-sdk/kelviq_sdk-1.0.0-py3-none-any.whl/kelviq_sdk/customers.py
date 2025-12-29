# kelviq_sdk/customers.py

from typing import TYPE_CHECKING, Dict, Any, Optional, List

# Import the SDK's logger
from . import logger

# Import Pydantic models
from .models.customers import (
    CustomerCreatePayload,
    CustomerUpdatePayload,
    CustomerResponse,
    PaginatedCustomerResponse,
    ArchiveSuccessResponse
)
# Import SDK exceptions
from .exceptions import InvalidRequestError, APIError
from pydantic import ValidationError

if TYPE_CHECKING:
    from .client import Kelviq  # Main client class

# Define the module-specific path prefix for customer endpoints
CUSTOMERS_MODULE_PREFIX = "/customers"


class CustomersSyncOperations:
    """
    Handles synchronous 'customers' related API operations.
    """

    def __init__(self, main_client: 'Kelviq'):
        self._main_client = main_client
        self._main_client.logger.debug("CustomersSyncOperations initialized.")

    def list(self, page: Optional[int] = None, page_size: Optional[int] = None) -> PaginatedCustomerResponse:
        """
        Retrieves a paginated list of customers.
        API endpoint: GET /api/{version}/customers/
        """
        endpoint_module_path = f"{CUSTOMERS_MODULE_PREFIX}/"

        query_params: Dict[str, Any] = {}
        if page is not None:
            query_params["page"] = page
        if page_size is not None:
            query_params["page_size"] = page_size  # DRF uses page_size

        self._main_client.logger.info(f"Initiating synchronous list customers. Params: {query_params or 'None'}")

        response_dict = self._main_client._request(
            method="GET",
            endpoint_module_path=endpoint_module_path,
            params=query_params if query_params else None
        )
        return PaginatedCustomerResponse.model_validate(response_dict)

    def create(
            self,
            customerId: str,  # Changed from payload to individual arg
            email: str,  # Changed from payload to individual arg
            name: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> CustomerResponse:
        """
        Creates a new customer.
        API endpoint: POST /api/{version}/customers/
        """
        endpoint_module_path = f"{CUSTOMERS_MODULE_PREFIX}/"
        self._main_client.logger.info(f"Initiating synchronous create customer for customerId: {customerId}")

        try:
            # Create Pydantic model internally for validation and serialization
            payload_model = CustomerCreatePayload(
                customerId=customerId,  # Uses camelCase as per method signature
                email=email,
                name=name,
                metadata=metadata
            )
            # Pydantic model uses alias "customer_id" for customerId,
            # so model_dump(by_alias=True) will produce "customer_id" in the JSON.
            request_data = payload_model.model_dump(by_alias=True, exclude_none=True)
            self._main_client.logger.debug(f"Create customer payload: {request_data}")
        except ValidationError as e:
            self._main_client.logger.warning(
                f"Pydantic validation failed for create customer. CustomerId: {customerId}, Errors: {e.errors(include_context=False)}")
            raise InvalidRequestError(
                message="Invalid parameters for create customer",
                details=e.errors(include_context=False)
            ) from e

        response_dict = self._main_client._request(
            method="POST",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return CustomerResponse.model_validate(response_dict)

    def retrieve(self, customerId: str) -> CustomerResponse:  # Changed from customer_db_id
        """
        Retrieves a specific customer by their client-defined customerId.
        API endpoint: GET /api/{version}/customers/{customerId}/
        (Assuming API endpoint uses customerId in path)
        """
        # IMPORTANT: This assumes your DRF ViewSet and URL patterns are configured
        # to look up customers by the 'customerId' field in the URL, not the primary key (id).
        # If it's still by primary key (UUID), this method should accept that UUID.
        endpoint_module_path = f"{CUSTOMERS_MODULE_PREFIX}/{customerId}/"
        self._main_client.logger.info(f"Initiating synchronous retrieve customer for customerId: {customerId}")

        response_dict = self._main_client._request(
            method="GET",
            endpoint_module_path=endpoint_module_path
        )
        return CustomerResponse.model_validate(response_dict)

    def update(
            self,
            customerId: str,  # Changed from customer_db_id
            email: Optional[str] = None,  # Now optional, API might require it though
            name: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> CustomerResponse:
        """
        Updates an existing customer (partially, using PATCH).
        API endpoint: PATCH /api/{version}/customers/{customerId}/
        (Assuming API endpoint uses customerId in path)
        """
        endpoint_module_path = f"{CUSTOMERS_MODULE_PREFIX}/{customerId}/"
        self._main_client.logger.info(f"Initiating synchronous update customer for customerId: {customerId}")

        try:
            # Create Pydantic model internally
            # CustomerUpdatePayload does not include customerId as it's part of the path
            payload_model = CustomerUpdatePayload(
                name=name,
                email=email,
                metadata=metadata
            )
            # Pydantic model fields are already Optional. model_dump with exclude_unset=True
            # will only include fields that were explicitly passed to this method (and not None).
            # by_alias=True is used if Pydantic model fields have aliases for JSON keys.
            request_data = payload_model.model_dump(by_alias=True, exclude_none=True, exclude_unset=True)
            self._main_client.logger.debug(f"Update customer payload: {request_data}")
            if not request_data:  # If payload is empty after exclude_unset
                raise InvalidRequestError(
                    message="Update payload cannot be empty for PATCH request. At least one field to update must be provided.")
        except ValidationError as e:  # Should only catch if Pydantic model has complex validation
            self._main_client.logger.warning(
                f"Pydantic validation failed for update customer. CustomerId: {customerId}, Errors: {e.errors(include_context=False)}")
            raise InvalidRequestError(
                message="Invalid parameters for update customer",
                details=e.errors(include_context=False)
            ) from e

        response_dict = self._main_client._request(
            method="PATCH",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return CustomerResponse.model_validate(response_dict)

    def archive(self, customerId: str) -> ArchiveSuccessResponse:
        """
        Archives (soft deletes) a customer.
        API endpoint: DELETE /api/{version}/customers/{customerId}/
        Handles 204 No Content from the API.
        """
        endpoint_module_path = f"{CUSTOMERS_MODULE_PREFIX}/{customerId}/"
        self._main_client.logger.info(f"Initiating synchronous archive customer for customerId: {customerId}")

        try:
            # _request will return {} if _process_response handles a 204 (no content)
            response_dict = self._main_client._request(
                method="DELETE",
                endpoint_module_path=endpoint_module_path
            )

            # If response_dict is empty, it implies a successful 204 No Content from the server.
            # The _process_response method in client.py returns {} for 204.
            if not response_dict:
                self._main_client.logger.info(f"Customer {customerId} archived successfully (204 No Content).")
                return ArchiveSuccessResponse(message="Customer archived successfully.")

            # If the API unexpectedly returns a body for DELETE (e.g. on a 200 or 202)
            # and it contains a "message" field, this will parse it.
            return ArchiveSuccessResponse.model_validate(response_dict)

        except APIError as e:
            # This block is for other API errors (4xx, 5xx) that _process_response would raise.
            # A specific check for e.status_code == 204 here is less likely to be hit
            # if _process_response correctly handles 204 by returning {}.
            self._main_client.logger.error(f"API error during archive customer {customerId}: {e}")
            raise


class CustomersAsyncOperations:
    """
    Handles asynchronous 'customers' related API operations.
    """

    def __init__(self, main_client: 'Kelviq'):
        self._main_client = main_client
        self._main_client.logger.debug("CustomersAsyncOperations initialized.")

    async def list(self, page: Optional[int] = None, page_size: Optional[int] = None) -> PaginatedCustomerResponse:
        """
        Retrieves a paginated list of customers asynchronously.
        """
        endpoint_module_path = f"{CUSTOMERS_MODULE_PREFIX}/"
        query_params: Dict[str, Any] = {}
        if page is not None: query_params["page"] = page
        if page_size is not None: query_params["page_size"] = page_size
        self._main_client.logger.info(f"Initiating asynchronous list customers. Params: {query_params or 'None'}")

        response_dict = await self._main_client._async_request(
            method="GET",
            endpoint_module_path=endpoint_module_path,
            params=query_params if query_params else None
        )
        return PaginatedCustomerResponse.model_validate(response_dict)

    async def create(
            self,
            customerId: str,
            email: str,
            name: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> CustomerResponse:
        """
        Creates a new customer asynchronously.
        """
        endpoint_module_path = f"{CUSTOMERS_MODULE_PREFIX}/"
        self._main_client.logger.info(f"Initiating asynchronous create customer for customerId: {customerId}")
        try:
            payload_model = CustomerCreatePayload(
                customerId=customerId, email=email, name=name, metadata=metadata
            )
            request_data = payload_model.model_dump(by_alias=True, exclude_none=True)
            self._main_client.logger.debug(f"Async create customer payload: {request_data}")
        except ValidationError as e:
            self._main_client.logger.warning(
                f"Pydantic validation failed for async create customer. CustomerId: {customerId}, Errors: {e.errors(include_context=False)}")
            raise InvalidRequestError(message="Invalid parameters for async create customer",
                                      details=e.errors(include_context=False)) from e

        response_dict = await self._main_client._async_request(
            method="POST",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return CustomerResponse.model_validate(response_dict)

    async def retrieve(self, customerId: str) -> CustomerResponse:  # Changed from customer_db_id
        """
        Retrieves a specific customer by their client-defined customerId asynchronously.
        """
        endpoint_module_path = f"{CUSTOMERS_MODULE_PREFIX}/{customerId}/"
        self._main_client.logger.info(f"Initiating asynchronous retrieve customer for customerId: {customerId}")

        response_dict = await self._main_client._async_request(
            method="GET",
            endpoint_module_path=endpoint_module_path
        )
        return CustomerResponse.model_validate(response_dict)

    async def update(
            self,
            customerId: str,  # Changed from customer_db_id
            email: Optional[str] = None,
            name: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> CustomerResponse:
        """
        Updates an existing customer (partially, using PATCH) asynchronously.
        """
        endpoint_module_path = f"{CUSTOMERS_MODULE_PREFIX}/{customerId}/"
        self._main_client.logger.info(f"Initiating asynchronous update customer for customerId: {customerId}")
        try:
            payload_model = CustomerUpdatePayload(name=name, email=email, metadata=metadata)
            request_data = payload_model.model_dump(by_alias=True, exclude_none=True, exclude_unset=True)
            self._main_client.logger.debug(f"Async update customer payload: {request_data}")
            if not request_data:
                raise InvalidRequestError(
                    message="Update payload cannot be empty for PATCH request. At least one field to update must be provided.")
        except ValidationError as e:
            self._main_client.logger.warning(
                f"Pydantic validation failed for async update customer. CustomerId: {customerId}, Errors: {e.errors(include_context=False)}")
            raise InvalidRequestError(message="Invalid parameters for async update customer",
                                      details=e.errors(include_context=False)) from e

        response_dict = await self._main_client._async_request(
            method="PATCH",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return CustomerResponse.model_validate(response_dict)

    async def archive(self, customerId: str) -> ArchiveSuccessResponse:
        """
        Archives (soft deletes) a customer asynchronously.
        Handles 204 No Content from the API.
        """
        endpoint_module_path = f"{CUSTOMERS_MODULE_PREFIX}/{customerId}/"
        self._main_client.logger.info(f"Initiating asynchronous archive customer for customerId: {customerId}")

        try:
            response_dict = await self._main_client._async_request(
                method="DELETE",
                endpoint_module_path=endpoint_module_path
            )

            # If _process_response returns an empty dict or a dict with a special marker for 204
            if response_dict == {"_status_code": 204} or not response_dict:
                self._main_client.logger.info(f"Customer {customerId} (async) archived successfully (204 No Content).")
                return ArchiveSuccessResponse(message="Customer archived successfully.")

            return ArchiveSuccessResponse.model_validate(response_dict)

        except APIError as e:
            if e.status_code == 204:
                self._main_client.logger.info(
                    f"Customer {customerId} (async) archived successfully (APIError with 204 status).")
                return ArchiveSuccessResponse(message="Customer archived successfully.")
            self._main_client.logger.error(f"API error during async archive customer {customerId}: {e}")
            raise
