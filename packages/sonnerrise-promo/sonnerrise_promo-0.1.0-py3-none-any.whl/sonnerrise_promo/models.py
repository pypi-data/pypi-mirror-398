"""SQLAlchemy models for Sonnerrise Promo."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sonnerrise_core.models import BaseModel

if TYPE_CHECKING:
    from sonnerrise_tracks.models import Track


class Promo(BaseModel):
    """Promotion materials for a track.

    Contains AI art generation prompts, pitch text, and promotional links
    for marketing and distribution of a track.
    """

    __tablename__ = "promos"

    # Track reference (one promo per track)
    track_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tracks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # AI art generation prompts
    track_art_definition: Mapped[str | None] = mapped_column(
        Text(length=32768),
        nullable=True,
    )
    track_canvas_definition: Mapped[str | None] = mapped_column(
        Text(length=32768),
        nullable=True,
    )

    # Marketing pitch/blurb
    pitch: Mapped[str | None] = mapped_column(
        Text(length=32768),
        nullable=True,
    )

    # Relationships
    links: Mapped[list["PromoLink"]] = relationship(
        "PromoLink",
        back_populates="promo",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Track relationship will be available when tracks module is loaded
    # track = relationship("Track", back_populates="promo")

    def __repr__(self) -> str:
        return f"<Promo(id={self.id}, track_id={self.track_id})>"


class PromoLink(BaseModel):
    """Promotion/media link associated with a promo."""

    __tablename__ = "promo_links"

    promo_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("promos.id", ondelete="CASCADE"),
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
    promo: Mapped[Promo] = relationship(
        "Promo",
        back_populates="links",
    )

    def __repr__(self) -> str:
        return f"<PromoLink(id={self.id}, url='{self.url[:50]}...')>"
