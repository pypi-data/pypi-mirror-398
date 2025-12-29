import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict


class ProductType(str, Enum):
    """Product type in Aggregation v2."""

    ACCOUNT = "Account"
    CARD = "Card"
    INVESTMENT = "Investment"
    LIABILITY = "Liability"


class Product(BaseModel):
    """Unified product from Aggregation v2."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    product_id: str
    product_type: ProductType
    connection_id: str | None = None
    name: str | None = None
    balance: Decimal | None = None
    currency: str | None = None
    iban: str | None = None
    labels: dict[str, str] | None = None


class ProductQuery(BaseModel):
    """Query parameters for listing products."""

    model_config = ConfigDict(extra="ignore")

    product_id_in: list[str] | None = None
    product_type_in: list[ProductType] | None = None
    connection_id_in: list[str] | None = None


class Transaction(BaseModel):
    """Transaction from Aggregation v2."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    transaction_id: str
    product_id: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    description: str | None = None
    date: datetime.date | None = None
    category: str | None = None
    labels: dict[str, str] | None = None


class TransactionQuery(BaseModel):
    """Query parameters for listing transactions."""

    model_config = ConfigDict(extra="ignore")

    transaction_id_in: list[str] | None = None
    product_id_in: list[str] | None = None
    connection_id_in: list[str] | None = None
    date_from: datetime.date | None = None
    date_to: datetime.date | None = None
