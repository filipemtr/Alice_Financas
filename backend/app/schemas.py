from datetime import date
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict, model_validator

Cents = Annotated[int, Field(ge=0,le=100_000_000_000, strict=True)]
PositiveCents = Annotated[int, Field(ge=1,le=100_000_000_000, strict=True)]
Name = Annotated[str, Field(min_length=1,max_length=120)]

class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)

class IncomeIn(BaseModel):
    income_cents: Cents

class FixedIn(BaseModel):
    name: Name
    amount_cents: Cents
    due_date: date | None = None
    is_paid: bool = False

class FixedPatch(BaseModel):
    name: Name | None = None
    amount_cents: Cents | None = None
    due_date: date | None = None
    is_paid: bool | None = None

class LeisureIn(BaseModel):
    name: Name
    amount_cents: PositiveCents
    expense_date: date
    notes: str = Field(default='',max_length=2500)

class LeisurePatch(BaseModel):
    name: Name | None = None
    amount_cents: PositiveCents | None = None
    expense_date: date | None = None
    notes: str | None = Field(default=None,max_length=2500)

class PurchaseIn(BaseModel):
    name: Name
    total_amount_cents: PositiveCents
    purchase_date: date
    description: str = Field(default='',max_length=2500)
    category: str = Field(default='Outros',min_length=1,max_length=60)
    installment_count: int = Field(default=1,ge=1,le=60)
    first_billing_year: int = Field(ge=2000,le=2100)
    first_billing_month: int = Field(ge=1,le=12)
    @model_validator(mode='after')
    def valid_installments(self):
        if self.installment_count > self.total_amount_cents:
            raise ValueError('Valor insuficiente para tantas parcelas')
        if self.first_billing_year*12+self.first_billing_month+self.installment_count-1 > 2100*12+12:
            raise ValueError('O parcelamento ultrapassa o ano permitido')
        return self

class CardBillIn(BaseModel):
    final_amount_cents: Cents | None
    is_paid: bool = False

class PaidIn(BaseModel):
    is_paid: bool

class ThemeIn(BaseModel):
    selected_theme: str = Field(pattern='^(kitty|pony|snoopy|amelie|coraline)$')
