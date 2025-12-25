"""Repository layer for Sonnerrise Promo."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func

from sonnerrise_promo.models import Promo, PromoLink
from sonnerrise_promo.schemas import (
    PromoCreate,
    PromoFilter,
    PromoList,
    PromoListItem,
    PromoRead,
    PromoUpdate,
)

if TYPE_CHECKING:
    from sonnerrise_core.database import DatabasePlugin


class PromoNotFoundError(Exception):
    """Raised when a promo is not found."""

    def __init__(self, promo_id: int) -> None:
        self.promo_id = promo_id
        super().__init__(f"Promo with id {promo_id} not found")


class PromoExistsError(Exception):
    """Raised when trying to create a promo for a track that already has one."""

    def __init__(self, track_id: int) -> None:
        self.track_id = track_id
        super().__init__(f"Promo already exists for track {track_id}")


class PromoRepository:
    """Repository for managing Promo entities.

    Provides CRUD operations and filtering for promotion materials.
    """

    def __init__(self, db: DatabasePlugin) -> None:
        """Initialize the repository.

        Args:
            db: Database plugin instance.
        """
        self._db = db

    def create(self, data: PromoCreate) -> PromoRead:
        """Create a new promo.

        Args:
            data: Promo creation data.

        Returns:
            The created promo.

        Raises:
            PromoExistsError: If a promo already exists for the track.
        """
        with self._db.session() as session:
            # Check if promo already exists for this track
            existing = (
                session.query(Promo)
                .filter(Promo.track_id == data.track_id)
                .first()
            )
            if existing:
                raise PromoExistsError(data.track_id)

            promo = Promo(
                track_id=data.track_id,
                track_art_definition=data.track_art_definition,
                track_canvas_definition=data.track_canvas_definition,
                pitch=data.pitch,
            )
            session.add(promo)
            session.flush()

            # Add links
            for link_data in data.links:
                link = PromoLink(
                    promo_id=promo.id,
                    url=link_data.url,
                    description=link_data.description,
                )
                session.add(link)

            session.commit()
            session.refresh(promo)
            return PromoRead.model_validate(promo)

    def get(self, promo_id: int) -> PromoRead:
        """Get a promo by ID.

        Args:
            promo_id: The promo ID.

        Returns:
            The promo.

        Raises:
            PromoNotFoundError: If promo not found.
        """
        with self._db.session() as session:
            promo = session.query(Promo).get(promo_id)
            if promo is None:
                raise PromoNotFoundError(promo_id)
            return PromoRead.model_validate(promo)

    def get_or_none(self, promo_id: int) -> PromoRead | None:
        """Get a promo by ID, returning None if not found.

        Args:
            promo_id: The promo ID.

        Returns:
            The promo or None.
        """
        try:
            return self.get(promo_id)
        except PromoNotFoundError:
            return None

    def get_by_track(self, track_id: int) -> PromoRead | None:
        """Get a promo by track ID.

        Args:
            track_id: The track ID.

        Returns:
            The promo or None if not found.
        """
        with self._db.session() as session:
            promo = (
                session.query(Promo)
                .filter(Promo.track_id == track_id)
                .first()
            )
            if promo is None:
                return None
            return PromoRead.model_validate(promo)

    def update(self, promo_id: int, data: PromoUpdate) -> PromoRead:
        """Update an existing promo.

        Args:
            promo_id: The promo ID.
            data: Update data (only non-None fields are updated).

        Returns:
            The updated promo.

        Raises:
            PromoNotFoundError: If promo not found.
        """
        with self._db.session() as session:
            promo = session.query(Promo).get(promo_id)
            if promo is None:
                raise PromoNotFoundError(promo_id)

            update_data = data.model_dump(exclude_unset=True, exclude={"links"})
            for field, value in update_data.items():
                setattr(promo, field, value)

            # Update links if provided
            if data.links is not None:
                for link in promo.links:
                    session.delete(link)
                for link_data in data.links:
                    link = PromoLink(
                        promo_id=promo.id,
                        url=link_data.url,
                        description=link_data.description,
                    )
                    session.add(link)

            session.commit()
            session.refresh(promo)
            return PromoRead.model_validate(promo)

    def delete(self, promo_id: int) -> bool:
        """Delete a promo.

        Args:
            promo_id: The promo ID.

        Returns:
            True if deleted, False if not found.
        """
        with self._db.session() as session:
            promo = session.query(Promo).get(promo_id)
            if promo is None:
                return False
            session.delete(promo)
            session.commit()
            return True

    def delete_by_track(self, track_id: int) -> bool:
        """Delete a promo by track ID.

        Args:
            track_id: The track ID.

        Returns:
            True if deleted, False if not found.
        """
        with self._db.session() as session:
            promo = (
                session.query(Promo)
                .filter(Promo.track_id == track_id)
                .first()
            )
            if promo is None:
                return False
            session.delete(promo)
            session.commit()
            return True

    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: PromoFilter | None = None,
    ) -> PromoList:
        """List promos with pagination and filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page.
            filters: Optional filter criteria.

        Returns:
            Paginated list of promos.
        """
        with self._db.session() as session:
            query = session.query(Promo)

            # Apply filters
            if filters:
                if filters.track_id is not None:
                    query = query.filter(Promo.track_id == filters.track_id)
                if filters.has_art_definition is not None:
                    if filters.has_art_definition:
                        query = query.filter(Promo.track_art_definition.isnot(None))
                    else:
                        query = query.filter(Promo.track_art_definition.is_(None))
                if filters.has_canvas_definition is not None:
                    if filters.has_canvas_definition:
                        query = query.filter(Promo.track_canvas_definition.isnot(None))
                    else:
                        query = query.filter(Promo.track_canvas_definition.is_(None))
                if filters.has_pitch is not None:
                    if filters.has_pitch:
                        query = query.filter(Promo.pitch.isnot(None))
                    else:
                        query = query.filter(Promo.pitch.is_(None))
                if filters.has_links is not None:
                    if filters.has_links:
                        query = query.filter(Promo.links.any())
                    else:
                        query = query.filter(~Promo.links.any())

            # Get total count
            total = query.count()

            # Calculate pagination
            pages = (total + per_page - 1) // per_page if total > 0 else 1
            offset = (page - 1) * per_page

            # Get items
            promos = (
                query.order_by(Promo.track_id)
                .offset(offset)
                .limit(per_page)
                .all()
            )

            return PromoList(
                items=[PromoListItem.from_promo(p) for p in promos],
                total=total,
                page=page,
                per_page=per_page,
                pages=pages,
            )

    def count(self) -> int:
        """Get total count of promos.

        Returns:
            Total number of promos.
        """
        with self._db.session() as session:
            return session.query(func.count(Promo.id)).scalar() or 0

    def exists(self, promo_id: int) -> bool:
        """Check if a promo exists.

        Args:
            promo_id: The promo ID.

        Returns:
            True if exists, False otherwise.
        """
        with self._db.session() as session:
            return (
                session.query(Promo.id)
                .filter(Promo.id == promo_id)
                .first()
                is not None
            )

    def exists_for_track(self, track_id: int) -> bool:
        """Check if a promo exists for a track.

        Args:
            track_id: The track ID.

        Returns:
            True if exists, False otherwise.
        """
        with self._db.session() as session:
            return (
                session.query(Promo.id)
                .filter(Promo.track_id == track_id)
                .first()
                is not None
            )

    # Link management

    def add_link(
        self,
        promo_id: int,
        url: str,
        description: str | None = None,
    ) -> PromoRead:
        """Add a link to a promo.

        Args:
            promo_id: The promo ID.
            url: The URL to add.
            description: Optional description.

        Returns:
            The updated promo.

        Raises:
            PromoNotFoundError: If promo not found.
        """
        with self._db.session() as session:
            promo = session.query(Promo).get(promo_id)
            if promo is None:
                raise PromoNotFoundError(promo_id)

            link = PromoLink(
                promo_id=promo_id,
                url=url,
                description=description,
            )
            session.add(link)
            session.commit()
            session.refresh(promo)
            return PromoRead.model_validate(promo)

    def remove_link(self, promo_id: int, link_id: int) -> PromoRead:
        """Remove a link from a promo.

        Args:
            promo_id: The promo ID.
            link_id: The link ID to remove.

        Returns:
            The updated promo.

        Raises:
            PromoNotFoundError: If promo not found.
        """
        with self._db.session() as session:
            promo = session.query(Promo).get(promo_id)
            if promo is None:
                raise PromoNotFoundError(promo_id)

            link = (
                session.query(PromoLink)
                .filter(
                    PromoLink.id == link_id,
                    PromoLink.promo_id == promo_id,
                )
                .first()
            )
            if link:
                session.delete(link)

            session.commit()
            session.refresh(promo)
            return PromoRead.model_validate(promo)

    def get_or_create_for_track(self, track_id: int) -> PromoRead:
        """Get existing promo for track or create a new empty one.

        Args:
            track_id: The track ID.

        Returns:
            The existing or newly created promo.
        """
        existing = self.get_by_track(track_id)
        if existing:
            return existing

        return self.create(PromoCreate(track_id=track_id))
