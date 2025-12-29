"""
Core client for the Zoho Creator SDK.
"""

# pylint: disable=too-many-lines

import logging
import time
from collections.abc import Generator, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any, Dict, List, NoReturn, Optional, Tuple, Union, cast

import httpx
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from pydantic import model_validator

from .auth import BaseAuthHandler, get_auth_handler
from .config import ConfigManager
from .exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    NetworkError,
    QuotaExceededError,
    RateLimitError,
    ResourceNotFoundError,
    ServerError,
    ZohoPermissionError,
    ZohoTimeoutError,
)
from .models import (
    APIConfig,
    Application,
    Connection,
    CustomAction,
    FieldConfig,
    Page,
    Permission,
    Record,
    Section,
    Workflow,
)
from .models.response import BulkResponse

logger = logging.getLogger(__name__)


class _FormRecordModel(BaseModel):
    ID: str

    # Accept any additional form fields while requiring the Creator record ID.
    model_config = {"extra": "allow"}


class _MinimalRecordModel(BaseModel):
    ID: Optional[str] = None
    id: Optional[str] = None
    data: Optional[Mapping[str, Any]] = None

    @model_validator(mode="after")
    def _ensure_valid_structure(self) -> "_MinimalRecordModel":
        if self.data is not None:
            if not self.id:
                raise ValueError(
                    "Form-style record must contain 'id' when 'data' is present"
                )
            return self

        if not self.ID:
            raise ValueError(
                "Record must contain 'ID', "
                "or both 'id' and 'data' for form-style records"
            )
        return self


