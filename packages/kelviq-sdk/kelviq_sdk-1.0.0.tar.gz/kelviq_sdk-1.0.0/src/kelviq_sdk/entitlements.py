# kelviq_sdk/entitlements.py

from typing import TYPE_CHECKING, Dict, Any, Optional, List

from . import logger, APIError

from .models.entitlements import (
    CheckEntitlementsPayload,
    CheckEntitlementsResponse
)
from .exceptions import InvalidRequestError
from pydantic import ValidationError

if TYPE_CHECKING:
    from .client import Kelviq  # Main client class

ENTITLEMENTS_MODULE_PREFIX = "/entitlements"


class EntitlementsSyncOperations:
    """
    Handles synchronous 'entitlements' related API operations.
    """

    def __init__(self, main_client: 'Kelviq'):
        self._main_client = main_client
        self._main_client.logger.debug("EntitlementsSyncOperations initialized.")

    def has_access(
            self,
            customerId: str,
            featureId: str
    ) -> bool:
        """
        Checks if a customer has access to a specific feature, synchronously.
        Returns True if access is granted, False otherwise.
        This operation targets the EDGE_API_URL.
        The endpoint is assumed to be POST /api/{version}/entitlements
        """

        query_params = {
            "customer_id": customerId,
            "feature_id": featureId
        }
        
        endpoint_module_path = f"{ENTITLEMENTS_MODULE_PREFIX}"

        self._main_client.logger.info(
            f"Initiating synchronous entitlements check (has_access) for customerId: {customerId}, featureId: {featureId}"
        )

        try:
            response_dict = self._main_client._request(
                method="GET",
                endpoint_module_path=endpoint_module_path,
                params=query_params,
                base_url_override=self._main_client.edge_api_url_to_use
            )
            response_model = CheckEntitlementsResponse.model_validate(response_dict)

            # Iterate through entitlements to find the specific feature
            for entitlement in response_model.entitlements:
                if entitlement.featureId == featureId:
                    status_to_return: bool

                    if entitlement.featureType == 'METER':
                        is_hard_limit_active = bool(entitlement.hardLimit)
                        no_usage_remaining = (entitlement.remaining is None or entitlement.remaining <= 0)

                        if is_hard_limit_active and no_usage_remaining:
                            status_to_return = False
                        else:
                            status_to_return = True
                    else:
                        status_to_return = entitlement.hasAccess

                    self._main_client.logger.info(
                        f"Access check for customerId: {customerId}, featureId: {featureId} - Result: {status_to_return}"
                    )
                    return status_to_return

            # If the featureId is not found in the entitlements list, assume no access
            self._main_client.logger.warning(
                f"FeatureId '{featureId}' not found in entitlements response for customerId: {customerId}. Returning hasAccess=False.")
            return False

        except APIError as e:  # Catch APIError to log and re-raise or handle
            self._main_client.logger.error(
                f"API error during has_access check for customerId: {customerId}, featureId: {featureId}: {e}")
            # Depending on desired behavior, you might return False on API error or re-raise.
            # For a simple "has_access", returning False on error might be acceptable if the API guarantees
            # a positive confirmation for access. Otherwise, re-raising is safer.
            # For now, let's re-raise to make API issues explicit to the caller.
            raise

    def get_entitlement(
            self,
            customerId: str,
            featureId: str
    ) -> CheckEntitlementsResponse:
        """
        Checks if a customer has access to a specific feature, synchronously.
        This operation targets the EDGE_API_URL.
        The endpoint is assumed to be POST /api/{version}/entitlements
        """
        # The specific path for this operation within the entitlements module
        
        endpoint_module_path = f"{ENTITLEMENTS_MODULE_PREFIX}"

        self._main_client.logger.info(
            f"Initiating synchronous entitlements check (has_access) for customerId: {customerId}, featureId: {featureId}"
        )
        query_params = {
            "customer_id": customerId,
            "feature_id": featureId
        }

        response_dict = self._main_client._request(
            method="GET",
            endpoint_module_path=endpoint_module_path,
            params=query_params,
            base_url_override=self._main_client.edge_api_url_to_use
        )
        # Assuming CheckEntitlementsResponse can also represent the response for a single feature check.
        # If the response structure is very different, a new Pydantic model would be needed.
        return CheckEntitlementsResponse.model_validate(response_dict)

    def get_all_entitlements(
            self,
            customerId: str
    ) -> CheckEntitlementsResponse:
        """
        Retrieves all entitlements for a given customer, synchronously.
        This operation targets the EDGE_API_URL.
        The endpoint is assumed to be POST /api/{version}/entitlements
        (payload with only customerId, and featureId being None or omitted).
        """
          # Assuming same endpoint, backend differentiates by payload
        endpoint_module_path = f"{ENTITLEMENTS_MODULE_PREFIX}"

        query_params = {
            "customer_id": customerId
        }

        self._main_client.logger.info(
            f"Initiating synchronous get_entitlements for customerId: {customerId}"
        )

        response_dict = self._main_client._request(
            method="GET",
            endpoint_module_path=endpoint_module_path,
            params=query_params,
            base_url_override=self._main_client.edge_api_url_to_use
        )
        return CheckEntitlementsResponse.model_validate(response_dict)


