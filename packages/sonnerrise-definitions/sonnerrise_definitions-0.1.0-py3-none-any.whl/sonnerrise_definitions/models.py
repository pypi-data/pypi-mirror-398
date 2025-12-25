"""SQLAlchemy models for Sonnerrise Definitions."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sonnerrise_core.models import BaseModel

if TYPE_CHECKING:
    from sonnerrise_personas.models import Persona


class ServiceType(str, enum.Enum):
    """Supported music generation services."""

    SUNO = "suno"


class ModelVersion(str, enum.Enum):
    """Supported Suno model versions."""

    V3_5 = "v3.5"
    V4_0 = "v4.0"
    V4_5_PLUS = "v4.5+"
    V5_0 = "v5.0"


class PersonaType(str, enum.Enum):
    """How a persona is used in a definition."""

    VOICE = "voice"
    STYLE = "style"


class VocalsType(str, enum.Enum):
    """Vocal type override."""

    ANY = "any"
    FEMALE = "female"
    MALE = "male"


class Definition(BaseModel):
    """Suno track generation definition.

    Contains all parameters needed to generate a track with Suno,
    including style, lyrics, persona references, and influence weights.
    """

    __tablename__ = "definitions"

    # Basic info
    title: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )
    annotation: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    # Service configuration
    service: Mapped[ServiceType] = mapped_column(
        Enum(ServiceType),
        nullable=False,
        default=ServiceType.SUNO,
    )
    model: Mapped[ModelVersion] = mapped_column(
        Enum(ModelVersion),
        nullable=False,
        default=ModelVersion.V4_0,
    )

    # Style and lyrics
    style_of_music: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    older_models_style: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    lyrics: Mapped[str | None] = mapped_column(
        Text(length=3000),
        nullable=True,
    )

    # Persona reference
    persona_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("personas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    persona_type: Mapped[PersonaType | None] = mapped_column(
        Enum(PersonaType),
        nullable=True,
    )

    # Vocal settings
    vocals: Mapped[VocalsType] = mapped_column(
        Enum(VocalsType),
        nullable=False,
        default=VocalsType.ANY,
    )

    # Influence weights (0-100)
    audio_influence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=25,
    )
    style_influence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=50,
    )
    weirdness: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=50,
    )

    # Cover reference
    cover_of_track_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("tracks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Comments
    comments: Mapped[str | None] = mapped_column(
        Text(length=32768),
        nullable=True,
    )

    # Relationships
    links: Mapped[list["DefinitionLink"]] = relationship(
        "DefinitionLink",
        back_populates="definition",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # These will be available when respective modules are loaded
    # persona = relationship("Persona", foreign_keys=[persona_id])
    # cover_of_track = relationship("Track", foreign_keys=[cover_of_track_id])
    # tracks = relationship("Track", back_populates="definition")

    def __repr__(self) -> str:
        return f"<Definition(id={self.id}, title='{self.title}')>"


class DefinitionLink(BaseModel):
    """URL link associated with a definition."""

    __tablename__ = "definition_links"

    definition_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    # Relationship
    definition: Mapped[Definition] = relationship(
        "Definition",
        back_populates="links",
    )

    def __repr__(self) -> str:
        return f"<DefinitionLink(id={self.id}, url='{self.url[:50]}...')>"
