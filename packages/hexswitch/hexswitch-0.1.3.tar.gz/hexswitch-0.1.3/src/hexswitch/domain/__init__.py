"""Domain layer for HexSwitch framework.

Provides base classes for repositories and services following hexagonal architecture.
"""

from hexswitch.domain.repositories.base_repository import BaseRepository, BaseRepositoryPort
from hexswitch.domain.services.base_service import BaseService

__all__ = [
    "BaseRepository",
    "BaseRepositoryPort",
    "BaseService",
]

