# kelviq_sdk/reporting.py

import datetime
from typing import TYPE_CHECKING, Dict, Any, Optional

# Import SDK constants
from .constants import BEHAVIOUR_CHOICES

# Import Pydantic models from the models sub-package
from .models.reporting import (
    ReportUsagePayload,
    ReportUsageResponse,
    ReportEventPayload,
    ReportEventResponse
)
# Import SDK exceptions for re-raising validation errors
from .exceptions import InvalidRequestError
from pydantic import ValidationError  # To catch Pydantic's specific validation error

if TYPE_CHECKING:
    from .client import Kelviq  # Main client class

# Define the base path for reporting-related endpoints.
REPORT_MODULE_PREFIX = "/report"


class ReportingSyncOperations:
    """
    Handles synchronous 'reporting' related API operations.
    """

    def __init__(self, main_client: 'Kelviq'):
        self._main_client = main_client
        self._main_client.logger.debug("ReportingSyncOperations initialized.")

    def report_usage(
            self,
            value: int,
            customerId: str,
            featureId: str,
            behaviour: BEHAVIOUR_CHOICES,  # Use the Literal type for better static analysis
            resourceId: Optional[str] = None
    ) -> ReportUsageResponse:
        """
        Reports usage information to the API synchronously.
        """
        logger = self._main_client.logger
        logger.info(
            f"Initiating synchronous report_usage for customerId: {customerId}, featureId: {featureId}"
        )
        endpoint_module_path = f"{REPORT_MODULE_PREFIX}/usage/"

        try:
            payload_model = ReportUsagePayload(
                value=value,
                customerId=customerId,
                featureId=featureId,
                behaviour=behaviour,
                resourceId=resourceId
            )
            # Log the validated payload (be mindful of sensitive data in real-world scenarios)
            # Using model_dump_json to get a string representation for logging.
            logger.debug(f"Validated report_usage payload: {payload_model.model_dump_json(exclude_none=True)}")
        except ValidationError as e:
            logger.warning(
                f"Pydantic validation failed for report_usage. CustomerId: {customerId}, "
                f"FeatureId: {featureId}, Errors: {e.errors(include_context=False)}"
            )
            # Re-raise as the SDK's custom exception
            raise InvalidRequestError(
                message=f"Invalid parameters for report_usage",
                details=e.errors(include_context=False)
            ) from e

        request_data = payload_model.model_dump(exclude_none=True)

        response_dict = self._main_client._request(
            method="POST",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return ReportUsageResponse.model_validate(response_dict)

    def report_event(
            self,
            customerId: str,
            eventName: str,
            idempotencyKey: str,
            timestamp: str,  # Accepts string directly
            resourceId: Optional[str] = None,
            properties: Optional[Dict[str, Any]] = None
    ) -> ReportEventResponse:
        """
        Reports an event to the API synchronously.
        The `timestamp` should be a string in "YYYY-MM-DD HH:MM:SS.ffffff" format.
        """
        logger = self._main_client.logger
        logger.debug(
            f"Initiating synchronous report_event for customerId: {customerId}, eventName: {eventName}"
        )
        endpoint_module_path = f"{REPORT_MODULE_PREFIX}/event/"

        try:
            payload_model = ReportEventPayload(
                customerId=customerId,     # Pass camelCase
                eventName=eventName,       # Pass camelCase
                idempotencyKey=idempotencyKey, # Pass camelCase
                timestamp=timestamp,
                resourceId=resourceId,   # Pass camelCase
                properties=properties
            )
            logger.debug(f"Validated report_event payload: {payload_model.model_dump_json(exclude_none=True)}")
        except ValidationError as e:
            logger.warning(
                f"Pydantic validation failed for report_event. CustomerId: {customerId}, "
                f"EventName: {eventName}, Errors: {e.errors(include_context=False)}"
            )
            raise InvalidRequestError(
                message=f"Invalid parameters for report_event",
                details=e.errors(include_context=False)
            ) from e

        request_data = payload_model.model_dump(exclude_none=True)

        response_dict = self._main_client._request(
            method="POST",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return ReportEventResponse.model_validate(response_dict)


class ReportingAsyncOperations:
    """
    Handles asynchronous 'reporting' related API operations.
    """

    def __init__(self, main_client: 'Kelviq'):
        self._main_client = main_client
        self._main_client.logger.debug("ReportingAsyncOperations initialized.")

    async def report_usage(
            self,
            value: int,
            customerId: str,
            featureId: str,
            behaviour: BEHAVIOUR_CHOICES,
            resourceId: Optional[str] = None
    ) -> ReportUsageResponse:
        """
        Reports usage information to the API asynchronously.
        """
        logger = self._main_client.logger
        logger.debug(
            f"Initiating asynchronous report_usage for customerId: {customerId}, featureId: {featureId}"
        )
        endpoint_module_path = f"{REPORT_MODULE_PREFIX}/usage/"

        try:
            payload_model = ReportUsagePayload(
                value=value,
                customerId=customerId,
                featureId=featureId,
                behaviour=behaviour,
                resourceId=resourceId
            )
            logger.debug(f"Validated async report_usage payload: {payload_model.model_dump_json(exclude_none=True)}")
        except ValidationError as e:
            logger.warning(
                f"Pydantic validation failed for async report_usage. CustomerId: {customerId}, "
                f"FeatureId: {featureId}, Errors: {e.errors(include_context=False)}"
            )
            raise InvalidRequestError(
                message=f"Invalid parameters for async report_usage",
                details=e.errors(include_context=False)
            ) from e

        request_data = payload_model.model_dump(exclude_none=True)

        response_dict = await self._main_client._async_request(
            method="POST",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return ReportUsageResponse.model_validate(response_dict)

    async def report_event(
            self,
            customerId: str,
            eventName: str,
            idempotencyKey: str,
            timestamp: str,  # Accepts string directly
            resourceId: Optional[str] = None,
            properties: Optional[Dict[str, Any]] = None
    ) -> ReportEventResponse:
        """
        Reports an event to the API asynchronously.
        The `timestamp` should be a string in "YYYY-MM-DD HH:MM:SS.ffffff" format.
        """
        logger = self._main_client.logger
        logger.debug(
            f"Initiating asynchronous report_event for customerId: {customerId}, eventName: {eventName}"
        )
        endpoint_module_path = f"{REPORT_MODULE_PREFIX}/event/"

        try:
            payload_model = ReportEventPayload(
                customerId=customerId,
                eventName=eventName,
                idempotencyKey=idempotencyKey,
                timestamp=timestamp,  # Pass the string directly
                resourceId=resourceId,
                properties=properties
            )
            logger.debug(f"Validated async report_event payload: {payload_model.model_dump_json(exclude_none=True)}")
        except ValidationError as e:
            logger.warning(
                f"Pydantic validation failed for async report_event. CustomerId: {customerId}, "
                f"EventName: {eventName}, Errors: {e.errors(include_context=False)}"
            )
            raise InvalidRequestError(
                message=f"Invalid parameters for async report_event",
                details=e.errors(include_context=False)
            ) from e

        request_data = payload_model.model_dump(exclude_none=True)

        response_dict = await self._main_client._async_request(
            method="POST",
            endpoint_module_path=endpoint_module_path,
            data=request_data
        )
        return ReportEventResponse.model_validate(response_dict)
