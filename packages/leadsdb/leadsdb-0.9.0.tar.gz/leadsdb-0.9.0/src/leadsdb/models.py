"""Data models for the LeadsDB SDK using Pydantic."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AttributeType(str, Enum):
    """Type of a dynamic attribute."""

    TEXT = "text"
    NUMBER = "number"
    BOOL = "bool"
    LIST = "list"
    OBJECT = "object"


class Attribute(BaseModel):
    """A dynamic key-value attribute on a lead."""

    model_config = ConfigDict(use_enum_values=True)

    name: str
    type: AttributeType
    value: Any


def text_attr(name: str, value: str) -> Attribute:
    """Create a text attribute."""
    return Attribute(name=name, type=AttributeType.TEXT, value=value)


def number_attr(name: str, value: float) -> Attribute:
    """Create a number attribute."""
    return Attribute(name=name, type=AttributeType.NUMBER, value=value)


def bool_attr(name: str, value: bool) -> Attribute:
    """Create a boolean attribute."""
    return Attribute(name=name, type=AttributeType.BOOL, value=value)


def list_attr(name: str, value: list[str]) -> Attribute:
    """Create a list attribute."""
    return Attribute(name=name, type=AttributeType.LIST, value=value)


def object_attr(name: str, value: dict[str, Any]) -> Attribute:
    """Create an object attribute."""
    return Attribute(name=name, type=AttributeType.OBJECT, value=value)


class Note(BaseModel):
    """A note attached to a lead."""

    id: str = ""
    lead_id: str = ""
    content: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def parse_timestamp(cls, v: Any) -> datetime | None:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v)
        return v


class Lead(BaseModel):
    """A business lead in the system."""

    model_config = ConfigDict(populate_by_name=True)

    # Required fields
    name: str
    source: str

    # Core identifiers (set by API)
    id: str = ""

    # Optional description
    description: str = ""

    # Location fields
    address: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    postal_code: str = Field(default="", alias="postal_code")
    latitude: float | None = None
    longitude: float | None = None

    # Contact information
    phone: str = ""
    email: str = ""
    website: str = ""

    # Business metrics
    rating: float | None = None
    review_count: int | None = Field(default=None, alias="review_count")

    # Categorization
    category: str = ""
    tags: list[str] = Field(default_factory=list)

    # Source tracking
    source_id: str = Field(default="", alias="source_id")
    logo_url: str = Field(default="", alias="logo_url")

    # Dynamic attributes
    attributes: list[Attribute] = Field(default_factory=list)

    # Associated notes (populated on get)
    notes: list[Note] = Field(default_factory=list)

    # Timestamps (set by API)
    created_at: datetime | None = Field(default=None, alias="created_at")
    updated_at: datetime | None = Field(default=None, alias="updated_at")

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def parse_timestamp(cls, v: Any) -> datetime | None:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v)
        return v

    def to_create_dict(self) -> dict[str, Any]:
        """Convert to API dict format for create requests (excludes empty fields)."""
        data: dict[str, Any] = {
            "name": self.name,
            "source": self.source,
        }

        # Optional string fields - only include if non-empty
        if self.description:
            data["description"] = self.description
        if self.address:
            data["address"] = self.address
        if self.city:
            data["city"] = self.city
        if self.state:
            data["state"] = self.state
        if self.country:
            data["country"] = self.country
        if self.postal_code:
            data["postal_code"] = self.postal_code
        if self.phone:
            data["phone"] = self.phone
        if self.email:
            data["email"] = self.email
        if self.website:
            data["website"] = self.website
        if self.category:
            data["category"] = self.category
        if self.source_id:
            data["source_id"] = self.source_id
        if self.logo_url:
            data["logo_url"] = self.logo_url

        # Optional numeric fields
        if self.latitude is not None:
            data["latitude"] = self.latitude
        if self.longitude is not None:
            data["longitude"] = self.longitude
        if self.rating is not None:
            data["rating"] = self.rating
        if self.review_count is not None:
            data["review_count"] = self.review_count

        # Lists - only include if non-empty
        if self.tags:
            data["tags"] = self.tags
        if self.attributes:
            data["attributes"] = [attr.model_dump() for attr in self.attributes]

        return data


class UpdateLeadInput(BaseModel):
    """Input for updating an existing lead. Only set fields will be sent."""

    name: str | None = None
    source: str | None = None
    description: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    rating: float | None = None
    review_count: int | None = None
    category: str | None = None
    tags: list[str] | None = None
    source_id: str | None = None
    logo_url: str | None = None
    attributes: list[Attribute] | None = None

    def to_update_dict(self) -> dict[str, Any]:
        """Convert to API dict format, only including explicitly set fields."""
        return self.model_dump(exclude_none=True, by_alias=True)


class BulkLeadResult(BaseModel):
    """Result for a successfully created lead in bulk operation."""

    index: int
    id: str
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_timestamp(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            return v
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v)
        return v


class BulkLeadError(BaseModel):
    """Error for a failed lead in bulk operation."""

    index: int
    message: str


class BulkCreateResult(BaseModel):
    """Result of a bulk create operation."""

    total: int
    success: int
    failed: int
    created: list[BulkLeadResult] = Field(default_factory=list)
    errors: list[BulkLeadError] = Field(default_factory=list)


class ListResult(BaseModel):
    """Result of a list operation."""

    leads: list[Lead] = Field(default_factory=list)
    count: int = 0
    has_more: bool = False
    next_cursor: str = ""
