"""
Payment Pydantic schemas — Stripe Checkout + Razorpay legacy.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


# ── Stripe Checkout ───────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    """Frontend sends only the order_id — backend fetches everything else."""
    order_id: int


class CheckoutResponse(BaseModel):
    """URL to redirect the user to Stripe hosted checkout page."""
    checkout_url: str
    session_id: str
    order_id: int


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: Decimal
    currency: str
    status: str
    payment_method: Optional[str] = None
    stripe_session_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Razorpay (legacy — kept for backward compatibility) ───────────────────────

class PaymentOrderCreate(BaseModel):
    """Razorpay flow order creation request."""
    order_id: int


class PaymentOrderResponse(BaseModel):
    id: str
    amount: str
    currency: str


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    order_id: int  # internal order ID — required for DB record


class PaymentVerifyResponse(BaseModel):
    status: str   # "success" | "failed"
    message: str = ""
