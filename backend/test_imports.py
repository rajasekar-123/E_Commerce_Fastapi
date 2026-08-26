import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, r"c:\Users\rajas\Downloads\OneDrive\Documents\Projects\Spring-Boot\E-commerce\ecommerce-fastapi\backend")

print("Testing imports...")
try:
    from app.services.email_service import EmailService
    print("EmailService imported successfully")
except Exception as e:
    print(f"EmailService error: {type(e).__name__}: {e}")

try:
    from app.services.stripe_service import StripeService
    print("StripeService imported successfully")
except Exception as e:
    print(f"StripeService error: {type(e).__name__}: {e}")
