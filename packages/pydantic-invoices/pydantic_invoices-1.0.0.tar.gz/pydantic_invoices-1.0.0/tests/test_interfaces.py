"""Tests for repository interfaces."""

import pytest
from abc import ABC
from pydantic_invoices.interfaces import (
    BaseRepository,
    InvoiceRepository,
    ClientRepository,
    PaymentRepository,
)


class TestBaseRepository:
    """Tests for BaseRepository interface."""

    def test_is_abstract(self):
        """Test that BaseRepository is abstract."""
        assert issubclass(BaseRepository, ABC)

    def test_cannot_instantiate(self):
        """Test that BaseRepository cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseRepository()


class TestInvoiceRepository:
    """Tests for InvoiceRepository interface."""

    def test_is_abstract(self):
        """Test that InvoiceRepository is abstract."""
        assert issubclass(InvoiceRepository, ABC)

    def test_inherits_from_base(self):
        """Test that InvoiceRepository inherits from BaseRepository."""
        assert issubclass(InvoiceRepository, BaseRepository)

    def test_has_required_methods(self):
        """Test that InvoiceRepository has all required methods."""
        required_methods = [
            "create",
            "get_by_id",
            "get_all",
            "update",
            "delete",
            "get_by_number",
            "get_by_client",
            "get_by_status",
            "get_overdue",
        ]
        for method in required_methods:
            assert hasattr(InvoiceRepository, method)


class TestClientRepository:
    """Tests for ClientRepository interface."""

    def test_is_abstract(self):
        """Test that ClientRepository is abstract."""
        assert issubclass(ClientRepository, ABC)

    def test_has_required_methods(self):
        """Test that ClientRepository has all required methods."""
        required_methods = [
            "create",
            "get_by_id",
            "get_all",
            "update",
            "delete",
            "get_by_name",
            "search",
        ]
        for method in required_methods:
            assert hasattr(ClientRepository, method)


class TestPaymentRepository:
    """Tests for PaymentRepository interface."""

    def test_is_abstract(self):
        """Test that PaymentRepository is abstract."""
        assert issubclass(PaymentRepository, ABC)

    def test_has_required_methods(self):
        """Test that PaymentRepository has all required methods."""
        required_methods = [
            "create",
            "get_by_id",
            "get_all",
            "update",
            "delete",
            "get_by_invoice",
            "get_total_for_invoice",
        ]
        for method in required_methods:
            assert hasattr(PaymentRepository, method)
