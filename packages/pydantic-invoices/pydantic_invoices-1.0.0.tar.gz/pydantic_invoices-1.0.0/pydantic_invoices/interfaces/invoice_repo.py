"""Invoice repository interface."""

from abc import abstractmethod
from typing import Optional, List, Dict, Any
from .base import BaseRepository
from ..schemas import Invoice


class InvoiceRepository(BaseRepository[Invoice]):
    """Abstract invoice repository interface."""

    @abstractmethod
    def get_by_number(self, number: str) -> Optional[Invoice]:
        """Get invoice by number."""
        pass

    @abstractmethod
    def get_by_client(self, client_id: int) -> List[Invoice]:
        """Get all invoices for a client."""
        pass

    @abstractmethod
    def get_by_status(self, status: str) -> List[Invoice]:
        """Get invoices by status."""
        pass

    @abstractmethod
    def get_overdue(self) -> List[Invoice]:
        """Get all overdue invoices."""
        pass

    @abstractmethod
    def get_summary(self) -> Dict[str, Any]:
        """Get invoice statistics summary."""
        pass
