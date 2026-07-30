from datetime import datetime

from pydantic import BaseModel, Field


class Item(BaseModel):
    """Товар или услуга."""

    name: str = Field(description="Название товара или услуги")
    price: float = Field(description="Цена товара или услуги")


class ExtractedDocument(BaseModel):
    """Данные, извлечённые из документа."""

    date: datetime | None = Field(
        default=None,
        description="Дата и время документа, если указаны",
    )

    document_number: str | None = Field(
        default=None,
        description="Номер документа, если указан",
    )

    total_amount: float | None = Field(
        default=None,
        description="Итоговая сумма документа, если указана",
    )

    items: list[Item] = Field(
        default_factory=list,
        description="Список товаров или услуг",
    )
