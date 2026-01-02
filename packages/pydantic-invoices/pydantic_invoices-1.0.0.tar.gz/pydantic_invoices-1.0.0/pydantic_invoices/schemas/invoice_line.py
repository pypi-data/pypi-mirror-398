"""Invoice line schemas - Pure Pydantic models."""

from pydantic import BaseModel, Field, ConfigDict, computed_field


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""

    description: str = Field(
        ..., min_length=1, max_length=500, description="Line item description"
    )
    quantity: int = Field(..., gt=0, description="Quantity")
    unit_price: float = Field(..., ge=0, description="Price per unit")


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""

    pass


class InvoiceLine(InvoiceLineBase):
    """Complete invoice line schema with computed properties."""

    id: int
    invoice_id: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(self) -> float:
        """Calculate line total (quantity × unit_price)."""
        return self.quantity * self.unit_price

    model_config = ConfigDict(from_attributes=True)
