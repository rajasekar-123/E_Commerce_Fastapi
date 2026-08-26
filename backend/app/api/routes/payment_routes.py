"""
Payment routes — Stripe Checkout (primary) + Razorpay legacy + Webhook.

CRITICAL SECURITY NOTES:
  - /checkout: Amount is NEVER from the request body — fetched server-side from Order
  - /stripe/webhook: Raw bytes needed for signature verification (no JSON parsing before verify)
  - Webhook endpoint does NOT require authentication (Stripe calls it directly)
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_payment_service
from app.core.security import get_current_user
from app.schemas.payment import (
    CheckoutRequest,
    CheckoutResponse,
    PaymentOrderCreate,
    PaymentOrderResponse,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
)

router = APIRouter()


# ── Stripe Checkout (primary flow) ────────────────────────────────────────────

@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=201,
    summary="Create a Stripe Checkout Session for an order",
)
async def create_checkout_session(
    request: CheckoutRequest,
    http_request: Request,
    current_user=Depends(get_current_user),
    payment_service=Depends(get_payment_service),
) -> CheckoutResponse:
    """
    Creates a Stripe Checkout Session.
    Amount is fetched server-side from the order — frontend sends only order_id.

    After creation, redirect the user to CheckoutResponse.checkout_url.
    """
    base_url = str(http_request.base_url).rstrip("/")
    return await payment_service.create_checkout_session(
        user_id=current_user.id,
        request=request,
        success_url=f"{base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base_url}/payment/cancelled",
        customer_email=current_user.email,
    )


@router.post(
    "/stripe/webhook",
    include_in_schema=True,
    summary="Stripe webhook receiver (signature verified)",
)
async def stripe_webhook(
    raw_request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    payment_service=Depends(get_payment_service),
):
    """
    Handles Stripe webhook events.

    CRITICAL:
      - Uses raw request body BEFORE any JSON parsing (required for signature verification)
      - Stripe-Signature header must be present and valid
      - Idempotent: duplicate events are silently ignored

    This endpoint is called by Stripe — no user JWT required.
    """
    if not stripe_signature:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Missing Stripe-Signature header"},
        )

    # IMPORTANT: Read raw bytes — do not use request.json() before this
    payload = await raw_request.body()

    result = await payment_service.handle_stripe_webhook(
        payload=payload,
        stripe_signature=stripe_signature,
    )
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)


# ── Razorpay legacy (backward compatibility) ──────────────────────────────────

@router.post(
    "/create-order",
    response_model=PaymentOrderResponse,
    summary="Create a Razorpay payment order",
)
async def create_payment_order(
    request: PaymentOrderCreate,
    current_user=Depends(get_current_user),
    payment_service=Depends(get_payment_service),
) -> PaymentOrderResponse:
    """Razorpay flow order creation."""
    return await payment_service.create_razorpay_order(request, user_id=current_user.id)


@router.post(
    "/verify-payment",
    response_model=PaymentVerifyResponse,
    summary="Verify Razorpay payment signature",
)
async def verify_payment(
    request: PaymentVerifyRequest,
    current_user=Depends(get_current_user),
    payment_service=Depends(get_payment_service),
) -> PaymentVerifyResponse:
    """Verify Razorpay payment signature and persist payment record."""
    return await payment_service.verify_razorpay_payment(request, user_id=current_user.id)
