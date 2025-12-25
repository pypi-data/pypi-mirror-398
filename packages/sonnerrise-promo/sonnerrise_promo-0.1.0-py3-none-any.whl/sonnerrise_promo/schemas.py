"""Pydantic schemas for Sonnerrise Promo."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PromoLinkBase(BaseModel):
    """Base schema for promo links."""

    url: Annotated[
        str,
        Field(max_length=2048, description="Promotion URL"),
    ]
    description: Annotated[
        str | None,
        Field(max_length=120, description="Link description/title"),
    ] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Basic URL validation."""
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class PromoLinkCreate(PromoLinkBase):
    """Schema for creating a promo link."""

    pass


class PromoLinkRead(PromoLinkBase):
    """Schema for reading a promo link."""

    model_config = ConfigDict(from_attributes=True)

    id: int


class PromoBase(BaseModel):
    """Base schema with common promo fields."""

    track_id: Annotated[
        int,
        Field(description="Reference to track (required)"),
    ]
    track_art_definition: Annotated[
        str | None,
        Field(max_length=32768, description="AI art generation prompt for still images"),
    ] = None
    track_canvas_definition: Annotated[
        str | None,
        Field(max_length=32768, description="AI art generation prompt for video/canvas"),
    ] = None
    pitch: Annotated[
        str | None,
        Field(max_length=32768, description="Marketing pitch/blurb text"),
    ] = None

    @field_validator("track_art_definition", "track_canvas_definition", "pitch")
    @classmethod
    def strip_text(cls, v: str | None) -> str | None:
        """Strip whitespace from text fields."""
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class PromoCreate(PromoBase):
    """Schema for creating a new promo."""

    links: list[PromoLinkCreate] = Field(default_factory=list)


class PromoUpdate(BaseModel):
    """Schema for updating an existing promo.

    All fields are optional - only provided fields will be updated.
    Note: track_id cannot be changed after creation.
    """

    track_art_definition: Annotated[
        str | None,
        Field(max_length=32768, description="AI art generation prompt for still images"),
    ] = None
    track_canvas_definition: Annotated[
        str | None,
        Field(max_length=32768, description="AI art generation prompt for video/canvas"),
    ] = None
    pitch: Annotated[
        str | None,
        Field(max_length=32768, description="Marketing pitch/blurb text"),
    ] = None
    links: list[PromoLinkCreate] | None = None

    @field_validator("track_art_definition", "track_canvas_definition", "pitch")
    @classmethod
    def strip_text(cls, v: str | None) -> str | None:
        """Strip whitespace from text fields."""
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class PromoRead(BaseModel):
    """Schema for reading a promo from the database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    track_id: int
    track_art_definition: str | None
    track_canvas_definition: str | None
    pitch: str | None
    links: list[PromoLinkRead]
    created_at: datetime
    updated_at: datetime


class PromoListItem(BaseModel):
    """Schema for promo list items (abbreviated)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    track_id: int
    has_art_definition: bool = False
    has_canvas_definition: bool = False
    has_pitch: bool = False
    link_count: int = 0

    @classmethod
    def from_promo(cls, promo) -> "PromoListItem":
        """Create from a Promo model instance."""
        return cls(
            id=promo.id,
            track_id=promo.track_id,
            has_art_definition=bool(promo.track_art_definition),
            has_canvas_definition=bool(promo.track_canvas_definition),
            has_pitch=bool(promo.pitch),
            link_count=len(promo.links) if promo.links else 0,
        )


class PromoList(BaseModel):
    """Schema for paginated list of promos."""

    items: list[PromoListItem]
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


class PromoFilter(BaseModel):
    """Filter criteria for listing promos."""

    track_id: int | None = None
    has_art_definition: bool | None = None
    has_canvas_definition: bool | None = None
    has_pitch: bool | None = None
    has_links: bool | None = None