class HTTPClient:
    """HTTP client wrapper for making API requests."""

    def __init__(self, auth_handler: BaseAuthHandler, config: APIConfig) -> None:
        self.auth_handler = auth_handler
        self.config = config
        self.client = httpx.Client(
            timeout=httpx.Timeout(self.config.timeout),
            follow_redirects=True,
        )
        default_headers: Dict[str, str] = {
            "User-Agent": "zoho-creator-sdk/0.1.0",
            "Content-Type": "application/json",
        }
        if getattr(self.config, "environment", None):
            default_headers["environment"] = cast(str, self.config.environment)
        if getattr(self.config, "demo_user_name", None):
            default_headers["demo_user_name"] = cast(str, self.config.demo_user_name)
        self.client.headers.update(default_headers)

    def get(
        self,
        url: str,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Mapping[str, Any]:
        """Perform a GET request."""
        extra_kwargs: Dict[str, Any] = {}
        if headers:
            extra_kwargs["headers"] = headers
        return self._make_request("GET", url, params=params, **extra_kwargs)

    def get_with_response(
        self,
        url: str,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Tuple[Mapping[str, Any], Mapping[str, str]]:
        """Perform a GET request and return both data and response headers."""
        kwargs: Dict[str, Any] = {}
        if params is not None:
            kwargs["params"] = params
        if headers is not None:
            kwargs["headers"] = headers

        # Get authentication headers
        auth_headers = self.auth_handler.get_auth_headers()
        existing_headers = kwargs.get("headers", {})
        kwargs["headers"] = {**existing_headers, **auth_headers}

        logger.debug("Making GET request to %s with response capture", url)
        if kwargs.get("params"):
            logger.debug("Request params: %s", kwargs["params"])

        try:
            response = self._make_request_with_retry("GET", url, **kwargs)
            data = self._process_response(response)
            logger.debug("Response status: %s", response.status_code)
            logger.debug("Response body: %s", data)
            return data, dict(response.headers)
        except AuthenticationError:
            logger.info("Authentication error. Attempting token refresh and retry.")
            try:
                self.auth_handler.refresh_auth()
                auth_headers = self.auth_handler.get_auth_headers()
                existing_headers = kwargs.get("headers", {})
                kwargs["headers"] = {**existing_headers, **auth_headers}
                response = self._make_request_with_retry("GET", url, **kwargs)
                data = self._process_response(response)
                logger.debug("Response status after retry: %s", response.status_code)
                logger.debug("Response body after retry: %s", data)
                return data, dict(response.headers)
            except AuthenticationError as exc:
                logger.error("Failed to refresh authentication token: %s", exc)
                raise

    def post(
        self, url: str, json: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        """Perform a POST request."""
        return self._make_request("POST", url, json=json)

    def patch(
        self, url: str, json: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        """Perform a PATCH request."""
        return self._make_request("PATCH", url, json=json)

    def delete(self, url: str) -> Mapping[str, Any]:
        """Perform a DELETE request."""
        return self._make_request("DELETE", url)

    def _make_request(self, method: str, url: str, **kwargs: Any) -> Mapping[str, Any]:
        """Make an HTTP request with authentication, retries, and error handling."""
        # Get authentication headers
        headers = self.auth_handler.get_auth_headers()
        existing_headers = kwargs.get("headers", {})
        kwargs["headers"] = {**existing_headers, **headers}

        # Log the request
        logger.debug("Making %s request to %s", method, url)
        if kwargs.get("params"):
            logger.debug("Request params: %s", kwargs["params"])
        if kwargs.get("json"):
            logger.debug("Request body: %s", kwargs["json"])

        # Try the request with automatic token refresh on 401 errors
        try:
            response = self._make_request_with_retry(method, url, **kwargs)
            result = self._process_response(response)

            # Log the response
            logger.debug("Response status: %s", response.status_code)
            logger.debug("Response body: %s", result)

            return result
        except AuthenticationError:
            # If we get an authentication error, try refreshing the token once
            logger.info("Authentication error. Attempting token refresh and retry.")
            try:
                self.auth_handler.refresh_auth()
                # Update headers with new token
                headers = self.auth_handler.get_auth_headers()
                existing_headers = kwargs.get("headers", {})
                kwargs["headers"] = {**existing_headers, **headers}
                # Retry the request
                response = self._make_request_with_retry(method, url, **kwargs)
                result = self._process_response(response)

                # Log the response
                logger.debug("Response status after retry: %s", response.status_code)
                logger.debug("Response body after retry: %s", result)

                return result
            except AuthenticationError as e:
                logger.error("Failed to refresh authentication token: %s", e)
                raise

    def _make_request_with_retry(
        self, method: str, url: str, **kwargs: Any
    ) -> httpx.Response:
        """Make an HTTP request with retry logic for server errors."""
        last_exception: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.client.request(method, url, **kwargs)

                # Handle rate limiting (429 errors)
                if response.status_code == 429:
                    retry_after = self._get_retry_after(response)
                    logger.warning(
                        "Rate limit hit (429). Retrying after %s seconds.", retry_after
                    )
                    if attempt < self.config.max_retries:
                        time.sleep(retry_after)
                        continue
                    raise RateLimitError("Rate limit exceeded after retry.")

                # Handle server errors (5xx)
                if response.status_code >= 500:
                    if attempt < self.config.max_retries:
                        delay = self.config.retry_delay * (2**attempt)
                        logger.warning(
                            "Server error (%s). Retrying in %.2f seconds.",
                            response.status_code,
                            delay,
                        )
                        time.sleep(delay)
                        continue
                    # If we've exhausted retries, raise ServerError
                    try:
                        data = response.json()
                        error_message = data.get("message", "Server error")
                        error_code = data.get("code")
                    except ValueError:
                        error_message = f"Server error: {response.status_code}"
                        error_code = None
                    raise ServerError(error_message, response.status_code, error_code)

                return response

            except (httpx.TimeoutException, httpx.ConnectError, NetworkError) as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2**attempt)
                    logger.warning("Network error. Retrying in %.2f seconds.", delay)
                    time.sleep(delay)
                    continue
                if isinstance(e, httpx.TimeoutException):
                    raise TimeoutError(
                        f"Request timed out after {self.config.timeout} seconds."
                    ) from e
                if isinstance(e, httpx.ConnectError):
                    raise NetworkError(f"Connection error: {e}") from e
                raise NetworkError(
                    f"Network error after {self.config.max_retries} retries."
                ) from e

        raise last_exception or APIError("Request failed after retries.")

    def _get_retry_after(self, response: httpx.Response) -> float:
        """Extract the Retry-After value from response headers."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                # Try to parse as HTTP date format
                try:
                    retry_date = datetime.strptime(
                        retry_after, "%a, %d %b %Y %H:%M:%S GMT"
                    ).replace(tzinfo=timezone.utc)
                    return (retry_date - datetime.now(timezone.utc)).total_seconds()
                except ValueError:
                    pass
        return self.config.retry_delay

    def _process_response(self, response: httpx.Response) -> Mapping[str, Any]:
        """Process the HTTP response and handle errors."""
        if 200 <= response.status_code < 300:
            if response.status_code == 204 or not response.text.strip():
                return {}
            try:
                data = response.json()
                return cast(Mapping[str, Any], data)
            except ValueError as exc:
                raise APIError(
                    f"Invalid JSON response: {response.text}",
                    status_code=response.status_code,
                ) from exc
        else:
            try:
                data = response.json()
            except ValueError as exc:
                raise APIError(
                    f"Invalid JSON response: {response.text}",
                    status_code=response.status_code,
                ) from exc
            self._handle_error_response(response, data)

    def _handle_error_response(
        self, response: httpx.Response, data: Mapping[str, Any]
    ) -> NoReturn:
        """Handle API error responses."""
        status_code = response.status_code
        error_message = data.get("message", "Unknown error")
        error_code = data.get("code")

        if status_code == 400:
            raise BadRequestError(error_message, status_code, error_code)
        if status_code == 401:
            raise AuthenticationError(message=error_message, error_code=error_code)
        if status_code == 403:
            raise ZohoPermissionError(error_message, status_code, error_code)
        if status_code == 404:
            raise ResourceNotFoundError(error_message, status_code, error_code)
        if status_code == 408:
            raise ZohoTimeoutError(error_message, status_code, error_code)
        if status_code == 429:
            raise QuotaExceededError(error_message, status_code, error_code)
        if status_code >= 500:
            raise ServerError(error_message, status_code, error_code)

        raise APIError(error_message, status_code, error_code)


class AppContext:
    """Fluent interface helper for application-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        owner_name: str,
        app_name: Optional[str] = None,
    ) -> None:
        self.http_client = http_client
        self.app_link_name: str = app_link_name or app_name or ""
        self.owner_name = owner_name

    def form(
        self, form_link_name: str, form_name: Optional[str] = None
    ) -> "FormContext":
        """Get a form instance for this application."""
        form_name_to_use = form_link_name or form_name
        if not form_name_to_use:
            raise ValueError("Either form_link_name or form_name must be provided")
        return FormContext(
            self.http_client,
            self.app_link_name,
            form_name_to_use,
            self.owner_name,
        )

    def report(
        self, report_link_name: str, report_name: Optional[str] = None
    ) -> "ReportContext":
        """Get a report instance for this application."""
        report_name_to_use = report_link_name or report_name
        if not report_name_to_use:
            raise ValueError("Either report_link_name or report_name must be provided")
        return ReportContext(
            self.http_client,
            self.app_link_name,
            report_name_to_use,
            self.owner_name,
        )

    def workflow(
        self, workflow_link_name: str, workflow_name: Optional[str] = None
    ) -> "WorkflowContext":
        """Get a workflow instance for this application."""
        workflow_name_to_use = workflow_link_name or workflow_name
        if not workflow_name_to_use:
            raise ValueError(
                "Either workflow_link_name or workflow_name must be provided"
            )
        return WorkflowContext(
            self.http_client,
            self.app_link_name,
            workflow_name_to_use,
            self.owner_name,
        )

    def permission(self, permission_id: str) -> "PermissionContext":
        """Get a permission instance for this application."""
        return PermissionContext(
            self.http_client,
            self.app_link_name,
            permission_id,
            self.owner_name,
        )

    def connection(self, connection_id: str) -> "ConnectionContext":
        """Get a connection instance for this application."""
        return ConnectionContext(
            self.http_client,
            self.app_link_name,
            connection_id,
            self.owner_name,
        )

    def custom_action(
        self, custom_action_link_name: str, custom_action_name: Optional[str] = None
    ) -> "CustomActionContext":
        """Get a custom action instance for this application."""
        custom_action_name_to_use = custom_action_link_name or custom_action_name
        if not custom_action_name_to_use:
            raise ValueError(
                "Either custom_action_link_name or custom_action_name must be provided"
            )
        return CustomActionContext(
            self.http_client,
            self.app_link_name,
            custom_action_name_to_use,
            self.owner_name,
        )


class FormContext:
    """Fluent interface helper for form-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        form_link_name: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.form_link_name = form_link_name
        self.owner_name = owner_name

    def add_record(self, data: Mapping[str, Any]) -> Mapping[str, Any]:
        """Add a new record to this form.

        Args:
            data: The record data to add

        Returns:
            Dict containing the created record information
        """
        url = (
            f"{self.http_client.config.base_url}/data/{self.owner_name}/"
            f"{self.app_link_name}/form/{self.form_link_name}"
        )
        payload = {"data": data}
        return self.http_client.post(url, json=payload)

    def add_records(
        self,
        records: List[Mapping[str, Any]],
        *,
        skip_workflow: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
        message: bool = True,
        tasks: bool = False,
    ) -> BulkResponse:
        """Add multiple records to this form in a single API call.

        Args:
            records: List of dictionaries, each representing a record's field data.
            skip_workflow: Optional list of workflow types to skip
                (e.g., ["form_workflow", "schedules"]).
            fields: Optional list of field link names to include in the response data.
            message: Whether to include success message in response (default True).
            tasks: Whether to include task info (redirect URLs) in response
                (default False).

        Returns:
            BulkResponse containing the results of the bulk operation.

        Raises:
            ValueError: If the number of records exceeds the API limit (200).
        """
        # Validate the number of records
        if len(records) > 200:
            raise ValueError("Maximum 200 records can be added in a single request")

        # Construct the URL
        url = (
            f"{self.http_client.config.base_url}/data/{self.owner_name}/"
            f"{self.app_link_name}/form/{self.form_link_name}"
        )

        # Construct the payload
        payload: Dict[str, Any] = {"data": records}

        # Add skip_workflow if provided
        if skip_workflow:
            payload["skip_workflow"] = skip_workflow

        # Add result configuration if needed
        if fields is not None or not message or tasks:
            payload["result"] = {}
            if fields:
                payload["result"]["fields"] = fields
            if not message:
                payload["result"]["message"] = False
            if tasks:
                payload["result"]["tasks"] = True

        # Make the API request
        response_data = self.http_client.post(url, json=payload)

        # Parse and return the response as BulkResponse
        return BulkResponse(**response_data)

    def get_records(
        self,
        *,
        criteria: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Generator[Record, None, None]:
        """Get records from this form with automatic pagination.

        Returns a generator that yields records one by one, automatically
        fetching subsequent pages as needed.

        Args:
            criteria: Optional filtering criteria. Can be a string (legacy format)
                     or a dictionary (structured format with multiple conditions).
            **kwargs: Additional query parameters for the API request

        Yields:
            Record: Individual records from the form
        """
        base_url = self.http_client.config.base_url
        url = (
            f"{base_url}/data/{self.owner_name}/{self.app_link_name}/"
            f"form/{self.form_link_name}"
        )

        params: Dict[str, Any] = dict(kwargs)

        # Handle criteria parameter
        if criteria is not None:
            if isinstance(criteria, dict):
                # Convert structured criteria to API format
                params["criteria"] = self._convert_criteria_to_api_format(criteria)
            else:
                # Use string criteria as-is (legacy format)
                params["criteria"] = criteria

        if (
            "max_records" not in params
            and "limit" not in params
            and "next_page_token" not in params
        ):
            params["max_records"] = self.http_client.config.max_records_per_request

        # Continue fetching pages until no more records are available
        while True:
            current_params = dict(params)
            response_data = self.http_client.get(url, params=current_params)

            # Extract records from the current page
            records_data = response_data.get("data", [])
            if not records_data:
                break

            # Yield each record individually
            for record_data in records_data:
                try:
                    _FormRecordModel(**record_data)
                    yield Record(**record_data)
                except PydanticValidationError as e:
                    raise APIError(f"Failed to parse record data: {e}") from e

            # Check for pagination indicators in the response meta
            meta = response_data.get("meta", {})
            more_records = meta.get("more_records", False)
            next_page_token = meta.get("next_page_token")

            # If there's no more_records, we're done
            if not more_records:
                break

            # If there's a next_page_token, use it for pagination
            if next_page_token:
                params["next_page_token"] = next_page_token
            else:
                # If no token but more_records is True, this shouldn't happen
                # but we'll break to avoid infinite loops
                logger.warning("more_records is True but no next_page_token provided")
                break

    def _convert_criteria_to_api_format(self, criteria: Dict[str, Any]) -> str:
        """Convert structured criteria to API-compatible string format.

        Args:
            criteria: Dictionary containing field conditions

        Returns:
            String representation of criteria for API
        """
        conditions: List[str] = []
        for field, condition in criteria.items():
            if isinstance(condition, list):
                # Handle list of conditions for the same field
                for c in condition:
                    self._process_condition(field, c, conditions)
            else:
                self._process_condition(field, condition, conditions)

        return " && ".join(conditions)

    def _process_condition(
        self, field: str, condition: Any, conditions: List[str]
    ) -> None:
        """Process a single condition and append to conditions list."""
        if isinstance(condition, dict):
            for operator, value in condition.items():
                condition_str = self._format_condition(field, operator, value)
                if condition_str:
                    conditions.append(f"({condition_str})")
        else:
            # Simple equality
            condition_str = self._format_simple_condition(field, condition)
            conditions.append(f"({condition_str})")

    def _format_condition(self, field: str, operator: str, value: Any) -> Optional[str]:
        """Format a single condition based on operator."""
        operator_handlers = {
            "equals": self._handle_equals,
            "not_equals": self._handle_not_equals,
            "greater_than": lambda f, v: f"{f} > {self._quote_value(v)}",
            "greater_than_or_equal": lambda f, v: f"{f} >= {self._quote_value(v)}",
            "less_than": lambda f, v: f"{f} < {self._quote_value(v)}",
            "less_than_or_equal": lambda f, v: f"{f} <= {self._quote_value(v)}",
            "between": self._handle_between,
            "contains": lambda f, v: f'{f}.contains("{v}")',
            "not_contains": lambda f, v: f'!({f}.contains("{v}"))',
            "starts_with": lambda f, v: f'{f}.startsWith("{v}")',
            "ends_with": lambda f, v: f'{f}.endsWith("{v}")',
            "in": self._handle_in,
            "not_in": self._handle_not_in,
            "is_empty": lambda f, v: f'{f} == ""',
            "is_not_empty": lambda f, v: f'{f} != ""',
        }

        handler = operator_handlers.get(operator)
        if handler:
            return handler(field, value)
        return None

    def _quote_value(self, value: Any) -> str:
        """Quote a value if it's a string, otherwise return as string."""
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)

    def _handle_equals(self, field: str, value: Any) -> str:
        """Handle equals operator."""
        return f"{field} == {self._quote_value(value)}"

    def _handle_not_equals(self, field: str, value: Any) -> str:
        """Handle not_equals operator."""
        return f"{field} != {self._quote_value(value)}"

    def _handle_in(self, field: str, value: Any) -> str:
        """Handle in operator."""
        # Quote string values to match Zoho Creator API format
        values_str = ",".join(self._quote_value(v) for v in value)
        return f"{field} in {{{values_str}}}"

    def _handle_not_in(self, field: str, value: Any) -> str:
        """Handle not_in operator."""
        # Quote string values to match Zoho Creator API format
        values_str = ",".join(self._quote_value(v) for v in value)
        return f"{field} not in {{{values_str}}}"

    def _handle_between(self, field: str, value: Any) -> str:
        """Handle between operator."""
        val1 = self._quote_value(value[0])
        val2 = self._quote_value(value[1])
        return f"{field} between {val1} and {val2}"

    def _format_simple_condition(self, field: str, condition: Any) -> str:
        """Format a simple equality condition."""
        return self._handle_equals(field, condition)


class ReportContext:
    """Fluent interface helper for report-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        report_link_name: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.report_link_name = report_link_name
        self.owner_name = owner_name

    def get_records(
        self,
        *,
        field_config: Optional[Union[FieldConfig, str]] = None,
        fields: Optional[Sequence[str]] = None,
        record_cursor: Optional[str] = None,
        criteria: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Generator[Record, None, None]:
        """Get records from this report with automatic pagination.

        Returns a generator that yields records one by one, automatically
        fetching subsequent pages as needed.

        Args:
            field_config: Optional typed value for the field_config parameter.
            fields: Optional list of field link names to request.
            record_cursor: Optional record cursor header for integration reports.
            criteria: Optional filtering criteria. Can be a string (legacy format)
                     or a dictionary (structured format with multiple conditions).
            **kwargs: Additional query parameters for the API request.

        Yields:
            Record: Individual records from the report
        """
        base_url = self.http_client.config.base_url
        url = (
            f"{base_url}/data/{self.owner_name}/{self.app_link_name}/report/"
            f"{self.report_link_name}"
        )

        params: Dict[str, Any] = dict(kwargs)

        # Handle criteria parameter
        if criteria is not None:
            if isinstance(criteria, dict):
                # Convert structured criteria to API format
                params["criteria"] = self._convert_criteria_to_api_format(criteria)
            else:
                # Use string criteria as-is (legacy format)
                params["criteria"] = criteria

        if field_config is not None:
            if isinstance(field_config, FieldConfig):
                params["field_config"] = field_config.value
            else:
                params["field_config"] = str(field_config)

        if fields is not None:
            params["fields"] = ",".join(fields)

        if (
            "max_records" not in params
            and "limit" not in params
            and "next_page_token" not in params
        ):
            params["max_records"] = self.http_client.config.max_records_per_request

        headers: Dict[str, str] = {}
        if record_cursor:
            headers["record_cursor"] = record_cursor

        # Continue fetching pages until no more records are available
        while True:
            current_params = dict(params)
            if headers:
                response_data = self.http_client.get(
                    url, params=current_params, headers=headers
                )
            else:
                response_data = self.http_client.get(url, params=current_params)

            # Extract records from the current page
            records_data = response_data.get("data", [])
            if not records_data:
                break

            # Yield each record individually
            for record_data in records_data:
                try:
                    _MinimalRecordModel(**record_data)
                    yield Record(**record_data)
                except PydanticValidationError as e:
                    raise APIError(f"Failed to parse record data: {e}") from e

            # Check for pagination indicators in the response meta
            meta = response_data.get("meta", {})
            more_records = meta.get("more_records", False)
            next_page_token = meta.get("next_page_token")

            # If there's no more_records, we're done
            if not more_records:
                break

            # If there's a next_page_token, use it for pagination
            if next_page_token:
                params["next_page_token"] = next_page_token
            else:
                # If no token but more_records is True, this shouldn't happen
                # but we'll break to avoid infinite loops
                logger.warning("more_records is True but no next_page_token provided")
                break

    def _convert_criteria_to_api_format(self, criteria: Dict[str, Any]) -> str:
        """Convert structured criteria to API-compatible string format.

        Args:
            criteria: Dictionary containing field conditions

        Returns:
            String representation of criteria for API
        """
        conditions: List[str] = []
        for field, condition in criteria.items():
            if isinstance(condition, list):
                # Handle list of conditions for the same field
                for c in condition:
                    self._process_condition(field, c, conditions)
            else:
                self._process_condition(field, condition, conditions)

        return " && ".join(conditions)

    def _process_condition(
        self, field: str, condition: Any, conditions: List[str]
    ) -> None:
        """Process a single condition and append to conditions list."""
        if isinstance(condition, dict):
            for operator, value in condition.items():
                condition_str = self._format_condition(field, operator, value)
                if condition_str:
                    conditions.append(f"({condition_str})")
        else:
            # Simple equality
            condition_str = self._format_simple_condition(field, condition)
            conditions.append(f"({condition_str})")

    def _format_condition(self, field: str, operator: str, value: Any) -> Optional[str]:
        """Format a single condition based on operator."""
        operator_handlers = {
            "equals": self._handle_equals,
            "not_equals": self._handle_not_equals,
            "greater_than": lambda f, v: f"{f} > {self._quote_value(v)}",
            "greater_than_or_equal": lambda f, v: f"{f} >= {self._quote_value(v)}",
            "less_than": lambda f, v: f"{f} < {self._quote_value(v)}",
            "less_than_or_equal": lambda f, v: f"{f} <= {self._quote_value(v)}",
            "between": self._handle_between,
            "contains": lambda f, v: f'{f}.contains("{v}")',
            "not_contains": lambda f, v: f'!({f}.contains("{v}"))',
            "starts_with": lambda f, v: f'{f}.startsWith("{v}")',
            "ends_with": lambda f, v: f'{f}.endsWith("{v}")',
            "in": self._handle_in,
            "not_in": self._handle_not_in,
            "is_empty": lambda f, v: f'{f} == ""',
            "is_not_empty": lambda f, v: f'{f} != ""',
        }

        handler = operator_handlers.get(operator)
        if handler:
            return handler(field, value)
        return None

    def _quote_value(self, value: Any) -> str:
        """Quote a value if it's a string, otherwise return as string."""
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)

    def _handle_equals(self, field: str, value: Any) -> str:
        """Handle equals operator."""
        return f"{field} == {self._quote_value(value)}"

    def _handle_not_equals(self, field: str, value: Any) -> str:
        """Handle not_equals operator."""
        return f"{field} != {self._quote_value(value)}"

    def _handle_in(self, field: str, value: Any) -> str:
        """Handle in operator."""
        # Quote string values to match Zoho Creator API format
        values_str = ",".join(self._quote_value(v) for v in value)
        return f"{field} in {{{values_str}}}"

    def _handle_not_in(self, field: str, value: Any) -> str:
        """Handle not_in operator."""
        # Quote string values to match Zoho Creator API format
        values_str = ",".join(self._quote_value(v) for v in value)
        return f"{field} not in {{{values_str}}}"

    def _handle_between(self, field: str, value: Any) -> str:
        """Handle between operator."""
        val1 = self._quote_value(value[0])
        val2 = self._quote_value(value[1])
        return f"{field} between {val1} and {val2}"

    def _format_simple_condition(self, field: str, condition: Any) -> str:
        """Format a simple equality condition."""
        return self._handle_equals(field, condition)

    def iter_records_with_cursor(
        self,
        *,
        field_config: Optional[Union[FieldConfig, str]] = None,
        fields: Optional[Sequence[str]] = None,
        record_cursor: Optional[str] = None,
        criteria: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Generator[Record, None, None]:
        """Iterate records using the record_cursor response header.

        This helper is intended for integration form reports where the Zoho
        Creator API returns a ``record_cursor`` header to page through large
        datasets.

        Args:
            field_config: Optional typed value for the field_config parameter.
            fields: Optional list of field link names to request.
            record_cursor: Optional initial record cursor header value.
            criteria: Optional filtering criteria. Can be a string (legacy format)
                     or a dictionary (structured format with multiple conditions).
            **kwargs: Additional query parameters for the API request.

        Yields:
            Record: Individual records from the report across all cursor pages.
        """
        base_url = self.http_client.config.base_url
        url = (
            f"{base_url}/data/{self.owner_name}/{self.app_link_name}/report/"
            f"{self.report_link_name}"
        )

        params: Dict[str, Any] = dict(kwargs)

        # Handle criteria parameter
        if criteria is not None:
            if isinstance(criteria, dict):
                # Convert structured criteria to API format
                params["criteria"] = self._convert_criteria_to_api_format(criteria)
            else:
                # Use string criteria as-is (legacy format)
                params["criteria"] = criteria

        if field_config is not None:
            if isinstance(field_config, FieldConfig):
                params["field_config"] = field_config.value
            else:
                params["field_config"] = str(field_config)

        if fields is not None:
            params["fields"] = ",".join(fields)

        if "max_records" not in params and "limit" not in params:
            params["max_records"] = self.http_client.config.max_records_per_request

        cursor = record_cursor

        while True:
            headers: Dict[str, str] = {}
            if cursor:
                headers["record_cursor"] = cursor

            data, response_headers = self.http_client.get_with_response(
                url, params=params, headers=headers or None
            )

            records_data = data.get("data", [])
            if not records_data:
                break

            for record_data in records_data:
                try:
                    _MinimalRecordModel(**record_data)
                    yield Record(**record_data)
                except PydanticValidationError as exc:
                    raise APIError(f"Failed to parse record data: {exc}") from exc

            cursor = response_headers.get("record_cursor")
            if not cursor:
                break


class WorkflowContext:
    """Fluent interface helper for workflow-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        workflow_link_name: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.workflow_link_name = workflow_link_name
        self.owner_name = owner_name

    def get_workflow(self) -> Workflow:
        """Get the workflow details."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/workflow/{self.workflow_link_name}"
        )
        response_data = self.http_client.get(url)
        try:
            return Workflow(**response_data.get("workflow", {}))
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse workflow data: {e}") from e

    def execute_workflow(self, record_id: str, **kwargs: Any) -> Mapping[str, Any]:
        """Execute the workflow on a specific record."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/workflow/{self.workflow_link_name}/"
            f"{record_id}/execute"
        )
        payload = {"data": kwargs}
        return self.http_client.post(url, json=payload)


class PermissionContext:
    """Fluent interface helper for permission-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        permission_id: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.permission_id = permission_id
        self.owner_name = owner_name

    def get_permission(self) -> Permission:
        """Get the permission details."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/permission/{self.permission_id}"
        )
        response_data = self.http_client.get(url)
        try:
            return Permission(**response_data.get("permission", {}))
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse permission data: {e}") from e

    def update_permission(self, data: Mapping[str, Any]) -> Mapping[str, Any]:
        """Update the permission."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/permission/{self.permission_id}"
        )
        payload = {"data": data}
        return self.http_client.patch(url, json=payload)


