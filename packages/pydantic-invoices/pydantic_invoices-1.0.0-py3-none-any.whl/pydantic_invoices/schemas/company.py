"""Company schema - for multi-company invoicing."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class CompanyBase(BaseModel):
    """Base company schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Company name")
    legal_name: Optional[str] = Field(
        None, max_length=255, description="Full legal name of the company"
    )
    tax_id: Optional[str] = Field(
        None, max_length=50, description="Tax identification number"
    )
    registration_number: Optional[str] = Field(
        None, max_length=50, description="Company registration number"
    )

    # Contact information
    address: Optional[str] = Field(None, max_length=500, description="Street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    postal_code: Optional[str] = Field(
        None, max_length=20, description="Postal/ZIP code"
    )
    country: Optional[str] = Field(None, max_length=100, description="Country")

    email: Optional[str] = Field(
        None, max_length=255, description="Contact email address"
    )
    phone: Optional[str] = Field(
        None, max_length=50, description="Contact phone number"
    )
    website: Optional[str] = Field(
        None, max_length=255, description="Company website URL"
    )

    # Branding
    logo_path: Optional[str] = Field(
        None, max_length=500, description="Path to company logo file"
    )

    # Settings
    is_active: bool = Field(default=True, description="Whether this company is active")
    is_default: bool = Field(
        default=False, description="Whether this is the default company for invoices"
    )


class CompanyCreate(CompanyBase):
    """Schema for creating a company."""

    pass


class CompanyUpdate(BaseModel):
    """Schema for updating a company."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    logo_path: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class Company(CompanyBase):
    """Complete company schema."""

    id: int

    model_config = ConfigDict(from_attributes=True)
