"""Repository layer for Sonnerrise Definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func

from sonnerrise_definitions.models import Definition, DefinitionLink
from sonnerrise_definitions.schemas import (
    DefinitionCreate,
    DefinitionFilter,
    DefinitionList,
    DefinitionListItem,
    DefinitionRead,
    DefinitionUpdate,
)

if TYPE_CHECKING:
    from sonnerrise_core.database import DatabasePlugin


class DefinitionNotFoundError(Exception):
    """Raised when a definition is not found."""

    def __init__(self, definition_id: int) -> None:
        self.definition_id = definition_id
        super().__init__(f"Definition with id {definition_id} not found")


class DefinitionRepository:
    """Repository for managing Definition entities.

    Provides CRUD operations, filtering, and search functionality.
    """

    def __init__(self, db: DatabasePlugin) -> None:
        """Initialize the repository.

        Args:
            db: Database plugin instance.
        """
        self._db = db

    def create(self, data: DefinitionCreate) -> DefinitionRead:
        """Create a new definition.

        Args:
            data: Definition creation data.

        Returns:
            The created definition.
        """
        with self._db.session() as session:
            # Create definition without links first
            definition = Definition(
                title=data.title,
                annotation=data.annotation,
                service=data.service,
                model=data.model,
                style_of_music=data.style_of_music,
                older_models_style=data.older_models_style,
                lyrics=data.lyrics,
                persona_id=data.persona_id,
                persona_type=data.persona_type,
                vocals=data.vocals,
                audio_influence=data.audio_influence,
                style_influence=data.style_influence,
                weirdness=data.weirdness,
                cover_of_track_id=data.cover_of_track_id,
                comments=data.comments,
            )
            session.add(definition)
            session.flush()

            # Add links
            for link_data in data.links:
                link = DefinitionLink(
                    definition_id=definition.id,
                    url=link_data.url,
                    description=link_data.description,
                )
                session.add(link)

            session.commit()
            session.refresh(definition)
            return DefinitionRead.model_validate(definition)

    def get(self, definition_id: int) -> DefinitionRead:
        """Get a definition by ID.

        Args:
            definition_id: The definition ID.

        Returns:
            The definition.

        Raises:
            DefinitionNotFoundError: If definition not found.
        """
        with self._db.session() as session:
            definition = session.query(Definition).get(definition_id)
            if definition is None:
                raise DefinitionNotFoundError(definition_id)
            return DefinitionRead.model_validate(definition)

    def get_or_none(self, definition_id: int) -> DefinitionRead | None:
        """Get a definition by ID, returning None if not found.

        Args:
            definition_id: The definition ID.

        Returns:
            The definition or None.
        """
        try:
            return self.get(definition_id)
        except DefinitionNotFoundError:
            return None

    def update(self, definition_id: int, data: DefinitionUpdate) -> DefinitionRead:
        """Update an existing definition.

        Args:
            definition_id: The definition ID.
            data: Update data (only non-None fields are updated).

        Returns:
            The updated definition.

        Raises:
            DefinitionNotFoundError: If definition not found.
        """
        with self._db.session() as session:
            definition = session.query(Definition).get(definition_id)
            if definition is None:
                raise DefinitionNotFoundError(definition_id)

            update_data = data.model_dump(exclude_unset=True, exclude={"links"})
            for field, value in update_data.items():
                setattr(definition, field, value)

            # Update links if provided
            if data.links is not None:
                # Remove existing links
                for link in definition.links:
                    session.delete(link)

                # Add new links
                for link_data in data.links:
                    link = DefinitionLink(
                        definition_id=definition.id,
                        url=link_data.url,
                        description=link_data.description,
                    )
                    session.add(link)

            session.commit()
            session.refresh(definition)
            return DefinitionRead.model_validate(definition)

    def delete(self, definition_id: int) -> bool:
        """Delete a definition.

        Args:
            definition_id: The definition ID.

        Returns:
            True if deleted, False if not found.
        """
        with self._db.session() as session:
            definition = session.query(Definition).get(definition_id)
            if definition is None:
                return False
            session.delete(definition)
            session.commit()
            return True

    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: DefinitionFilter | None = None,
    ) -> DefinitionList:
        """List definitions with pagination and filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page.
            filters: Optional filter criteria.

        Returns:
            Paginated list of definitions.
        """
        with self._db.session() as session:
            query = session.query(Definition)

            # Apply filters
            if filters:
                if filters.title:
                    query = query.filter(
                        Definition.title.ilike(f"%{filters.title}%")
                    )
                if filters.service:
                    query = query.filter(Definition.service == filters.service)
                if filters.model:
                    query = query.filter(Definition.model == filters.model)
                if filters.vocals:
                    query = query.filter(Definition.vocals == filters.vocals)
                if filters.persona_id is not None:
                    query = query.filter(Definition.persona_id == filters.persona_id)
                if filters.has_lyrics is not None:
                    if filters.has_lyrics:
                        query = query.filter(Definition.lyrics.isnot(None))
                    else:
                        query = query.filter(Definition.lyrics.is_(None))
                if filters.has_cover is not None:
                    if filters.has_cover:
                        query = query.filter(Definition.cover_of_track_id.isnot(None))
                    else:
                        query = query.filter(Definition.cover_of_track_id.is_(None))

            # Get total count
            total = query.count()

            # Calculate pagination
            pages = (total + per_page - 1) // per_page if total > 0 else 1
            offset = (page - 1) * per_page

            # Get items
            definitions = (
                query.order_by(Definition.title)
                .offset(offset)
                .limit(per_page)
                .all()
            )

            return DefinitionList(
                items=[DefinitionListItem.from_definition(d) for d in definitions],
                total=total,
                page=page,
                per_page=per_page,
                pages=pages,
            )

    def search(self, query: str, limit: int = 20) -> list[DefinitionRead]:
        """Search definitions by title or style.

        Args:
            query: Search query (substring match).
            limit: Maximum results to return.

        Returns:
            List of matching definitions.
        """
        with self._db.session() as session:
            definitions = (
                session.query(Definition)
                .filter(
                    (Definition.title.ilike(f"%{query}%"))
                    | (Definition.style_of_music.ilike(f"%{query}%"))
                )
                .order_by(Definition.title)
                .limit(limit)
                .all()
            )
            return [DefinitionRead.model_validate(d) for d in definitions]

    def count(self) -> int:
        """Get total count of definitions.

        Returns:
            Total number of definitions.
        """
        with self._db.session() as session:
            return session.query(func.count(Definition.id)).scalar() or 0

    def exists(self, definition_id: int) -> bool:
        """Check if a definition exists.

        Args:
            definition_id: The definition ID.

        Returns:
            True if exists, False otherwise.
        """
        with self._db.session() as session:
            return (
                session.query(Definition.id)
                .filter(Definition.id == definition_id)
                .first()
                is not None
            )

    def get_by_persona(self, persona_id: int) -> list[DefinitionRead]:
        """Get all definitions using a specific persona.

        Args:
            persona_id: The persona ID.

        Returns:
            List of definitions using this persona.
        """
        with self._db.session() as session:
            definitions = (
                session.query(Definition)
                .filter(Definition.persona_id == persona_id)
                .order_by(Definition.title)
                .all()
            )
            return [DefinitionRead.model_validate(d) for d in definitions]

    def add_link(
        self,
        definition_id: int,
        url: str,
        description: str | None = None,
    ) -> DefinitionRead:
        """Add a link to a definition.

        Args:
            definition_id: The definition ID.
            url: The URL to add.
            description: Optional description.

        Returns:
            The updated definition.

        Raises:
            DefinitionNotFoundError: If definition not found.
        """
        with self._db.session() as session:
            definition = session.query(Definition).get(definition_id)
            if definition is None:
                raise DefinitionNotFoundError(definition_id)

            link = DefinitionLink(
                definition_id=definition_id,
                url=url,
                description=description,
            )
            session.add(link)
            session.commit()
            session.refresh(definition)
            return DefinitionRead.model_validate(definition)

    def remove_link(self, definition_id: int, link_id: int) -> DefinitionRead:
        """Remove a link from a definition.

        Args:
            definition_id: The definition ID.
            link_id: The link ID to remove.

        Returns:
            The updated definition.

        Raises:
            DefinitionNotFoundError: If definition not found.
        """
        with self._db.session() as session:
            definition = session.query(Definition).get(definition_id)
            if definition is None:
                raise DefinitionNotFoundError(definition_id)

            link = (
                session.query(DefinitionLink)
                .filter(
                    DefinitionLink.id == link_id,
                    DefinitionLink.definition_id == definition_id,
                )
                .first()
            )
            if link:
                session.delete(link)

            session.commit()
            session.refresh(definition)
            return DefinitionRead.model_validate(definition)
