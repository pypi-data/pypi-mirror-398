"""Utility helper functions for Callbotics SDK"""
from typing import Dict, Any, Optional
import requests
from ..exceptions import APIError, ResourceNotFoundError, RateLimitError


def make_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    json: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Make HTTP request to Callbotics API with error handling

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        url: Full URL for request
        headers: Request headers (including auth)
        json: JSON body for request
        params: Query parameters
        timeout: Request timeout in seconds

    Returns:
        Response data as dictionary

    Raises:
        APIError: If request fails or returns error status
        ResourceNotFoundError: If resource is not found (404)
        RateLimitError: If rate limit is exceeded (429)
    """
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            params=params,
            timeout=timeout,
        )

        # Handle specific status codes
        if response.status_code == 404:
            raise ResourceNotFoundError(
                f"Resource not found: {url}",
                status_code=404,
                response_data=response.json() if response.content else None,
            )

        if response.status_code == 429:
            raise RateLimitError(
                "API rate limit exceeded",
                status_code=429,
                response_data=response.json() if response.content else None,
            )

        # Parse response
        try:
            data = response.json()
        except ValueError:
            # Response is not JSON
            if response.ok:
                return {"status_code": response.status_code, "data": None}
            else:
                raise APIError(
                    f"API request failed: {response.status_code} - {response.text}",
                    status_code=response.status_code,
                )

        # Check if response indicates error
        if not response.ok or data.get("status_code", 200) >= 400:
            raise APIError(
                f"API error: {data.get('message', 'Unknown error')}",
                status_code=data.get("status_code", response.status_code),
                response_data=data,
            )

        return data

    except requests.RequestException as e:
        raise APIError(f"Request failed: {str(e)}")


def validate_phone_number(phone: str) -> str:
    """
    Validate and format phone number

    Args:
        phone: Phone number string

    Returns:
        Formatted phone number

    Raises:
        ValueError: If phone number is invalid
    """
    # Remove common formatting characters
    cleaned = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # Ensure it starts with + for international format
    if not cleaned.startswith("+"):
        # Assume US number if no country code
        if len(cleaned) == 10:
            cleaned = f"+1{cleaned}"
        else:
            cleaned = f"+{cleaned}"

    # Basic validation
    if len(cleaned) < 11 or not cleaned[1:].isdigit():
        raise ValueError(f"Invalid phone number format: {phone}")

    return cleaned


def build_pagination_params(
    page: int = 1, per_page: int = 10, sort_by: str = "created_at", sort_order: str = "desc"
) -> Dict[str, Any]:
    """
    Build pagination query parameters

    Args:
        page: Page number (1-indexed)
        per_page: Items per page
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)

    Returns:
        Dictionary of query parameters
    """
    return {
        "current_page": page,
        "per_page": per_page,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }
