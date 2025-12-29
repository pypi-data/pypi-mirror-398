# kelviq_sdk/checkout.py

import datetime
from typing import TYPE_CHECKING, Dict, Any, Optional, List

# Import SDK constants (if any specific to checkout, or general ones like BEHAVIOUR_CHOICES if reused)
# from .constants import ...

# Import Pydantic models from the models sub-package
from .models.checkout import (
    CreateCheckoutSessionPayload,
    CreateCheckoutSessionResponse,
    ChargePeriod,  # For type hinting the chargePeriod parameter
    FeatureListItem  # For type hinting features parameter
)
# Import SDK exceptions for re-raising validation errors
from .exceptions import InvalidRequestError
from pydantic import ValidationError

if TYPE_CHECKING:
    from .client import Kelviq  # Main client class

# Define the base path for checkout-related endpoints.
CHECKOUT_MODULE_PREFIX = "/checkout"


class CheckoutSyncOperations:
    """
    Handles synchronous 'checkout' related API operations.
    """

    def __init__(self, main_client: 'Kelviq'):
        self._main_client = main_client
        self._main_client.logger.debug("CheckoutSyncOperations initialized.")

    def create_session(
            self,
            planIdentifier: str,
            chargePeriod: ChargePeriod,
            pricingTableId: Optional[str] = None,
            ruleId: Optional[str] = None,
            customerId: Optional[str] = None,
            features: Optional[List[FeatureListItem]] = None,
            offeringId: Optional[str] = None,
            successUrl: Optional[str] = None,
            ipAddress: Optional[str] = None,
    ) -> CreateCheckoutSessionResponse:
        """
        Creates a new checkout session synchronously.
        The API endpoint is assumed to be POST /api/{version}/checkout/
        """
        endpoint_module_path = f"{CHECKOUT_MODULE_PREFIX}/"  # POST to /checkout/

        logger = self._main_client.logger  # Use client's logger
        logger.info(
            f"Initiating synchronous create_checkout_session for customerId: {customerId}, pricingTableId: {pricingTableId}"
        )

        try:
            payload_model = CreateCheckoutSessionPayload(
                offeringId=offeringId,
                planIdentifier=planIdentifier,
                pricingTableId=pricingTableId,
                ruleId=ruleId,
                chargePeriod=chargePeriod,
                customerId=customerId,
                features=features,
                successUrl=successUrl,
                ipAddress=ipAddress
            )
            logger.debug(
                f"Create checkout session payload validated: {payload_model.model_dump_json(exclude_none=True)}")
        except ValidationError as e:
            logger.warning(
                f"Pydantic validation failed for create_checkout_session. CustomerId: {customerId}, "
                f"pricingTableId: {pricingTableId}, Errors: {e.errors(include_context=False)}"
            )
            raise InvalidRequestError(
                message="Invalid parameters for create_checkout_session",
                details=e.errors(include_context=False)
            ) from e

        request_data = payload_model.model_dump(exclude_none=True)

        response_dict = self._main_client._request(
            method="POST",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return CreateCheckoutSessionResponse.model_validate(response_dict)


class CheckoutAsyncOperations:
    """
    Handles asynchronous 'checkout' related API operations.
    """

    def __init__(self, main_client: 'Kelviq'):
        self._main_client = main_client
        self._main_client.logger.debug("CheckoutAsyncOperations initialized.")

    async def create_session(
            self,
            planIdentifier: str,
            chargePeriod: ChargePeriod,
            pricingTableId: Optional[str] = None,
            ruleId: Optional[str] = None,
            customerId: Optional[str] = None,
            features: Optional[List[FeatureListItem]] = None,
            offeringId: Optional[str] = None,
            successUrl: Optional[str] = None,
            ipAddress: Optional[str] = None,
    ) -> CreateCheckoutSessionResponse:
        """
        Creates a new checkout session asynchronously.
        The API endpoint is assumed to be POST /api/{version}/checkout/
        """
        endpoint_module_path = f"{CHECKOUT_MODULE_PREFIX}/"  # POST to /checkout/

        logger = self._main_client.logger
        logger.info(
            f"Initiating asynchronous create_checkout_session for customerId: {customerId}, pricingTableId: {pricingTableId}"
        )

        try:
            payload_model = CreateCheckoutSessionPayload(
                offeringId=offeringId,
                planIdentifier=planIdentifier,
                pricingTableId=pricingTableId,
                ruleId=ruleId,
                chargePeriod=chargePeriod,
                customerId=customerId,
                features=features,
                successUrl=successUrl,
                ipAddress=ipAddress
            )
            logger.debug(
                f"Create async checkout session payload validated: {payload_model.model_dump_json(exclude_none=True)}")
        except ValidationError as e:
            logger.warning(
                f"Pydantic validation failed for async create_checkout_session. CustomerId: {customerId}, "
                f"pricingTableId: {pricingTableId}, Errors: {e.errors(include_context=False)}"
            )
            raise InvalidRequestError(
                message="Invalid parameters for async create_checkout_session",
                details=e.errors(include_context=False)
            ) from e

        request_data = payload_model.model_dump(exclude_none=True)

        response_dict = await self._main_client._async_request(
            method="POST",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return CreateCheckoutSessionResponse.model_validate(response_dict)
