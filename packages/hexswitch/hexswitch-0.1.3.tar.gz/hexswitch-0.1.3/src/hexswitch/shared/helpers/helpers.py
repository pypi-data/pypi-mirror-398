"""Helper functions for HexSwitch handlers."""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def parse_path_params(path: str, route_path: str) -> dict[str, str]:
    """Parse path parameters from request path.

    Args:
        path: Actual request path (e.g., "/orders/123").
        route_path: Route pattern with parameters (e.g., "/orders/:id").

    Returns:
        Dictionary of path parameters.

    Example:
        >>> parse_path_params("/orders/123", "/orders/:id")
        {"id": "123"}
    """
    params: dict[str, str] = {}

    # Convert route pattern to regex
    pattern = route_path
    param_names: list[str] = []

    # Find all :param patterns
    param_pattern = r":(\w+)"
    matches = re.finditer(param_pattern, pattern)
    for match in matches:
        param_names.append(match.group(1))
        # Replace :param with regex group
        pattern = pattern.replace(match.group(0), r"([^/]+)")

    # Match path against pattern
    regex = re.compile(f"^{pattern}$")
    match = regex.match(path)

    if match:
        # Extract parameter values
        for i, param_name in enumerate(param_names):
            if i + 1 < len(match.groups()) + 1:
                params[param_name] = match.groups()[i]

    return params


def parse_request_body(body: str | None) -> dict[str, Any] | None:
    """Parse request body as JSON.

    Args:
        body: Request body string.

    Returns:
        Parsed JSON as dictionary, or None if body is empty or invalid.

    Example:
        >>> parse_request_body('{"key": "value"}')
        {"key": "value"}
    """
    if not body:
        return None

    try:
        return json.loads(body)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse request body as JSON: {body}")
        return None


def format_response(data: Any, status_code: int = 200) -> dict[str, Any] | tuple[int, dict[str, Any]]:
    """Format response data.

    Args:
        data: Response data (dict, list, or other).
        status_code: HTTP status code (default: 200).

    Returns:
        Response as dict or tuple (status_code, dict).

    Example:
        >>> format_response({"order_id": "123"})
        {"order_id": "123"}
        >>> format_response({"error": "Not found"}, 404)
        (404, {"error": "Not found"})
    """
    if isinstance(data, dict):
        if status_code != 200:
            return (status_code, data)
        return data
    elif isinstance(data, tuple) and len(data) == 2:
        # Already formatted as (status_code, data)
        return data
    else:
        # Wrap in result dict
        response = {"result": data}
        if status_code != 200:
            return (status_code, response)
        return response


def extract_query_params(query_params: dict[str, Any]) -> dict[str, Any]:
    """Extract and normalize query parameters.

    Args:
        query_params: Query parameters dictionary (may contain lists).

    Returns:
        Normalized query parameters (single values, not lists).

    Example:
        >>> extract_query_params({"id": ["123"], "name": "test"})
        {"id": "123", "name": "test"}
    """
    normalized: dict[str, Any] = {}
    for key, value in query_params.items():
        if isinstance(value, list):
            # Take first value if list
            normalized[key] = value[0] if len(value) == 1 else value
        else:
            normalized[key] = value
    return normalized


def prepare_request_data(
    path: str,
    route_path: str,
    method: str | None = None,
    query_params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    body: str | None = None,
) -> dict[str, Any]:
    """Prepare request data dictionary for port handlers.

    Args:
        path: Request path.
        route_path: Route pattern (for path parameter extraction).
        method: HTTP method (optional).
        query_params: Query parameters (optional).
        headers: Request headers (optional).
        body: Request body (optional).

    Returns:
        Request data dictionary.

    Example:
        >>> prepare_request_data("/orders/123", "/orders/:id", "GET", {"filter": "active"})
        {
            "path": "/orders/123",
            "method": "GET",
            "path_params": {"id": "123"},
            "query_params": {"filter": "active"},
            "headers": {},
            "body": None
        }
    """
    request_data: dict[str, Any] = {
        "path": path,
        "path_params": parse_path_params(path, route_path),
        "query_params": extract_query_params(query_params or {}),
        "headers": headers or {},
        "body": parse_request_body(body),
    }

    if method:
        request_data["method"] = method

    return request_data

