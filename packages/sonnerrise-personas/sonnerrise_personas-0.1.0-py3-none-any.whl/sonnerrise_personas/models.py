"""SQLAlchemy models for Sonnerrise Personas."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sonnerrise_core.models import BaseModel


class Persona(BaseModel):
    """Suno Persona model.

    Represents a voice or style persona that can be referenced
    in track definitions.

    Attributes:
        name: Persona name (up to 48 characters).
        style_of_music: Optional style description (up to 1000 characters).
        parental_track_id: Optional reference to a parent track.
        comments: Optional freeform comments (up to 32KB).
    """

    __tablename__ = "personas"

    name: Mapped[str] = mapped_column(
        String(48),
        nullable=False,
        index=True,
    )
    style_of_music: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    parental_track_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("tracks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    comments: Mapped[str | None] = mapped_column(
        Text(length=32768),
        nullable=True,
    )

    # Relationship will be defined when tracks module is available
    # parental_track = relationship("Track", back_populates="child_personas")

    def __repr__(self) -> str:
        return f"<Persona(id={self.id}, name='{self.name}')>"
