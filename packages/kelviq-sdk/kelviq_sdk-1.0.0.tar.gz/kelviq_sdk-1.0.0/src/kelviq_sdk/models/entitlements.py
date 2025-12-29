# kelviq_sdk/models/entitlements.py
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
import datetime  # For potential datetime parsing if resetAt were a datetime object

# Define allowed feature types if they are known and limited


class CheckEntitlementsPayload(BaseModel):
    """
    Payload for checking customer entitlements.
    """
    customerId: str = Field(..., description="The ID of the customer whose entitlements are being checked.")
    featureId: Optional[str] = Field(None, description="Optional. A specific feature ID to check entitlements for.")

    model_config = ConfigDict(extra='forbid')


class EntitlementDetail(BaseModel):
    """
    Represents a single entitlement for a feature.
    """
    featureId: str = Field(..., description="The ID of the feature.")
    featureType: Optional[str] = Field(None, description="The type of the feature (e.g., METER, BOOLEAN, LIMIT).")
    hasAccess: bool = Field(..., description="Whether the customer has access to this feature.")
    resetAt: Optional[str] = Field(None,
                         description="Timestamp indicating when the usage for this feature resets. Null if not applicable.")  # Assuming it might be a datetime or null
    hardLimit: Optional[bool] = Field(None, description="Indicates if the usage limit is a hard limit.")
    usageLimit: Optional[int] = Field(None,
                                        description="The configured usage limit for the feature. Null if not applicable (e.g., for BOOLEAN features).")  # Changed to float to accommodate potential non-integer limits
    currentUsage: Optional[int] = Field(None,
                                          description="The current usage recorded for the feature. Null if not applicable.")  # Changed to float
    remaining: Optional[int] = Field(None,
                                       description="The remaining usage allowed for the feature. Null if not applicable.")  # Changed to float

    model_config = ConfigDict(
        extra='ignore',  # Be flexible with extra fields from server
        use_enum_values=True  # If FeatureType were a proper Enum
    )


class CheckEntitlementsResponse(BaseModel):
    """
    Response for the check entitlements operation.
    """
    customerId: str = Field(..., description="The ID of the customer.")
    entitlements: List[EntitlementDetail] = Field(..., description="A list of entitlements for the customer.")

    model_config = ConfigDict(extra='ignore')
