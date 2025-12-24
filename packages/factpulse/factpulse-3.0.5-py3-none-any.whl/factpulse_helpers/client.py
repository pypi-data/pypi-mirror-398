"""Simplified client for the FactPulse API with built-in JWT authentication and polling."""
import base64
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

import factpulse
from factpulse import ApiClient, Configuration, InvoiceProcessingApi

from .exceptions import (
    FactPulseAuthError,
    FactPulsePollingTimeout,
    FactPulseValidationError,
    ValidationErrorDetail,
)

logger = logging.getLogger(__name__)


# =============================================================================
# JSON Encoder for Decimal and other non-serializable types
# =============================================================================

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal and other Python types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            # Convert to string to preserve monetary precision
            return str(obj)
        if hasattr(obj, "isoformat"):
            # datetime, date, time
            return obj.isoformat()
        if hasattr(obj, "to_dict"):
            # Pydantic models or dataclasses with to_dict
            return obj.to_dict()
        return super().default(obj)


def json_dumps_safe(data: Any, **kwargs) -> str:
    """Serialize to JSON handling Decimal and other Python types.

    Args:
        data: Data to serialize (dict, list, etc.)
        **kwargs: Additional arguments for json.dumps

    Returns:
        JSON string

    Example:
        >>> from decimal import Decimal
        >>> json_dumps_safe({"amount": Decimal("1234.56")})
        '{"amount": "1234.56"}'
    """
    kwargs.setdefault("ensure_ascii", False)
    kwargs.setdefault("cls", DecimalEncoder)
    return json.dumps(data, **kwargs)


# =============================================================================
# Credentials dataclasses - for simplified configuration
# =============================================================================

