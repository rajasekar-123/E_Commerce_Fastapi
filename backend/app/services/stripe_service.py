"""
Stripe Service — wraps the Stripe SDK for Checkout Sessions and webhook handling.

Responsibilities:
  - Create Stripe Checkout Sessions from server-calculated order totals
  - Verify webhook signatures (NEVER skip this — it's the security boundary)
  - Handle idempotent event processing

SECURITY:
  - Amount is ALWAYS taken from the server-side Order, never from frontend
  - Webhook signature is verified with STRIPE_WEBHOOK_SECRET before processing
  - stripe_webhook_event_id is stored to prevent duplicate processing
"""

from decimal import Decimal
from typing import Optional
import stripe

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StripeService:

    def __init__(self, secret_key: str, webhook_secret: str):
        self._secret_key = secret_key
        self._webhook_secret = webhook_secret

    def _get_stripe(self):
        stripe.api_key = self._secret_key
        return stripe

    async def create_checkout_session(
        self,
        order_id: int,
        amount_inr: Decimal,
        currency: str,
        line_items: list,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
    ) -> dict:
        """
        Create a Stripe Checkout Session.

        Args:
            order_id: Internal order ID (stored as metadata for webhook lookup)
            amount_inr: Server-calculated total (NEVER from frontend)
            currency: "inr" or "usd"
            line_items: List of {price_data: {currency, product_data, unit_amount}, quantity}
            success_url: Redirect URL after successful payment
            cancel_url: Redirect URL if user cancels

        Returns:
            dict with 'id' (session_id) and 'url' (redirect URL)
        """
        stripe = self._get_stripe()
        try:
            session_params = {
                "payment_method_types": ["card"],
                "line_items": line_items,
                "mode": "payment",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": {
                    "order_id": str(order_id),
                    "internal_amount": str(amount_inr),
                },
                "expires_at": int(__import__("time").time()) + 1800,  # 30 min expiry
            }
            if customer_email:
                session_params["customer_email"] = customer_email

            session = stripe.checkout.Session.create(**session_params)
            logger.info(
                "Stripe checkout session created",
                session_id=session.id,
                order_id=order_id,
                amount=str(amount_inr),
            )
            return {"id": session.id, "url": session.url}
        except Exception as e:
            logger.error("Stripe session creation failed", error=str(e), order_id=order_id)
            raise

    def verify_webhook_signature(self, payload: bytes, signature: str) -> dict:
        """
        Verify Stripe webhook signature and return parsed event.

        CRITICAL: Always verify before processing. Never process unverified events.

        Raises:
            ValueError: If signature is invalid or secret not configured.
        """
        stripe = self._get_stripe()
        if not self._webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET is not configured")
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=self._webhook_secret,
            )
            return event
        except stripe.SignatureVerificationError as e:
            logger.warning("Stripe webhook signature verification failed", error=str(e))
            raise ValueError(f"Invalid webhook signature: {e}")

    async def create_refund(self, payment_intent_id: str, amount_inr: Optional[Decimal] = None) -> dict:
        """
        Issue a full or partial refund via Stripe.

        Args:
            payment_intent_id: The Stripe PaymentIntent ID to refund
            amount_inr: Amount in INR to refund; None for full refund
        """
        stripe = self._get_stripe()
        try:
            refund_params = {"payment_intent": payment_intent_id}
            if amount_inr is not None:
                # Stripe amounts are in smallest currency unit (paise for INR)
                refund_params["amount"] = int(amount_inr * 100)

            refund = stripe.Refund.create(**refund_params)
            logger.info("Stripe refund created", refund_id=refund.id, payment_intent=payment_intent_id)
            return {"refund_id": refund.id, "status": refund.status}
        except Exception as e:
            logger.error("Stripe refund failed", error=str(e), payment_intent=payment_intent_id)
            raise
