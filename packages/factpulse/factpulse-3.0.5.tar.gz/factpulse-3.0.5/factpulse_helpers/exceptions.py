"""Custom exceptions for the FactPulse client.

This module defines an exception hierarchy aligned with the FactPulse API error format
(APIError, ValidationErrorDetail) compliant with AFNOR XP Z12-013 standard.

Exception hierarchy:
- FactPulseError (base)
  ├── FactPulseAuthError (401)
  ├── FactPulseValidationError (400, 422) - with structured details
  ├── FactPulsePollingTimeout (polling timeout)
  ├── FactPulseNotFoundError (404)
  ├── FactPulseServiceUnavailableError (503)
  └── FactPulseAPIError (generic with error_code)
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class FactPulseError(Exception):
    """Base class for all FactPulse errors."""
    pass


class FactPulseAuthError(FactPulseError):
    """FactPulse authentication error (401).

    Raised when:
    - Invalid email/password
    - Expired or invalid JWT token
    - client_uid not found
    """
    def __init__(self, message: str = "Authentication required"):
        self.message = message
        super().__init__(message)


class FactPulsePollingTimeout(FactPulseError):
    """Timeout while polling an asynchronous task."""
    def __init__(self, task_id: str, timeout: int):
        self.task_id = task_id
        self.timeout = timeout
        super().__init__(f"Timeout ({timeout}ms) reached for task {task_id}")


@dataclass
class ValidationErrorDetail:
    """Validation error detail in AFNOR format.

    Aligned with the AcknowledgementDetail schema from AFNOR XP Z12-013 standard.

    Attributes:
        level: Severity level ('Error' or 'Warning')
        item: Identifier of the affected element (BR-FR rule, field, XPath)
        reason: Error description
        source: Error source (schematron, pydantic, pdfa, afnor, chorus_pro)
        code: Unique error code (e.g., SCHEMATRON_BR_FR_01)
    """
    level: str = ""
    item: str = ""
    reason: str = ""
    source: Optional[str] = None
    code: Optional[str] = None

    def __str__(self) -> str:
        item = self.item or "unknown"
        reason = self.reason or "Unknown error"
        source_str = f" [{self.source}]" if self.source else ""
        return f"[{item}]{source_str} {reason}"


class FactPulseValidationError(FactPulseError):
    """Validation error with structured details (400, 422).

    Contains a list of ValidationErrorDetail for diagnostics.

    Attributes:
        errors: List of detailed errors
        error_code: API error code (e.g., VALIDATION_FAILED, SCHEMATRON_VALIDATION_FAILED)
    """
    def __init__(
        self,
        message: str,
        errors: Optional[List[ValidationErrorDetail]] = None,
        error_code: str = "VALIDATION_FAILED",
    ):
        self.errors = errors or []
        self.error_code = error_code
        if self.errors:
            details = "\n".join(f"  - {e}" for e in self.errors)
            message = f"{message}\n\nDetails:\n{details}"
        super().__init__(message)


class FactPulseNotFoundError(FactPulseError):
    """Resource not found (404).

    Attributes:
        resource: Resource type (invoice, structure, flow, client)
        identifier: Resource identifier
    """
    def __init__(self, resource: str, identifier: str = ""):
        self.resource = resource
        self.identifier = identifier
        message = f"{resource.capitalize()} not found"
        if identifier:
            message = f"{resource.capitalize()} '{identifier}' not found"
        super().__init__(message)


class FactPulseServiceUnavailableError(FactPulseError):
    """External service unavailable (503).

    Attributes:
        service_name: Service name (AFNOR PDP, Chorus Pro, Django)
        original_error: Original exception (optional)
    """
    def __init__(self, service_name: str, original_error: Optional[Exception] = None):
        self.service_name = service_name
        self.original_error = original_error
        message = f"Service {service_name} is unavailable"
        if original_error:
            message = f"{message}: {str(original_error)}"
        super().__init__(message)


class FactPulseAPIError(FactPulseError):
    """Generic API error with structured error code.

    Used for errors not covered by specific exceptions.

    Attributes:
        status_code: HTTP response status code
        error_code: API error code (e.g., INTERNAL_ERROR)
        error_message: API error message
        details: Optional details (ValidationErrorDetail)
    """
    def __init__(
        self,
        status_code: int,
        error_code: str,
        error_message: str,
        details: Optional[List[ValidationErrorDetail]] = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.error_message = error_message
        self.details = details or []
        super().__init__(f"[{error_code}] {error_message}")


def parse_api_error(response_json: Dict[str, Any], status_code: int = 400) -> FactPulseError:
    """Parse an API error response and return the appropriate exception.

    This function parses the unified FactPulse API error format
    (APIError with errorCode, errorMessage, details) and returns
    the appropriate Python exception.

    Args:
        response_json: Error response JSON (dict)
        status_code: HTTP response status code

    Returns:
        Appropriate exception based on status_code and error_code

    Example:
        >>> response = requests.post(url, json=data)
        >>> if response.status_code >= 400:
        ...     error = parse_api_error(response.json(), response.status_code)
        ...     raise error
    """
    # Extract API error fields
    # Support both formats: camelCase (API) and snake_case
    error_code = response_json.get("errorCode") or response_json.get("error_code") or "UNKNOWN_ERROR"
    error_message = response_json.get("errorMessage") or response_json.get("error_message") or "Unknown error"
    details_raw = response_json.get("details") or []

    # Sometimes the error is wrapped in a "detail" field
    if "detail" in response_json and isinstance(response_json["detail"], dict):
        detail = response_json["detail"]
        error_code = detail.get("error") or detail.get("errorCode") or error_code
        error_message = detail.get("message") or detail.get("errorMessage") or error_message
        details_raw = detail.get("details") or details_raw

    # Parse details into ValidationErrorDetail
    details = []
    for d in details_raw:
        if isinstance(d, dict):
            details.append(ValidationErrorDetail(
                level=d.get("level", "Error"),
                item=d.get("item", ""),
                reason=d.get("reason", ""),
                source=d.get("source"),
                code=d.get("code"),
            ))

    # Return appropriate exception based on status_code
    if status_code == 401:
        return FactPulseAuthError(error_message)
    elif status_code == 404:
        # Try to extract resource from message
        resource = "resource"
        if "client" in error_message.lower():
            resource = "client"
        elif "flux" in error_message.lower() or "flow" in error_message.lower():
            resource = "flow"
        elif "facture" in error_message.lower() or "invoice" in error_message.lower():
            resource = "invoice"
        elif "structure" in error_message.lower():
            resource = "structure"
        return FactPulseNotFoundError(resource)
    elif status_code == 503:
        service_name = "API"
        if "afnor" in error_message.lower() or "pdp" in error_message.lower():
            service_name = "AFNOR PDP"
        elif "chorus" in error_message.lower():
            service_name = "Chorus Pro"
        return FactPulseServiceUnavailableError(service_name)
    elif status_code in (400, 422) and details:
        return FactPulseValidationError(error_message, details, error_code)
    else:
        return FactPulseAPIError(status_code, error_code, error_message, details)


def api_exception_to_validation_error(api_exception) -> FactPulseValidationError:
    """Convert an SDK-generated ApiException to FactPulseValidationError.

    The openapi-generator SDK generates ApiException objects that are not
    very user-friendly. This function converts them to FactPulse exceptions
    with intelligent error parsing.

    Args:
        api_exception: ApiException from the generated SDK

    Returns:
        FactPulseValidationError with structured details
    """
    import json

    status_code = getattr(api_exception, "status", 400)
    body = getattr(api_exception, "body", "{}")

    try:
        response_json = json.loads(body) if isinstance(body, str) else body
    except (json.JSONDecodeError, TypeError):
        response_json = {"errorMessage": str(api_exception)}

    error = parse_api_error(response_json, status_code)

    # Convert to FactPulseValidationError if not already
    if isinstance(error, FactPulseValidationError):
        return error
    else:
        return FactPulseValidationError(str(error))
