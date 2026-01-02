"""Product repository interface."""

from abc import abstractmethod
from typing import Optional, List
from .base import BaseRepository
from ..schemas.product import Product


class ProductRepository(BaseRepository[Product]):
    """Abstract product repository interface."""

    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Product]:
        """Get product by unique code."""
        pass

    @abstractmethod
    def get_active(self) -> List[Product]:
        """Get all active products."""
        pass

    @abstractmethod
    def search(self, query: str) -> List[Product]:
        """Search products by name, code, or description."""
        pass

    @abstractmethod
    def get_by_category(self, category: str) -> List[Product]:
        """Get products by category."""
        pass
