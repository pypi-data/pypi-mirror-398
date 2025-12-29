# kelviq_sdk/models/subscription.py
from typing import Optional, List, Dict, Any, Literal as PyLiteral  # Renamed to avoid conflict
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import datetime


class FeatureListItem(BaseModel):  # Placeholder if not imported
    identifier: str = Field(..., description="The identifier of the feature.")
    quantity: int = Field(..., description="The quantity of the feature.")


CancellationType = PyLiteral["IMMEDIATE", "CURRENT_PERIOD_ENDS", "SPECIFIC_DATE"]
ChargePeriod = PyLiteral[
    "ONE_TIME", "MONTHLY", "YEARLY", "WEEKLY", "DAILY", "THREE_MONTHS", "SIX_MONTHS"]



class CancelSubscriptionPayload(BaseModel):
    cancellationType: CancellationType = Field(..., alias="cancellation_type", description="The type of cancellation.")
    cancellationDate: Optional[str] = Field(None, alias="cancellation_date",
                                            description="The specific date for cancellation if type is SPECIFIC_DATE, format YYYY-MM-DD.")

    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    @field_validator('cancellationDate')
    @classmethod
    def validate_cancellation_date_format(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            try:
                datetime.datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValueError("cancellationDate must be in YYYY-MM-DD format if provided.")
        return value

    @model_validator(mode='after')
    def check_cancellation_date_logic(cls, values):
        cancellation_type = values.cancellationType
        cancellation_date = values.cancellationDate
        if cancellation_type == "SPECIFIC_DATE" and cancellation_date is None:
            raise ValueError("cancellationDate is required when cancellationType is SPECIFIC_DATE.")
        return values


class CancelSubscriptionResponse(BaseModel):
    message: str = Field(..., description="Confirmation message for subscription cancellation.")
    model_config = ConfigDict(extra='ignore')


# --- New Models for Update Subscription ---
class UpdateSubscriptionPayload(BaseModel):
    """
    Pydantic model for the payload to update a subscription.
    Uses aliases to convert camelCase Python fields to snake_case for JSON.
    """
    planIdentifier: str = Field(..., alias="plan_identifier", description="The identifier of the new plan.")
    chargePeriod: ChargePeriod = Field(..., alias="charge_period",
                                       description="The new charging period for the subscription.")

    probationBehaviour: Optional[str] = Field(None, alias="probation_behaviour",
                                              description="Behavior for probation period, if applicable.")
    ipAddress: Optional[str] = Field(None, description="IP Address of the customer.")
    offeringId: Optional[str] = Field(None, alias="offering_id", description="Optional. ID of the new offering.")
    pricingTableId: Optional[str] = Field(None, alias="pricing_table_id", description="Optional. ID of the new pricingTable.")
    ruleId: Optional[str] = Field(None, alias="rule_id", description="Optional. ID of the new rule.")
    features: Optional[List[FeatureListItem]] = Field(None,
                                                      description="Optional. List of features and their quantities to update. E.g., [{'identifier': 'seats', 'quantity': 5}]")

    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True  # Crucial for aliases to work during serialization (model_dump with by_alias=True)
    )


class UpdateSubscriptionResponse(BaseModel):
    """
    Pydantic model for the response when a subscription is updated.
    """
    subscriptionId: str = Field(..., description="UUID of the updated subscription")

    model_config = ConfigDict(
        extra='ignore'
    )
