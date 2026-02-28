"""
Seed the knowledge base with sample company documents.
Run after setting OPENAI_API_KEY in .env. Usage: python seed_kb.py
"""

import os
import sys

# Add backend root so we can import db
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from db import add_documents_to_kb

# Sample company knowledge base content for demo
SAMPLE_DOCUMENTS = [
    """Welcome to Acme Support. Our business hours are Monday–Friday 9am–6pm EST. 
For urgent issues outside these hours, use the "Connect to human support" option and we will respond within 24 hours.""",
    """Returns and refunds: You can return most items within 30 days of delivery for a full refund. 
Items must be unused and in original packaging. To start a return, go to My Account > Orders > Request Return.""",
    """Shipping: Standard shipping is 5–7 business days. Express shipping is 2–3 business days. 
Free shipping on orders over $50. International shipping available to select countries.""",
    """Account security: We never ask for your password via email. Enable two-factor authentication in 
Account Settings > Security. If you suspect unauthorized access, change your password and contact support immediately.""",
    """Billing and subscriptions: You can cancel your subscription anytime from Account > Billing. 
Cancellation takes effect at the end of the current billing period. No refunds for partial months.""",
]


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set. Add it to backend/.env")
        sys.exit(1)
    count = add_documents_to_kb(SAMPLE_DOCUMENTS)
    print(f"Seeded knowledge base with {count} chunks from {len(SAMPLE_DOCUMENTS)} documents.")


if __name__ == "__main__":
    main()
