"""Payment note repository interface."""

from abc import abstractmethod
from typing import Optional, List
from .base import BaseRepository
from ..schemas.payment_note import PaymentNote


class PaymentNoteRepository(BaseRepository[PaymentNote]):
    """Abstract payment note repository interface."""

    @abstractmethod
    def get_by_company(self, company_id: Optional[int] = None) -> List[PaymentNote]:
        """Get payment notes for a specific company, or global notes if company_id is None."""
        pass

    @abstractmethod
    def get_default(self, company_id: Optional[int] = None) -> Optional[PaymentNote]:
        """Get the default payment note for a company."""
        pass

    @abstractmethod
    def get_active(self) -> List[PaymentNote]:
        """Get all active payment notes."""
        pass
