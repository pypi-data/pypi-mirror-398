# kelviq_sdk/models/checkout.py
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict
import datetime

# Define allowed charge periods
ChargePeriod = Literal[
    "ONE_TIME", "MONTHLY", "YEARLY", "WEEKLY", "DAILY", "THREE_MONTHS", "SIX_MONTHS"
]

# Define the structure for items in features
class FeatureListItem(BaseModel):
    """
    Represents a single feature item with its ID and quantity.
    """
    identifier: str = Field(..., description="The identifier of the feature.")
    quantity: int = Field(..., description="The quantity of the feature.")


class CreateCheckoutSessionPayload(BaseModel):
    """
    Pydantic model for the payload to create a checkout session.
    """
    offeringId: Optional[str] = Field(
        None,
        description="ID of the offering. This is optional if planIdentifier is provided."
    )
    planIdentifier: str = Field(
        ...,
        description="Identifier of the plan. This field is mandatory."
    )
    pricingTableId: Optional[str] = Field(None, description="ID of the pricingTable. This field is optional.")
    ipAddress: Optional[str] = Field(None, description="IP Address of the customer.")
    ruleId: Optional[str] = Field(None, description="ID of the rule. This field is optional.")
    chargePeriod: ChargePeriod = Field(..., description="The charging period for the subscription.")
    customerId: Optional[str] = Field(None, description="ID of the customer initiating the checkout. This field is optional.")
    features: Optional[List[FeatureListItem]] = Field(
        None,
        description="List of features and their quantities. E.g., [{'id': 'seats', 'quantity': 10}]. This field is optional."
    )
    successUrl: str = Field(
        None,
        description="URL to redirect to after successful checkout. Defaults to UI if called from UI."
    )

    model_config = ConfigDict(
        extra='forbid',  # Disallow extra fields not defined in the model
        use_enum_values=True  # This is relevant if ChargePeriod were an Enum, less so for Literal[str]
    )


class CreateCheckoutSessionResponse(BaseModel):
    """
    Pydantic model for the response when a checkout session is created.
    This is an example; adjust based on your actual API response.
    """
    checkoutSessionId: str = Field(..., description="The ID of the created checkout session.")
    checkoutUrl: str = Field(..., description="The URL for the customer to complete the checkout.")

    model_config = ConfigDict(
        extra='ignore'  # Or 'forbid' if you want strict response validation
    )

