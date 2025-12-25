"""Repository layer for Sonnerrise Personas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from sonnerrise_personas.models import Persona
from sonnerrise_personas.schemas import (
    PersonaCreate,
    PersonaList,
    PersonaRead,
    PersonaUpdate,
)

if TYPE_CHECKING:
    from sonnerrise_core.database import DatabasePlugin


class PersonaNotFoundError(Exception):
    """Raised when a persona is not found."""

    def __init__(self, persona_id: int) -> None:
        self.persona_id = persona_id
        super().__init__(f"Persona with id {persona_id} not found")


class PersonaRepository:
    """Repository for managing Persona entities.

    Provides CRUD operations and search functionality for personas.
    """

    def __init__(self, db: DatabasePlugin) -> None:
        """Initialize the repository.

        Args:
            db: Database plugin instance.
        """
        self._db = db

    def create(self, data: PersonaCreate) -> PersonaRead:
        """Create a new persona.

        Args:
            data: Persona creation data.

        Returns:
            The created persona.
        """
        with self._db.session() as session:
            persona = Persona(
                name=data.name,
                style_of_music=data.style_of_music,
                parental_track_id=data.parental_track_id,
                comments=data.comments,
            )
            session.add(persona)
            session.commit()
            session.refresh(persona)
            return PersonaRead.model_validate(persona)

    def get(self, persona_id: int) -> PersonaRead:
        """Get a persona by ID.

        Args:
            persona_id: The persona ID.

        Returns:
            The persona.

        Raises:
            PersonaNotFoundError: If persona not found.
        """
        with self._db.session() as session:
            persona = session.query(Persona).get(persona_id)
            if persona is None:
                raise PersonaNotFoundError(persona_id)
            return PersonaRead.model_validate(persona)

    def get_or_none(self, persona_id: int) -> PersonaRead | None:
        """Get a persona by ID, returning None if not found.

        Args:
            persona_id: The persona ID.

        Returns:
            The persona or None.
        """
        try:
            return self.get(persona_id)
        except PersonaNotFoundError:
            return None

    def update(self, persona_id: int, data: PersonaUpdate) -> PersonaRead:
        """Update an existing persona.

        Args:
            persona_id: The persona ID.
            data: Update data (only non-None fields are updated).

        Returns:
            The updated persona.

        Raises:
            PersonaNotFoundError: If persona not found.
        """
        with self._db.session() as session:
            persona = session.query(Persona).get(persona_id)
            if persona is None:
                raise PersonaNotFoundError(persona_id)

            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(persona, field, value)

            session.commit()
            session.refresh(persona)
            return PersonaRead.model_validate(persona)

    def delete(self, persona_id: int) -> bool:
        """Delete a persona.

        Args:
            persona_id: The persona ID.

        Returns:
            True if deleted, False if not found.
        """
        with self._db.session() as session:
            persona = session.query(Persona).get(persona_id)
            if persona is None:
                return False
            session.delete(persona)
            session.commit()
            return True

    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        name_filter: str | None = None,
    ) -> PersonaList:
        """List personas with pagination.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page.
            name_filter: Optional substring filter for name.

        Returns:
            Paginated list of personas.
        """
        with self._db.session() as session:
            query = session.query(Persona)

            # Apply name filter if provided
            if name_filter:
                query = query.filter(Persona.name.ilike(f"%{name_filter}%"))

            # Get total count
            total = query.count()

            # Calculate pagination
            pages = (total + per_page - 1) // per_page if total > 0 else 1
            offset = (page - 1) * per_page

            # Get items
            personas = (
                query.order_by(Persona.name)
                .offset(offset)
                .limit(per_page)
                .all()
            )

            return PersonaList(
                items=[PersonaRead.model_validate(p) for p in personas],
                total=total,
                page=page,
                per_page=per_page,
                pages=pages,
            )

    def search(self, query: str, limit: int = 20) -> list[PersonaRead]:
        """Search personas by name.

        Args:
            query: Search query (substring match).
            limit: Maximum results to return.

        Returns:
            List of matching personas.
        """
        with self._db.session() as session:
            personas = (
                session.query(Persona)
                .filter(Persona.name.ilike(f"%{query}%"))
                .order_by(Persona.name)
                .limit(limit)
                .all()
            )
            return [PersonaRead.model_validate(p) for p in personas]

    def count(self) -> int:
        """Get total count of personas.

        Returns:
            Total number of personas.
        """
        with self._db.session() as session:
            return session.query(func.count(Persona.id)).scalar() or 0

    def exists(self, persona_id: int) -> bool:
        """Check if a persona exists.

        Args:
            persona_id: The persona ID.

        Returns:
            True if exists, False otherwise.
        """
        with self._db.session() as session:
            return (
                session.query(Persona.id)
                .filter(Persona.id == persona_id)
                .first()
                is not None
            )
