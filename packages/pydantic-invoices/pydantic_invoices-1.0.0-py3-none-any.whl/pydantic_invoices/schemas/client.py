"""Client schema - invoice recipient."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class ClientBase(BaseModel):
    """Base client schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Client name")
    address: Optional[str] = Field(None, max_length=500, description="Client address")
    tax_id: Optional[str] = Field(
        None, max_length=50, description="Client tax ID number"
    )
    email: Optional[str] = Field(
        None, max_length=255, description="Client email address"
    )
    phone: Optional[str] = Field(None, max_length=50, description="Client phone number")


class ClientCreate(ClientBase):
    """Schema for creating a client."""

    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)


class Client(ClientBase):
    """Complete client schema."""

    id: int

    model_config = ConfigDict(from_attributes=True)
