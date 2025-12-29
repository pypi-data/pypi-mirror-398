"""Sage SDK client implementation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from sage_sdk.exceptions import (
    SageAPIError,
    SageConfigError,
    SageRateLimitError,
)
from sage_sdk.types import Customer, Ticket, TicketPriority

logger = logging.getLogger("sage_sdk")

DEFAULT_API_URL = "https://api.sage.roselabs.io"
DEFAULT_TIMEOUT = 30.0


@dataclass
class SageConfig:
    """Configuration for the Sage SDK client."""

    api_key: str
    api_url: str = DEFAULT_API_URL
    timeout: float = DEFAULT_TIMEOUT
    debug: bool = False

    # Optional default metadata to include with all tickets
    default_metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate the configuration, raising SageConfigError if invalid."""
        errors: list[str] = []

        if not self.api_key:
            errors.append("api_key is required")
        elif not isinstance(self.api_key, str):
            errors.append("api_key must be a string")
        elif not self.api_key.startswith("sk_sage_"):
            errors.append("api_key must start with 'sk_sage_'")
        elif len(self.api_key) < 20:
            errors.append("api_key appears to be too short")

        if not self.api_url:
            errors.append("api_url is required")
        elif not self.api_url.startswith(("http://", "https://")):
            errors.append("api_url must start with http:// or https://")

        if self.timeout <= 0:
            errors.append("timeout must be positive")

        if errors:
            raise SageConfigError(
                f"Invalid Sage configuration:\n  - " + "\n  - ".join(errors)
            )


