import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict


class Currency(str, Enum):
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"


class Portfolio(BaseModel):
    """Investment portfolio."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    portfolio_id: str
    name: str | None = None
    total_value: Decimal | None = None
    currency: str | None = None


class Investment(BaseModel):
    """Investment position."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    investment_id: str
    portfolio_id: str | None = None
    name: str | None = None
    isin: str | None = None
    quantity: Decimal | None = None
    value: Decimal | None = None
    currency: str | None = None


class Account(BaseModel):
    """Bank account."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    account_id: str
    iban: str | None = None
    name: str | None = None
    balance: Decimal | None = None
    currency: str | None = None


class Transaction(BaseModel):
    """Financial transaction."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    transaction_id: str
    account_id: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    description: str | None = None
    date: datetime.date | None = None
    category: str | None = None


class Liability(BaseModel):
    """Liability (loan, mortgage, etc.)."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    liability_id: str
    name: str | None = None
    balance: Decimal | None = None
    currency: str | None = None
    interest_rate: Decimal | None = None


class Card(BaseModel):
    """Credit/debit card."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    card_id: str
    name: str | None = None
    masked_number: str | None = None
    balance: Decimal | None = None
    currency: str | None = None


class Identity(BaseModel):
    """Account holder identity."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    name: str | None = None
    email: str | None = None
    phone: str | None = None


class Holder(BaseModel):
    """Account holder information."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    holder_id: str | None = None
    name: str | None = None
    document_type: str | None = None
    document_number: str | None = None
