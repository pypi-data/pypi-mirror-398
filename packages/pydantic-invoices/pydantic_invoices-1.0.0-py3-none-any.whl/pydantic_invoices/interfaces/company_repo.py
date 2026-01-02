"""Company repository interface."""

from abc import abstractmethod
from typing import Optional, List
from .base import BaseRepository
from ..schemas.company import Company


class CompanyRepository(BaseRepository[Company]):
    """Abstract company repository interface."""

    @abstractmethod
    def get_default(self) -> Optional[Company]:
        """Get the default company."""
        pass

    @abstractmethod
    def get_active(self) -> List[Company]:
        """Get all active companies."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Company]:
        """Get company by name."""
        pass
