"""Typed tool-input schemas for agent Function Calling."""

from pydantic import BaseModel, Field, field_validator

from app.storage.models import (
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
)


class CreateIncidentInput(BaseModel):
    """Arguments accepted by the create_incident tool."""

    title: str = Field(
        ...,
        description="Short descriptive title for the organizational incident",
    )
    description: str = Field(
        ...,
        description="Factual description of the reported problem",
    )
    category: IncidentCategory = Field(
        ...,
        description="Incident category",
    )
    severity: IncidentSeverity = Field(
        ...,
        description="Estimated incident severity",
    )

    @field_validator("title", "description")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value cannot be empty or whitespace only")
        return value


class SearchIncidentsInput(BaseModel):
    """Arguments accepted by the search_incidents tool."""

    query: str | None = Field(
        default=None,
        description="Optional text to find in title, description or incident ID",
    )
    status: IncidentStatus | None = Field(
        default=None,
        description="Optional incident-status filter",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of incidents to return",
    )


class AppendIncidentNoteInput(BaseModel):
    """Arguments accepted by the append_incident_note tool."""

    incident_id: str = Field(
        ...,
        description="Public incident identifier such as INC-00001",
    )
    note: str = Field(
        ...,
        description="Follow-up information to append to the incident",
    )

    @field_validator("incident_id", "note")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value cannot be empty or whitespace only")
        return value
