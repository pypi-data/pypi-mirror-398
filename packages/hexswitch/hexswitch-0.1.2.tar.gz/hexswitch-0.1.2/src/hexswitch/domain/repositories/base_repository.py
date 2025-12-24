"""Base repository port and implementation for hexagonal architecture."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar('T')


class BaseRepositoryPort(ABC, Generic[T]):
    """Abstract port interface for repository operations.

    This is the port (interface) that should be defined in the domain layer.
    Services depend on this port, not on concrete implementations.

    Example:
        class ExampleRepositoryPort(BaseRepositoryPort[ExampleEntity]):
            @abstractmethod
            def find_by_name(self, name: str) -> Optional[ExampleEntity]:
    """

    @abstractmethod
    def save(self, entity: T) -> T:
        """Save entity to repository.

        Args:
            entity: Entity to save.

        Returns:
            Saved entity.
        """

    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[T]:
        """Find entity by ID.

        Args:
            entity_id: Entity ID.

        Returns:
            Entity if found, None otherwise.
        """

    @abstractmethod
    def list_all(self) -> List[T]:
        """List all entities.

        Returns:
            List of all entities.
        """

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID.

        Args:
            entity_id: Entity ID.

        Returns:
            True if deleted, False if not found.
        """


class BaseRepository(BaseRepositoryPort[T], Generic[T]):
    """Base repository implementation with common CRUD operations.

    This provides a foundation for concrete repository implementations.
    Subclasses can override methods or add domain-specific methods.

    Example:
        class ExampleRepository(BaseRepository[ExampleEntity]):
            def find_by_name(self, name: str) -> Optional[ExampleEntity]:
                # Custom implementation
                return next(
                    (e for e in self._storage.values() if e.name == name), None
                )
    """

    def __init__(self) -> None:
        """Initialize repository with empty storage."""
        self._storage: Dict[str, T] = {}

    def save(self, entity: T) -> T:
        """Save entity to repository.

        Args:
            entity: Entity to save.

        Returns:
            Saved entity.
        """
        # Assume entity has an 'id' attribute
        entity_id = getattr(entity, 'id', None)
        if entity_id is None:
            raise ValueError("Entity must have an 'id' attribute")

        self._storage[entity_id] = entity
        return entity

    def find_by_id(self, entity_id: str) -> Optional[T]:
        """Find entity by ID.

        Args:
            entity_id: Entity ID.

        Returns:
            Entity if found, None otherwise.
        """
        return self._storage.get(entity_id)

    def list_all(self) -> List[T]:
        """List all entities.

        Returns:
            List of all entities.
        """
        return list(self._storage.values())

    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID.

        Args:
            entity_id: Entity ID.

        Returns:
            True if deleted, False if not found.
        """
        if entity_id in self._storage:
            del self._storage[entity_id]
            return True
        return False

    def count(self) -> int:
        """Get total number of entities.

        Returns:
            Number of entities in repository.
        """
        return len(self._storage)

    def exists(self, entity_id: str) -> bool:
        """Check if entity exists.

        Args:
            entity_id: Entity ID.

        Returns:
            True if entity exists, False otherwise.
        """
        return entity_id in self._storage

    def from_dict(self, data: Dict[str, Any]) -> T:
        """Create entity from dictionary.

        This is a helper method that subclasses should override
        to create domain entities from dictionaries.

        Args:
            data: Dictionary containing entity data.

        Returns:
            Created entity.

        Raises:
            NotImplementedError: If not overridden by subclass.
        """
        raise NotImplementedError("Subclasses must implement from_dict()")
