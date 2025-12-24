"""
FactPulse Helpers - Simplified client with built-in JWT authentication and polling.

This module provides:
- FactPulseClient: Client with JWT auth and automatic polling
- ChorusProCredentials / AFNORCredentials: Dataclasses for Zero-Trust mode
- Amount helpers: amount(), invoice_totals(), invoice_line(), vat_line()
- JSON helpers: DecimalEncoder, json_dumps_safe() for serializing Decimal/datetime

Example:
    >>> from factpulse_helpers import (
    ...     FactPulseClient,
    ...     ChorusProCredentials,
    ...     AFNORCredentials,
    ...     invoice_totals,
    ...     invoice_line,
    ... )
    >>>
    >>> client = FactPulseClient(
    ...     email="user@example.com",
    ...     password="password",
    ...     chorus_credentials=ChorusProCredentials(
    ...         piste_client_id="...",
    ...         piste_client_secret="...",
    ...         chorus_pro_login="...",
    ...         chorus_pro_password="..."
    ...     )
    ... )
"""
from .client import (
    FactPulseClient,
    ChorusProCredentials,
    AFNORCredentials,
    amount,
    invoice_totals,
    invoice_line,
    vat_line,
    postal_address,
    electronic_address,
    supplier,
    recipient,
    # JSON utilities
    DecimalEncoder,
    json_dumps_safe,
)
from .exceptions import (
    FactPulseError,
    FactPulseAuthError,
    FactPulsePollingTimeout,
    FactPulseValidationError,
    FactPulseNotFoundError,
    FactPulseServiceUnavailableError,
    FactPulseAPIError,
    ValidationErrorDetail,
    parse_api_error,
    api_exception_to_validation_error,
)

__all__ = [
    # Main client
    "FactPulseClient",
    # Credentials
    "ChorusProCredentials",
    "AFNORCredentials",
    # Amount and line helpers
    "amount",
    "invoice_totals",
    "invoice_line",
    "vat_line",
    # Party helpers (supplier/recipient)
    "postal_address",
    "electronic_address",
    "supplier",
    "recipient",
    # JSON utilities (Decimal, datetime handling, etc.)
    "DecimalEncoder",
    "json_dumps_safe",
    # Exceptions
    "FactPulseError",
    "FactPulseAuthError",
    "FactPulsePollingTimeout",
    "FactPulseValidationError",
    "FactPulseNotFoundError",
    "FactPulseServiceUnavailableError",
    "FactPulseAPIError",
    "ValidationErrorDetail",
    # Helpers for parsing API errors
    "parse_api_error",
    "api_exception_to_validation_error",
]


# Backward compatibility alias
def format_amount(value) -> str:
    """Format an amount for the FactPulse API. Alias for amount()."""
    return amount(value)
