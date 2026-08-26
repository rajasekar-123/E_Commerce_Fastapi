"""
Payment Service — orchestrates Stripe Checkout and webhook processing.

SECURITY CONTRACT:
  1. Amount is ALWAYS fetched from the Order in DB — never from frontend
  2. Stripe webhook signature is verified BEFORE processing
  3. Duplicate webhook events are rejected (idempotency via stripe_webhook_event_id)
  4. Payment status flows: PENDING → SUCCESS | FAILED | REFUNDED
  5. Order status is updated only after confirmed payment from webhook
"""

import hashlib
import hmac
import time
import razorpay
from decimal import Decimal
from typing import Optional

from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, InternalError, NotFoundError
from app.core.logging import get_logger
from app.models.order import Order, OrderStatus, PaymentStatus as OrderPaymentStatus
from app.models.payment import Payment, PaymentStatus
from app.repositories.order_repository import OrderRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import CheckoutRequest, CheckoutResponse, PaymentOrderCreate, PaymentOrderResponse, PaymentResponse, PaymentVerifyRequest, PaymentVerifyResponse
from app.services.stripe_service import StripeService

logger = get_logger(__name__)

# Tax / shipping constants — must match CartService values
TAX_RATE = Decimal("0.00")
FREE_SHIPPING_THRESHOLD = Decimal("999.00")
SHIPPING_FEE = Decimal("49.00")


