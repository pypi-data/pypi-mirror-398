"""Pydantic schemas for Sonnerrise Definitions."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sonnerrise_definitions.models import (
    ModelVersion,
    PersonaType,
    ServiceType,
    VocalsType,
)


class LinkBase(BaseModel):
    """Base schema for definition links."""

    url: Annotated[
        str,
        Field(max_length=2048, description="URL"),
    ]
    description: Annotated[
        str | None,
        Field(max_length=120, description="Link description"),
    ] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Basic URL validation."""
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class LinkCreate(LinkBase):
    """Schema for creating a link."""

    pass


class LinkRead(LinkBase):
    """Schema for reading a link."""

    model_config = ConfigDict(from_attributes=True)

    id: int


class DefinitionBase(BaseModel):
    """Base schema with common definition fields."""

    title: Annotated[
        str,
        Field(min_length=1, max_length=120, description="Definition title"),
    ]
    annotation: Annotated[
        str | None,
        Field(max_length=200, description="Short annotation"),
    ] = None
    service: Annotated[
        ServiceType,
        Field(description="Music generation service"),
    ] = ServiceType.SUNO
    model: Annotated[
        ModelVersion,
        Field(description="Model version to use"),
    ] = ModelVersion.V4_0
    style_of_music: Annotated[
        str | None,
        Field(max_length=1000, description="Style of music description"),
    ] = None
    older_models_style: Annotated[
        bool,
        Field(description="Limit style to 200 chars for older models"),
    ] = False
    lyrics: Annotated[
        str | None,
        Field(max_length=3000, description="Song lyrics"),
    ] = None
    persona_id: Annotated[
        int | None,
        Field(description="Reference to persona"),
    ] = None
    persona_type: Annotated[
        PersonaType | None,
        Field(description="How to use the persona"),
    ] = None
    vocals: Annotated[
        VocalsType,
        Field(description="Vocal type override"),
    ] = VocalsType.ANY
    audio_influence: Annotated[
        int,
        Field(ge=0, le=100, description="Audio influence weight"),
    ] = 25
    style_influence: Annotated[
        int,
        Field(ge=0, le=100, description="Style influence weight"),
    ] = 50
    weirdness: Annotated[
        int,
        Field(ge=0, le=100, description="Weirdness level"),
    ] = 50
    cover_of_track_id: Annotated[
        int | None,
        Field(description="Track this is a cover of"),
    ] = None
    comments: Annotated[
        str | None,
        Field(max_length=32768, description="Additional comments"),
    ] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not just whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty or whitespace only")
        return v

    @field_validator("style_of_music")
    @classmethod
    def validate_style(cls, v: str | None) -> str | None:
        """Strip whitespace from style."""
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @model_validator(mode="after")
    def validate_style_or_lyrics(self) -> "DefinitionBase":
        """Ensure either style_of_music or lyrics is provided."""
        if not self.style_of_music and not self.lyrics:
            raise ValueError("Either 'style_of_music' or 'lyrics' must be provided")
        return self

    @model_validator(mode="after")
    def validate_older_models_style_length(self) -> "DefinitionBase":
        """If older_models_style is True, validate style length."""
        if self.older_models_style and self.style_of_music:
            if len(self.style_of_music) > 200:
                raise ValueError(
                    "Style of music must be 200 characters or less when 'older_models_style' is enabled"
                )
        return self

    @model_validator(mode="after")
    def validate_persona_type_with_persona(self) -> "DefinitionBase":
        """Ensure persona_type is set when persona_id is provided."""
        if self.persona_id is not None and self.persona_type is None:
            raise ValueError("persona_type must be set when persona_id is provided")
        return self


class DefinitionCreate(DefinitionBase):
    """Schema for creating a new definition."""

    links: list[LinkCreate] = Field(default_factory=list)


class DefinitionUpdate(BaseModel):
    """Schema for updating an existing definition.

    All fields are optional - only provided fields will be updated.
    """

    title: Annotated[
        str | None,
        Field(min_length=1, max_length=120, description="Definition title"),
    ] = None
    annotation: Annotated[
        str | None,
        Field(max_length=200, description="Short annotation"),
    ] = None
    service: ServiceType | None = None
    model: ModelVersion | None = None
    style_of_music: Annotated[
        str | None,
        Field(max_length=1000, description="Style of music description"),
    ] = None
    older_models_style: bool | None = None
    lyrics: Annotated[
        str | None,
        Field(max_length=3000, description="Song lyrics"),
    ] = None
    persona_id: int | None = None
    persona_type: PersonaType | None = None
    vocals: VocalsType | None = None
    audio_influence: Annotated[
        int | None,
        Field(ge=0, le=100, description="Audio influence weight"),
    ] = None
    style_influence: Annotated[
        int | None,
        Field(ge=0, le=100, description="Style influence weight"),
    ] = None
    weirdness: Annotated[
        int | None,
        Field(ge=0, le=100, description="Weirdness level"),
    ] = None
    cover_of_track_id: int | None = None
    comments: Annotated[
        str | None,
        Field(max_length=32768, description="Additional comments"),
    ] = None
    links: list[LinkCreate] | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        """Ensure title is not just whitespace if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Title cannot be empty or whitespace only")
        return v


class DefinitionRead(BaseModel):
    """Schema for reading a definition from the database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    annotation: str | None
    service: ServiceType
    model: ModelVersion
    style_of_music: str | None
    older_models_style: bool
    lyrics: str | None
    persona_id: int | None
    persona_type: PersonaType | None
    vocals: VocalsType
    audio_influence: int
    style_influence: int
    weirdness: int
    cover_of_track_id: int | None
    comments: str | None
    links: list[LinkRead]
    created_at: datetime
    updated_at: datetime


class DefinitionListItem(BaseModel):
    """Schema for definition list items (abbreviated)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    service: ServiceType
    model: ModelVersion
    style_snippet: str | None = None

    @classmethod
    def from_definition(cls, definition) -> "DefinitionListItem":
        """Create from a Definition model instance."""
        style_snippet = None
        if definition.style_of_music:
            style = definition.style_of_music
            style_snippet = style[:30] + "..." if len(style) > 30 else style

        return cls(
            id=definition.id,
            title=definition.title,
            service=definition.service,
            model=definition.model,
            style_snippet=style_snippet,
        )


class DefinitionList(BaseModel):
    """Schema for paginated list of definitions."""

    items: list[DefinitionListItem]
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


class DefinitionFilter(BaseModel):
    """Filter criteria for listing definitions."""

    title: str | None = None
    service: ServiceType | None = None
    model: ModelVersion | None = None
    vocals: VocalsType | None = None
    persona_id: int | None = None
    has_lyrics: bool | None = None
    has_cover: bool | None = None
