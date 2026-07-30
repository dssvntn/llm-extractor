from datetime import datetime

from pydantic import BaseModel, Field


class Item(BaseModel):
    """A single product or service extracted from a document."""

    name: str = Field(description="Product or service name")
    price: float = Field(description="Price of the product or service")


class ExtractedDocument(BaseModel):
    """Structured data extracted from a document."""

    date: datetime | None = Field(
        default=None,
        description="Document date and time, if present",
    )

    document_number: str | None = Field(
        default=None,
        description="Document number, if present",
    )

    total_amount: float | None = Field(
        default=None,
        description="Final total amount, if present",
    )

    items: list[Item] = Field(
        default_factory=list,
        description="Products or services found in the document",
    )
