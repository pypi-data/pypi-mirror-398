"""Synchronous client for the LeadsDB API."""

from __future__ import annotations

import random
import time
from enum import Enum
from typing import TYPE_CHECKING, Iterator

import httpx

from leadsdb.exceptions import (
    RateLimitedError,
    ValidationError,
    raise_for_status,
)
from leadsdb.filters import Filter, ListOptions, SortField, SortOrder
from leadsdb.models import (
    BulkCreateResult,
    Lead,
    ListResult,
    Note,
    UpdateLeadInput,
)

if TYPE_CHECKING:
    from typing import Any

# Constants
DEFAULT_BASE_URL = "https://getleadsdb.com/api/v1"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0
MAX_JITTER = 0.5
MAX_BATCH_SIZE = 100


class ExportFormat(str, Enum):
    """Format for exporting leads."""

    CSV = "csv"
    JSON = "json"


class LeadsDB:
    """Synchronous client for the LeadsDB API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the LeadsDB client.

        Args:
            api_key: Your LeadsDB API key.
            base_url: Base URL for the API (default: https://getleadsdb.com/api/v1).
            timeout: Request timeout in seconds (default: 60).
            max_retries: Maximum number of retry attempts (default: 3).
            http_client: Custom httpx.Client to use (optional).
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries

        if http_client is not None:
            self._client = http_client
            self._owns_client = False
        else:
            self._client = httpx.Client(timeout=timeout)
            self._owns_client = True

    def __enter__(self) -> LeadsDB:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        if self._owns_client:
            self._client.close()

    # Lead CRUD operations

    def get(self, lead_id: str) -> Lead:
        """Get a lead by ID.

        Args:
            lead_id: The lead ID.

        Returns:
            The lead.

        Raises:
            NotFoundError: If the lead is not found.
            ValidationError: If lead_id is empty.
        """
        if not lead_id:
            raise ValidationError("lead_id is required")

        data = self._request("GET", f"/leads/{lead_id}")
        return Lead.model_validate(data)

    def create(self, lead: Lead) -> Lead:
        """Create a new lead.

        Args:
            lead: The lead to create (name and source are required).

        Returns:
            The created lead with ID and timestamps.

        Raises:
            ValidationError: If required fields are missing.
            BadRequestError: If the request is invalid.
        """
        if not lead.name:
            raise ValidationError("name is required")
        if not lead.source:
            raise ValidationError("source is required")

        data = self._request("POST", "/leads", json=lead.to_create_dict())
        # API returns id, created_at, message - merge with original lead
        lead.id = data.get("id", "")
        return lead

    def update(self, lead_id: str, input: UpdateLeadInput) -> Lead:
        """Update a lead by ID.

        Args:
            lead_id: The lead ID.
            input: The fields to update.

        Returns:
            The updated lead.

        Raises:
            NotFoundError: If the lead is not found.
            ValidationError: If lead_id is empty.
        """
        if not lead_id:
            raise ValidationError("lead_id is required")

        data = self._request("PATCH", f"/leads/{lead_id}", json=input.to_update_dict())
        return Lead.model_validate(data)

    def delete(self, lead_id: str) -> None:
        """Delete a lead by ID.

        Args:
            lead_id: The lead ID.

        Raises:
            NotFoundError: If the lead is not found.
            ValidationError: If lead_id is empty.
        """
        if not lead_id:
            raise ValidationError("lead_id is required")

        self._request("DELETE", f"/leads/{lead_id}")

    # List and iteration

    def list(
        self,
        *filters: Filter,
        limit: int | None = None,
        cursor: str | None = None,
        sort_by: SortField | str | None = None,
        sort_order: SortOrder | None = None,
        options: ListOptions | None = None,
    ) -> ListResult:
        """List leads with optional filtering, sorting, and pagination.

        Args:
            *filters: Filter conditions to apply.
            limit: Maximum number of results (default: 50, max: 1000).
            cursor: Pagination cursor from previous response.
            sort_by: Field to sort by.
            sort_order: Sort order (ASC or DESC).
            options: ListOptions object (alternative to individual params).

        Returns:
            ListResult with leads, count, has_more, and next_cursor.

        Example:
            # Using individual filters
            result = client.list(
                city().eq("Berlin"),
                rating().gte(4.0),
                limit=20,
                sort_by=SortField.RATING,
                sort_order=SortOrder.DESC,
            )

            # Using ListOptions
            opts = ListOptions().with_limit(20).with_filter(city().eq("Berlin"))
            result = client.list(options=opts)
        """
        if options is not None:
            params = options.to_params()
        else:
            opts = ListOptions(
                limit=limit,
                cursor=cursor,
                sort_by=sort_by,
                sort_order=sort_order,
            )
            if filters:
                opts = opts.with_filters(*filters)
            params = opts.to_params()

        data = self._request("GET", "/leads", params=params)
        return ListResult.model_validate(data)

    def iterate(
        self,
        *filters: Filter,
        limit: int | None = None,
        sort_by: SortField | str | None = None,
        sort_order: SortOrder | None = None,
        options: ListOptions | None = None,
    ) -> Iterator[Lead]:
        """Iterate over all leads matching the filters.

        Handles pagination automatically.

        Args:
            *filters: Filter conditions to apply.
            limit: Maximum number of results per page (default: 50, max: 1000).
            sort_by: Field to sort by.
            sort_order: Sort order (ASC or DESC).
            options: ListOptions object (alternative to individual params).

        Yields:
            Lead objects matching the filters.

        Example:
            for lead in client.iterate(city().eq("Berlin")):
                print(lead.name)
        """
        cursor: str | None = None

        while True:
            if options is not None:
                opts = ListOptions(
                    limit=options.limit,
                    cursor=cursor,
                    sort_by=options.sort_by,
                    sort_order=options.sort_order,
                    filters=options.filters,
                )
            else:
                opts = ListOptions(
                    limit=limit,
                    cursor=cursor,
                    sort_by=sort_by,
                    sort_order=sort_order,
                )
                if filters:
                    opts = opts.with_filters(*filters)

            result = self.list(options=opts)

            yield from result.leads

            if not result.has_more:
                break
            cursor = result.next_cursor

    # Bulk operations

    def bulk_create(self, leads: list[Lead]) -> BulkCreateResult:
        """Create up to 100 leads in a single request.

        Args:
            leads: List of leads to create (max 100).

        Returns:
            BulkCreateResult with success/failure counts and details.

        Raises:
            ValidationError: If leads is empty or exceeds 100.
        """
        if not leads:
            raise ValidationError("leads is required")
        if len(leads) > MAX_BATCH_SIZE:
            raise ValidationError(f"maximum {MAX_BATCH_SIZE} leads allowed")

        for i, lead in enumerate(leads):
            if not lead.name:
                raise ValidationError(f"lead at index {i}: name is required")
            if not lead.source:
                raise ValidationError(f"lead at index {i}: source is required")

        body = {"leads": [lead.to_create_dict() for lead in leads]}
        data = self._request("POST", "/leads/batch", json=body)
        return BulkCreateResult.model_validate(data)

    # Notes

    def create_note(self, lead_id: str, content: str) -> Note:
        """Create a note for a lead.

        Args:
            lead_id: The lead ID.
            content: The note content.

        Returns:
            The created note.

        Raises:
            NotFoundError: If the lead is not found.
            ValidationError: If lead_id or content is empty.
        """
        if not lead_id:
            raise ValidationError("lead_id is required")
        if not content:
            raise ValidationError("content is required")

        data = self._request("POST", f"/leads/{lead_id}/notes", json={"content": content})
        return Note.model_validate(data)

    def list_notes(self, lead_id: str) -> list[Note]:
        """List all notes for a lead.

        Args:
            lead_id: The lead ID.

        Returns:
            List of notes.

        Raises:
            NotFoundError: If the lead is not found.
            ValidationError: If lead_id is empty.
        """
        if not lead_id:
            raise ValidationError("lead_id is required")

        data = self._request("GET", f"/leads/{lead_id}/notes")
        return [Note.model_validate(note) for note in data]

    def update_note(self, note_id: str, content: str) -> Note:
        """Update a note's content.

        Args:
            note_id: The note ID.
            content: The new content.

        Returns:
            The updated note.

        Raises:
            NotFoundError: If the note is not found.
            ValidationError: If note_id or content is empty.
        """
        if not note_id:
            raise ValidationError("note_id is required")
        if not content:
            raise ValidationError("content is required")

        data = self._request("PUT", f"/leads/notes/{note_id}", json={"content": content})
        return Note.model_validate(data)

    def delete_note(self, note_id: str) -> None:
        """Delete a note.

        Args:
            note_id: The note ID.

        Raises:
            NotFoundError: If the note is not found.
            ValidationError: If note_id is empty.
        """
        if not note_id:
            raise ValidationError("note_id is required")

        self._request("DELETE", f"/leads/notes/{note_id}")

    # Export

    def export(self, format: ExportFormat = ExportFormat.CSV) -> bytes:
        """Export leads in the specified format.

        Args:
            format: Export format (CSV or JSON).

        Returns:
            The exported data as bytes.
        """
        response = self._request_raw("POST", f"/leads/export?format={format.value}")
        return response.content

    # Internal methods

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Make an HTTP request and return the JSON response."""
        response = self._request_raw(method, path, params=params, json=json)

        if response.status_code == 204 or not response.content:
            return {}

        return response.json()

    def _request_raw(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Make an HTTP request with retries."""
        url = f"{self._base_url}{path}"
        headers = {
            "X-API-Key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                response = self._client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json,
                )

                # Success
                if response.status_code < 400:
                    return response

                # Parse error response
                try:
                    error_body = response.json()
                except Exception:
                    error_body = None

                # Check for rate limiting
                retry_after = None
                if response.status_code == 429:
                    retry_after_header = response.headers.get("Retry-After")
                    if retry_after_header:
                        try:
                            retry_after = int(retry_after_header)
                        except ValueError:
                            pass

                # Raise or retry based on status code
                if self._should_retry(response.status_code):
                    last_error = RateLimitedError(retry_after=retry_after)
                    self._backoff(attempt, retry_after)
                    continue

                raise_for_status(response.status_code, error_body)

            except httpx.RequestError as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    self._backoff(attempt, None)
                    continue
                raise

        # If we exhausted retries, raise the last error
        if last_error is not None:
            raise last_error

        raise RuntimeError("Unexpected state: no response and no error")

    def _should_retry(self, status_code: int) -> bool:
        """Check if the request should be retried."""
        return status_code in (429, 500, 502, 503, 504)

    def _backoff(self, attempt: int, retry_after: int | None) -> None:
        """Wait before retrying."""
        if retry_after is not None:
            delay = float(retry_after)
        else:
            delay = DEFAULT_BASE_DELAY * (2**attempt)

        jitter = random.uniform(0, MAX_JITTER)
        time.sleep(delay + jitter)
