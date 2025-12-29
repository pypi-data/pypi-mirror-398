"""Filter builders for querying leads."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self


class SortOrder(str, Enum):
    """Sort order for list queries."""

    ASC = "ASC"
    DESC = "DESC"


class SortField(str, Enum):
    """Known fields for sorting."""

    NAME = "name"
    CITY = "city"
    COUNTRY = "country"
    STATE = "state"
    CATEGORY = "category"
    SOURCE = "source"
    EMAIL = "email"
    PHONE = "phone"
    WEBSITE = "website"
    RATING = "rating"
    REVIEW_COUNT = "review_count"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class _Logic(str, Enum):
    """Filter logic (AND/OR)."""

    AND = "and"
    OR = "or"


@dataclass
class Filter:
    """A single filter condition."""

    logic: _Logic
    operator: str
    field: str
    value: str = ""

    def to_string(self) -> str:
        """Convert to API filter string format."""
        if self.value:
            return f"{self.logic.value}.{self.operator}.{self.field}.{self.value}"
        return f"{self.logic.value}.{self.operator}.{self.field}"


def _format_number(value: float) -> str:
    """Format a number for filter value, removing trailing .0."""
    if value == int(value):
        return str(int(value))
    return str(value)


class TextField:
    """Builder for text field filters."""

    def __init__(self, field: str, logic: _Logic = _Logic.AND) -> None:
        self._field = field
        self._logic = logic

    def eq(self, value: str) -> Filter:
        """Equals (case insensitive)."""
        return Filter(logic=self._logic, operator="eq", field=self._field, value=value)

    def neq(self, value: str) -> Filter:
        """Not equals."""
        return Filter(logic=self._logic, operator="neq", field=self._field, value=value)

    def contains(self, value: str) -> Filter:
        """Contains substring."""
        return Filter(logic=self._logic, operator="contains", field=self._field, value=value)

    def not_contains(self, value: str) -> Filter:
        """Does not contain substring."""
        return Filter(logic=self._logic, operator="not_contains", field=self._field, value=value)

    def is_empty(self) -> Filter:
        """Field is empty."""
        return Filter(logic=self._logic, operator="is_empty", field=self._field)

    def is_not_empty(self) -> Filter:
        """Field is not empty."""
        return Filter(logic=self._logic, operator="is_not_empty", field=self._field)


class NumberField:
    """Builder for numeric field filters."""

    def __init__(self, field: str, logic: _Logic = _Logic.AND) -> None:
        self._field = field
        self._logic = logic

    def eq(self, value: float) -> Filter:
        """Equals."""
        return Filter(
            logic=self._logic, operator="eq", field=self._field, value=_format_number(value)
        )

    def neq(self, value: float) -> Filter:
        """Not equals."""
        return Filter(
            logic=self._logic, operator="neq", field=self._field, value=_format_number(value)
        )

    def gt(self, value: float) -> Filter:
        """Greater than."""
        return Filter(
            logic=self._logic, operator="gt", field=self._field, value=_format_number(value)
        )

    def gte(self, value: float) -> Filter:
        """Greater than or equal."""
        return Filter(
            logic=self._logic, operator="gte", field=self._field, value=_format_number(value)
        )

    def lt(self, value: float) -> Filter:
        """Less than."""
        return Filter(
            logic=self._logic, operator="lt", field=self._field, value=_format_number(value)
        )

    def lte(self, value: float) -> Filter:
        """Less than or equal."""
        return Filter(
            logic=self._logic, operator="lte", field=self._field, value=_format_number(value)
        )


class ArrayField:
    """Builder for array field filters (e.g., tags)."""

    def __init__(self, field: str, logic: _Logic = _Logic.AND) -> None:
        self._field = field
        self._logic = logic

    def contains(self, value: str) -> Filter:
        """Array contains value."""
        return Filter(
            logic=self._logic, operator="array_contains", field=self._field, value=value
        )

    def not_contains(self, value: str) -> Filter:
        """Array does not contain value."""
        return Filter(
            logic=self._logic, operator="array_not_contains", field=self._field, value=value
        )

    def is_empty(self) -> Filter:
        """Array is empty."""
        return Filter(logic=self._logic, operator="array_empty", field=self._field)

    def is_not_empty(self) -> Filter:
        """Array is not empty."""
        return Filter(logic=self._logic, operator="array_not_empty", field=self._field)


class LocationField:
    """Builder for location-based filters."""

    def __init__(self, logic: _Logic = _Logic.AND) -> None:
        self._logic = logic

    def within_radius(self, lat: float, lon: float, km: float) -> Filter:
        """Within radius in kilometers."""
        value = f"{_format_number(lat)},{_format_number(lon)},{_format_number(km)}"
        return Filter(logic=self._logic, operator="within_radius", field="location", value=value)

    def is_set(self) -> Filter:
        """Coordinates are set."""
        return Filter(logic=self._logic, operator="is_set", field="location")

    def is_not_set(self) -> Filter:
        """Coordinates are not set."""
        return Filter(logic=self._logic, operator="is_not_set", field="location")


class AttrField:
    """Builder for custom attribute filters."""

    def __init__(self, name: str, logic: _Logic = _Logic.AND) -> None:
        self._name = name
        self._logic = logic

    @property
    def _field(self) -> str:
        return f"attr:{self._name}"

    def eq(self, value: str) -> Filter:
        """Text equals."""
        return Filter(logic=self._logic, operator="eq", field=self._field, value=value)

    def neq(self, value: str) -> Filter:
        """Text not equals."""
        return Filter(logic=self._logic, operator="neq", field=self._field, value=value)

    def contains(self, value: str) -> Filter:
        """Text contains."""
        return Filter(logic=self._logic, operator="contains", field=self._field, value=value)

    def eq_number(self, value: float) -> Filter:
        """Number equals."""
        return Filter(
            logic=self._logic, operator="eq", field=self._field, value=_format_number(value)
        )

    def gt(self, value: float) -> Filter:
        """Number greater than."""
        return Filter(
            logic=self._logic, operator="gt", field=self._field, value=_format_number(value)
        )

    def gte(self, value: float) -> Filter:
        """Number greater than or equal."""
        return Filter(
            logic=self._logic, operator="gte", field=self._field, value=_format_number(value)
        )

    def lt(self, value: float) -> Filter:
        """Number less than."""
        return Filter(
            logic=self._logic, operator="lt", field=self._field, value=_format_number(value)
        )

    def lte(self, value: float) -> Filter:
        """Number less than or equal."""
        return Filter(
            logic=self._logic, operator="lte", field=self._field, value=_format_number(value)
        )


class OrBuilder:
    """Builder for OR logic filters."""

    def city(self) -> TextField:
        """City field with OR logic."""
        return TextField("city", _Logic.OR)

    def country(self) -> TextField:
        """Country field with OR logic."""
        return TextField("country", _Logic.OR)

    def state(self) -> TextField:
        """State field with OR logic."""
        return TextField("state", _Logic.OR)

    def name(self) -> TextField:
        """Name field with OR logic."""
        return TextField("name", _Logic.OR)

    def email(self) -> TextField:
        """Email field with OR logic."""
        return TextField("email", _Logic.OR)

    def phone(self) -> TextField:
        """Phone field with OR logic."""
        return TextField("phone", _Logic.OR)

    def website(self) -> TextField:
        """Website field with OR logic."""
        return TextField("website", _Logic.OR)

    def category(self) -> TextField:
        """Category field with OR logic."""
        return TextField("category", _Logic.OR)

    def source(self) -> TextField:
        """Source field with OR logic."""
        return TextField("source", _Logic.OR)

    def rating(self) -> NumberField:
        """Rating field with OR logic."""
        return NumberField("rating", _Logic.OR)

    def review_count(self) -> NumberField:
        """Review count field with OR logic."""
        return NumberField("review_count", _Logic.OR)

    def tags(self) -> ArrayField:
        """Tags field with OR logic."""
        return ArrayField("tags", _Logic.OR)

    def location(self) -> LocationField:
        """Location field with OR logic."""
        return LocationField(_Logic.OR)

    def attr(self, name: str) -> AttrField:
        """Custom attribute field with OR logic."""
        return AttrField(name, _Logic.OR)


# Module-level filter starters (default AND logic)


def city() -> TextField:
    """City field filter."""
    return TextField("city")


def country() -> TextField:
    """Country field filter."""
    return TextField("country")


def state() -> TextField:
    """State field filter."""
    return TextField("state")


def name() -> TextField:
    """Name field filter."""
    return TextField("name")


def email() -> TextField:
    """Email field filter."""
    return TextField("email")


def phone() -> TextField:
    """Phone field filter."""
    return TextField("phone")


def website() -> TextField:
    """Website field filter."""
    return TextField("website")


def category() -> TextField:
    """Category field filter."""
    return TextField("category")


def source() -> TextField:
    """Source field filter."""
    return TextField("source")


def rating() -> NumberField:
    """Rating field filter."""
    return NumberField("rating")


def review_count() -> NumberField:
    """Review count field filter."""
    return NumberField("review_count")


def tags() -> ArrayField:
    """Tags field filter."""
    return ArrayField("tags")


def location() -> LocationField:
    """Location field filter."""
    return LocationField()


def attr(name: str) -> AttrField:
    """Custom attribute field filter."""
    return AttrField(name)


def or_() -> OrBuilder:
    """Start an OR filter chain."""
    return OrBuilder()


@dataclass
class ListOptions:
    """Options for listing leads."""

    limit: int | None = None
    cursor: str | None = None
    sort_by: SortField | str | None = None
    sort_order: SortOrder | None = None
    filters: list[Filter] | None = None

    def with_limit(self, limit: int) -> Self:
        """Set the maximum number of results."""
        self.limit = limit
        return self

    def with_cursor(self, cursor: str) -> Self:
        """Set the pagination cursor."""
        self.cursor = cursor
        return self

    def with_sort(self, field: SortField | str, order: SortOrder = SortOrder.ASC) -> Self:
        """Set the sort field and order."""
        self.sort_by = field
        self.sort_order = order
        return self

    def with_filter(self, filter: Filter) -> Self:
        """Add a filter."""
        if self.filters is None:
            self.filters = []
        self.filters.append(filter)
        return self

    def with_filters(self, *filters: Filter) -> Self:
        """Add multiple filters."""
        if self.filters is None:
            self.filters = []
        self.filters.extend(filters)
        return self

    def to_params(self) -> dict[str, str | list[str]]:
        """Convert to query parameters."""
        params: dict[str, str | list[str]] = {}

        if self.limit is not None:
            params["limit"] = str(self.limit)
        if self.cursor:
            params["cursor"] = self.cursor
        if self.sort_by:
            sort_value = self.sort_by.value if isinstance(self.sort_by, SortField) else self.sort_by
            params["sort_by"] = sort_value
        if self.sort_order:
            params["sort_order"] = self.sort_order.value
        if self.filters:
            params["filter"] = [f.to_string() for f in self.filters]

        return params


def attr_sort_field(name: str) -> str:
    """Create a sort field for a custom attribute."""
    return f"attr:{name}"