class ConnectionContext:
    """Fluent interface helper for connection-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        connection_id: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.connection_id = connection_id
        self.owner_name = owner_name

    def get_connection(self) -> Connection:
        """Get the connection details."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/connection/{self.connection_id}"
        )
        response_data = self.http_client.get(url)
        connection_present = "connection" in response_data
        raw_connection = response_data.get("connection", {})

        try:
            connection = Connection(**raw_connection)
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse connection data: {e}") from e

        # If the API explicitly returns an empty connection object, treat this as
        # invalid data so that higher-level contexts surface an APIError, while
        # still allowing completely missing "connection" fields to succeed.
        if connection_present and not raw_connection:
            raise APIError("Failed to parse connection data: empty payload")

        return connection

    def test_connection(self) -> Mapping[str, Any]:
        """Test the connection."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/connection/{self.connection_id}/test"
        )
        return self.http_client.get(url)


class CustomActionContext:
    """Fluent interface helper for custom action-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        custom_action_link_name: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.custom_action_link_name = custom_action_link_name
        self.owner_name = owner_name

    def get_custom_action(self) -> CustomAction:
        """Get the custom action details."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/customaction/{self.custom_action_link_name}"
        )
        response_data = self.http_client.get(url)
        custom_action_present = "customaction" in response_data
        raw_custom_action = response_data.get("customaction", {})

        try:
            custom_action = CustomAction(**raw_custom_action)
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse custom action data: {e}") from e

        # If the API explicitly returns an empty custom action object, treat this
        # as invalid data so that higher-level contexts surface an APIError,
        # while still allowing completely missing "customaction" fields to
        # succeed.
        if custom_action_present and not raw_custom_action:
            raise APIError("Failed to parse custom action data: empty payload")

        return custom_action

    def execute_custom_action(self, record_id: str, **kwargs: Any) -> Mapping[str, Any]:
        """Execute the custom action on a specific record."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/customaction/{self.custom_action_link_name}/"
            f"{record_id}/execute"
        )
        payload = {"data": kwargs}
        return self.http_client.post(url, json=payload)


