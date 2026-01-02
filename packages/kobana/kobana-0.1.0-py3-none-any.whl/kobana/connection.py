"""HTTP connection handling for Kobana SDK."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from kobana.configuration import Configuration
from kobana.errors import (
    APIError,
    ConnectionError,
    ResourceNotFoundError,
    UnauthorizedError,
    ValidationError,
)

logger = logging.getLogger("kobana")


class Connection:
    """Handles HTTP connections to the Kobana API."""

    def __init__(self, configuration: Configuration) -> None:
        """Initialize connection with configuration."""
        self.configuration = configuration
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> httpx.Client:
        """Create a new HTTP client with configured settings."""
        headers = {
            "Authorization": f"Bearer {self.configuration.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "kobana-python-client/0.1.0",
        }
        headers.update(self.configuration.custom_headers)

        return httpx.Client(
            base_url=self.configuration.base_url,
            headers=headers,
            timeout=self.configuration.timeout,
        )

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def _log_request(self, method: str, path: str, **kwargs: Any) -> None:
        """Log request details if debug is enabled."""
        if self.configuration.debug:
            logger.debug(f"Request: {method} {path}")
            if "json" in kwargs:
                logger.debug(f"Body: {kwargs['json']}")
            if "params" in kwargs:
                logger.debug(f"Params: {kwargs['params']}")

    def _log_response(self, response: httpx.Response) -> None:
        """Log response details if debug is enabled."""
        if self.configuration.debug:
            logger.debug(f"Response: {response.status_code}")
            logger.debug(f"Body: {response.text[:500]}")

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate errors."""
        self._log_response(response)

        if response.status_code == 204:
            return {}

        try:
            data = response.json() if response.text else {}
        except ValueError:
            data = {}

        if response.status_code in (200, 201):
            return data

        if response.status_code == 401:
            raise UnauthorizedError()

        if response.status_code == 404:
            raise ResourceNotFoundError()

        if response.status_code == 422:
            errors = data.get("errors", {})
            if isinstance(errors, dict):
                raise ValidationError(errors=errors)
            raise ValidationError(message=str(errors))

        # Handle other error responses
        errors = data.get("errors", [])
        if isinstance(errors, list):
            raise APIError(
                message=f"API request failed with status {response.status_code}",
                status=response.status_code,
                response_body=data,
                errors=errors,
            )

        raise APIError(
            message=f"API request failed with status {response.status_code}",
            status=response.status_code,
            response_body=data,
        )

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request."""
        self._log_request("GET", path, params=params)
        try:
            response = self.client.get(path, params=params)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise ConnectionError(f"Request failed: {e}") from e

    def post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Make a POST request."""
        self._log_request("POST", path, json=data)
        headers = {}
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key

        try:
            response = self.client.post(path, json=data, headers=headers)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise ConnectionError(f"Request failed: {e}") from e

    def put(
        self,
        path: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a PUT request."""
        self._log_request("PUT", path, json=data)
        try:
            response = self.client.put(path, json=data)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise ConnectionError(f"Request failed: {e}") from e

    def delete(self, path: str) -> dict[str, Any]:
        """Make a DELETE request."""
        self._log_request("DELETE", path)
        try:
            response = self.client.delete(path)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise ConnectionError(f"Request failed: {e}") from e

    def get_list(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Make a GET request and return list with pagination metadata."""
        self._log_request("GET", path, params=params)
        try:
            response = self.client.get(path, params=params)
            self._log_response(response)

            if response.status_code != 200:
                self._handle_response(response)

            data = response.json() if response.text else []

            # Extract pagination info from headers
            pagination = {
                "total_count": int(response.headers.get("X-Total-Count", 0)),
                "total_pages": int(response.headers.get("X-Total-Pages", 0)),
                "current_page": int(params.get("page", 1)) if params else 1,
                "per_page": int(params.get("per_page", 25)) if params else 25,
            }

            return data, pagination
        except httpx.RequestError as e:
            raise ConnectionError(f"Request failed: {e}") from e
