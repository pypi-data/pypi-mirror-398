"""
Standardized response models for the Zoho Creator SDK.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ZohoCreatorResponse(BaseModel):
    """Base model for all Zoho Creator API responses."""

    code: int
    message: Optional[str] = None


class TaskInfo(BaseModel):
    """Model for redirection task information."""

    type: str
    url: str


class SuccessResponse(ZohoCreatorResponse):
    """Model for a successful response with a single data object."""

    data: Dict[str, Any]
    tasks: Optional[Dict[str, TaskInfo]] = None


class ListInfo(BaseModel):
    """Model for pagination information in list responses."""

    more_records: bool = Field(..., alias="moreRecords")
    next_page_token: Optional[str] = Field(None, alias="next_page_token")
    page: Optional[int] = None
    per_page: Optional[int] = None
    count: Optional[int] = None


class ListResponse(ZohoCreatorResponse):
    """Model for a successful response with a list of data objects."""

    data: List[Dict[str, Any]]
    info: Optional[ListInfo] = None


class BulkResult(BaseModel):
    """Model for the result of a single bulk operation."""

    code: int
    message: str
    data: Optional[Dict[str, Any]] = None
    tasks: Optional[Dict[str, TaskInfo]] = None


class BulkResponse(ZohoCreatorResponse):
    """Model for a bulk operation response."""

    result: List[BulkResult]


class ErrorInfo(BaseModel):
    """Model for detailed error information."""

    code: str
    message: str


class ErrorResponse(ZohoCreatorResponse):
    """Model for an error response."""

    description: Optional[str] = None
    error: Optional[Union[Dict[str, Any], List[ErrorInfo]]] = None


class TokenResponse(BaseModel):
    """Model for an OAuth2 token response."""

    access_token: str
    expires_in: int
    api_domain: str
    token_type: str


class StatusResponse(BaseModel):
    """Model for a simple status response."""

    status: str
