"""Asynchronous client for the LeadsDB API."""

from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING, AsyncIterator

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

from leadsdb.client import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    DEFAULT_BASE_DELAY,
    MAX_BATCH_SIZE,
    MAX_JITTER,
    ExportFormat,
)


class AsyncLeadsDB:
    """Asynchronous client for the LeadsDB API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the async LeadsDB client.

        Args:
            api_key: Your LeadsDB API key.
            base_url: Base URL for the API (default: https://getleadsdb.com/api/v1).
            timeout: Request timeout in seconds (default: 60).
            max_retries: Maximum number of retry attempts (default: 3).
            http_client: Custom httpx.AsyncClient to use (optional).
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries

        if http_client is not None:
            self._client = http_client
            self._owns_client = False
        else:
            self._client = httpx.AsyncClient(timeout=timeout)
            self._owns_client = True

    async def __aenter__(self) -> AsyncLeadsDB:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._owns_client:
            await self._client.aclose()

    # Lead CRUD operations

    async def get(self, lead_id: str) -> Lead:
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

        data = await self._request("GET", f"/leads/{lead_id}")
        return Lead.model_validate(data)

    async def create(self, lead: Lead) -> Lead:
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

        data = await self._request("POST", "/leads", json=lead.to_create_dict())
        lead.id = data.get("id", "")
        return lead

    async def update(self, lead_id: str, input: UpdateLeadInput) -> Lead:
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

        data = await self._request("PATCH", f"/leads/{lead_id}", json=input.to_update_dict())
        return Lead.model_validate(data)

    async def delete(self, lead_id: str) -> None:
        """Delete a lead by ID.

        Args:
            lead_id: The lead ID.

        Raises:
            NotFoundError: If the lead is not found.
            ValidationError: If lead_id is empty.
        """
        if not lead_id:
            raise ValidationError("lead_id is required")

        await self._request("DELETE", f"/leads/{lead_id}")

    # List and iteration

    async def list(
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

        data = await self._request("GET", "/leads", params=params)
        return ListResult.model_validate(data)

    async def iterate(
        self,
        *filters: Filter,
        limit: int | None = None,
        sort_by: SortField | str | None = None,
        sort_order: SortOrder | None = None,
        options: ListOptions | None = None,
    ) -> AsyncIterator[Lead]:
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
            async for lead in client.iterate(city().eq("Berlin")):
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

            result = await self.list(options=opts)

            for lead in result.leads:
                yield lead

            if not result.has_more:
                break
            cursor = result.next_cursor

    # Bulk operations

    async def bulk_create(self, leads: list[Lead]) -> BulkCreateResult:
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
        data = await self._request("POST", "/leads/batch", json=body)
        return BulkCreateResult.model_validate(data)

    # Notes

    async def create_note(self, lead_id: str, content: str) -> Note:
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

        data = await self._request("POST", f"/leads/{lead_id}/notes", json={"content": content})
        return Note.model_validate(data)

    async def list_notes(self, lead_id: str) -> list[Note]:
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

        data = await self._request("GET", f"/leads/{lead_id}/notes")
        return [Note.model_validate(note) for note in data]

    async def update_note(self, note_id: str, content: str) -> Note:
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

        data = await self._request("PUT", f"/leads/notes/{note_id}", json={"content": content})
        return Note.model_validate(data)

    async def delete_note(self, note_id: str) -> None:
        """Delete a note.

        Args:
            note_id: The note ID.

        Raises:
            NotFoundError: If the note is not found.
            ValidationError: If note_id is empty.
        """
        if not note_id:
            raise ValidationError("note_id is required")

        await self._request("DELETE", f"/leads/notes/{note_id}")

    # Export

    async def export(self, format: ExportFormat = ExportFormat.CSV) -> bytes:
        """Export leads in the specified format.

        Args:
            format: Export format (CSV or JSON).

        Returns:
            The exported data as bytes.
        """
        response = await self._request_raw("POST", f"/leads/export?format={format.value}")
        return response.content

    # Internal methods

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Make an HTTP request and return the JSON response."""
        response = await self._request_raw(method, path, params=params, json=json)

        if response.status_code == 204 or not response.content:
            return {}

        return response.json()

    async def _request_raw(
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
                response = await self._client.request(
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
                    await self._backoff(attempt, retry_after)
                    continue

                raise_for_status(response.status_code, error_body)

            except httpx.RequestError as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    await self._backoff(attempt, None)
                    continue
                raise

        # If we exhausted retries, raise the last error
        if last_error is not None:
            raise last_error

        raise RuntimeError("Unexpected state: no response and no error")

    def _should_retry(self, status_code: int) -> bool:
        """Check if the request should be retried."""
        return status_code in (429, 500, 502, 503, 504)

    async def _backoff(self, attempt: int, retry_after: int | None) -> None:
        """Wait before retrying."""
        if retry_after is not None:
            delay = float(retry_after)
        else:
            delay = DEFAULT_BASE_DELAY * (2**attempt)

        jitter = random.uniform(0, MAX_JITTER)
        await asyncio.sleep(delay + jitter)
