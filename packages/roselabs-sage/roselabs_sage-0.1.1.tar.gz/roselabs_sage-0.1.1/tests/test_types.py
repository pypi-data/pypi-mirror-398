"""Tests for Sage SDK types."""

import pytest
from datetime import datetime

from sage_sdk.types import (
    Customer,
    Ticket,
    TicketMessage,
    TicketStatus,
    TicketPriority,
    _parse_datetime,
)


# =============================================================================
# Enum Tests
# =============================================================================

class TestTicketStatus:
    """Tests for TicketStatus enum."""

    def test_open_value(self):
        assert TicketStatus.OPEN.value == "open"

    def test_in_progress_value(self):
        assert TicketStatus.IN_PROGRESS.value == "in_progress"

    def test_waiting_on_customer_value(self):
        assert TicketStatus.WAITING_ON_CUSTOMER.value == "waiting_on_customer"

    def test_resolved_value(self):
        assert TicketStatus.RESOLVED.value == "resolved"

    def test_closed_value(self):
        assert TicketStatus.CLOSED.value == "closed"

    def test_is_string(self):
        """TicketStatus should be a string."""
        assert isinstance(TicketStatus.OPEN, str)
        assert TicketStatus.OPEN == "open"


class TestTicketPriority:
    """Tests for TicketPriority enum."""

    def test_low_value(self):
        assert TicketPriority.LOW.value == "low"

    def test_medium_value(self):
        assert TicketPriority.MEDIUM.value == "medium"

    def test_high_value(self):
        assert TicketPriority.HIGH.value == "high"

    def test_urgent_value(self):
        assert TicketPriority.URGENT.value == "urgent"

    def test_is_string(self):
        """TicketPriority should be a string."""
        assert isinstance(TicketPriority.HIGH, str)
        assert TicketPriority.HIGH == "high"


# =============================================================================
# Customer Tests
# =============================================================================

class TestCustomer:
    """Tests for Customer dataclass."""

    def test_from_dict_minimal(self):
        """Should create Customer with minimal data."""
        data = {
            "id": "cust_123",
            "email": "test@example.com",
        }

        customer = Customer.from_dict(data)

        assert customer.id == "cust_123"
        assert customer.email == "test@example.com"
        assert customer.name is None
        assert customer.external_id is None
        assert customer.company is None
        assert customer.phone is None
        assert customer.custom_data == {}

    def test_from_dict_full(self):
        """Should create Customer with all fields."""
        data = {
            "id": "cust_123",
            "email": "test@example.com",
            "name": "John Doe",
            "external_id": "ext_123",
            "company": "Acme Inc",
            "phone": "+1234567890",
            "custom_data": {"plan": "enterprise", "mrr": 299},
            "created_at": "2024-01-01T00:00:00Z",
        }

        customer = Customer.from_dict(data)

        assert customer.id == "cust_123"
        assert customer.email == "test@example.com"
        assert customer.name == "John Doe"
        assert customer.external_id == "ext_123"
        assert customer.company == "Acme Inc"
        assert customer.phone == "+1234567890"
        assert customer.custom_data == {"plan": "enterprise", "mrr": 299}
        assert customer.created_at is not None

    def test_to_dict_minimal(self):
        """Should serialize Customer with minimal fields."""
        customer = Customer(id="cust_123", email="test@example.com")

        result = customer.to_dict()

        assert result == {"id": "cust_123", "email": "test@example.com"}

    def test_to_dict_full(self):
        """Should serialize Customer with all fields."""
        customer = Customer(
            id="cust_123",
            email="test@example.com",
            name="John Doe",
            external_id="ext_123",
            company="Acme Inc",
            phone="+1234567890",
            custom_data={"plan": "enterprise"},
        )

        result = customer.to_dict()

        assert result["id"] == "cust_123"
        assert result["email"] == "test@example.com"
        assert result["name"] == "John Doe"
        assert result["external_id"] == "ext_123"
        assert result["company"] == "Acme Inc"
        assert result["phone"] == "+1234567890"
        assert result["custom_data"] == {"plan": "enterprise"}


# =============================================================================
# TicketMessage Tests
# =============================================================================

class TestTicketMessage:
    """Tests for TicketMessage dataclass."""

    def test_from_dict_minimal(self):
        """Should create TicketMessage with minimal data."""
        data = {
            "id": "msg_123",
            "content": "Hello world",
            "sender_type": "customer",
        }

        message = TicketMessage.from_dict(data)

        assert message.id == "msg_123"
        assert message.content == "Hello world"
        assert message.sender_type == "customer"
        assert message.sender_name is None
        assert message.is_internal is False

    def test_from_dict_full(self):
        """Should create TicketMessage with all fields."""
        data = {
            "id": "msg_123",
            "content": "Internal note",
            "sender_type": "agent",
            "sender_name": "Agent Smith",
            "is_internal": True,
            "created_at": "2024-01-01T12:00:00Z",
        }

        message = TicketMessage.from_dict(data)

        assert message.id == "msg_123"
        assert message.content == "Internal note"
        assert message.sender_type == "agent"
        assert message.sender_name == "Agent Smith"
        assert message.is_internal is True
        assert message.created_at is not None

    def test_from_dict_system_message(self):
        """Should create system message."""
        data = {
            "id": "msg_123",
            "content": "Ticket status changed to resolved",
            "sender_type": "system",
            "is_internal": False,
        }

        message = TicketMessage.from_dict(data)

        assert message.sender_type == "system"


# =============================================================================
# Ticket Tests
# =============================================================================

