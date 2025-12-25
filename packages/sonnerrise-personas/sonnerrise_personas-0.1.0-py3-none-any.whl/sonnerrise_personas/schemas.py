"""Pydantic schemas for Sonnerrise Personas."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PersonaBase(BaseModel):
    """Base schema with common persona fields."""

    name: Annotated[
        str,
        Field(min_length=1, max_length=48, description="Persona name"),
    ]
    style_of_music: Annotated[
        str | None,
        Field(max_length=1000, description="Style of music description"),
    ] = None
    parental_track_id: Annotated[
        int | None,
        Field(description="Reference to parent track"),
    ] = None
    comments: Annotated[
        str | None,
        Field(max_length=32768, description="Additional comments"),
    ] = None

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip()

    @field_validator("style_of_music")
    @classmethod
    def validate_style(cls, v: str | None) -> str | None:
        """Strip whitespace from style if provided."""
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class PersonaCreate(PersonaBase):
    """Schema for creating a new persona."""

    pass


class PersonaUpdate(BaseModel):
    """Schema for updating an existing persona.

    All fields are optional - only provided fields will be updated.
    """

    name: Annotated[
        str | None,
        Field(min_length=1, max_length=48, description="Persona name"),
    ] = None
    style_of_music: Annotated[
        str | None,
        Field(max_length=1000, description="Style of music description"),
    ] = None
    parental_track_id: Annotated[
        int | None,
        Field(description="Reference to parent track"),
    ] = None
    comments: Annotated[
        str | None,
        Field(max_length=32768, description="Additional comments"),
    ] = None

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str | None) -> str | None:
        """Ensure name is not just whitespace if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Name cannot be empty or whitespace only")
        return v


class PersonaRead(PersonaBase):
    """Schema for reading a persona from the database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PersonaList(BaseModel):
    """Schema for paginated list of personas."""

    items: list[PersonaRead]
    total: int
    page: int
    per_page: int
    pages: int

    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1