@dataclass
class ChorusProCredentials:
    """Chorus Pro credentials for Zero-Trust mode.

    These credentials are passed in each request and never stored server-side.

    Attributes:
        piste_client_id: PISTE Client ID (government API portal)
        piste_client_secret: PISTE Client Secret
        chorus_pro_login: Chorus Pro login
        chorus_pro_password: Chorus Pro password
        sandbox: True for sandbox environment, False for production
    """
    piste_client_id: str
    piste_client_secret: str
    chorus_pro_login: str
    chorus_pro_password: str
    sandbox: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API."""
        return {
            "piste_client_id": self.piste_client_id,
            "piste_client_secret": self.piste_client_secret,
            "chorus_pro_login": self.chorus_pro_login,
            "chorus_pro_password": self.chorus_pro_password,
            "sandbox": self.sandbox,
        }


@dataclass
class AFNORCredentials:
    """AFNOR PDP credentials for Zero-Trust mode.

    These credentials are passed in each request and never stored server-side.
    The FactPulse API uses these credentials to authenticate with the AFNOR PDP
    and obtain a specific OAuth2 token.

    Attributes:
        flow_service_url: PDP Flow Service URL (e.g., https://api.pdp.fr/flow/v1)
        token_url: PDP OAuth2 server URL (e.g., https://auth.pdp.fr/oauth/token)
        client_id: PDP OAuth2 Client ID
        client_secret: PDP OAuth2 Client Secret
        directory_service_url: Directory Service URL (optional, derived from flow_service_url)
    """
    flow_service_url: str
    token_url: str
    client_id: str
    client_secret: str
    directory_service_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API."""
        result = {
            "flow_service_url": self.flow_service_url,
            "token_url": self.token_url,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.directory_service_url:
            result["directory_service_url"] = self.directory_service_url
        return result


# =============================================================================
# Helpers for anyOf types - avoids verbosity of generated wrappers
# =============================================================================

def amount(value: Union[str, float, int, Decimal, None]) -> str:
    """Convert a value to an amount string for the API.

    The FactPulse API accepts amounts as strings or floats.
    This function normalizes to string to guarantee monetary precision.
    """
    if value is None:
        return "0.00"
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    if isinstance(value, str):
        return value
    return "0.00"


def invoice_totals(
    total_excl_tax: Union[str, float, int, Decimal],
    total_vat: Union[str, float, int, Decimal],
    total_incl_tax: Union[str, float, int, Decimal],
    amount_due: Union[str, float, int, Decimal],
    discount_incl_tax: Union[str, float, int, Decimal, None] = None,
    discount_reason: Optional[str] = None,
    prepayment: Union[str, float, int, Decimal, None] = None,
) -> Dict[str, Any]:
    """Create a simplified InvoiceTotals object.

    Avoids having to use wrappers like TotalNetAmount, VatAmount, etc.
    """
    result = {
        "totalNetAmount": amount(total_excl_tax),
        "vatAmount": amount(total_vat),
        "totalGrossAmount": amount(total_incl_tax),
        "amountDue": amount(amount_due),
    }
    if discount_incl_tax is not None:
        result["globalAllowanceAmount"] = amount(discount_incl_tax)
    if discount_reason is not None:
        result["globalAllowanceReason"] = discount_reason
    if prepayment is not None:
        result["prepayment"] = amount(prepayment)
    return result


def invoice_line(
    line_number: int,
    description: str,
    quantity: Union[str, float, int, Decimal],
    unit_price_excl_tax: Union[str, float, int, Decimal],
    line_total_excl_tax: Union[str, float, int, Decimal],
    vat_rate_code: Optional[str] = None,
    vat_rate_value: Union[str, float, int, Decimal, None] = "20.00",
    vat_category: str = "S",
    unit: str = "FORFAIT",
    reference: Optional[str] = None,
    discount_excl_tax: Union[str, float, int, Decimal, None] = None,
    discount_reason_code: Optional[str] = None,
    discount_reason: Optional[str] = None,
    period_start_date: Optional[str] = None,
    period_end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Create an invoice line for the FactPulse API.

    JSON keys are in camelCase (FactPulse API convention).
    Fields correspond exactly to LigneDePoste in models.py.

    For VAT rate, you can use either:
    - vat_rate_code: Predefined code (e.g., "TVA20", "TVA10", "TVA5.5")
    - vat_rate_value: Numeric value (e.g., "20.00", 20, 20.0)

    Args:
        line_number: Line number
        description: Product/service description
        quantity: Quantity
        unit_price_excl_tax: Unit price excl. tax
        line_total_excl_tax: Line total excl. tax
        vat_rate_code: Predefined VAT code (e.g., "TVA20") - optional
        vat_rate_value: VAT rate value (default: "20.00") - used if vat_rate_code not provided
        vat_category: VAT category - S (standard), Z (zero), E (exempt), AE (reverse charge), K (intra-community)
        unit: Billing unit (default: "FORFAIT")
        reference: Item reference
        discount_excl_tax: Discount amount excl. tax (optional)
        discount_reason_code: Discount reason code
        discount_reason: Discount reason description
        period_start_date: Billing period start date (YYYY-MM-DD)
        period_end_date: Billing period end date (YYYY-MM-DD)
    """
    result = {
        "lineNumber": line_number,
        "itemName": description,
        "quantity": amount(quantity),
        "unitNetPrice": amount(unit_price_excl_tax),
        "lineNetAmount": amount(line_total_excl_tax),
        "vatCategory": vat_category,
        "unit": unit,
    }
    # Either vat_rate_code (code) or vat_rate_value (value)
    if vat_rate_code is not None:
        result["vatRate"] = vat_rate_code
    elif vat_rate_value is not None:
        result["manualVatRate"] = amount(vat_rate_value)
    if reference is not None:
        result["reference"] = reference
    if discount_excl_tax is not None:
        result["lineAllowanceAmount"] = amount(discount_excl_tax)
    if discount_reason_code is not None:
        result["allowanceReasonCode"] = discount_reason_code
    if discount_reason is not None:
        result["allowanceReason"] = discount_reason
    if period_start_date is not None:
        result["periodStartDate"] = period_start_date
    if period_end_date is not None:
        result["periodEndDate"] = period_end_date
    return result


def vat_line(
    base_amount_excl_tax: Union[str, float, int, Decimal],
    vat_amount: Union[str, float, int, Decimal],
    rate_code: Optional[str] = None,
    rate_value: Union[str, float, int, Decimal, None] = "20.00",
    category: str = "S",
) -> Dict[str, Any]:
    """Create a VAT line for the FactPulse API.

    JSON keys are in camelCase (FactPulse API convention).
    Fields correspond exactly to LigneDeTVA in models.py.

    For VAT rate, you can use either:
    - rate_code: Predefined code (e.g., "TVA20", "TVA10", "TVA5.5")
    - rate_value: Numeric value (e.g., "20.00", 20, 20.0)

    Args:
        base_amount_excl_tax: Base amount excl. tax
        vat_amount: VAT amount
        rate_code: Predefined VAT code (e.g., "TVA20") - optional
        rate_value: VAT rate value (default: "20.00") - used if rate_code not provided
        category: VAT category (default: "S" for standard)
    """
    result = {
        "taxableAmount": amount(base_amount_excl_tax),
        "vatAmount": amount(vat_amount),
        "category": category,
    }
    # Either rate_code (code) or rate_value (value)
    if rate_code is not None:
        result["rate"] = rate_code
    elif rate_value is not None:
        result["manualRate"] = amount(rate_value)
    return result


def postal_address(
    line1: str,
    postal_code: str,
    city: str,
    country: str = "FR",
    line2: Optional[str] = None,
    line3: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a postal address for the FactPulse API.

    Args:
        line1: First address line (number, street)
        postal_code: Postal code
        city: City name
        country: ISO country code (default: "FR")
        line2: Second address line (optional)
        line3: Third address line (optional)

    Example:
        >>> address = postal_address("123 Example Street", "75001", "Paris")
    """
    result = {
        "lineOne": line1,
        "postalCode": postal_code,
        "city": city,
        "countryCode": country,
    }
    if line2:
        result["lineTwo"] = line2
    if line3:
        result["lineThree"] = line3
    return result


def electronic_address(
    identifier: str,
    scheme_id: str = "0009",
) -> Dict[str, Any]:
    """Create an electronic address for the FactPulse API.

    Args:
        identifier: Address identifier (SIRET, SIREN, etc.)
        scheme_id: Identification scheme (default: "0009" for SIREN)
            - "0009": SIREN
            - "0088": EAN
            - "0096": DUNS
            - "0130": Custom coding
            - "0225": FR - SIRET (French scheme)

    Example:
        >>> address = electronic_address("12345678901234", "0225")  # SIRET
    """
    return {
        "identifier": identifier,
        "schemeId": scheme_id,
    }


def supplier(
    name: str,
    siret: str,
    address_line1: str,
    postal_code: str,
    city: str,
    supplier_id: int = 0,
    siren: Optional[str] = None,
    vat_number: Optional[str] = None,
    iban: Optional[str] = None,
    country: str = "FR",
    address_line2: Optional[str] = None,
    service_code: Optional[int] = None,
    bank_details_code: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a supplier (invoice issuer) for the FactPulse API.

    This function simplifies supplier creation by automatically generating:
    - Structured postal address
    - Electronic address (based on SIRET)
    - SIREN (extracted from SIRET if not provided)
    - Intra-community VAT number (calculated from SIREN if not provided)

    Args:
        name: Company name / trade name
        siret: SIRET number (14 digits)
        address_line1: First address line
        postal_code: Postal code
        city: City
        supplier_id: Chorus Pro supplier ID (default: 0)
        siren: SIREN number (9 digits) - calculated from SIRET if absent
        vat_number: Intra-community VAT number - calculated if absent
        iban: IBAN for payment
        country: ISO country code (default: "FR")
        address_line2: Second address line (optional)
        service_code: Chorus Pro supplier service ID (optional)
        bank_details_code: Chorus Pro bank details code (optional)

    Returns:
        Dict ready to be used in an invoice

    Example:
        >>> s = supplier(
        ...     name="My Company SAS",
        ...     siret="12345678900001",
        ...     address_line1="123 Republic Street",
        ...     postal_code="75001",
        ...     city="Paris",
        ...     iban="FR7630006000011234567890189",
        ... )
    """
    # Auto-calculate SIREN from SIRET
    if not siren and len(siret) == 14:
        siren = siret[:9]

    # Auto-calculate French intra-community VAT number
    if not vat_number and siren and len(siren) == 9:
        # VAT key = (12 + 3 * (SIREN % 97)) % 97
        try:
            key = (12 + 3 * (int(siren) % 97)) % 97
            vat_number = f"FR{key:02d}{siren}"
        except ValueError:
            pass  # Non-numeric SIREN, skip

    result: Dict[str, Any] = {
        "name": name,
        "supplierId": supplier_id,
        "siret": siret,
        "electronicAddress": electronic_address(siret, "0225"),
        "postalAddress": postal_address(address_line1, postal_code, city, country, address_line2),
    }

    if siren:
        result["siren"] = siren
    if vat_number:
        result["vatNumber"] = vat_number
    if iban:
        result["iban"] = iban
    if service_code:
        result["supplierServiceId"] = service_code
    if bank_details_code:
        result["supplierBankDetailsCode"] = bank_details_code

    return result


def recipient(
    name: str,
    siret: str,
    address_line1: str,
    postal_code: str,
    city: str,
    siren: Optional[str] = None,
    country: str = "FR",
    address_line2: Optional[str] = None,
    service_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a recipient (invoice customer) for the FactPulse API.

    This function simplifies recipient creation by automatically generating:
    - Structured postal address
    - Electronic address (based on SIRET)
    - SIREN (extracted from SIRET if not provided)

    Args:
        name: Company name / trade name
        siret: SIRET number (14 digits)
        address_line1: First address line
        postal_code: Postal code
        city: City
        siren: SIREN number (9 digits) - calculated from SIRET if absent
        country: ISO country code (default: "FR")
        address_line2: Second address line (optional)
        service_code: Recipient service code (optional)

    Returns:
        Dict ready to be used in an invoice

    Example:
        >>> r = recipient(
        ...     name="Client SARL",
        ...     siret="98765432109876",
        ...     address_line1="456 Champs Avenue",
        ...     postal_code="69001",
        ...     city="Lyon",
        ... )
    """
    # Auto-calculate SIREN from SIRET
    if not siren and len(siret) == 14:
        siren = siret[:9]

    result: Dict[str, Any] = {
        "name": name,
        "siret": siret,
        "electronicAddress": electronic_address(siret, "0225"),
        "postalAddress": postal_address(address_line1, postal_code, city, country, address_line2),
    }

    if siren:
        result["siren"] = siren
    if service_code:
        result["executingServiceCode"] = service_code

    return result


def payee(
    name: str,
    siret: Optional[str] = None,
    siren: Optional[str] = None,
    iban: Optional[str] = None,
    bic: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a payee (factor) for factoring.

    The payee (BG-10 / PayeeTradeParty) is used when payment must be made
    to a third party different from the supplier, typically a factor
    (factoring company).

    For factored invoices, you must also:
    - Use a factored document type (393, 396, 501, 502, 472, 473)
    - Add an ACC note with the assignment clause
    - The payee's IBAN will be used for payment

    Args:
        name: Factor's company name (BT-59)
        siret: Factor's SIRET number (BT-60, schemeID 0009) - 14 digits
        siren: Factor's SIREN number (BT-61, schemeID 0002) - calculated from SIRET if absent
        iban: Factor's IBAN - to receive payment
        bic: Factor's bank BIC (optional)

    Returns:
        Dict ready to be used in a factored invoice

    Example:
        >>> # Simple factored invoice
        >>> factor = payee(
        ...     name="FACTOR SAS",
        ...     siret="30000000700033",
        ...     iban="FR76 3000 4000 0500 0012 3456 789",
        ... )
        >>> invoice = {
        ...     "invoiceNumber": "INV-2025-001-FACT",
        ...     "supplier": supplier(...),
        ...     "recipient": recipient(...),
        ...     "payee": factor,  # Factor receives payment
        ...     "references": {
        ...         "invoiceType": "393",  # Factored invoice
        ...         ...
        ...     },
        ...     "notes": [
        ...         {
        ...             "content": "This receivable has been assigned to FACTOR SAS. Contract n. FACT-2025",
        ...             "subjectCode": "ACC",  # Mandatory assignment code
        ...         },
        ...         ...
        ...     ],
        ...     ...
        ... }

    See Also:
        - Factoring guide: docs/factoring_guide.md
        - Factored document types: 393 (invoice), 396 (credit note), 501, 502, 472, 473
        - ACC note: Mandatory factoring assignment clause
    """
    # Auto-calculate SIREN from SIRET
    if not siren and siret and len(siret) == 14:
        siren = siret[:9]

    result: Dict[str, Any] = {
        "name": name,
    }

    if siret:
        result["siret"] = siret
    if siren:
        result["siren"] = siren
    if iban:
        result["iban"] = iban
    if bic:
        result["bic"] = bic

    return result




class FactPulseClient:
    """Simplified client for the FactPulse API.

    Handles JWT authentication, asynchronous task polling,
    and allows configuring Chorus Pro / AFNOR credentials at initialization.
    """

    DEFAULT_API_URL = "https://factpulse.fr"
    DEFAULT_POLLING_INTERVAL = 2000  # ms
    DEFAULT_POLLING_TIMEOUT = 120000  # ms
    DEFAULT_MAX_RETRIES = 1

    def __init__(
        self,
        email: str,
        password: str,
        api_url: Optional[str] = None,
        client_uid: Optional[str] = None,
        chorus_credentials: Optional[ChorusProCredentials] = None,
        afnor_credentials: Optional[AFNORCredentials] = None,
        polling_interval: Optional[int] = None,
        polling_timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        self.email = email
        self.password = password
        self.api_url = (api_url or self.DEFAULT_API_URL).rstrip("/")
        self.client_uid = client_uid
        self.chorus_credentials = chorus_credentials
        self.afnor_credentials = afnor_credentials
        self.polling_interval = polling_interval or self.DEFAULT_POLLING_INTERVAL
        self.polling_timeout = polling_timeout or self.DEFAULT_POLLING_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else self.DEFAULT_MAX_RETRIES

        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._api_client: Optional[ApiClient] = None

    def get_chorus_credentials_for_api(self) -> Optional[Dict[str, Any]]:
        """Return Chorus Pro credentials in API format."""
        return self.chorus_credentials.to_dict() if self.chorus_credentials else None

    def get_afnor_credentials_for_api(self) -> Optional[Dict[str, Any]]:
        """Return AFNOR credentials in API format."""
        return self.afnor_credentials.to_dict() if self.afnor_credentials else None

    # Shorter aliases for convenience
    def get_chorus_pro_credentials(self) -> Optional[Dict[str, Any]]:
        """Alias for get_chorus_credentials_for_api()."""
        return self.get_chorus_credentials_for_api()

    def get_afnor_credentials(self) -> Optional[Dict[str, Any]]:
        """Alias for get_afnor_credentials_for_api()."""
        return self.get_afnor_credentials_for_api()

    def _obtain_token(self) -> Dict[str, str]:
        """Obtain a new JWT token."""
        token_url = f"{self.api_url}/api/token/"
        payload = {"username": self.email, "password": self.password}
        if self.client_uid:
            payload["client_uid"] = self.client_uid

        try:
            response = requests.post(token_url, json=payload, timeout=30)
            response.raise_for_status()
            logger.info("JWT token obtained for %s", self.email)
            return response.json()
        except requests.RequestException as e:
            error_detail = ""
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except Exception:
                    error_detail = str(e)
            raise FactPulseAuthError(f"Unable to obtain JWT token: {error_detail or e}")

    def _refresh_access_token(self) -> str:
        """Refresh the access token."""
        if not self._refresh_token:
            raise FactPulseAuthError("No refresh token available")

        refresh_url = f"{self.api_url}/api/token/refresh/"
        try:
            response = requests.post(
                refresh_url, json={"refresh": self._refresh_token}, timeout=30
            )
            response.raise_for_status()
            logger.info("Token refreshed successfully")
            return response.json()["access"]
        except requests.RequestException:
            logger.warning("Refresh failed, obtaining new token")
            tokens = self._obtain_token()
            self._refresh_token = tokens["refresh"]
            return tokens["access"]

    def ensure_authenticated(self, force_refresh: bool = False) -> None:
        """Ensure the client is authenticated."""
        now = datetime.now()

        if force_refresh or not self._access_token or not self._token_expires_at or now >= self._token_expires_at:
            if self._refresh_token and self._token_expires_at and not force_refresh:
                try:
                    self._access_token = self._refresh_access_token()
                    self._token_expires_at = now + timedelta(minutes=28)
                    return
                except FactPulseAuthError:
                    pass

            tokens = self._obtain_token()
            self._access_token = tokens["access"]
            self._refresh_token = tokens["refresh"]
            self._token_expires_at = now + timedelta(minutes=28)

    def reset_auth(self) -> None:
        """Reset authentication."""
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = None
        self._api_client = None
        logger.info("Authentication reset")

    def _request(
        self,
        method: str,
        endpoint: str,
        files: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> requests.Response:
        """Perform an HTTP request to the FactPulse API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Relative endpoint (e.g., /processing/validate-pdf)
            files: Files for multipart/form-data
            data: Form data
            json_data: JSON data

        Returns:
            API response

        Raises:
            FactPulseValidationError: On API error
        """
        self.ensure_authenticated()
        url = f"{self.api_url}/api/v1{endpoint}"
        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            if files:
                response = requests.request(method, url, files=files, data=data, headers=headers, timeout=60)
            elif json_data:
                response = requests.request(method, url, json=json_data, headers=headers, timeout=30)
            else:
                response = requests.request(method, url, data=data, headers=headers, timeout=30)
        except requests.RequestException as e:
            raise FactPulseValidationError(f"Network error: {e}")

        if response.status_code >= 400:
            try:
                error_json = response.json()
                error_msg = error_json.get("detail", error_json.get("errorMessage", str(error_json)))
            except Exception:
                error_msg = response.text or f"HTTP error {response.status_code}"
            raise FactPulseValidationError(f"API error: {error_msg}")

        return response

    def get_processing_api(self) -> InvoiceProcessingApi:
        """Return the invoice processing API."""
        self.ensure_authenticated()
        config = Configuration(host=f"{self.api_url}/api/facturation")
        config.access_token = self._access_token
        self._api_client = ApiClient(configuration=config)
        return InvoiceProcessingApi(api_client=self._api_client)

    def poll_task(self, task_id: str, timeout: Optional[int] = None, interval: Optional[int] = None) -> Dict[str, Any]:
        """Poll a task until completion."""
        timeout_ms = timeout or self.polling_timeout
        interval_ms = interval or self.polling_interval

        start_time = time.time() * 1000
        current_interval = float(interval_ms)

        logger.info("Starting polling for task %s (timeout: %dms)", task_id, timeout_ms)

        while True:
            elapsed = (time.time() * 1000) - start_time

            if elapsed > timeout_ms:
                raise FactPulsePollingTimeout(task_id, timeout_ms)

            try:
                logger.debug("Polling task %s (elapsed: %.0fms)...", task_id, elapsed)
                api = self.get_processing_api()
                status = api.get_task_status_api_v1_processing_tasks_task_id_status_get(task_id=task_id)
                logger.debug("Status response received: %s", status)

                status_value = status.status.value if hasattr(status.status, "value") else str(status.status)
                logger.info("Task %s: status=%s (%.0fms)", task_id, status_value, elapsed)

                if status_value == "SUCCESS":
                    logger.info("Task %s completed successfully", task_id)
                    if status.result:
                        if hasattr(status.result, "to_dict"):
                            return status.result.to_dict()
                        return dict(status.result)
                    return {}

                if status_value == "FAILURE":
                    error_msg = "Unknown error"
                    errors = []
                    if status.result:
                        result = status.result.to_dict() if hasattr(status.result, "to_dict") else dict(status.result)
                        # AFNOR format: errorMessage, details
                        error_msg = result.get("errorMessage", error_msg)
                        for err in result.get("details", []):
                            errors.append(ValidationErrorDetail(
                                level=err.get("level", ""),
                                item=err.get("item", ""),
                                reason=err.get("reason", ""),
                                source=err.get("source"),
                                code=err.get("code"),
                            ))
                    raise FactPulseValidationError(f"Task {task_id} failed: {error_msg}", errors)

            except (FactPulseValidationError, FactPulsePollingTimeout):
                raise
            except Exception as e:
                error_str = str(e)
                logger.warning("Error during polling: %s", error_str)

                # Rate limit (429) - wait and retry with backoff
                if "429" in error_str:
                    wait_time = min(current_interval * 2, 30000)  # Max 30s
                    logger.warning("Rate limit (429), waiting %.1fs before retry...", wait_time / 1000)
                    time.sleep(wait_time / 1000)
                    current_interval = wait_time
                    continue

                # Token expired (401) - re-authenticate
                if "401" in error_str:
                    logger.warning("Token expired, re-authenticating...")
                    self.reset_auth()
                    continue

                # Temporary server error (502, 503, 504) - retry with backoff
                if any(code in error_str for code in ("502", "503", "504")):
                    wait_time = min(current_interval * 1.5, 15000)
                    logger.warning("Temporary server error, waiting %.1fs before retry...", wait_time / 1000)
                    time.sleep(wait_time / 1000)
                    current_interval = wait_time
                    continue

                raise FactPulseValidationError(f"API error: {e}")

            time.sleep(current_interval / 1000)
            current_interval = min(current_interval * 1.5, 10000)

    def generate_facturx(
        self,
        invoice_data: Union[Dict, str, Any],
        pdf_source: Union[bytes, str, Path],
        profile: str = "EN16931",
        output_format: str = "pdf",
        sync: bool = True,
        timeout: Optional[int] = None,
    ) -> bytes:
        """Generate a Factur-X invoice.

        Accepts invoice data in multiple forms:
        - Dict: Python dictionary (recommended with helpers invoice_totals(), invoice_line(), etc.)
        - str: Serialized JSON
        - Pydantic model: SDK-generated model (will be converted via .to_dict())

        Args:
            invoice_data: Invoice data (dict, JSON string, or Pydantic model)
            pdf_source: Path to source PDF, or PDF bytes
            profile: Factur-X profile (MINIMUM, BASIC, EN16931, EXTENDED)
            output_format: Output format (pdf, xml, both)
            sync: If True, wait for task completion and return result
            timeout: Polling timeout in ms

        Returns:
            bytes: Generated file content (PDF or XML)
        """
        # Convert data to JSON string (handles Decimal, datetime, etc.)
        if isinstance(invoice_data, str):
            json_data = invoice_data
        elif isinstance(invoice_data, dict):
            json_data = json_dumps_safe(invoice_data)
        elif hasattr(invoice_data, "to_dict"):
            # Pydantic model generated by SDK
            json_data = json_dumps_safe(invoice_data.to_dict())
        else:
            raise FactPulseValidationError(f"Unsupported data type: {type(invoice_data)}")

        # Prepare PDF
        if isinstance(pdf_source, (str, Path)):
            pdf_path = Path(pdf_source)
            pdf_bytes = pdf_path.read_bytes()
            pdf_filename = pdf_path.name
        else:
            pdf_bytes = pdf_source
            pdf_filename = "source.pdf"

        # Direct send via requests (bypass SDK Pydantic models)
        for attempt in range(self.max_retries + 1):
            self.ensure_authenticated()
            try:
                url = f"{self.api_url}/api/v1/processing/generate-invoice"
                files = {
                    "invoice_data": (None, json_data, "application/json"),
                    "profile": (None, profile),
                    "output_format": (None, output_format),
                    "source_pdf": (pdf_filename, pdf_bytes, "application/pdf"),
                }
                headers = {"Authorization": f"Bearer {self._access_token}"}
                response = requests.post(url, files=files, headers=headers, timeout=60)

                if response.status_code == 401 and attempt < self.max_retries:
                    logger.warning("Error 401, resetting token (attempt %d/%d)", attempt + 1, self.max_retries + 1)
                    self.reset_auth()
                    continue

                # Handle HTTP errors with response body extraction
                if response.status_code >= 400:
                    error_body = None
                    try:
                        error_body = response.json()
                    except Exception:
                        error_body = {"detail": response.text or f"HTTP {response.status_code}"}

                    # Detailed error logging
                    logger.error("API error %d: %s", response.status_code, error_body)

                    # Extract error details in standardized format
                    errors = []
                    error_msg = f"HTTP error {response.status_code}"

                    if isinstance(error_body, dict):
                        # FastAPI/Pydantic format: {"detail": [{"loc": [...], "msg": "...", "type": "..."}]}
                        if "detail" in error_body:
                            detail = error_body["detail"]
                            if isinstance(detail, list):
                                # Pydantic validation error list
                                error_msg = "Validation error"
                                for err in detail:
                                    if isinstance(err, dict):
                                        loc = err.get("loc", [])
                                        loc_str = " -> ".join(str(l) for l in loc) if loc else ""
                                        errors.append(ValidationErrorDetail(
                                            level="ERROR",
                                            item=loc_str,
                                            reason=err.get("msg", str(err)),
                                            source="validation",
                                            code=err.get("type"),
                                        ))
                            elif isinstance(detail, str):
                                error_msg = detail
                        # AFNOR format: {"errorMessage": "...", "details": [...]}
                        elif "errorMessage" in error_body:
                            error_msg = error_body["errorMessage"]
                            for err in error_body.get("details", []):
                                errors.append(ValidationErrorDetail(
                                    level=err.get("level", "ERROR"),
                                    item=err.get("item", ""),
                                    reason=err.get("reason", ""),
                                    source=err.get("source"),
                                    code=err.get("code"),
                                ))

                    # For 422 errors (validation), don't retry
                    if response.status_code == 422:
                        raise FactPulseValidationError(error_msg, errors)

                    # For other client errors (4xx), don't retry either
                    if 400 <= response.status_code < 500:
                        raise FactPulseValidationError(error_msg, errors)

                    # For server errors (5xx), retry if possible
                    if attempt < self.max_retries:
                        logger.warning("Server error %d (attempt %d/%d)", response.status_code, attempt + 1, self.max_retries + 1)
                        continue
                    raise FactPulseValidationError(error_msg, errors)

                result = response.json()
                task_id = result.get("task_id")

                if not task_id:
                    raise FactPulseValidationError("No task ID in response")

                if not sync:
                    return task_id.encode()

                poll_result = self.poll_task(task_id, timeout)

                if poll_result.get("status") == "ERROR":
                    # AFNOR format: errorMessage, details
                    error_msg = poll_result.get("errorMessage", "Validation error")
                    errors = [
                        ValidationErrorDetail(
                            level=e.get("level", ""),
                            item=e.get("item", ""),
                            reason=e.get("reason", ""),
                            source=e.get("source"),
                            code=e.get("code"),
                        )
                        for e in poll_result.get("details", [])
                    ]
                    raise FactPulseValidationError(error_msg, errors)

                if "content_b64" in poll_result:
                    return base64.b64decode(poll_result["content_b64"])

                raise FactPulseValidationError("Result does not contain content")

            except requests.RequestException as e:
                # Network errors (connection, timeout, etc.) - no HTTP error
                if attempt < self.max_retries:
                    logger.warning("Network error (attempt %d/%d): %s", attempt + 1, self.max_retries + 1, e)
                    continue
                raise FactPulseValidationError(f"Network error: {e}")

        raise FactPulseValidationError("Failed after all attempts")


    @staticmethod
    def format_amount(value) -> str:
        """Format an amount for the FactPulse API."""
        if value is None:
            return "0.00"
        if isinstance(value, Decimal):
            return f"{value:.2f}"
        if isinstance(value, (int, float)):
            return f"{value:.2f}"
        if isinstance(value, str):
            return value
        return "0.00"

    # =========================================================================
    # AFNOR PDP/PA - Flow Service
    # =========================================================================
    #
    # ARCHITECTURE SET IN STONE - DO NOT MODIFY WITHOUT UNDERSTANDING
    #
    # The AFNOR proxy is 100% TRANSPARENT. It has the same OpenAPI as AFNOR.
    # The SDK must ALWAYS:
    # 1. Obtain AFNOR credentials (stored mode: via /credentials, zero-trust mode: provided)
    # 2. Perform AFNOR OAuth itself
    # 3. Call endpoints with AFNOR token + X-PDP-Base-URL header
    #
    # The FactPulse JWT token is NEVER used to call the PDP!
    # It's only used to retrieve credentials in stored mode.
    # =========================================================================

    def _get_afnor_credentials(self) -> "AFNORCredentials":
        """Obtain AFNOR credentials (stored or zero-trust mode).

        **Zero-trust mode**: Returns afnor_credentials provided to constructor.
        **Stored mode**: Retrieves credentials via GET /api/v1/afnor/credentials.

        Returns:
            AFNORCredentials with flow_service_url, token_url, client_id, client_secret

        Raises:
            FactPulseAuthError: If no credentials available
            FactPulseServiceUnavailableError: If server is unavailable
        """
        from .exceptions import FactPulseServiceUnavailableError

        # Zero-trust mode: credentials provided to constructor
        if self.afnor_credentials:
            logger.info("Zero-trust mode: using provided AFNORCredentials")
            return self.afnor_credentials

        # Stored mode: retrieve credentials via API
        logger.info("Stored mode: retrieving credentials via /api/v1/afnor/credentials")

        self.ensure_authenticated()  # Ensure we have a FactPulse JWT token

        url = f"{self.api_url}/api/v1/afnor/credentials"
        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
        except requests.RequestException as e:
            raise FactPulseServiceUnavailableError("FactPulse AFNOR credentials", e)

        if response.status_code == 400:
            error_json = response.json()
            error_detail = error_json.get("detail", {})
            if isinstance(error_detail, dict) and error_detail.get("error") == "NO_CLIENT_UID":
                raise FactPulseAuthError(
                    "No client_uid in JWT. "
                    "To use AFNOR endpoints, either:\n"
                    "1. Generate a token with a client_uid (stored mode)\n"
                    "2. Provide AFNORCredentials to the client constructor (zero-trust mode)"
                )
            raise FactPulseAuthError(f"AFNOR credentials error: {error_detail}")

        if response.status_code != 200:
            try:
                error_json = response.json()
                error_msg = error_json.get("detail", str(error_json))
            except Exception:
                error_msg = response.text or f"HTTP {response.status_code}"
            raise FactPulseAuthError(f"Failed to retrieve AFNOR credentials: {error_msg}")

        creds = response.json()
        logger.info(f"AFNOR credentials retrieved for PDP: {creds.get('flow_service_url')}")

        # Create temporary AFNORCredentials
        return AFNORCredentials(
            flow_service_url=creds["flow_service_url"],
            token_url=creds["token_url"],
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
        )

    def _get_afnor_token_and_url(self) -> Tuple[str, str]:
        """Obtain AFNOR OAuth2 token and PDP URL.

        This method:
        1. Retrieves AFNOR credentials (stored or zero-trust mode)
        2. Performs AFNOR OAuth to obtain a token
        3. Returns the token and PDP URL

        Returns:
            Tuple (afnor_token, pdp_base_url)

        Raises:
            FactPulseAuthError: If authentication fails
            FactPulseServiceUnavailableError: If service is unavailable
        """
        from .exceptions import FactPulseServiceUnavailableError

        # Step 1: Get AFNOR credentials
        credentials = self._get_afnor_credentials()

        # Step 2: Perform AFNOR OAuth
        logger.info(f"AFNOR OAuth to: {credentials.token_url}")

        url = f"{self.api_url}/api/v1/afnor/oauth/token"
        oauth_data = {
            "grant_type": "client_credentials",
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
        }
        headers = {
            "X-PDP-Token-URL": credentials.token_url,
        }

        try:
            response = requests.post(url, data=oauth_data, headers=headers, timeout=10)
        except requests.RequestException as e:
            raise FactPulseServiceUnavailableError("AFNOR OAuth", e)

        if response.status_code != 200:
            try:
                error_json = response.json()
                error_msg = error_json.get("detail", error_json.get("error", str(error_json)))
            except Exception:
                error_msg = response.text or f"HTTP {response.status_code}"
            raise FactPulseAuthError(f"AFNOR OAuth2 failed: {error_msg}")

        token_data = response.json()
        afnor_token = token_data.get("access_token")

        if not afnor_token:
            raise FactPulseAuthError("Invalid AFNOR OAuth2 response: missing access_token")

        logger.info("AFNOR OAuth2 token obtained successfully")
        return afnor_token, credentials.flow_service_url

    def _make_afnor_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> requests.Response:
        """Perform a request to the AFNOR API with auth and error handling.

        ================================================================================
        ARCHITECTURE SET IN STONE
        ================================================================================

        This method:
        1. Retrieves AFNOR credentials (stored mode: API, zero-trust mode: provided)
        2. Performs AFNOR OAuth to obtain an AFNOR token
        3. Calls the endpoint with:
           - Authorization: Bearer {afnor_token}  <- AFNOR TOKEN, NOT FACTPULSE JWT!
           - X-PDP-Base-URL: {pdp_url}  <- For proxy to route to correct PDP

        The FactPulse JWT token is NEVER used to call the PDP.
        It's only used to retrieve credentials in stored mode.

        ================================================================================

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Relative endpoint (e.g., /flow/v1/flows)
            json_data: JSON data (optional)
            files: Multipart files (optional)
            params: Query params (optional)

        Returns:
            API response

        Raises:
            FactPulseAuthError: If 401 or missing credentials
            FactPulseNotFoundError: If 404
            FactPulseServiceUnavailableError: If 503
            FactPulseValidationError: If 400/422
            FactPulseAPIError: Other errors
        """
        from .exceptions import (
            parse_api_error,
            FactPulseServiceUnavailableError,
        )

        # Get AFNOR token and PDP URL
        # (stored mode: retrieves credentials via API, zero-trust mode: uses provided credentials)
        afnor_token, pdp_base_url = self._get_afnor_token_and_url()

        url = f"{self.api_url}/api/v1/afnor{endpoint}"

        # ALWAYS use AFNOR token + X-PDP-Base-URL header
        # The FactPulse JWT token is NEVER used to call the PDP!
        headers = {
            "Authorization": f"Bearer {afnor_token}",
            "X-PDP-Base-URL": pdp_base_url,
        }

        try:
            if files:
                response = requests.request(
                    method, url, files=files, headers=headers, params=params, timeout=60
                )
            else:
                response = requests.request(
                    method, url, json=json_data, headers=headers, params=params, timeout=30
                )
        except requests.RequestException as e:
            raise FactPulseServiceUnavailableError("AFNOR PDP", e)

        if response.status_code >= 400:
            try:
                error_json = response.json()
            except Exception:
                error_json = {"errorMessage": response.text or f"HTTP error {response.status_code}"}
            raise parse_api_error(error_json, response.status_code)

        return response

    def submit_invoice_afnor(
        self,
        flow_name: str,
        pdf_path: Optional[Union[str, Path]] = None,
        pdf_bytes: Optional[bytes] = None,
        pdf_filename: str = "invoice.pdf",
        flow_syntax: str = "CII",
        flow_profile: str = "EN16931",
        tracking_id: Optional[str] = None,
        sha256: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit a Factur-X invoice to a PDP via the AFNOR API.

        Authentication uses either the client_uid from JWT (stored mode),
        or afnor_credentials provided to constructor (zero-trust mode).

        Args:
            flow_name: Flow name (e.g., "Invoice INV-2025-001")
            pdf_path: Path to PDF/A-3 file (exclusive with pdf_bytes)
            pdf_bytes: PDF content as bytes (exclusive with pdf_path)
            pdf_filename: Filename for bytes (default: "invoice.pdf")
            flow_syntax: Flow syntax (CII or UBL)
            flow_profile: Factur-X profile (MINIMUM, BASIC, EN16931, EXTENDED)
            tracking_id: Business tracking identifier (optional)
            sha256: SHA-256 hash of file (calculated automatically if absent)

        Returns:
            Dict with flowId, trackingId, status, sha256, etc.

        Raises:
            FactPulseValidationError: If PDF is not valid
            FactPulseServiceUnavailableError: If PDP is unavailable
            ValueError: If neither pdf_path nor pdf_bytes is provided

        Example:
            >>> # With a file path
            >>> result = client.submit_invoice_afnor(
            ...     flow_name="Invoice INV-2025-001",
            ...     pdf_path="invoice.pdf",
            ...     tracking_id="INV-2025-001",
            ... )
            >>> print(result["flowId"])

            >>> # With bytes (e.g., after Factur-X generation)
            >>> result = client.submit_invoice_afnor(
            ...     flow_name="Invoice INV-2025-001",
            ...     pdf_bytes=pdf_content,
            ...     pdf_filename="INV-2025-001.pdf",
            ...     tracking_id="INV-2025-001",
            ... )
        """
        import hashlib

        # Load PDF from path if provided
        filename = pdf_filename
        if pdf_path:
            pdf_path = Path(pdf_path)
            pdf_bytes = pdf_path.read_bytes()
            filename = pdf_path.name

        if not pdf_bytes:
            raise ValueError("pdf_path or pdf_bytes required")

        # Calculate SHA-256 if not provided
        if not sha256:
            sha256 = hashlib.sha256(pdf_bytes).hexdigest()

        # Prepare flowInfo
        flow_info = {
            "name": flow_name,
            "flowSyntax": flow_syntax,
            "flowProfile": flow_profile,
            "sha256": sha256,
        }
        if tracking_id:
            flow_info["trackingId"] = tracking_id

        files = {
            "file": (filename, pdf_bytes, "application/pdf"),
            "flowInfo": (None, json_dumps_safe(flow_info), "application/json"),
        }

        response = self._make_afnor_request("POST", "/flow/v1/flows", files=files)
        return response.json()


    def search_flows_afnor(
        self,
        tracking_id: Optional[str] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 25,
    ) -> Dict[str, Any]:
        """Search AFNOR invoice flows.

        Args:
            tracking_id: Filter by trackingId
            status: Filter by status (submitted, processing, delivered, etc.)
            offset: Start index (pagination)
            limit: Max number of results

        Returns:
            Dict with flows (list), total, offset, limit

        Example:
            >>> results = client.search_flows_afnor(tracking_id="INV-2025-001")
            >>> for flow in results["flows"]:
            ...     print(flow["flowId"], flow["status"])
        """
        search_body = {
            "offset": offset,
            "limit": limit,
            "where": {},
        }
        if tracking_id:
            search_body["where"]["trackingId"] = tracking_id
        if status:
            search_body["where"]["status"] = status

        response = self._make_afnor_request("POST", "/flow/v1/flows/search", json_data=search_body)
        return response.json()


    def download_flow_afnor(self, flow_id: str) -> bytes:
        """Download the PDF file of an AFNOR flow.

        Args:
            flow_id: Flow identifier (UUID)

        Returns:
            PDF file content

        Raises:
            FactPulseNotFoundError: If flow doesn't exist

        Example:
            >>> pdf_bytes = client.download_flow_afnor("550e8400-e29b-41d4-a716-446655440000")
            >>> with open("invoice.pdf", "wb") as f:
            ...     f.write(pdf_bytes)
        """
        response = self._make_afnor_request("GET", f"/flow/v1/flows/{flow_id}")
        return response.content


    def get_incoming_invoice_afnor(
        self,
        flow_id: str,
        include_document: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve JSON metadata of an incoming flow (supplier invoice).

        Downloads an incoming flow from the AFNOR PDP and extracts invoice
        metadata to a unified JSON format. Supports Factur-X, CII and UBL formats.

        Note: This endpoint uses FactPulse JWT authentication (not AFNOR OAuth).
        The FactPulse server handles calling the PDP with stored credentials.

        Args:
            flow_id: Flow identifier (UUID)
            include_document: If True, include original document encoded in base64

        Returns:
            Dict with invoice metadata:
                - flow_id: Flow identifier
                - source_format: Detected format (Factur-X, CII, UBL)
                - supplier_reference: Supplier invoice number
                - document_type: Type code (380=invoice, 381=credit note, etc.)
                - supplier: Dict with name, siret, vat_number
                - billing_site_name: Recipient name
                - billing_site_siret: Recipient SIRET
                - document_date: Invoice date (YYYY-MM-DD)
                - due_date: Due date (YYYY-MM-DD)
                - currency: Currency code (EUR, USD, etc.)
                - total_excl_tax: Total excl. tax
                - total_vat: VAT amount
                - total_incl_tax: Total incl. tax
                - document_base64: (if include_document=True) Encoded document
                - document_content_type: (if include_document=True) MIME type
                - document_filename: (if include_document=True) Filename

        Raises:
            FactPulseNotFoundError: If flow doesn't exist
            FactPulseValidationError: If format is not supported

        Example:
            >>> # Retrieve incoming invoice metadata
            >>> invoice = client.get_incoming_invoice_afnor("550e8400-e29b-41d4-a716-446655440000")
            >>> print(f"Supplier: {invoice['supplier']['name']}")
            >>> print(f"Total incl. tax: {invoice['total_incl_tax']} {invoice['currency']}")

            >>> # With original document
            >>> invoice = client.get_incoming_invoice_afnor(flow_id, include_document=True)
            >>> if invoice.get('document_base64'):
            ...     import base64
            ...     pdf_bytes = base64.b64decode(invoice['document_base64'])
            ...     with open(invoice['document_filename'], 'wb') as f:
            ...         f.write(pdf_bytes)
        """
        from .exceptions import FactPulseNotFoundError, FactPulseServiceUnavailableError, parse_api_error

        self.ensure_authenticated()

        url = f"{self.api_url}/api/v1/afnor/incoming-flows/{flow_id}"
        params = {}
        if include_document:
            params["include_document"] = "true"

        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            response = requests.get(url, headers=headers, params=params if params else None, timeout=60)
        except requests.RequestException as e:
            raise FactPulseServiceUnavailableError("FactPulse AFNOR incoming flows", e)

        if response.status_code >= 400:
            try:
                error_json = response.json()
            except Exception:
                error_json = {"detail": response.text or f"HTTP error {response.status_code}"}
            raise parse_api_error(error_json, response.status_code)

        return response.json()


    def healthcheck_afnor(self) -> Dict[str, Any]:
        """Check AFNOR Flow Service availability.

        Returns:
            Dict with status and service

        Example:
            >>> status = client.healthcheck_afnor()
            >>> print(status["status"])  # "ok"
        """
        response = self._make_afnor_request("GET", "/flow/v1/healthcheck")
        return response.json()

    # =========================================================================
    # Chorus Pro
    # =========================================================================

    def _make_chorus_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> requests.Response:
        """Perform a request to the Chorus Pro API with auth and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Relative endpoint (e.g., /structures/rechercher)
            json_data: JSON data (optional)
            params: Query params (optional)

        Returns:
            API response
        """
        from .exceptions import (
            parse_api_error,
            FactPulseServiceUnavailableError,
        )

        self.ensure_authenticated()
        url = f"{self.api_url}/api/v1/chorus-pro{endpoint}"

        headers = {"Authorization": f"Bearer {self._access_token}"}

        # Add credentials to body if zero-trust mode
        if json_data is None:
            json_data = {}
        if self.chorus_credentials:
            json_data["credentials"] = self.chorus_credentials.to_dict()

        try:
            response = requests.request(
                method, url, json=json_data, headers=headers, params=params, timeout=30
            )
        except requests.RequestException as e:
            raise FactPulseServiceUnavailableError("Chorus Pro", e)

        if response.status_code >= 400:
            try:
                error_json = response.json()
            except Exception:
                error_json = {"errorMessage": response.text or f"HTTP error {response.status_code}"}
            raise parse_api_error(error_json, response.status_code)

        return response

    def search_structure_chorus(
        self,
        structure_identifier: Optional[str] = None,
        company_name: Optional[str] = None,
        identifier_type: str = "SIRET",
        restrict_to_private: bool = True,
    ) -> Dict[str, Any]:
        """Search structures on Chorus Pro.

        Args:
            structure_identifier: Structure SIRET or SIREN
            company_name: Company name (partial search)
            identifier_type: Identifier type (SIRET, SIREN, etc.)
            restrict_to_private: If True, limit to private structures

        Returns:
            Dict with liste_structures, total, code_retour, libelle

        Example:
            >>> result = client.search_structure_chorus(structure_identifier="12345678901234")
            >>> for struct in result["liste_structures"]:
            ...     print(struct["id_structure_cpp"], struct["designation_structure"])
        """
        body = {
            "restreindre_structures_privees": restrict_to_private,
        }
        if structure_identifier:
            body["identifiant_structure"] = structure_identifier
        if company_name:
            body["raison_sociale_structure"] = company_name
        if identifier_type:
            body["type_identifiant_structure"] = identifier_type

        response = self._make_chorus_request("POST", "/structures/rechercher", json_data=body)
        return response.json()


    def get_structure_details_chorus(self, structure_cpp_id: int) -> Dict[str, Any]:
        """Get details of a Chorus Pro structure.

        Returns mandatory parameters for submitting an invoice:
        - code_service_doit_etre_renseigne
        - numero_ej_doit_etre_renseigne

        Args:
            structure_cpp_id: Chorus Pro structure ID

        Returns:
            Dict with structure details and parameters

        Example:
            >>> details = client.get_structure_details_chorus(12345)
            >>> if details["parametres"]["code_service_doit_etre_renseigne"]:
            ...     print("Service code required")
        """
        body = {"id_structure_cpp": structure_cpp_id}
        response = self._make_chorus_request("POST", "/structures/consulter", json_data=body)
        return response.json()

    def get_chorus_id_from_siret(
        self,
        siret: str,
        identifier_type: str = "SIRET",
    ) -> Dict[str, Any]:
        """Get Chorus Pro ID from SIRET.

        Convenient shortcut to get id_structure_cpp before submitting an invoice.

        Args:
            siret: SIRET or SIREN number
            identifier_type: Identifier type (SIRET or SIREN)

        Returns:
            Dict with id_structure_cpp, designation_structure, message

        Example:
            >>> result = client.get_chorus_id_from_siret("12345678901234")
            >>> id_cpp = result["id_structure_cpp"]
            >>> if id_cpp > 0:
            ...     print(f"Structure found: {result['designation_structure']}")
        """
        body = {
            "siret": siret,
            "type_identifiant": identifier_type,
        }
        response = self._make_chorus_request("POST", "/structures/obtenir-id-depuis-siret", json_data=body)
        return response.json()

    def list_structure_services_chorus(self, structure_cpp_id: int) -> Dict[str, Any]:
        """List services of a Chorus Pro structure.

        Args:
            structure_cpp_id: Chorus Pro structure ID

        Returns:
            Dict with liste_services, total, code_retour, libelle

        Example:
            >>> services = client.list_structure_services_chorus(12345)
            >>> for svc in services["liste_services"]:
            ...     if svc["est_actif"]:
            ...         print(svc["code_service"], svc["libelle_service"])
        """
        response = self._make_chorus_request("GET", f"/structures/{structure_cpp_id}/services")
        return response.json()

    def submit_invoice_chorus(
        self,
        invoice_number: str,
        invoice_date: str,
        due_date: str,
        structure_cpp_id: int,
        total_excl_tax: str,
        total_vat: str,
        total_incl_tax: str,
        main_attachment_id: Optional[int] = None,
        main_attachment_name: str = "Invoice",
        service_code: Optional[str] = None,
        commitment_number: Optional[str] = None,
        purchase_order_number: Optional[str] = None,
        contract_number: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit an invoice to Chorus Pro.

        **Complete workflow**:
        1. Get id_structure_cpp via search_structure_chorus()
        2. Check mandatory parameters via get_structure_details_chorus()
        3. Upload PDF via /transverses/ajouter-fichier API
        4. Submit invoice with this method

        Args:
            invoice_number: Invoice number
            invoice_date: Invoice date (YYYY-MM-DD)
            due_date: Due date (YYYY-MM-DD)
            structure_cpp_id: Chorus Pro recipient ID
            total_excl_tax: Total excl. tax (e.g., "1000.00")
            total_vat: VAT amount (e.g., "200.00")
            total_incl_tax: Total incl. tax (e.g., "1200.00")
            main_attachment_id: Attachment ID (optional)
            main_attachment_name: Attachment name (default: "Invoice")
            service_code: Service code (if required by structure)
            commitment_number: Commitment number (if required)
            purchase_order_number: Purchase order number
            contract_number: Contract number
            comment: Free comment

        Returns:
            Dict with identifiant_facture_cpp, numero_flux_depot, code_retour, libelle

        Example:
            >>> result = client.submit_invoice_chorus(
            ...     invoice_number="INV-2025-001",
            ...     invoice_date="2025-01-15",
            ...     due_date="2025-02-15",
            ...     structure_cpp_id=12345,
            ...     total_excl_tax="1000.00",
            ...     total_vat="200.00",
            ...     total_incl_tax="1200.00",
            ... )
            >>> print(f"Invoice submitted: {result['identifiant_facture_cpp']}")
        """
        body = {
            "numero_facture": invoice_number,
            "date_facture": invoice_date,
            "date_echeance_paiement": due_date,
            "id_structure_cpp": structure_cpp_id,
            "montant_ht_total": total_excl_tax,
            "montant_tva": total_vat,
            "montant_ttc_total": total_incl_tax,
        }
        if main_attachment_id:
            body["piece_jointe_principale_id"] = main_attachment_id
            body["piece_jointe_principale_designation"] = main_attachment_name
        if service_code:
            body["code_service"] = service_code
        if commitment_number:
            body["numero_engagement"] = commitment_number
        if purchase_order_number:
            body["numero_bon_commande"] = purchase_order_number
        if contract_number:
            body["numero_marche"] = contract_number
        if comment:
            body["commentaire"] = comment

        response = self._make_chorus_request("POST", "/factures/soumettre", json_data=body)
        return response.json()

    def get_invoice_status_chorus(self, invoice_cpp_id: int) -> Dict[str, Any]:
        """Get status of a Chorus Pro invoice.

        Args:
            invoice_cpp_id: Chorus Pro invoice ID

        Returns:
            Dict with statut_courant, numero_facture, date_facture, montant_ttc_total, etc.

        Example:
            >>> status = client.get_invoice_status_chorus(12345)
            >>> print(f"Status: {status['statut_courant']['code']}")
        """
        body = {"identifiant_facture_cpp": invoice_cpp_id}
        response = self._make_chorus_request("POST", "/factures/consulter", json_data=body)
        return response.json()

    # ==================== AFNOR Directory ====================

    def search_siret_afnor(self, siret: str) -> Dict[str, Any]:
        """Search a company by SIRET in the AFNOR directory.

        Args:
            siret: SIRET number (14 digits)

        Returns:
            Dict with company info: company_name, address, etc.

        Example:
            >>> result = client.search_siret_afnor("12345678901234")
            >>> print(f"Company: {result['raison_sociale']}")
        """
        response = self._make_afnor_request("GET", f"/directory/siret/{siret}")
        return response.json()


    def search_siren_afnor(self, siren: str) -> Dict[str, Any]:
        """Search a company by SIREN in the AFNOR directory.

        Args:
            siren: SIREN number (9 digits)

        Returns:
            Dict with company info and list of establishments

        Example:
            >>> result = client.search_siren_afnor("123456789")
            >>> for estab in result.get('etablissements', []):
            ...     print(f"SIRET: {estab['siret']}")
        """
        response = self._make_afnor_request("GET", f"/directory/siren/{siren}")
        return response.json()


    def list_routing_codes_afnor(self, siren: str) -> List[Dict[str, Any]]:
        """List available routing codes for a SIREN.

        Args:
            siren: SIREN number (9 digits)

        Returns:
            List of routing codes with their parameters

        Example:
            >>> codes = client.list_routing_codes_afnor("123456789")
            >>> for code in codes:
            ...     print(f"Code: {code['code_routage']}")
        """
        response = self._make_afnor_request("GET", f"/directory/siren/{siren}/routing-codes")
        return response.json()


    # ==================== Validation ====================

    def validate_facturx_pdf(
        self,
        pdf_path: Optional[str] = None,
        pdf_bytes: Optional[bytes] = None,
        profile: Optional[str] = None,
        use_verapdf: bool = False,
    ) -> Dict[str, Any]:
        """Validate a Factur-X PDF.

        Args:
            pdf_path: Path to PDF file (exclusive with pdf_bytes)
            pdf_bytes: PDF content as bytes (exclusive with pdf_path)
            profile: Expected Factur-X profile (MINIMUM, BASIC, EN16931, EXTENDED).
                If None, profile is auto-detected from embedded XML.
            use_verapdf: Enable strict PDF/A validation with VeraPDF (default: False).
                - False: Fast metadata validation (~100ms)
                - True: Strict ISO 19005 validation with 146+ rules (2-10s, recommended in production)

        Returns:
            Dict with:
                - is_compliant (bool): True if PDF is compliant
                - xml_present (bool): True if Factur-X XML is embedded
                - xml_compliant (bool): True if XML is valid according to Schematron
                - detected_profile (str): Detected profile (MINIMUM, BASIC, EN16931, EXTENDED)
                - xml_errors (list): XML validation errors
                - pdfa_compliant (bool): True if PDF/A compliant
                - pdfa_version (str): Detected PDF/A version (e.g., "PDF/A-3B")
                - pdfa_validation_method (str): "metadata" or "verapdf"
                - pdfa_errors (list): PDF/A compliance errors

        Example:
            >>> # Validation with auto-detected profile
            >>> result = client.validate_facturx_pdf("invoice.pdf")
            >>> print(f"Detected profile: {result['detected_profile']}")

            >>> # Strict validation with VeraPDF (recommended in production)
            >>> result = client.validate_facturx_pdf("invoice.pdf", use_verapdf=True)
            >>> if result['is_compliant']:
            ...     print("Valid Factur-X PDF!")
            >>> else:
            ...     for err in result.get('pdfa_errors', []):
            ...         print(f"PDF/A error: {err}")
        """
        if pdf_path:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
        if not pdf_bytes:
            raise ValueError("pdf_path or pdf_bytes required")

        files = {"pdf_file": ("invoice.pdf", pdf_bytes, "application/pdf")}
        data: Dict[str, Any] = {"use_verapdf": str(use_verapdf).lower()}
        if profile:
            data["profile"] = profile
        response = self._request("POST", "/processing/validate-facturx-pdf", files=files, data=data)
        return response.json()


    def validate_pdf_signature(
        self,
        pdf_path: Optional[str] = None,
        pdf_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Validate the signature of a signed PDF.

        Args:
            pdf_path: Path to signed PDF file
            pdf_bytes: PDF content as bytes

        Returns:
            Dict with: is_signed (bool), signatures (list), etc.

        Example:
            >>> result = client.validate_pdf_signature("signed_invoice.pdf")
            >>> if result['is_signed']:
            ...     print("PDF is signed!")
            ...     for sig in result.get('signatures', []):
            ...         print(f"Signed by: {sig.get('signer_cn')}")
        """
        if pdf_path:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
        if not pdf_bytes:
            raise ValueError("pdf_path or pdf_bytes required")

        files = {"pdf_file": ("document.pdf", pdf_bytes, "application/pdf")}
        response = self._request("POST", "/processing/validate-pdf-signature", files=files)
        return response.json()


    # ==================== Signature ====================

    def sign_pdf(
        self,
        pdf_path: Optional[str] = None,
        pdf_bytes: Optional[bytes] = None,
        reason: Optional[str] = None,
        location: Optional[str] = None,
        contact: Optional[str] = None,
        use_pades_lt: bool = False,
        use_timestamp: bool = True,
        output_path: Optional[str] = None
    ) -> Union[bytes, str]:
        """Sign a PDF with the server-side configured certificate.

        The certificate must be pre-configured in Django Admin
        for the client identified by the JWT client_uid.

        Args:
            pdf_path: Path to PDF to sign
            pdf_bytes: PDF content as bytes
            reason: Signature reason (optional)
            location: Signature location (optional)
            contact: Contact email (optional)
            use_pades_lt: Enable PAdES-B-LT for long-term archiving (default: False)
            use_timestamp: Enable RFC 3161 timestamping (default: True)
            output_path: If provided, save signed PDF to this path

        Returns:
            Signed PDF bytes, or path if output_path provided

        Example:
            >>> signed_pdf = client.sign_pdf(
            ...     pdf_path="invoice.pdf",
            ...     reason="Factur-X Compliance",
            ...     output_path="signed_invoice.pdf"
            ... )
        """
        if pdf_path:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

        if not pdf_bytes:
            raise ValueError("pdf_path or pdf_bytes required")

        files = {
            "pdf_file": ("document.pdf", pdf_bytes, "application/pdf"),
        }
        data: Dict[str, Any] = {
            "use_pades_lt": str(use_pades_lt).lower(),
            "use_timestamp": str(use_timestamp).lower(),
        }
        if reason:
            data["reason"] = reason
        if location:
            data["location"] = location
        if contact:
            data["contact"] = contact

        response = self._request("POST", "/processing/sign-pdf", files=files, data=data)
        result = response.json()

        # API returns JSON with signed_pdf_base64
        pdf_signed_b64 = result.get("signed_pdf_base64")
        if not pdf_signed_b64:
            raise FactPulseValidationError("Invalid signature response")

        import base64
        pdf_signed = base64.b64decode(pdf_signed_b64)

        if output_path:
            with open(output_path, "wb") as f:
                f.write(pdf_signed)
            return output_path

        return pdf_signed


    def generate_test_certificate(
        self,
        cn: str = "Test Organisation",
        organisation: str = "Test Organisation",
        email: str = "test@example.com",
        validity_days: int = 365,
        key_size: int = 2048,
    ) -> Dict[str, Any]:
        """Generate a test certificate for signing (NOT FOR PRODUCTION).

        The generated certificate must then be configured in Django Admin.

        Args:
            cn: Certificate Common Name
            organisation: Organisation name
            email: Email associated with certificate
            validity_days: Validity duration in days (default: 365)
            key_size: RSA key size (2048 or 4096)

        Returns:
            Dict with certificat_pem, cle_privee_pem, pkcs12_base64, etc.

        Example:
            >>> result = client.generate_test_certificate(
            ...     cn="My Company - Seal",
            ...     organisation="My Company SAS",
            ...     email="contact@mycompany.com",
            ... )
            >>> print(result["certificat_pem"])
        """
        data = {
            "cn": cn,
            "organisation": organisation,
            "email": email,
            "validity_days": validity_days,
            "key_size": key_size,
        }
        response = self._request("POST", "/processing/generate-test-certificate", json_data=data)
        return response.json()


    # ==================== Complete workflow ====================

    def generate_complete_facturx(
        self,
        invoice: Dict[str, Any],
        pdf_source_path: Optional[str] = None,
        pdf_source_bytes: Optional[bytes] = None,
        profile: str = "EN16931",
        validate: bool = True,
        sign: bool = False,
        submit_afnor: bool = False,
        afnor_flow_name: Optional[str] = None,
        afnor_tracking_id: Optional[str] = None,
        output_path: Optional[str] = None,
        timeout: int = 120000
    ) -> Dict[str, Any]:
        """Generate a complete Factur-X PDF with optional validation, signing and submission.

        This method automatically chains:
        1. Factur-X PDF generation
        2. Validation (optional)
        3. Signing (optional, uses server-side certificate)
        4. AFNOR PDP submission (optional)

        Note: Signing uses the certificate configured in Django Admin
        for the client identified by the JWT client_uid.

        Args:
            invoice: Invoice data (FactureFacturX format)
            pdf_source_path: Path to source PDF
            pdf_source_bytes: Source PDF as bytes
            profile: Factur-X profile (MINIMUM, BASIC, EN16931, EXTENDED)
            validate: If True, validate generated PDF
            sign: If True, sign PDF (server-side certificate)
            submit_afnor: If True, submit PDF to AFNOR PDP
            afnor_flow_name: AFNOR flow name (default: "Invoice {invoice_number}")
            afnor_tracking_id: AFNOR tracking ID (default: invoice_number)
            output_path: Output path for final PDF
            timeout: Polling timeout in ms

        Returns:
            Dict with:
                - pdf_bytes: Final PDF bytes
                - pdf_path: Path if output_path provided
                - validation: Validation result if validate=True
                - signature: Signature info if sign=True
                - afnor: AFNOR submission result if submit_afnor=True

        Example:
            >>> result = client.generate_complete_facturx(
            ...     invoice=my_invoice,
            ...     pdf_source_path="quote.pdf",
            ...     profile="EN16931",
            ...     validate=True,
            ...     sign=True,
            ...     submit_afnor=True,
            ...     output_path="final_invoice.pdf"
            ... )
            >>> if result['validation']['is_compliant']:
            ...     print(f"Invoice submitted! Flow ID: {result['afnor']['flowId']}")
        """
        result: Dict[str, Any] = {}

        # 1. Generation
        if pdf_source_path:
            with open(pdf_source_path, "rb") as f:
                pdf_source_bytes = f.read()

        pdf_bytes = self.generate_facturx(
            invoice_data=invoice,
            pdf_source=pdf_source_bytes,
            profile=profile,
            timeout=timeout
        )
        result["pdf_bytes"] = pdf_bytes

        # 2. Validation
        if validate:
            validation = self.validate_facturx_pdf(pdf_bytes=pdf_bytes, profile=profile)
            result["validation"] = validation
            if not validation.get("est_conforme", False) and not validation.get("is_compliant", False):
                # Return result with errors
                if output_path:
                    with open(output_path, "wb") as f:
                        f.write(pdf_bytes)
                    result["pdf_path"] = output_path
                return result

        # 3. Signing (uses server-side certificate)
        if sign:
            pdf_bytes = self.sign_pdf(pdf_bytes=pdf_bytes)
            result["pdf_bytes"] = pdf_bytes
            result["signature"] = {"signed": True}

        # 4. AFNOR submission
        if submit_afnor:
            invoice_number = invoice.get("invoiceNumber", invoice.get("numeroFacture", invoice.get("numero_facture", "INVOICE")))
            flow_name = afnor_flow_name or f"Invoice {invoice_number}"
            tracking_id = afnor_tracking_id or invoice_number

            # Direct submission with bytes (no temp file needed)
            afnor_result = self.submit_invoice_afnor(
                flow_name=flow_name,
                pdf_bytes=pdf_bytes,
                pdf_filename=f"{invoice_number}.pdf",
                tracking_id=tracking_id,
            )
            result["afnor"] = afnor_result

        # Final save
        if output_path:
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
            result["pdf_path"] = output_path

        return result
