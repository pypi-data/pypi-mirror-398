"""LeadsDB Python SDK.

A Python client for the LeadsDB API (https://getleadsdb.com).

Usage:
    # Synchronous client
    from leadsdb import LeadsDB, Lead

    client = LeadsDB("your-api-key")
    lead = client.create(Lead(name="Acme Corp", source="website"))

    # Async client
    from leadsdb import AsyncLeadsDB

    async with AsyncLeadsDB("your-api-key") as client:
        lead = await client.create(Lead(name="Acme Corp", source="website"))
"""

from leadsdb._async_client import AsyncLeadsDB
from leadsdb.client import ExportFormat, LeadsDB
from leadsdb.exceptions import (
    APIError,
    BadRequestError,
    ForbiddenError,
    LeadsDBError,
    NotFoundError,
    RateLimitedError,
    UnauthorizedError,
    ValidationError,
)
from leadsdb.filters import (
    ArrayField,
    AttrField,
    Filter,
    ListOptions,
    LocationField,
    NumberField,
    OrBuilder,
    SortField,
    SortOrder,
    TextField,
    attr,
    attr_sort_field,
    category,
    city,
    country,
    email,
    location,
    name,
    or_,
    phone,
    rating,
    review_count,
    source,
    state,
    tags,
    website,
)
from leadsdb.models import (
    Attribute,
    AttributeType,
    BulkCreateResult,
    BulkLeadError,
    BulkLeadResult,
    Lead,
    ListResult,
    Note,
    UpdateLeadInput,
    bool_attr,
    list_attr,
    number_attr,
    object_attr,
    text_attr,
)

__version__ = "0.9.0"

__all__ = [
    # Version
    "__version__",
    # Clients
    "LeadsDB",
    "AsyncLeadsDB",
    # Models
    "Lead",
    "Note",
    "Attribute",
    "AttributeType",
    "UpdateLeadInput",
    "ListResult",
    "BulkCreateResult",
    "BulkLeadResult",
    "BulkLeadError",
    # Attribute helpers
    "text_attr",
    "number_attr",
    "bool_attr",
    "list_attr",
    "object_attr",
    # Export
    "ExportFormat",
    # Filters
    "Filter",
    "ListOptions",
    "SortField",
    "SortOrder",
    "TextField",
    "NumberField",
    "ArrayField",
    "LocationField",
    "AttrField",
    "OrBuilder",
    # Filter starters
    "city",
    "country",
    "state",
    "name",
    "email",
    "phone",
    "website",
    "category",
    "source",
    "rating",
    "review_count",
    "tags",
    "location",
    "attr",
    "or_",
    "attr_sort_field",
    # Exceptions
    "LeadsDBError",
    "APIError",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
    "RateLimitedError",
    "BadRequestError",
    "ValidationError",
]
