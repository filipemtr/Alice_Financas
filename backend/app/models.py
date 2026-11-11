from datetime import datetime, timezone, date
from sqlalchemy import ForeignKey, String, Integer, BigInteger, DateTime, Date, Boolean, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def now(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__='users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class Session(Base):
    __tablename__='sessions'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    csrf_token: Mapped[str] = mapped_column(String(100))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class LoginAttempt(Base):
    __tablename__='login_attempts'
    id: Mapped[int] = mapped_column(primary_key=True)
    ip_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)

class MonthlyBudget(Base):
    __tablename__='monthly_budgets'
    __table_args__ = (UniqueConstraint('user_id','year','month'), CheckConstraint('month between 1 and 12'), CheckConstraint('income_cents >= 0'))
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id',ondelete='CASCADE'))
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    income_cents: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now,onupdate=now)

class FixedExpense(Base):
    __tablename__='fixed_expenses'
    __table_args__ = (CheckConstraint('amount_cents >= 0'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey('monthly_budgets.id',ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(120))
    amount_cents: Mapped[int] = mapped_column(BigInteger, default=0)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now,onupdate=now)

class LeisureExpense(Base):
    __tablename__='leisure_expenses'
    __table_args__ = (CheckConstraint('amount_cents >= 0'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey('monthly_budgets.id',ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(120))
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    expense_date: Mapped[date] = mapped_column(Date)
    notes: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now,onupdate=now)

class Purchase(Base):
    __tablename__='credit_card_purchases'
    __table_args__ = (CheckConstraint('total_amount_cents > 0'), CheckConstraint('installment_count between 1 and 60'), CheckConstraint('first_billing_month between 1 and 12'))
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id',ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String(120))
    total_amount_cents: Mapped[int] = mapped_column(BigInteger)
    purchase_date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(Text, default='')
    category: Mapped[str] = mapped_column(String(60), default='Outros')
    installment_count: Mapped[int] = mapped_column(Integer, default=1)
    first_billing_year: Mapped[int] = mapped_column(Integer)
    first_billing_month: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now,onupdate=now)

class Installment(Base):
    __tablename__='credit_card_installments'
    __table_args__ = (UniqueConstraint('purchase_id','installment_number'), CheckConstraint('amount_cents >= 0'))
    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey('credit_card_purchases.id',ondelete='CASCADE'),index=True)
    installment_number: Mapped[int] = mapped_column(Integer)
    billing_year: Mapped[int] = mapped_column(Integer, index=True)
    billing_month: Mapped[int] = mapped_column(Integer, index=True)
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    purchase: Mapped[Purchase] = relationship()

class MonthlyCardBill(Base):
    __tablename__='monthly_card_bills'
    __table_args__ = (UniqueConstraint('budget_id'), CheckConstraint('final_amount_cents >= 0'))
    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey('monthly_budgets.id',ondelete='CASCADE'))
    final_amount_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean,default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now,onupdate=now)

class Preference(Base):
    __tablename__='user_preferences'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id',ondelete='CASCADE'),unique=True)
    selected_theme: Mapped[str] = mapped_column(String(30),default='kitty')
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now,onupdate=now)
