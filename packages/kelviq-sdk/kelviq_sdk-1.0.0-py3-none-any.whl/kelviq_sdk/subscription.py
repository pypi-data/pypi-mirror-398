# kelviq_sdk/subscription.py

from typing import TYPE_CHECKING, Dict, Any, Optional, List

# Import the SDK's logger
from . import logger

# Import SDK constants (if any specific base URL needed, though this module uses default)
# from .constants import ...

# Import Pydantic models
from .models.subscription import (
    CancelSubscriptionPayload,
    CancelSubscriptionResponse,
    CancellationType,
    UpdateSubscriptionPayload,  # New
    UpdateSubscriptionResponse,  # New
    ChargePeriod  # For type hinting
)
# Assuming FeatureListItem is correctly imported/defined within models.subscription or models.checkout
# and then re-exported by models/__init__.py for UpdateSubscriptionPayload to use.
# If FeatureListItem is from models.checkout:
from .models.checkout import FeatureListItem

# Import SDK exceptions
from .exceptions import InvalidRequestError
from pydantic import ValidationError

if TYPE_CHECKING:
    from .client import Kelviq  # Main client class

# Define the module-specific path prefix for subscription endpoints
SUBSCRIPTION_MODULE_PREFIX = "/subscriptions"


class SubscriptionSyncOperations:
    """
    Handles synchronous 'subscription' related API operations.
    """

    def __init__(self, main_client: 'Kelviq'):
        self._main_client = main_client
        self._main_client.logger.debug("SubscriptionSyncOperations initialized.")

    def cancel(
            self,
            subscriptionId: str,
            cancellationType: CancellationType,
            cancellationDate: Optional[str] = None
    ) -> CancelSubscriptionResponse:
        """
        Cancels a subscription, synchronously.
        API endpoint: POST /api/{version}/subscription/{subscription_id}/cancel
        """
        endpoint_module_path = f"{SUBSCRIPTION_MODULE_PREFIX}/{subscriptionId}/cancel/"

        self._main_client.logger.info(
            f"Initiating synchronous subscription cancellation for subscriptionId: {subscriptionId}, type: {cancellationType}"
        )

        try:
            payload_model = CancelSubscriptionPayload(
                cancellationType=cancellationType,  # Pydantic model expects camelCase
                cancellationDate=cancellationDate  # Pydantic model expects camelCase
            )
            self._main_client.logger.debug(
                f"Cancel subscription payload validated: {payload_model.model_dump_json(exclude_none=True, by_alias=True)}")
        except ValidationError as e:
            self._main_client.logger.warning(
                f"Pydantic validation failed for subscription cancellation. SubscriptionId: {subscriptionId}, "
                f"Errors: {e.errors(include_context=False)}"
            )
            raise InvalidRequestError(
                message="Invalid parameters for subscription cancellation",
                details=e.errors(include_context=False)
            ) from e

        request_data = payload_model.model_dump(exclude_none=True, by_alias=True)

        response_dict = self._main_client._request(
            method="POST",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return CancelSubscriptionResponse.model_validate(response_dict)

    def update(
            self,
            subscriptionId: str,
            planIdentifier: str,
            chargePeriod: ChargePeriod,
            probationBehaviour: Optional[str] = None,
            offeringId: Optional[str] = None,
            pricingTableId: Optional[str] = None,
            ruleId: Optional[str] = None,
            ipAddress: Optional[str] = None,
            features: Optional[List[Dict[str, Any]]] = None,
            # User provides list of dicts like [{"identifier": "seats", "quantity": 5}]
    ) -> UpdateSubscriptionResponse:
        """
        Updates an existing subscription, synchronously.
        API endpoint: POST /api/{version}/subscription/{subscription_id}/update/
        """
        endpoint_module_path = f"{SUBSCRIPTION_MODULE_PREFIX}/{subscriptionId}/update/"

        self._main_client.logger.info(
            f"Initiating synchronous subscription update for subscriptionId: {subscriptionId}"
        )

        try:
            # The Pydantic model UpdateSubscriptionPayload expects camelCase for its fields
            # but will serialize to snake_case for the API due to aliases.
            payload_model = UpdateSubscriptionPayload(
                planIdentifier=planIdentifier,
                chargePeriod=chargePeriod,
                probationBehaviour=probationBehaviour,
                offeringId=offeringId,
                pricingTableId=pricingTableId,
                ruleId=ruleId,
                ipAddress=ipAddress,
                features=features  # Pydantic will validate this list of dicts against List[FeatureListItem]
            )
            self._main_client.logger.debug(
                f"Update subscription payload validated: {payload_model.model_dump_json(exclude_none=True, by_alias=True)}")
        except ValidationError as e:
            self._main_client.logger.warning(
                f"Pydantic validation failed for subscription update. SubscriptionId: {subscriptionId}, "
                f"Errors: {e.errors(include_context=False)}"
            )
            raise InvalidRequestError(
                message="Invalid parameters for subscription update",
                details=e.errors(include_context=False)
            ) from e

        request_data = payload_model.model_dump(exclude_none=True, by_alias=True)

        response_dict = self._main_client._request(
            method="POST",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return UpdateSubscriptionResponse.model_validate(response_dict)


class SubscriptionAsyncOperations:
    """
    Handles asynchronous 'subscription' related API operations.
    """

    def __init__(self, main_client: 'Kelviq'):
        self._main_client = main_client
        self._main_client.logger.debug("SubscriptionAsyncOperations initialized.")

    async def cancel(
            self,
            subscriptionId: str,
            cancellationType: CancellationType,
            cancellationDate: Optional[str] = None
    ) -> CancelSubscriptionResponse:
        """
        Cancels a subscription, asynchronously.
        API endpoint: POST /api/{version}/subscription/{subscription_id}/cancel
        """
        endpoint_module_path = f"{SUBSCRIPTION_MODULE_PREFIX}/{subscriptionId}/cancel/"

        self._main_client.logger.info(
            f"Initiating asynchronous subscription cancellation for subscriptionId: {subscriptionId}, type: {cancellationType}"
        )

        try:
            payload_model = CancelSubscriptionPayload(
                cancellationType=cancellationType,
                cancellationDate=cancellationDate
            )
            self._main_client.logger.debug(
                f"Async cancel subscription payload validated: {payload_model.model_dump_json(exclude_none=True, by_alias=True)}")
        except ValidationError as e:
            self._main_client.logger.warning(
                f"Pydantic validation failed for async subscription cancellation. SubscriptionId: {subscriptionId}, "
                f"Errors: {e.errors(include_context=False)}"
            )
            raise InvalidRequestError(
                message="Invalid parameters for async subscription cancellation",
                details=e.errors(include_context=False)
            ) from e

        request_data = payload_model.model_dump(exclude_none=True, by_alias=True)

        response_dict = await self._main_client._async_request(
            method="POST",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return CancelSubscriptionResponse.model_validate(response_dict)

    async def update(
            self,
            subscriptionId: str,
            planIdentifier: str,
            chargePeriod: ChargePeriod,
            probationBehaviour: Optional[str] = None,
            offeringId: Optional[str] = None,
            pricingTableId: Optional[str] = None,
            ruleId: Optional[str] = None,
            ipAddress: Optional[str] = None,
            features: Optional[List[Dict[str, Any]]] = None,  # User provides list of dicts
    ) -> UpdateSubscriptionResponse:
        """
        Updates an existing subscription, asynchronously.
        API endpoint: POST /api/{version}/subscription/{subscription_id}/update/
        """
        endpoint_module_path = f"{SUBSCRIPTION_MODULE_PREFIX}/{subscriptionId}/update/"

        self._main_client.logger.info(
            f"Initiating asynchronous subscription update for subscriptionId: {subscriptionId}"
        )

        try:
            payload_model = UpdateSubscriptionPayload(
                planIdentifier=planIdentifier,
                chargePeriod=chargePeriod,
                probationBehaviour=probationBehaviour,
                offeringId=offeringId,
                pricingTableId=pricingTableId,
                ruleId=ruleId,
                ipAddress=ipAddress,
                features=features
            )
            self._main_client.logger.debug(
                f"Async update subscription payload validated: {payload_model.model_dump_json(exclude_none=True, by_alias=True)}")
        except ValidationError as e:
            self._main_client.logger.warning(  # Corrected to use self._main_client.logger
                f"Pydantic validation failed for async subscription update. SubscriptionId: {subscriptionId}, "
                f"Errors: {e.errors(include_context=False)}"
            )
            raise InvalidRequestError(
                message="Invalid parameters for async subscription update",
                details=e.errors(include_context=False)
            ) from e

        request_data = payload_model.model_dump(exclude_none=True, by_alias=True)

        response_dict = await self._main_client._async_request(
            method="POST",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return UpdateSubscriptionResponse.model_validate(response_dict)
