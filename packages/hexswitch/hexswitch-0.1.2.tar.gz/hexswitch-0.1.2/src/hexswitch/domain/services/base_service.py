"""Base service class for business logic layer."""

from abc import ABC
import logging
from typing import Generic, List, TypeVar

from hexswitch.domain.repositories.base_repository import BaseRepositoryPort

T = TypeVar('T')
R = TypeVar('R', bound=BaseRepositoryPort)


class BaseService(ABC, Generic[T, R]):
    """Base service class for business logic operations.

    Services contain business logic and coordinate between repositories
    and other services. They depend on repository ports, not implementations.

    Example:
        class ExampleService(BaseService[ExampleEntity, ExampleRepositoryPort]):
            def __init__(self, repository: ExampleRepositoryPort):
                super().__init__(repository)

            def get_by_name(self, name: str) -> ExampleEntity:
                entity = self.repository.find_by_name(name)
                if not entity:
                    raise ValueError(f"Entity with name '{name}' not found")
                return entity
    """

    def __init__(self, repository: R) -> None:
        """Initialize service with repository.

        Args:
            repository: Repository port implementation.
        """
        self.repository = repository
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"{self.__class__.__name__} initialized")

    def get_by_id(self, entity_id: str) -> T:
        """Get entity by ID.

        Args:
            entity_id: Entity ID.

        Returns:
            Entity.

        Raises:
            ValueError: If entity not found.
        """
        entity = self.repository.find_by_id(entity_id)
        if not entity:
            raise ValueError(f"Entity with id '{entity_id}' not found")
        return entity

    def list_all(self) -> List[T]:
        """List all entities.

        Returns:
            List of all entities.
        """
        return self.repository.list_all()

    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID.

        Args:
            entity_id: Entity ID.

        Returns:
            True if deleted, False if not found.
        """
        deleted = self.repository.delete(entity_id)
        if deleted:
            self.logger.info(f"Deleted entity: {entity_id}")
        else:
            self.logger.warning(f"Entity not found for deletion: {entity_id}")
        return deleted

    def exists(self, entity_id: str) -> bool:
        """Check if entity exists.

        Args:
            entity_id: Entity ID.

        Returns:
            True if entity exists, False otherwise.
        """
        return self.repository.exists(entity_id) if hasattr(self.repository, 'exists') else self.repository.find_by_id(entity_id) is not None

    def count(self) -> int:
        """Get total number of entities.

        Returns:
            Number of entities.
        """
        if hasattr(self.repository, 'count'):
            return self.repository.count()
        return len(self.repository.list_all())

