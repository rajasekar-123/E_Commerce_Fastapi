"""
002_add_cart_payment_brand_order_fields

Revision: 002
Previous: 001_initial_schema

Adds:
  - carts table (one per user, unique constraint on user_id)
  - cart_items table (unique per cart+product pair)
  - payments table (Stripe + Razorpay, idempotency via webhook event ID)
  - products.brand column
  - orders: payment_status enum, subtotal, tax, shipping_fee, discount_amount,
             billing_address_id, cancellation_reason columns
  - orders.status enum: adds PAYMENT_PENDING, PAYMENT_FAILED, REFUNDED values
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Add brand to products ──────────────────────────────────────────────
    op.add_column("products", sa.Column("brand", sa.String(100), nullable=True))
    op.create_index("ix_products_brand", "products", ["brand"])

    # ── 2. Extend order_status enum (new values) ──────────────────────────────
    op.execute("ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'PAYMENT_PENDING'")
    op.execute("ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'PAYMENT_FAILED'")
    op.execute("ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'REFUNDED'")

    # ── 3. Create order_payment_status enum ───────────────────────────────────
    order_payment_status = sa.Enum(
        "UNPAID", "PAID", "REFUNDED", "FAILED",
        name="order_payment_status"
    )
    order_payment_status.create(op.get_bind(), checkfirst=True)

    # ── 4. Add new columns to orders ──────────────────────────────────────────
    op.add_column("orders", sa.Column(
        "payment_status",
        sa.Enum("UNPAID", "PAID", "REFUNDED", "FAILED", name="order_payment_status"),
        nullable=False,
        server_default="UNPAID",
    ))
    op.add_column("orders", sa.Column("subtotal", sa.Numeric(12, 2), nullable=False, server_default="0.00"))
    op.add_column("orders", sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"))
    op.add_column("orders", sa.Column("tax", sa.Numeric(12, 2), nullable=False, server_default="0.00"))
    op.add_column("orders", sa.Column("shipping_fee", sa.Numeric(12, 2), nullable=False, server_default="0.00"))
    op.add_column("orders", sa.Column(
        "billing_address_id",
        sa.Integer(),
        sa.ForeignKey("addresses.id"),
        nullable=True,
    ))
    op.add_column("orders", sa.Column("cancellation_reason", sa.String(500), nullable=True))
    op.add_column("orders", sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    ))
    op.create_index("ix_orders_payment_status", "orders", ["payment_status"])

    # ── 5. Create payment_status enum ─────────────────────────────────────────
    payment_status = sa.Enum(
        "PENDING", "SUCCESS", "FAILED", "REFUNDED", "CANCELLED",
        name="payment_status"
    )
    payment_status.create(op.get_bind(), checkfirst=True)

    # ── 6. Create payments table ──────────────────────────────────────────────
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column(
            "status",
            sa.Enum("PENDING", "SUCCESS", "FAILED", "REFUNDED", "CANCELLED", name="payment_status"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("stripe_session_id", sa.String(500), unique=True, nullable=True),
        sa.Column("stripe_payment_intent_id", sa.String(500), nullable=True),
        sa.Column("stripe_webhook_event_id", sa.String(500), nullable=True),
        sa.Column("razorpay_order_id", sa.String(200), nullable=True),
        sa.Column("razorpay_payment_id", sa.String(200), nullable=True),
        sa.Column("payment_method", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("stripe_webhook_event_id", name="uq_stripe_webhook_event"),
    )
    op.create_index("ix_payments_order_id", "payments", ["order_id"])
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_status", "payments", ["status"])

    # ── 7. Create carts table ─────────────────────────────────────────────────
    op.create_table(
        "carts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_carts_user_id", "carts", ["user_id"])

    # ── 8. Create cart_items table ────────────────────────────────────────────
    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("cart_id", sa.Integer(), sa.ForeignKey("carts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),
    )
    op.create_index("ix_cart_items_cart_id", "cart_items", ["cart_id"])


def downgrade() -> None:
    op.drop_table("cart_items")
    op.drop_table("carts")
    op.drop_table("payments")
    op.drop_index("ix_orders_payment_status", table_name="orders")
    op.drop_column("orders", "cancellation_reason")
    op.drop_column("orders", "billing_address_id")
    op.drop_column("orders", "shipping_fee")
    op.drop_column("orders", "tax")
    op.drop_column("orders", "discount_amount")
    op.drop_column("orders", "subtotal")
    op.drop_column("orders", "payment_status")
    op.drop_column("orders", "updated_at")
    op.execute("DROP TYPE IF EXISTS order_payment_status")
    op.execute("DROP TYPE IF EXISTS payment_status")
    op.drop_index("ix_products_brand", table_name="products")
    op.drop_column("products", "brand")
