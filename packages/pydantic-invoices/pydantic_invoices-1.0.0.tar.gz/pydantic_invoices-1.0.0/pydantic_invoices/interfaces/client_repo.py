"""Client repository interface."""

from abc import abstractmethod
from typing import Optional, List
from .base import BaseRepository
from ..schemas import Client


class ClientRepository(BaseRepository[Client]):
    """Abstract client repository interface."""

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Client]:
        """Get client by name."""
        pass

    @abstractmethod
    def search(self, query: str) -> List[Client]:
        """Search clients by name or tax ID."""
        pass