class PageContext:
    """Fluent interface helper for page-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        page_link_name: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.page_link_name = page_link_name
        self.owner_name = owner_name

    def get_page(self) -> Page:
        """Get the page details."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/page/{self.page_link_name}"
        )
        response_data = self.http_client.get(url)
        try:
            return Page(**response_data.get("page", {}))
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse page data: {e}") from e


class SectionContext:
    """Fluent interface helper for section-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        section_link_name: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.section_link_name = section_link_name
        self.owner_name = owner_name

    def get_section(self) -> Section:
        """Get the section details."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/section/{self.section_link_name}"
        )
        response_data = self.http_client.get(url)
        try:
            return Section(**response_data.get("section", {}))
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse section data: {e}") from e


class ZohoCreatorClient:
    """The main client module for interacting with Zoho Creator APIs."""

    def __init__(self) -> None:
        """Initialize the Zoho Creator client with zero-config setup."""
        # Create a ConfigManager which will automatically load from env vars and files
        self.config_manager = ConfigManager()

        # Use the loaded config to create the AuthHandler and HTTPClient internally
        self.auth_config = self.config_manager.get_auth_config()
        self.api_config = self.config_manager.get_api_config()

        # Create the auth handler
        self.auth_handler = get_auth_handler(self.auth_config, self.api_config)

        # Create the HTTP client
        self.http_client = HTTPClient(self.auth_handler, self.api_config)

    def workflow(
        self, app_link_name: str, owner_name: str, workflow_link_name: str
    ) -> WorkflowContext:
        """Get a workflow context for fluent interface operations."""
        return WorkflowContext(
            self.http_client, app_link_name, workflow_link_name, owner_name
        )

    def permission(
        self, app_link_name: str, owner_name: str, permission_id: str
    ) -> PermissionContext:
        """Get a permission context for fluent interface operations."""
        return PermissionContext(
            self.http_client, app_link_name, permission_id, owner_name
        )

    def connection(
        self, app_link_name: str, owner_name: str, connection_id: str
    ) -> ConnectionContext:
        """Get a connection context for fluent interface operations."""
        return ConnectionContext(
            self.http_client, app_link_name, connection_id, owner_name
        )

    def custom_action(
        self, app_link_name: str, owner_name: str, custom_action_link_name: str
    ) -> CustomActionContext:
        """Get a custom action context for fluent interface operations."""
        return CustomActionContext(
            self.http_client, app_link_name, custom_action_link_name, owner_name
        )

    def form(
        self, app_link_name: str, owner_name: str, form_link_name: str
    ) -> FormContext:
        """Get a form context for fluent interface operations."""
        return FormContext(self.http_client, app_link_name, form_link_name, owner_name)

    def report(
        self, app_link_name: str, owner_name: str, report_link_name: str
    ) -> ReportContext:
        """Get a report context for fluent interface operations."""
        return ReportContext(
            self.http_client, app_link_name, report_link_name, owner_name
        )

    def page(
        self, app_link_name: str, owner_name: str, page_link_name: str
    ) -> PageContext:
        """Get a page context for fluent interface operations."""
        return PageContext(self.http_client, app_link_name, page_link_name, owner_name)

    def section(
        self, app_link_name: str, owner_name: str, section_link_name: str
    ) -> SectionContext:
        """Get a section context for fluent interface operations."""
        return SectionContext(
            self.http_client, app_link_name, section_link_name, owner_name
        )

    def application(
        self, app_link_name: str, owner_name: str, app_name: Optional[str] = None
    ) -> AppContext:
        """Get an application context for fluent interface operations."""
        return AppContext(self.http_client, app_link_name, owner_name, app_name)

    def get_applications(self, owner_name: str) -> Sequence[Application]:
        """Get all applications."""
        url = f"{self.api_config.base_url}/meta/{owner_name}/applications"
        response_data = self.http_client.get(url)
        try:
            return [Application(**app) for app in response_data.get("applications", [])]
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse application data: {e}") from e

    def get_permissions(
        self, owner_name: str, app_link_name: str
    ) -> Sequence[Permission]:
        """Get all permissions for an application."""
        url = (
            f"{self.api_config.base_url}/settings/{owner_name}/{app_link_name}/"
            "permissions"
        )
        response_data = self.http_client.get(url)
        try:
            return [Permission(**perm) for perm in response_data.get("permissions", [])]
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse permission data: {e}") from e

    def update_record(
        self,
        owner_name: str,
        app_link_name: str,
        report_link_name: str,
        record_id: str,
        *,
        data: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Update an existing record."""
        url = (
            f"{self.api_config.base_url}/data/{owner_name}/{app_link_name}/"
            f"report/{report_link_name}/{record_id}"
        )
        payload = {"data": data}
        return self.http_client.patch(url, json=payload)

    def delete_record(
        self, owner_name: str, app_link_name: str, report_link_name: str, record_id: str
    ) -> Mapping[str, Any]:
        """Delete a record."""
        url = (
            f"{self.api_config.base_url}/data/{owner_name}/{app_link_name}/"
            f"report/{report_link_name}/{record_id}"
        )
        return self.http_client.delete(url)
