# kelviq_sdk/models/customers.py
import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


# Assuming BaseResponse might be defined in models.reporting or a common models.base
# If not, define it here or adjust import. For now, let's assume it's not strictly needed for Customer models.
# from .reporting import BaseResponse # Example if BaseResponse is shared

class CustomerBase(BaseModel):
    """Base model for customer fields, used for request payloads."""
    name: Optional[str] = Field(None, description="Name of the customer.")
    email: Optional[str] = Field(..., description="Email address of the customer.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the customer.")

    model_config = ConfigDict(
        populate_by_name=True,  # Important for aliases to work during serialization
        extra='ignore'  # Allow extra fields from server in response, but payload is stricter
    )


class CustomerCreatePayload(CustomerBase):
    """
    Payload for creating a new customer.
    Corresponds to CustomerSerializer.
    """
    customerId: str = Field(..., alias="customer_id", min_length=1,
                            description="Unique identifier for the customer, provided by the client.")

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid'  # Be strict for creation payload
    )


class CustomerUpdatePayload(BaseModel):
    """
    Payload for updating an existing customer.
    Corresponds to CustomerUpdateSerializer (PATCH).
    customerId is read-only and not part of the update payload.
    """
    name: Optional[str] = Field(None, description="New name of the customer.")
    email: Optional[str] = Field(None,
                                      description="New email address of the customer. Required by API if updating.")  # API requires it, but PATCH can be partial
    metadata: Optional[Dict[str, Any]] = Field(None, description="New metadata for the customer.")

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid'  # Be strict for update payload
    )


class CustomerResponse(CustomerBase):
    """
    Pydantic model representing a customer object as returned by the API.
    """
    id: str = Field(..., description="Internal database ID (UUID) of the customer.")  # Usually UUID
    customerId: str = Field(..., alias="customer_id", description="Client-defined unique identifier for the customer.")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details about the customer (read-only).")
    createdOn: datetime.datetime = Field(..., alias="created_on",
                                         description="Timestamp of when the customer was created.")
    modifiedOn: datetime.datetime = Field(..., alias="modified_on",
                                          description="Timestamp of when the customer was last modified.")

    model_config = ConfigDict(
        populate_by_name=True,  # Allows Pydantic to use aliases for deserialization
        extra='ignore'  # Be flexible with extra fields from server response
    )


class PaginatedCustomerResponse(BaseModel):
    """
    Pydantic model for a paginated list of customers.
    Matches DRF's default pagination structure (or your custom one).
    """
    count: int = Field(..., description="Total number of customers.")
    next: Optional[str] = Field(None, description="URL for the next page of results, if any.")
    previous: Optional[str] = Field(None, description="URL for the previous page of results, if any.")
    results: List[CustomerResponse] = Field(..., description="List of customer objects on the current page.")

    model_config = ConfigDict(
        populate_by_name=True,
        extra='ignore'
    )


class ArchiveSuccessResponse(BaseModel):
    """
    Response for a successful archive (delete) operation.
    """
    message: str = Field(..., description="Confirmation message.")

    model_config = ConfigDict(
        populate_by_name=True,
        extra='ignore'
    )
