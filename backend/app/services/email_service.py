"""
Email Service — async order confirmation emails.

FIXED:
  - Removed the module-level `_pending_order` global that caused race conditions
  - `send_order_confirmation` takes the order directly as argument
  - Gracefully handles missing SMTP config (logs warning, does not crash)
"""

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Handles transactional emails for the e-commerce platform."""

    async def send_order_confirmation(self, order) -> None:
        """
        Send an order confirmation email to the customer.

        Designed to be called as a FastAPI BackgroundTask:
            background_tasks.add_task(email_service.send_order_confirmation, order)

        Silently skips if SMTP is not configured (development mode).
        """
        if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
            logger.info(
                "SMTP not configured — skipping order confirmation email",
                order_id=order.id if order else None,
            )
            return

        if order is None:
            logger.warning("send_order_confirmation called with None order")
            return

        try:
            from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

            conf = ConnectionConfig(
                MAIL_USERNAME=settings.MAIL_USERNAME,
                MAIL_PASSWORD=settings.MAIL_PASSWORD,
                MAIL_FROM=settings.MAIL_FROM,
                MAIL_PORT=settings.MAIL_PORT,
                MAIL_SERVER=settings.MAIL_HOST,
                MAIL_STARTTLS=settings.MAIL_STARTTLS,
                MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
                USE_CREDENTIALS=True,
                VALIDATE_CERTS=True,
            )

            html_content = self._build_order_html(order)

            recipient_email = None
            if hasattr(order, "user") and order.user and order.user.email:
                recipient_email = order.user.email

            if not recipient_email:
                logger.warning("No recipient email found for order", order_id=order.id)
                return

            message = MessageSchema(
                subject=f"Order Confirmation — #{order.id}",
                recipients=[recipient_email],
                body=html_content,
                subtype=MessageType.html,
            )

            fm = FastMail(conf)
            await fm.send_message(message)
            logger.info(
                "Order confirmation email sent",
                order_id=order.id,
                email=recipient_email,
            )

        except Exception as e:
            logger.error(
                "Failed to send order confirmation email",
                order_id=order.id if order else None,
                error=str(e),
            )

    def _build_order_html(self, order) -> str:
        items_html = "".join(
            f"<li>{item.product.name if item.product else 'Product'} × {item.quantity} — ₹{item.price}</li>"
            for item in order.items
        )
        first_name = "Customer"
        if hasattr(order, "user") and order.user and order.user.first_name:
            first_name = order.user.first_name

        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h1 style="color: #6366f1;">Thank you for your order! 🎉</h1>
          <p>Hi {first_name},</p>
          <p>Your order <strong>#{order.id}</strong> has been successfully placed.</p>
          <h3>Order Details:</h3>
          <ul>{items_html}</ul>
          <table style="width: 100%; margin-top: 16px;">
            <tr><td>Subtotal</td><td align="right">₹{order.subtotal}</td></tr>
            <tr><td>Tax</td><td align="right">₹{order.tax}</td></tr>
            <tr><td>Shipping</td><td align="right">₹{order.shipping_fee}</td></tr>
            <tr style="font-weight: bold; border-top: 2px solid #333;">
              <td>Total</td><td align="right">₹{order.total_amount}</td>
            </tr>
          </table>
          <p style="margin-top: 24px;">We will notify you when your order ships.</p>
          <p style="color: #6366f1; font-weight: bold;">E-Shop Team</p>
        </div>
        """
