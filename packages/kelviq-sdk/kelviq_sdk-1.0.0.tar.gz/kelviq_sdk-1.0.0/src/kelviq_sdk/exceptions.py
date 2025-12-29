# kelviq_sdk/exceptions.py
import json
from typing import Optional, Any, List, Dict


class APIError(Exception):
    """Base class for API related errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details  # Can be a string, dict, or list of dicts (from Pydantic)

    def __str__(self):
        """
        Provides a standardized string representation of the APIError.
        If 'details' contains Pydantic validation errors, they are formatted for readability.
        """
        base_message = super().__str__()
        if self.status_code is not None:
            base_message = f"{base_message} (Status Code: {self.status_code})"

        if self.details is not None:
            details_str_parts = ["\nDetails:"]
            if isinstance(self.details, list) and all(isinstance(item, dict) for item in self.details):
                # Likely Pydantic e.errors() output
                for error_item in self.details:
                    loc_str = " -> ".join(map(str, error_item.get("loc", ())))
                    msg = error_item.get("msg", "Unknown validation error")
                    input_val = error_item.get("input", "N/A")
                    error_type = error_item.get("type", "N/A")

                    details_str_parts.append(
                        f"  - Field '{loc_str}': {msg} (Input: '{input_val}', Type: '{error_type}')"
                    )
            elif isinstance(self.details, dict):
                try:
                    details_str_parts.append(f"  {json.dumps(self.details, indent=2)}")
                except (TypeError, OverflowError):
                    details_str_parts.append(f"  {str(self.details)}")
            else:  # String or other type
                details_str_parts.append(f"  {str(self.details)}")

            base_message += "\n".join(details_str_parts)

        return base_message


class AuthenticationError(APIError):
    """
    Raised for authentication failures (e.g., 401 Unauthorized, 403 Forbidden).
    This could be due to an invalid, missing, or expired access token, or insufficient permissions.
    """
    def __init__(self, message: str = "Authentication failed. Please check your access token and permissions.",
                 status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message, status_code, details)


class InvalidRequestError(APIError):
    """
    Raised for client-side errors like invalid input (e.g., 400 Bad Request).
    The 'details' attribute often contains specific information about which fields were invalid.
    """
    def __init__(self, message: str = "The request was invalid or malformed. Please check the input parameters.",
                 status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message, status_code, details)


class ServerError(APIError):
    """
    Raised for server-side errors (e.g., 5xx status codes).
    This indicates an issue with the API server itself.
    """
    def __init__(self, message: str = "The API server encountered an internal error. Please try again later.",
                 status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message, status_code, details)


class NotFoundError(APIError):
    """
    Raised when a requested resource is not found (e.g., 404 Not Found).
    """
    def __init__(self, message: str = "The requested resource was not found.",
                 status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message, status_code, details)
