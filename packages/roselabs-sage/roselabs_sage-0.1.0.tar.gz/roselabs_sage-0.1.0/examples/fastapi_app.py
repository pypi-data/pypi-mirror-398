"""FastAPI integration example for Sage SDK."""

import os
from fastapi import FastAPI, Request, Depends, HTTPException
from pydantic import BaseModel

from sage_sdk import Sage
from sage_sdk.fastapi import instrument_fastapi

# Initialize Sage
sage = Sage(
    api_key=os.environ["SAGE_API_KEY"],
    default_metadata={"app": "my-fastapi-app"},
)

app = FastAPI(title="My App with Sage Support")


# Optional: Extract customer email from authenticated requests
def get_customer_email(request: Request) -> str | None:
    """Get customer email from request state (set by auth middleware)."""
    if hasattr(request.state, "user"):
        return request.state.user.email
    return None


# Instrument FastAPI with Sage
# This captures exceptions and optionally creates tickets
instrument_fastapi(
    app,
    sage,
    create_tickets=True,  # Auto-create tickets for errors
    get_customer_email=get_customer_email,
)


# Example: Manual ticket creation endpoint
class SupportRequest(BaseModel):
    subject: str
    message: str
    priority: str = "medium"


@app.post("/api/support/tickets")
async def create_support_ticket(
    request: Request,
    support_request: SupportRequest,
):
    """Create a support ticket from the app."""
    # Get user email from auth (assumes auth middleware sets this)
    user_email = getattr(request.state, "user_email", "anonymous@example.com")

    ticket = await sage.create_ticket_async(
        customer_email=user_email,
        subject=support_request.subject,
        message=support_request.message,
        priority=support_request.priority,
        metadata={
            "source": "api",
            "user_agent": request.headers.get("user-agent"),
        },
    )

    return {
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "portal_url": ticket.portal_url,
    }


# Example: Endpoint that might throw an error
@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """Get a user - might throw an error that creates a ticket."""
    if user_id == "error":
        raise HTTPException(status_code=500, detail="Something went wrong!")

    return {"user_id": user_id, "name": "Test User"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
