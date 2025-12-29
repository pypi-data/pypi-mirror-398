# Sage Python SDK

The official Python SDK for [Sage](https://sage.roselabs.io) - Customer support ticketing made simple.

## Installation

```bash
pip install roselabs-sage
```

With framework support:

```bash
pip install roselabs-sage[fastapi]  # FastAPI/Starlette
pip install roselabs-sage[flask]    # Flask
pip install roselabs-sage[django]   # Django
pip install roselabs-sage[all]      # All frameworks
```

## Quick Start

```python
from sage_sdk import Sage

sage = Sage(api_key="sk_sage_...")

# Create a support ticket
ticket = sage.create_ticket(
    customer_email="user@example.com",
    subject="Help with billing",
    message="I need to update my payment method",
    metadata={"plan": "pro", "user_id": "123"}
)

print(f"Created ticket #{ticket.ticket_number}")
print(f"Portal URL: {ticket.portal_url}")
```

## Features

- **Simple API** - Create tickets with a single function call
- **Async Support** - Full async/await support for modern Python
- **Framework Integrations** - FastAPI, Flask, and Django support
- **Type Hints** - Full type annotations for IDE support
- **Fail Fast** - Configuration validated at initialization

## API Reference

### Creating Tickets

```python
from sage_sdk import Sage

sage = Sage(api_key="sk_sage_...")

# Basic ticket
ticket = sage.create_ticket(
    customer_email="user@example.com",
    subject="Can't login",
    message="I forgot my password and reset email isn't arriving",
)

# With priority and metadata
ticket = sage.create_ticket(
    customer_email="user@example.com",
    subject="Urgent: Production down",
    message="Our application is not responding",
    customer_name="Jane Smith",
    priority="urgent",  # low, medium, high, urgent
    metadata={
        "user_id": "u_123",
        "plan": "enterprise",
        "environment": "production",
    }
)
```

### Async Usage

```python
from sage_sdk import Sage

sage = Sage(api_key="sk_sage_...")

async def handle_support_request():
    ticket = await sage.create_ticket_async(
        customer_email="user@example.com",
        subject="Need help",
        message="...",
    )
    return ticket
```

### Identifying Customers

Pre-create or update customer profiles:

```python
customer = sage.identify_customer(
    email="user@example.com",
    name="Jane Smith",
    external_id="cust_123",  # Your internal ID
    company="Acme Corp",
    phone="+1-555-0123",
    metadata={
        "plan": "enterprise",
        "mrr": 299,
        "signup_date": "2024-01-15",
    }
)
```

### Adding Messages

Add messages to existing tickets:

```python
ticket = sage.add_message(
    ticket_id="ticket_abc123",
    message="Here's an update on your issue...",
    sender_type="system",  # customer, agent, or system
)
```

### Module-Level Functions

For simpler usage without managing instances:

```python
from sage_sdk import init, create_ticket

# Initialize once
init(api_key="sk_sage_...")

# Use anywhere
ticket = create_ticket(
    customer_email="user@example.com",
    subject="Help needed",
    message="...",
)
```

## Framework Integrations

### FastAPI

```python
from fastapi import FastAPI
from sage_sdk import Sage
from sage_sdk.fastapi import instrument_fastapi

sage = Sage(api_key="sk_sage_...")
app = FastAPI()

# Capture exceptions automatically
instrument_fastapi(app, sage)

# Or with auto-ticket creation
def get_user_email(request):
    return request.state.user.email if hasattr(request.state, 'user') else None

instrument_fastapi(
    app,
    sage,
    create_tickets=True,
    get_customer_email=get_user_email,
)
```

### Flask

```python
from flask import Flask, g
from sage_sdk import Sage
from sage_sdk.flask import init_app

app = Flask(__name__)
sage = Sage(api_key="sk_sage_...")

def get_email():
    return getattr(g, 'user_email', None)

init_app(app, sage, create_tickets=True, get_customer_email=get_email)
```

Or using app config:

```python
from flask import Flask
from sage_sdk.flask import SageFlask

app = Flask(__name__)
app.config["SAGE_API_KEY"] = "sk_sage_..."

sage_ext = SageFlask(app)
```

### Django

```python
# settings.py
SAGE_API_KEY = "sk_sage_..."
SAGE_CREATE_TICKETS = True  # Auto-create tickets for exceptions

MIDDLEWARE = [
    ...
    'sage_sdk.django.SageMiddleware',
]
```

```python
# views.py
from sage_sdk.django import get_sage

sage = get_sage()
ticket = sage.create_ticket(...)
```

## Configuration

```python
from sage_sdk import Sage

sage = Sage(
    api_key="sk_sage_...",          # Required
    api_url="https://...",          # Custom API URL (optional)
    timeout=30.0,                   # Request timeout in seconds
    debug=False,                    # Enable debug logging
    default_metadata={              # Included with all tickets
        "app_version": "1.2.3",
        "environment": "production",
    },
)
```

### Configuration Validation

The SDK validates configuration at initialization:

```python
from sage_sdk import Sage, SageConfigError

try:
    sage = Sage(api_key="invalid")
except SageConfigError as e:
    print(e)
    # Invalid Sage configuration:
    #   - api_key must start with 'sk_sage_'
```

## Error Handling

```python
from sage_sdk import Sage, SageAPIError, SageRateLimitError

sage = Sage(api_key="sk_sage_...")

try:
    ticket = sage.create_ticket(...)
except SageRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except SageAPIError as e:
    print(f"API error [{e.status_code}]: {e}")
```

## Context Manager

The client can be used as a context manager:

```python
with Sage(api_key="sk_sage_...") as sage:
    ticket = sage.create_ticket(...)
# Client automatically closed

# Async version
async with Sage(api_key="sk_sage_...") as sage:
    ticket = await sage.create_ticket_async(...)
```

## Types

The SDK provides typed dataclasses:

```python
from sage_sdk import Ticket, Customer, TicketStatus, TicketPriority

ticket: Ticket
ticket.id              # str
ticket.ticket_number   # str (e.g., "T-1234")
ticket.subject         # str
ticket.status          # TicketStatus (open, in_progress, resolved, closed)
ticket.priority        # TicketPriority (low, medium, high, urgent)
ticket.portal_url      # str | None
ticket.messages        # list[TicketMessage]
ticket.metadata        # dict[str, Any]
```

## License

MIT