class EntitlementsAsyncOperations:
    """
    Handles asynchronous 'entitlements' related API operations.
    """

    def __init__(self, main_client: 'Kelviq'):
        self._main_client = main_client
        self._main_client.logger.debug("EntitlementsAsyncOperations initialized.")

    async def has_access(
            self,
            customerId: str,
            featureId: str
    ) -> bool:
        """
        Checks if a customer has access to a specific feature, synchronously.
        Returns True if access is granted, False otherwise.
        This operation targets the EDGE_API_URL.
        The endpoint is assumed to be POST /api/{version}/entitlements
        """

        query_params = {
            "customer_id": customerId,
            "feature_id": featureId
        }

        endpoint_module_path = f"{ENTITLEMENTS_MODULE_PREFIX}"

        self._main_client.logger.info(
            f"Initiating synchronous entitlements check (has_access) for customerId: {customerId}, featureId: {featureId}"
        )

        try:
            response_dict = await self._main_client._async_request(
                method="GET",
                endpoint_module_path=endpoint_module_path,
                params=query_params,
                base_url_override=self._main_client.edge_api_url_to_use
            )
            response_model = CheckEntitlementsResponse.model_validate(response_dict)

            # Iterate through entitlements to find the specific feature
            for entitlement in response_model.entitlements:
                if entitlement.featureId == featureId:
                    status_to_return: bool

                    if entitlement.featureType == 'METER':
                        is_hard_limit_active = bool(entitlement.hardLimit)
                        no_usage_remaining = (entitlement.remaining is None or entitlement.remaining <= 0)

                        if is_hard_limit_active and no_usage_remaining:
                            status_to_return = False
                        else:
                            status_to_return = True
                    else:
                        status_to_return = entitlement.hasAccess

                    self._main_client.logger.info(
                        f"Access check for customerId: {customerId}, featureId: {featureId} - Result: {status_to_return}"
                    )
                    return status_to_return

            # If the featureId is not found in the entitlements list, assume no access
            self._main_client.logger.warning(
                f"FeatureId '{featureId}' not found in entitlements response for customerId: {customerId}. Returning hasAccess=False.")
            return False

        except APIError as e:  # Catch APIError to log and re-raise or handle
            self._main_client.logger.error(
                f"API error during has_access check for customerId: {customerId}, featureId: {featureId}: {e}")
            # Depending on desired behavior, you might return False on API error or re-raise.
            # For a simple "has_access", returning False on error might be acceptable if the API guarantees
            # a positive confirmation for access. Otherwise, re-raising is safer.
            # For now, let's re-raise to make API issues explicit to the caller.
            raise

    async def get_entitlement(
            self,
            customerId: str,
            featureId: str
    ) -> CheckEntitlementsResponse:
        """
        Checks if a customer has access to a specific feature, asynchronously.
        This operation targets the EDGE_API_URL.
        The endpoint is assumed to be POST /api/{version}/entitlements
        """
        
        endpoint_module_path = f"{ENTITLEMENTS_MODULE_PREFIX}"

        self._main_client.logger.info(
            f"Initiating asynchronous entitlements check (has_access) for customerId: {customerId}, featureId: {featureId}"
        )

        query_params = {
            "customer_id": customerId,
            "feature_id": featureId
        }

        response_dict = await self._main_client._async_request(
            method="GET",
            endpoint_module_path=endpoint_module_path,
            params=query_params,
            base_url_override=self._main_client.edge_api_url_to_use  # Using EDGE_API_URL
        )
        return CheckEntitlementsResponse.model_validate(response_dict)

    async def get_all_entitlements(
            self,
            customerId: str
    ) -> CheckEntitlementsResponse:
        """
        Retrieves all entitlements for a given customer, asynchronously.
        This operation targets the EDGE_API_URL.
        The endpoint is assumed to be POST /api/{version}/entitlements
        (payload with only customerId, and featureId being None or omitted).
        """
        
        endpoint_module_path = f"{ENTITLEMENTS_MODULE_PREFIX}"

        self._main_client.logger.info(
            f"Initiating asynchronous get_entitlements for customerId: {customerId}"
        )

        query_params = {
            "customer_id": customerId
        }

        response_dict = await self._main_client._async_request(
            method="GET",
            endpoint_module_path=endpoint_module_path,
            params=query_params,
            base_url_override=self._main_client.edge_api_url_to_use
        )
        return CheckEntitlementsResponse.model_validate(response_dict)
