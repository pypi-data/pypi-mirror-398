"""Basic Sage SDK usage example."""

import os
from sage_sdk import Sage

# Initialize with your API key
sage = Sage(
    api_key=os.environ["SAGE_API_KEY"],
    debug=True,  # Enable for development
)

# Create a support ticket
ticket = sage.create_ticket(
    customer_email="user@example.com",
    subject="Help with billing",
    message="I need to update my payment method. How do I do that?",
    customer_name="Jane Smith",
    priority="medium",
    metadata={
        "user_id": "u_123",
        "plan": "pro",
        "source": "in-app",
    },
)

print(f"Created ticket #{ticket.ticket_number}")
print(f"Ticket ID: {ticket.id}")
print(f"Status: {ticket.status.value}")
print(f"Portal URL: {ticket.portal_url}")

# Identify/update a customer
customer = sage.identify_customer(
    email="user@example.com",
    name="Jane Smith",
    external_id="cust_jane_123",
    company="Acme Corp",
    metadata={
        "signup_date": "2024-01-15",
        "lifetime_value": 1234.56,
    },
)

print(f"\nCustomer: {customer.name} ({customer.email})")
print(f"Company: {customer.company}")

# Add a follow-up message
updated_ticket = sage.add_message(
    ticket_id=ticket.id,
    message="Additional context: I'm using the mobile app.",
    sender_type="customer",
)

print(f"\nMessages on ticket: {len(updated_ticket.messages)}")