class Sage:
    """
    Sage SDK client for creating support tickets programmatically.

    Example:
        sage = Sage(api_key="sk_sage_...")

        ticket = sage.create_ticket(
            customer_email="user@example.com",
            subject="Help with billing",
            message="I need to update my payment method",
            metadata={"plan": "pro", "user_id": "123"}
        )

        print(f"Created ticket #{ticket.ticket_number}")
        print(f"Portal URL: {ticket.portal_url}")
    """

    def __init__(
        self,
        api_key: str,
        *,
        api_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        debug: bool = False,
        default_metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize the Sage client.

        Args:
            api_key: Your Sage API key (starts with sk_sage_)
            api_url: Custom API URL (optional, defaults to production)
            timeout: Request timeout in seconds (default: 30)
            debug: Enable debug logging (default: False)
            default_metadata: Default metadata to include with all tickets

        Raises:
            SageConfigError: If configuration is invalid
        """
        self.config = SageConfig(
            api_key=api_key,
            api_url=api_url or DEFAULT_API_URL,
            timeout=timeout,
            debug=debug,
            default_metadata=default_metadata or {},
        )

        # Validate configuration on init (fail fast)
        self.config.validate()

        if self.config.debug:
            logging.basicConfig(level=logging.DEBUG)
            logger.setLevel(logging.DEBUG)

        self._sync_client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None

    def _get_sync_client(self) -> httpx.Client:
        """Get or create the synchronous HTTP client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self.config.api_url,
                timeout=self.config.timeout,
                headers=self._get_headers(),
            )
        return self._sync_client

    def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.config.api_url,
                timeout=self.config.timeout,
                headers=self._get_headers(),
            )
        return self._async_client

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "sage-python-sdk/0.1.0",
        }

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response, raising appropriate errors."""
        if self.config.debug:
            logger.debug(f"Response [{response.status_code}]: {response.text[:500]}")

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise SageRateLimitError(
                "Rate limit exceeded. Please slow down your requests.",
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code >= 400:
            try:
                body = response.json()
                message = body.get("detail", body.get("message", str(body)))
            except Exception:
                message = response.text or f"HTTP {response.status_code}"

            raise SageAPIError(
                message=message,
                status_code=response.status_code,
                response_body=body if "body" in dir() else None,
            )

        return response.json()

    # -------------------------------------------------------------------------
    # Ticket Operations
    # -------------------------------------------------------------------------

    def create_ticket(
        self,
        customer_email: str,
        subject: str,
        message: str,
        *,
        customer_name: str | None = None,
        priority: TicketPriority | str = "medium",
        metadata: dict[str, Any] | None = None,
    ) -> Ticket:
        """
        Create a support ticket.

        Args:
            customer_email: Customer's email address
            subject: Ticket subject line
            message: Initial message content
            customer_name: Customer's name (optional)
            priority: Ticket priority - low, medium, high, urgent (default: medium)
            metadata: Additional context data (optional)

        Returns:
            The created Ticket object with id, ticket_number, and portal_url

        Example:
            ticket = sage.create_ticket(
                customer_email="user@example.com",
                subject="Can't login",
                message="I forgot my password and the reset email isn't arriving",
                metadata={"user_id": "u_123", "plan": "pro"}
            )
        """
        # Merge default metadata with provided metadata
        merged_metadata = {**self.config.default_metadata}
        if metadata:
            merged_metadata.update(metadata)

        # Normalize priority
        if isinstance(priority, TicketPriority):
            priority_value = priority.value
        else:
            priority_value = priority.lower()

        payload = {
            "customer_email": customer_email,
            "subject": subject,
            "message": message,
            "priority": priority_value,
        }

        if customer_name:
            payload["customer_name"] = customer_name
        if merged_metadata:
            payload["metadata"] = merged_metadata

        if self.config.debug:
            logger.debug(f"Creating ticket: {payload}")

        client = self._get_sync_client()
        response = client.post("/v1/tickets", json=payload)
        data = self._handle_response(response)

        return Ticket.from_dict(data)

    async def create_ticket_async(
        self,
        customer_email: str,
        subject: str,
        message: str,
        *,
        customer_name: str | None = None,
        priority: TicketPriority | str = "medium",
        metadata: dict[str, Any] | None = None,
    ) -> Ticket:
        """
        Create a support ticket asynchronously.

        Same as create_ticket() but for async contexts.
        """
        merged_metadata = {**self.config.default_metadata}
        if metadata:
            merged_metadata.update(metadata)

        if isinstance(priority, TicketPriority):
            priority_value = priority.value
        else:
            priority_value = priority.lower()

        payload = {
            "customer_email": customer_email,
            "subject": subject,
            "message": message,
            "priority": priority_value,
        }

        if customer_name:
            payload["customer_name"] = customer_name
        if merged_metadata:
            payload["metadata"] = merged_metadata

        if self.config.debug:
            logger.debug(f"Creating ticket (async): {payload}")

        client = self._get_async_client()
        response = await client.post("/v1/tickets", json=payload)
        data = self._handle_response(response)

        return Ticket.from_dict(data)

    def get_ticket(self, ticket_id: str) -> Ticket:
        """
        Get a ticket by ID.

        Args:
            ticket_id: The ticket ID

        Returns:
            The Ticket object with messages
        """
        client = self._get_sync_client()
        response = client.get(f"/v1/tickets/{ticket_id}")
        data = self._handle_response(response)
        return Ticket.from_dict(data)

    async def get_ticket_async(self, ticket_id: str) -> Ticket:
        """Get a ticket by ID asynchronously."""
        client = self._get_async_client()
        response = await client.get(f"/v1/tickets/{ticket_id}")
        data = self._handle_response(response)
        return Ticket.from_dict(data)

    def add_message(
        self,
        ticket_id: str,
        message: str,
        *,
        sender_type: str = "system",
    ) -> Ticket:
        """
        Add a message to an existing ticket.

        Args:
            ticket_id: The ticket ID
            message: Message content
            sender_type: Who is sending - customer, agent, or system (default: system)

        Returns:
            The updated Ticket object
        """
        payload = {
            "content": message,
            "sender_type": sender_type,
        }

        client = self._get_sync_client()
        response = client.post(f"/v1/tickets/{ticket_id}/messages", json=payload)
        data = self._handle_response(response)
        return Ticket.from_dict(data)

    async def add_message_async(
        self,
        ticket_id: str,
        message: str,
        *,
        sender_type: str = "system",
    ) -> Ticket:
        """Add a message to an existing ticket asynchronously."""
        payload = {
            "content": message,
            "sender_type": sender_type,
        }

        client = self._get_async_client()
        response = await client.post(f"/v1/tickets/{ticket_id}/messages", json=payload)
        data = self._handle_response(response)
        return Ticket.from_dict(data)

    # -------------------------------------------------------------------------
    # Customer Operations
    # -------------------------------------------------------------------------

    def identify_customer(
        self,
        email: str,
        *,
        name: str | None = None,
        external_id: str | None = None,
        company: str | None = None,
        phone: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Customer:
        """
        Identify or create a customer.

        If a customer with this email already exists, their profile will be updated.
        Otherwise, a new customer will be created.

        Args:
            email: Customer's email address (required)
            name: Customer's name
            external_id: Your internal ID for this customer
            company: Customer's company name
            phone: Customer's phone number
            metadata: Additional custom data

        Returns:
            The Customer object

        Example:
            customer = sage.identify_customer(
                email="user@example.com",
                name="Jane Smith",
                external_id="cust_123",
                metadata={"plan": "enterprise", "mrr": 299}
            )
        """
        payload: dict[str, Any] = {"email": email}

        if name:
            payload["name"] = name
        if external_id:
            payload["external_id"] = external_id
        if company:
            payload["company"] = company
        if phone:
            payload["phone"] = phone
        if metadata:
            payload["custom_data"] = metadata

        if self.config.debug:
            logger.debug(f"Identifying customer: {payload}")

        client = self._get_sync_client()
        response = client.post("/v1/customers/identify", json=payload)
        data = self._handle_response(response)

        return Customer.from_dict(data)

    async def identify_customer_async(
        self,
        email: str,
        *,
        name: str | None = None,
        external_id: str | None = None,
        company: str | None = None,
        phone: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Customer:
        """Identify or create a customer asynchronously."""
        payload: dict[str, Any] = {"email": email}

        if name:
            payload["name"] = name
        if external_id:
            payload["external_id"] = external_id
        if company:
            payload["company"] = company
        if phone:
            payload["phone"] = phone
        if metadata:
            payload["custom_data"] = metadata

        client = self._get_async_client()
        response = await client.post("/v1/customers/identify", json=payload)
        data = self._handle_response(response)

        return Customer.from_dict(data)

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def close(self) -> None:
        """Close HTTP clients and release resources."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None

    async def aclose(self) -> None:
        """Close async HTTP client."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    def __enter__(self) -> "Sage":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    async def __aenter__(self) -> "Sage":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