class PaymentService:

    def __init__(
        self,
        order_repo: OrderRepository,
        payment_repo: PaymentRepository,
        stripe_service: StripeService,
    ):
        self._order_repo = order_repo
        self._payment_repo = payment_repo
        self._stripe = stripe_service

    # ── Stripe Checkout (primary flow) ───────────────────────────────────────

    async def create_checkout_session(
        self,
        user_id: int,
        request: CheckoutRequest,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
    ) -> CheckoutResponse:
        """
        Create a Stripe Checkout Session for an existing order.

        Steps:
          1. Load order from DB and verify ownership
          2. Verify order is in a payable state
          3. Check no existing payment record in SUCCESS state
          4. Build line items from server-side order data
          5. Create Stripe session
          6. Create/update Payment record with PENDING status
          7. Update Order status to PAYMENT_PENDING
        """
        order = await self._order_repo.find_by_id(request.order_id)
        if order is None:
            raise NotFoundError(f"Order {request.order_id} not found")
        if order.user_id != user_id:
            raise ForbiddenError("You do not have access to this order")
        if order.payment_status == OrderPaymentStatus.PAID:
            raise ConflictError("This order has already been paid")
        if order.status == OrderStatus.CANCELLED:
            raise BadRequestError("Cannot pay for a cancelled order")

        # Server-side price — NEVER from frontend
        total_amount = order.total_amount

        # Build Stripe line items from order items
        line_items = []
        for item in order.items:
            product = item.product
            product_name = product.name if product else f"Product #{item.product_id}"
            line_items.append({
                "price_data": {
                    "currency": "inr",
                    "product_data": {"name": product_name},
                    # Stripe uses smallest unit (paise for INR)
                    "unit_amount": int(item.price * 100),
                },
                "quantity": item.quantity,
            })

        # Add shipping as a line item if applicable
        if order.shipping_fee > 0:
            line_items.append({
                "price_data": {
                    "currency": "inr",
                    "product_data": {"name": "Shipping Fee"},
                    "unit_amount": int(order.shipping_fee * 100),
                },
                "quantity": 1,
            })

        try:
            session = await self._stripe.create_checkout_session(
                order_id=order.id,
                amount_inr=total_amount,
                currency="inr",
                line_items=line_items,
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
            )
        except Exception as e:
            logger.error("Stripe session creation failed", order_id=order.id, error=str(e))
            raise InternalError("Payment gateway error. Please try again.")

        # Upsert Payment record
        payment = await self._payment_repo.find_by_order_id(order.id)
        if payment is None:
            payment = Payment(
                order_id=order.id,
                user_id=user_id,
                amount=total_amount,
                currency="INR",
                status=PaymentStatus.PENDING,
                stripe_session_id=session["id"],
            )
        else:
            payment.stripe_session_id = session["id"]
            payment.status = PaymentStatus.PENDING

        await self._payment_repo.save(payment)

        # Update order status
        order.status = OrderStatus.PAYMENT_PENDING
        await self._order_repo.save(order)

        logger.info(
            "Checkout session created",
            order_id=order.id,
            session_id=session["id"],
            amount=str(total_amount),
        )

        return CheckoutResponse(
            checkout_url=session["url"],
            session_id=session["id"],
            order_id=order.id,
        )

    # ── Stripe Webhook (the source of truth) ─────────────────────────────────

    async def handle_stripe_webhook(self, payload: bytes, stripe_signature: str) -> dict:
        """
        Process a Stripe webhook event.

        CRITICAL:
          - Signature is verified FIRST — reject anything that doesn't pass
          - Each event_id is stored → duplicate events return early (idempotency)
          - Payment/order status only updated here, never from frontend
        """
        try:
            event = self._stripe.verify_webhook_signature(payload, stripe_signature)
        except ValueError as e:
            logger.warning("Webhook signature verification failed", error=str(e))
            raise BadRequestError("Invalid webhook signature")

        event_id = event["id"]
        event_type = event["type"]

        logger.info("Stripe webhook received", event_id=event_id, event_type=event_type)

        # Idempotency check
        if await self._payment_repo.webhook_event_processed(event_id):
            logger.info("Duplicate webhook event ignored", event_id=event_id)
            return {"received": True, "status": "already_processed"}

        try:
            if event_type == "checkout.session.completed":
                await self._handle_checkout_completed(event, event_id)
            elif event_type == "checkout.session.expired":
                await self._handle_checkout_expired(event, event_id)
            elif event_type == "payment_intent.payment_failed":
                await self._handle_payment_failed(event, event_id)
            elif event_type == "charge.refunded":
                await self._handle_charge_refunded(event, event_id)
            else:
                logger.info("Unhandled webhook event type", event_type=event_type)
        except Exception as e:
            logger.error("Webhook processing error", event_id=event_id, event_type=event_type, error=str(e))
            # Return 200 to prevent Stripe retries for internal errors
            # Log for manual review
            return {"received": True, "status": "error", "detail": "Internal processing error"}

        return {"received": True, "status": "processed"}

    async def _handle_checkout_completed(self, event: dict, event_id: str) -> None:
        session = event["data"]["object"]
        session_id = session["id"]
        payment_intent_id = session.get("payment_intent")
        payment_method = session.get("payment_method_types", [None])[0]

        payment = await self._payment_repo.find_by_stripe_session_id(session_id)
        if payment is None:
            logger.warning("Payment not found for session", session_id=session_id)
            return

        payment.status = PaymentStatus.SUCCESS
        payment.stripe_payment_intent_id = payment_intent_id
        payment.stripe_webhook_event_id = event_id
        payment.payment_method = payment_method
        await self._payment_repo.save(payment)

        # Update order
        order = await self._order_repo.find_by_id(payment.order_id)
        if order:
            order.payment_status = OrderPaymentStatus.PAID
            order.status = OrderStatus.CONFIRMED
            await self._order_repo.save(order)

        logger.info(
            "Payment confirmed via webhook",
            session_id=session_id,
            order_id=payment.order_id,
            payment_id=payment.id,
        )

    async def _handle_checkout_expired(self, event: dict, event_id: str) -> None:
        session = event["data"]["object"]
        session_id = session["id"]

        payment = await self._payment_repo.find_by_stripe_session_id(session_id)
        if payment:
            payment.status = PaymentStatus.FAILED
            payment.stripe_webhook_event_id = event_id
            await self._payment_repo.save(payment)

            order = await self._order_repo.find_by_id(payment.order_id)
            if order and order.status == OrderStatus.PAYMENT_PENDING:
                order.status = OrderStatus.PAYMENT_FAILED
                await self._order_repo.save(order)

        logger.info("Checkout session expired", session_id=session_id)

    async def _handle_payment_failed(self, event: dict, event_id: str) -> None:
        intent = event["data"]["object"]
        intent_id = intent["id"]

        payment = await self._payment_repo.find_by_stripe_payment_intent(intent_id)
        if payment:
            payment.status = PaymentStatus.FAILED
            payment.stripe_webhook_event_id = event_id
            await self._payment_repo.save(payment)

            order = await self._order_repo.find_by_id(payment.order_id)
            if order:
                order.status = OrderStatus.PAYMENT_FAILED
                await self._order_repo.save(order)

        logger.info("Payment failed via webhook", intent_id=intent_id)

    async def _handle_charge_refunded(self, event: dict, event_id: str) -> None:
        charge = event["data"]["object"]
        intent_id = charge.get("payment_intent")

        if intent_id:
            payment = await self._payment_repo.find_by_stripe_payment_intent(intent_id)
            if payment:
                payment.status = PaymentStatus.REFUNDED
                payment.stripe_webhook_event_id = event_id
                await self._payment_repo.save(payment)

                order = await self._order_repo.find_by_id(payment.order_id)
                if order:
                    order.payment_status = OrderPaymentStatus.REFUNDED
                    order.status = OrderStatus.REFUNDED
                    await self._order_repo.save(order)

        logger.info("Charge refunded via webhook", intent_id=intent_id)

    # ── Razorpay legacy (keep for backward compatibility) ─────────────────────

    async def create_razorpay_order(self, request: PaymentOrderCreate, user_id: int) -> PaymentOrderResponse:
        """Create a Razorpay payment order based on the server-calculated amount."""
        order = await self._order_repo.find_by_id(request.order_id)
        if order is None:
            raise NotFoundError(f"Order {request.order_id} not found")
        if order.user_id != user_id:
            raise ForbiddenError("You do not have access to this order")
        if order.payment_status == OrderPaymentStatus.PAID:
            raise ConflictError("This order has already been paid")
        if order.status == OrderStatus.CANCELLED:
            raise BadRequestError("Cannot pay for a cancelled order")

        amount_in_paise = int(order.total_amount * 100)
        if amount_in_paise < 100:
            raise BadRequestError("Minimum amount for Razorpay is 1 INR (100 paise)")

        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            order_data = {
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": f"receipt_order_{order.id}_{time.time_ns()}",
            }
            rzp_order = client.order.create(data=order_data)
            
            # Upsert Payment record with PENDING status
            payment = await self._payment_repo.find_by_order_id(order.id)
            if payment is None:
                payment = Payment(
                    order_id=order.id,
                    user_id=user_id,
                    amount=order.total_amount,
                    currency="INR",
                    status=PaymentStatus.PENDING,
                    razorpay_order_id=rzp_order["id"],
                )
            else:
                payment.razorpay_order_id = rzp_order["id"]
                payment.status = PaymentStatus.PENDING

            await self._payment_repo.save(payment)
            
            # Update order status
            order.status = OrderStatus.PAYMENT_PENDING
            await self._order_repo.save(order)

            return PaymentOrderResponse(id=rzp_order["id"], amount=str(rzp_order["amount"]), currency=rzp_order["currency"])
        except Exception as e:
            logger.error("Razorpay order creation failed", error=str(e))
            raise InternalError("Payment gateway error")

    async def verify_razorpay_payment(self, request: PaymentVerifyRequest, user_id: int) -> PaymentVerifyResponse:
        """Verify Razorpay HMAC signature and persist payment record."""
        body = f"{request.razorpay_order_id}|{request.razorpay_payment_id}"
        expected_sig = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, request.razorpay_signature):
            raise BadRequestError("Payment signature verification failed")

        # Persist payment record
        order = await self._order_repo.find_by_id(request.order_id)
        if order is None:
            raise NotFoundError(f"Order {request.order_id} not found")
        if order.user_id != user_id:
            raise ForbiddenError("Access denied")

        payment = await self._payment_repo.find_by_order_id(request.order_id)
        if payment is None:
            payment = Payment(
                order_id=request.order_id,
                user_id=user_id,
                amount=order.total_amount,
                currency="INR",
                status=PaymentStatus.SUCCESS,
                razorpay_order_id=request.razorpay_order_id,
                razorpay_payment_id=request.razorpay_payment_id,
            )
        else:
            payment.status = PaymentStatus.SUCCESS
            payment.razorpay_payment_id = request.razorpay_payment_id

        await self._payment_repo.save(payment)

        order.payment_status = OrderPaymentStatus.PAID
        order.status = OrderStatus.CONFIRMED
        await self._order_repo.save(order)

        logger.info("Razorpay payment verified", order_id=order.id, payment_id=payment.id)
        return PaymentVerifyResponse(status="success", message="Payment verified successfully")
