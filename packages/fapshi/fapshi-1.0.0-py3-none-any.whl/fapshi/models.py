"""Data models for the Fapshi SDK."""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class Transaction:
    """Transaction model representing a payment transaction."""
    
    trans_id: str
    status: str  # CREATED, PENDING, SUCCESSFUL, FAILED, EXPIRED
    medium: Optional[str] = None  # "mobile money" or "orange money"
    service_name: Optional[str] = None
    amount: Optional[int] = None
    revenue: Optional[int] = None
    payer_name: Optional[str] = None
    email: Optional[str] = None
    redirect_url: Optional[str] = None
    external_id: Optional[str] = None
    user_id: Optional[str] = None
    webhook: Optional[str] = None
    financial_trans_id: Optional[str] = None
    date_initiated: Optional[datetime] = None
    date_confirmed: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """Create a Transaction instance from a dictionary."""
        # Convert date strings to datetime objects if present
        date_initiated = None
        date_confirmed = None
        
        if "dateInitiated" in data and data["dateInitiated"]:
            try:
                date_initiated = datetime.fromisoformat(data["dateInitiated"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        
        if "dateConfirmed" in data and data["dateConfirmed"]:
            try:
                date_confirmed = datetime.fromisoformat(data["dateConfirmed"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        
        return cls(
            trans_id=data.get("transId", ""),
            status=data.get("status", ""),
            medium=data.get("medium"),
            service_name=data.get("serviceName"),
            amount=data.get("amount"),
            revenue=data.get("revenue"),
            payer_name=data.get("payerName"),
            email=data.get("email"),
            redirect_url=data.get("redirectUrl"),
            external_id=data.get("externalId"),
            user_id=data.get("userId"),
            webhook=data.get("webhook"),
            financial_trans_id=data.get("financialTransId"),
            date_initiated=date_initiated,
            date_confirmed=date_confirmed,
        )


@dataclass
class PaymentResponse:
    """Response model for payment initiation endpoints."""
    
    message: str
    link: Optional[str] = None  # For initiate-pay
    trans_id: str = ""
    date_initiated: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "PaymentResponse":
        """Create a PaymentResponse instance from a dictionary."""
        date_initiated = None
        if "dateInitiated" in data and data["dateInitiated"]:
            try:
                date_initiated = datetime.fromisoformat(data["dateInitiated"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        
        return cls(
            message=data.get("message", ""),
            link=data.get("link"),
            trans_id=data.get("transId", ""),
            date_initiated=date_initiated,
        )


@dataclass
class BalanceResponse:
    """Response model for balance endpoint."""
    
    service: str
    balance: int
    currency: str
    
    @classmethod
    def from_dict(cls, data: dict) -> "BalanceResponse":
        """Create a BalanceResponse instance from a dictionary."""
        return cls(
            service=data.get("service", ""),
            balance=data.get("balance", 0),
            currency=data.get("currency", ""),
        )


@dataclass
class ErrorResponse:
    """Response model for error responses."""
    
    message: str
    
    @classmethod
    def from_dict(cls, data: dict) -> "ErrorResponse":
        """Create an ErrorResponse instance from a dictionary."""
        return cls(message=data.get("message", ""))

