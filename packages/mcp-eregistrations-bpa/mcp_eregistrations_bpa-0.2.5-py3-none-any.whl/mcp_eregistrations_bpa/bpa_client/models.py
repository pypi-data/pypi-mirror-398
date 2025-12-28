"""Pydantic models for BPA API responses.

These models provide type-safe representations of BPA API entities.
All models use Pydantic v2 conventions.

Note: These are base models for the most common entities. Additional
models for specific endpoints may be added in future stories.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "BPABaseModel",
    "Service",
    "Registration",
    "FormField",
    "Determinant",
    "Role",
    "Cost",
    "Document",
    "Action",
    "Form",
    "PaginatedResponse",
]


class BPABaseModel(BaseModel):
    """Base model for all BPA entities.

    Provides common configuration for all models.
    """

    model_config = ConfigDict(
        extra="allow",  # Allow unknown fields from API
        populate_by_name=True,  # Support field aliases
        str_strip_whitespace=True,  # Clean string values
    )


class Service(BPABaseModel):
    """BPA Service entity.

    A service represents a government procedure or registration type.
    Services contain registrations, forms, fields, determinants, and roles.
    """

    id: int = Field(description="Unique service identifier")
    name: str = Field(description="Service name")
    short_name: str | None = Field(
        default=None, alias="shortName", description="Short name abbreviation"
    )
    description: str | None = Field(default=None, description="Service description")
    status: str | None = Field(default=None, description="Service status")
    category: str | None = Field(default=None, description="Service category")


class Registration(BPABaseModel):
    """BPA Registration entity.

    A registration is a concrete instance of a service procedure.
    Registrations can link to fields, determinants, costs, and documents.
    """

    id: int = Field(
        description="Unique registration identifier", alias="registration_id"
    )
    name: str = Field(description="Registration name")
    service_id: int | None = Field(
        default=None, alias="serviceId", description="Parent service ID"
    )
    description: str | None = Field(
        default=None, description="Registration description"
    )
    status: str | None = Field(default=None, description="Registration status")


class FormField(BPABaseModel):
    """BPA Form Field entity.

    A field is a data input element in a form. Fields have many-to-many
    relationships with determinants and registrations.
    """

    id: int = Field(description="Unique field identifier", alias="field_id")
    name: str = Field(description="Field name")
    label: str | None = Field(default=None, description="Field label for display")
    type: str | None = Field(default=None, description="Field data type")
    required: bool = Field(default=False, description="Whether field is required")
    description: str | None = Field(default=None, description="Field description")
    service_id: int | None = Field(
        default=None, alias="serviceId", description="Parent service ID"
    )


class Determinant(BPABaseModel):
    """BPA Determinant entity.

    A determinant controls conditional logic and field visibility.
    Determinants have many-to-many relationships with fields and registrations.
    """

    id: int = Field(description="Unique determinant identifier", alias="determinant_id")
    name: str = Field(description="Determinant name")
    type: str | None = Field(default=None, description="Determinant type")
    description: str | None = Field(default=None, description="Determinant description")
    service_id: int | None = Field(
        default=None, alias="serviceId", description="Parent service ID"
    )


class Role(BPABaseModel):
    """BPA Role entity.

    A role represents an actor in the registration process.
    """

    id: int = Field(description="Unique role identifier", alias="role_id")
    name: str = Field(description="Role name")
    description: str | None = Field(default=None, description="Role description")
    service_id: int | None = Field(
        default=None, alias="serviceId", description="Parent service ID"
    )


class Cost(BPABaseModel):
    """BPA Cost entity.

    A cost represents a fee associated with a registration.
    """

    id: int = Field(description="Unique cost identifier", alias="cost_id")
    name: str = Field(description="Cost name")
    amount: float | None = Field(default=None, description="Cost amount")
    currency: str | None = Field(default=None, description="Currency code")
    description: str | None = Field(default=None, description="Cost description")
    registration_id: int | None = Field(
        default=None, alias="registrationId", description="Parent registration ID"
    )


class Document(BPABaseModel):
    """BPA Document entity.

    A document is a file or attachment required for a registration.
    """

    id: int = Field(description="Unique document identifier", alias="document_id")
    name: str = Field(description="Document name")
    type: str | None = Field(default=None, description="Document type/format")
    required: bool = Field(default=False, description="Whether document is required")
    description: str | None = Field(default=None, description="Document description")
    registration_id: int | None = Field(
        default=None, alias="registrationId", description="Parent registration ID"
    )


class Action(BPABaseModel):
    """BPA Action entity.

    An action represents a step or operation in a workflow.
    """

    id: int = Field(description="Unique action identifier", alias="action_id")
    name: str = Field(description="Action name")
    type: str | None = Field(default=None, description="Action type")
    description: str | None = Field(default=None, description="Action description")


class Form(BPABaseModel):
    """BPA Form entity.

    A form is a collection of fields presented as a UI screen.
    """

    id: int = Field(description="Unique form identifier", alias="form_id")
    name: str = Field(description="Form name")
    description: str | None = Field(default=None, description="Form description")
    service_id: int | None = Field(
        default=None, alias="serviceId", description="Parent service ID"
    )


class PaginatedResponse(BPABaseModel):
    """Generic paginated response wrapper.

    Used for API responses that return lists with pagination.
    """

    items: list[dict[str, Any]] = Field(
        default_factory=list, description="List of items"
    )
    total: int | None = Field(default=None, description="Total number of items")
    page: int | None = Field(default=None, description="Current page number")
    page_size: int | None = Field(
        default=None, alias="pageSize", description="Items per page"
    )
    has_more: bool | None = Field(
        default=None, alias="hasMore", description="Whether more pages exist"
    )
