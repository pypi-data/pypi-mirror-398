"""
Sage SDK for Python - Customer support ticketing made simple.

Basic usage:
    from sage_sdk import Sage

    sage = Sage(api_key="sk_sage_...")

    sage.create_ticket(
        customer_email="user@example.com",
        subject="Help with billing",
        message="I need to update my payment method",
        metadata={"plan": "pro", "user_id": "123"}
    )
"""

from sage_sdk.client import Sage, SageConfig
from sage_sdk.types import (
    Customer,
    Ticket,
    TicketMessage,
    TicketPriority,
    TicketStatus,
)
from sage_sdk.exceptions import (
    SageError,
    SageConfigError,
    SageAPIError,
    SageRateLimitError,
)

__version__ = "0.1.0"
__all__ = [
    # Main client
    "Sage",
    "SageConfig",
    # Types
    "Customer",
    "Ticket",
    "TicketMessage",
    "TicketPriority",
    "TicketStatus",
    # Exceptions
    "SageError",
    "SageConfigError",
    "SageAPIError",
    "SageRateLimitError",
]

# Default instance for module-level convenience functions
_default_instance: Sage | None = None


def init(
    api_key: str,
    *,
    api_url: str | None = None,
    timeout: float = 30.0,
    debug: bool = False,
) -> Sage:
    """
    Initialize the default Sage instance.

    Args:
        api_key: Your Sage API key (starts with sk_sage_)
        api_url: Custom API URL (optional)
        timeout: Request timeout in seconds (default: 30)
        debug: Enable debug logging (default: False)

    Returns:
        The initialized Sage instance

    Example:
        from sage_sdk import init, create_ticket

        init(api_key="sk_sage_...")
        create_ticket(
            customer_email="user@example.com",
            subject="Help needed",
            message="..."
        )
    """
    global _default_instance
    _default_instance = Sage(
        api_key=api_key,
        api_url=api_url,
        timeout=timeout,
        debug=debug,
    )
    return _default_instance


def get_instance() -> Sage | None:
    """Get the default Sage instance, or None if not initialized."""
    return _default_instance


def _get_instance() -> Sage:
    """Get the default instance, raising an error if not initialized."""
    if _default_instance is None:
        raise SageError(
            "Sage SDK not initialized. Call sage_sdk.init() first, "
            "or create a Sage instance directly."
        )
    return _default_instance


def create_ticket(
    customer_email: str,
    subject: str,
    message: str,
    *,
    customer_name: str | None = None,
    priority: TicketPriority | str = "medium",
    metadata: dict | None = None,
) -> Ticket:
    """
    Create a support ticket using the default Sage instance.

    Args:
        customer_email: Customer's email address
        subject: Ticket subject line
        message: Initial message content
        customer_name: Customer's name (optional)
        priority: Ticket priority (low, medium, high, urgent)
        metadata: Additional context data (optional)

    Returns:
        The created Ticket object
    """
    return _get_instance().create_ticket(
        customer_email=customer_email,
        subject=subject,
        message=message,
        customer_name=customer_name,
        priority=priority,
        metadata=metadata,
    )


async def create_ticket_async(
    customer_email: str,
    subject: str,
    message: str,
    *,
    customer_name: str | None = None,
    priority: TicketPriority | str = "medium",
    metadata: dict | None = None,
) -> Ticket:
    """
    Create a support ticket asynchronously using the default Sage instance.
    """
    return await _get_instance().create_ticket_async(
        customer_email=customer_email,
        subject=subject,
        message=message,
        customer_name=customer_name,
        priority=priority,
        metadata=metadata,
    )


def identify_customer(
    email: str,
    *,
    name: str | None = None,
    external_id: str | None = None,
    company: str | None = None,
    phone: str | None = None,
    metadata: dict | None = None,
) -> Customer:
    """
    Identify or create a customer using the default Sage instance.
    """
    return _get_instance().identify_customer(
        email=email,
        name=name,
        external_id=external_id,
        company=company,
        phone=phone,
        metadata=metadata,
    )
