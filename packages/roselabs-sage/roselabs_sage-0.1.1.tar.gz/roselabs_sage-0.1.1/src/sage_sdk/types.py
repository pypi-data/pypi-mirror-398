"""Sage SDK type definitions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal


class TicketStatus(str, Enum):
    """Ticket status values."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_ON_CUSTOMER = "waiting_on_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Ticket priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


MessageSenderType = Literal["customer", "agent", "system"]


@dataclass
class Customer:
    """A customer in the Sage system."""
    id: str
    email: str
    name: str | None = None
    external_id: str | None = None
    company: str | None = None
    phone: str | None = None
    custom_data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Customer":
        """Create a Customer from API response data."""
        return cls(
            id=data["id"],
            email=data["email"],
            name=data.get("name"),
            external_id=data.get("external_id"),
            company=data.get("company"),
            phone=data.get("phone"),
            custom_data=data.get("custom_data", {}),
            created_at=_parse_datetime(data.get("created_at")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        result: dict[str, Any] = {
            "id": self.id,
            "email": self.email,
        }
        if self.name:
            result["name"] = self.name
        if self.external_id:
            result["external_id"] = self.external_id
        if self.company:
            result["company"] = self.company
        if self.phone:
            result["phone"] = self.phone
        if self.custom_data:
            result["custom_data"] = self.custom_data
        return result


@dataclass
class TicketMessage:
    """A message within a ticket thread."""
    id: str
    content: str
    sender_type: MessageSenderType
    sender_name: str | None = None
    is_internal: bool = False
    created_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TicketMessage":
        """Create a TicketMessage from API response data."""
        return cls(
            id=data["id"],
            content=data["content"],
            sender_type=data["sender_type"],
            sender_name=data.get("sender_name"),
            is_internal=data.get("is_internal", False),
            created_at=_parse_datetime(data.get("created_at")),
        )


@dataclass
class Ticket:
    """A support ticket."""
    id: str
    ticket_number: str
    subject: str
    status: TicketStatus
    priority: TicketPriority
    customer_id: str
    customer_email: str | None = None
    customer_name: str | None = None
    assigned_to: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    messages: list[TicketMessage] = field(default_factory=list)
    portal_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Ticket":
        """Create a Ticket from API response data."""
        messages = [
            TicketMessage.from_dict(m)
            for m in data.get("messages", [])
        ]

        return cls(
            id=data["id"],
            ticket_number=data.get("ticket_number", data["id"][:8]),
            subject=data["subject"],
            status=TicketStatus(data["status"]),
            priority=TicketPriority(data["priority"]),
            customer_id=data["customer_id"],
            customer_email=data.get("customer_email"),
            customer_name=data.get("customer_name"),
            assigned_to=data.get("assigned_to"),
            metadata=data.get("metadata", {}),
            messages=messages,
            portal_url=data.get("portal_url"),
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "ticket_number": self.ticket_number,
            "subject": self.subject,
            "status": self.status.value,
            "priority": self.priority.value,
            "customer_id": self.customer_id,
            "customer_email": self.customer_email,
            "customer_name": self.customer_name,
            "assigned_to": self.assigned_to,
            "metadata": self.metadata,
            "portal_url": self.portal_url,
        }


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO datetime string."""
    if value is None:
        return None
    try:
        # Handle various ISO formats
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