class TestTicket:
    """Tests for Ticket dataclass."""

    def test_from_dict_minimal(self):
        """Should create Ticket with minimal data."""
        data = {
            "id": "ticket_123",
            "subject": "Test ticket",
            "status": "open",
            "priority": "medium",
            "customer_id": "cust_123",
        }

        ticket = Ticket.from_dict(data)

        assert ticket.id == "ticket_123"
        assert ticket.subject == "Test ticket"
        assert ticket.status == TicketStatus.OPEN
        assert ticket.priority == TicketPriority.MEDIUM
        assert ticket.customer_id == "cust_123"
        assert ticket.metadata == {}
        assert ticket.messages == []

    def test_from_dict_full(self):
        """Should create Ticket with all fields."""
        data = {
            "id": "ticket_123",
            "ticket_number": "TKT-001",
            "subject": "Help with billing",
            "status": "in_progress",
            "priority": "high",
            "customer_id": "cust_123",
            "customer_email": "test@example.com",
            "customer_name": "John Doe",
            "assigned_to": "agent_123",
            "metadata": {"user_id": "123", "plan": "pro"},
            "messages": [
                {
                    "id": "msg_1",
                    "content": "Hello",
                    "sender_type": "customer",
                    "is_internal": False,
                }
            ],
            "portal_url": "https://portal.example.com/ticket/123",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T12:00:00Z",
        }

        ticket = Ticket.from_dict(data)

        assert ticket.id == "ticket_123"
        assert ticket.ticket_number == "TKT-001"
        assert ticket.subject == "Help with billing"
        assert ticket.status == TicketStatus.IN_PROGRESS
        assert ticket.priority == TicketPriority.HIGH
        assert ticket.customer_id == "cust_123"
        assert ticket.customer_email == "test@example.com"
        assert ticket.customer_name == "John Doe"
        assert ticket.assigned_to == "agent_123"
        assert ticket.metadata == {"user_id": "123", "plan": "pro"}
        assert len(ticket.messages) == 1
        assert ticket.messages[0].content == "Hello"
        assert ticket.portal_url == "https://portal.example.com/ticket/123"
        assert ticket.created_at is not None
        assert ticket.updated_at is not None

    def test_from_dict_fallback_ticket_number(self):
        """Should use id prefix as fallback ticket_number."""
        data = {
            "id": "ticket_abc123def456",
            "subject": "Test",
            "status": "open",
            "priority": "medium",
            "customer_id": "cust_123",
        }

        ticket = Ticket.from_dict(data)

        assert ticket.ticket_number == "ticket_a"  # First 8 chars of id

    def test_from_dict_with_multiple_messages(self):
        """Should handle multiple messages."""
        data = {
            "id": "ticket_123",
            "subject": "Test",
            "status": "open",
            "priority": "medium",
            "customer_id": "cust_123",
            "messages": [
                {"id": "msg_1", "content": "Hello", "sender_type": "customer", "is_internal": False},
                {"id": "msg_2", "content": "Hi there!", "sender_type": "agent", "is_internal": False},
                {"id": "msg_3", "content": "Internal note", "sender_type": "agent", "is_internal": True},
            ],
        }

        ticket = Ticket.from_dict(data)

        assert len(ticket.messages) == 3
        assert ticket.messages[0].sender_type == "customer"
        assert ticket.messages[1].sender_type == "agent"
        assert ticket.messages[2].is_internal is True

    def test_to_dict(self):
        """Should serialize Ticket to dictionary."""
        ticket = Ticket(
            id="ticket_123",
            ticket_number="TKT-001",
            subject="Test ticket",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            customer_id="cust_123",
            customer_email="test@example.com",
            customer_name="John Doe",
            assigned_to="agent_123",
            metadata={"key": "value"},
            portal_url="https://portal.example.com",
        )

        result = ticket.to_dict()

        assert result["id"] == "ticket_123"
        assert result["ticket_number"] == "TKT-001"
        assert result["subject"] == "Test ticket"
        assert result["status"] == "open"
        assert result["priority"] == "medium"
        assert result["customer_id"] == "cust_123"
        assert result["customer_email"] == "test@example.com"
        assert result["customer_name"] == "John Doe"
        assert result["assigned_to"] == "agent_123"
        assert result["metadata"] == {"key": "value"}
        assert result["portal_url"] == "https://portal.example.com"

    def test_all_status_values(self):
        """Should handle all status values."""
        for status in TicketStatus:
            data = {
                "id": "ticket_123",
                "subject": "Test",
                "status": status.value,
                "priority": "medium",
                "customer_id": "cust_123",
            }
            ticket = Ticket.from_dict(data)
            assert ticket.status == status

    def test_all_priority_values(self):
        """Should handle all priority values."""
        for priority in TicketPriority:
            data = {
                "id": "ticket_123",
                "subject": "Test",
                "status": "open",
                "priority": priority.value,
                "customer_id": "cust_123",
            }
            ticket = Ticket.from_dict(data)
            assert ticket.priority == priority


# =============================================================================
# Datetime Parsing Tests
# =============================================================================

class TestDatetimeParsing:
    """Tests for _parse_datetime function."""

    def test_parse_iso_format(self):
        """Should parse standard ISO format."""
        result = _parse_datetime("2024-01-15T10:30:00+00:00")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_z_suffix(self):
        """Should parse Z suffix (UTC)."""
        result = _parse_datetime("2024-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2024

    def test_parse_none(self):
        """Should return None for None input."""
        result = _parse_datetime(None)
        assert result is None

    def test_parse_invalid_format(self):
        """Should return None for invalid format."""
        result = _parse_datetime("invalid-date")
        assert result is None

    def test_parse_empty_string(self):
        """Should return None for empty string."""
        result = _parse_datetime("")
        assert result is None

    def test_parse_with_microseconds(self):
        """Should parse datetime with microseconds."""
        result = _parse_datetime("2024-01-15T10:30:00.123456+00:00")
        assert result is not None
        assert result.microsecond == 123456
