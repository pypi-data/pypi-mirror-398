"""Tests for Sage SDK client."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from sage_sdk import Sage, SageConfig
from sage_sdk.exceptions import (
    SageError,
    SageConfigError,
    SageAPIError,
    SageRateLimitError,
)
from sage_sdk.types import Ticket, Customer, TicketPriority


# =============================================================================
# Configuration Tests
# =============================================================================

class TestSageConfig:
    """Tests for SageConfig validation."""

    def test_valid_config(self):
        """Should accept valid configuration."""
        config = SageConfig(api_key="sk_sage_valid_key_12345678901234567890")
        config.validate()  # Should not raise

    def test_missing_api_key(self):
        """Should reject missing api_key."""
        config = SageConfig(api_key="")
        with pytest.raises(SageConfigError) as exc_info:
            config.validate()
        assert "api_key is required" in str(exc_info.value)

    def test_invalid_api_key_prefix(self):
        """Should reject api_key without sk_sage_ prefix."""
        config = SageConfig(api_key="invalid_key_12345678901234567890")
        with pytest.raises(SageConfigError) as exc_info:
            config.validate()
        assert "must start with 'sk_sage_'" in str(exc_info.value)

    def test_api_key_too_short(self):
        """Should reject api_key that is too short."""
        config = SageConfig(api_key="sk_sage_short")
        with pytest.raises(SageConfigError) as exc_info:
            config.validate()
        assert "too short" in str(exc_info.value)

    def test_invalid_api_url(self):
        """Should reject api_url without http prefix."""
        config = SageConfig(
            api_key="sk_sage_valid_key_12345678901234567890",
            api_url="invalid-url"
        )
        with pytest.raises(SageConfigError) as exc_info:
            config.validate()
        assert "must start with http" in str(exc_info.value)

    def test_empty_api_url(self):
        """Should reject empty api_url."""
        config = SageConfig(
            api_key="sk_sage_valid_key_12345678901234567890",
            api_url=""
        )
        with pytest.raises(SageConfigError) as exc_info:
            config.validate()
        assert "api_url is required" in str(exc_info.value)

    def test_invalid_timeout(self):
        """Should reject non-positive timeout."""
        config = SageConfig(
            api_key="sk_sage_valid_key_12345678901234567890",
            timeout=0
        )
        with pytest.raises(SageConfigError) as exc_info:
            config.validate()
        assert "timeout must be positive" in str(exc_info.value)

    def test_negative_timeout(self):
        """Should reject negative timeout."""
        config = SageConfig(
            api_key="sk_sage_valid_key_12345678901234567890",
            timeout=-1
        )
        with pytest.raises(SageConfigError) as exc_info:
            config.validate()
        assert "timeout must be positive" in str(exc_info.value)

    def test_custom_api_url(self):
        """Should accept custom api_url."""
        config = SageConfig(
            api_key="sk_sage_valid_key_12345678901234567890",
            api_url="https://custom.api.com"
        )
        config.validate()  # Should not raise
        assert config.api_url == "https://custom.api.com"

    def test_http_api_url(self):
        """Should accept http api_url."""
        config = SageConfig(
            api_key="sk_sage_valid_key_12345678901234567890",
            api_url="http://localhost:8000"
        )
        config.validate()  # Should not raise

    def test_default_metadata(self):
        """Should accept default_metadata."""
        config = SageConfig(
            api_key="sk_sage_valid_key_12345678901234567890",
            default_metadata={"app": "test", "version": "1.0"}
        )
        config.validate()
        assert config.default_metadata == {"app": "test", "version": "1.0"}


# =============================================================================
# Sage Client Tests
# =============================================================================

class TestSageClient:
    """Tests for Sage client initialization."""

    def test_init_with_valid_config(self):
        """Should initialize with valid configuration."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        assert sage.config.api_key == "sk_sage_valid_key_12345678901234567890"

    def test_init_with_invalid_config_raises(self):
        """Should raise SageConfigError with invalid configuration."""
        with pytest.raises(SageConfigError):
            Sage(api_key="invalid")

    def test_init_with_custom_options(self):
        """Should accept custom options."""
        sage = Sage(
            api_key="sk_sage_valid_key_12345678901234567890",
            api_url="https://custom.api.com",
            timeout=60.0,
            debug=True,
            default_metadata={"env": "test"}
        )
        assert sage.config.api_url == "https://custom.api.com"
        assert sage.config.timeout == 60.0
        assert sage.config.debug is True
        assert sage.config.default_metadata == {"env": "test"}

    def test_get_headers(self):
        """Should include correct headers."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        headers = sage._get_headers()

        assert headers["Authorization"] == "Bearer sk_sage_valid_key_12345678901234567890"
        assert headers["Content-Type"] == "application/json"
        assert "sage-python-sdk" in headers["User-Agent"]

    def test_context_manager(self):
        """Should work as context manager."""
        with Sage(api_key="sk_sage_valid_key_12345678901234567890") as sage:
            assert sage is not None

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Should work as async context manager."""
        async with Sage(api_key="sk_sage_valid_key_12345678901234567890") as sage:
            assert sage is not None


# =============================================================================
# API Response Handling Tests
# =============================================================================

class TestResponseHandling:
    """Tests for API response handling."""

    def test_handle_rate_limit_response(self):
        """Should raise SageRateLimitError for 429 response."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")

        response = Mock()
        response.status_code = 429
        response.headers = {"Retry-After": "60"}

        with pytest.raises(SageRateLimitError) as exc_info:
            sage._handle_response(response)

        assert exc_info.value.retry_after == 60
        assert exc_info.value.status_code == 429

    def test_handle_rate_limit_without_retry_after(self):
        """Should handle 429 without Retry-After header."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")

        response = Mock()
        response.status_code = 429
        response.headers = {}

        with pytest.raises(SageRateLimitError) as exc_info:
            sage._handle_response(response)

        assert exc_info.value.retry_after is None

    def test_handle_api_error_with_detail(self):
        """Should extract detail from error response."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")

        response = Mock()
        response.status_code = 400
        response.json.return_value = {"detail": "Invalid email format"}

        with pytest.raises(SageAPIError) as exc_info:
            sage._handle_response(response)

        assert "Invalid email format" in str(exc_info.value)
        assert exc_info.value.status_code == 400

    def test_handle_api_error_with_message(self):
        """Should extract message from error response."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")

        response = Mock()
        response.status_code = 500
        response.json.return_value = {"message": "Internal server error"}

        with pytest.raises(SageAPIError) as exc_info:
            sage._handle_response(response)

        assert "Internal server error" in str(exc_info.value)

    def test_handle_api_error_json_parse_failure(self):
        """Should handle response when JSON parsing fails."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")

        response = Mock()
        response.status_code = 500
        response.json.side_effect = Exception("Invalid JSON")
        response.text = "Server Error"

        with pytest.raises(SageAPIError) as exc_info:
            sage._handle_response(response)

        assert "Server Error" in str(exc_info.value)

    def test_handle_successful_response(self):
        """Should return JSON for successful response."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")

        response = Mock()
        response.status_code = 200
        response.json.return_value = {"id": "ticket_123"}

        result = sage._handle_response(response)
        assert result == {"id": "ticket_123"}


# =============================================================================
# Create Ticket Tests
# =============================================================================

class TestCreateTicket:
    """Tests for create_ticket method."""

    @patch.object(Sage, '_get_sync_client')
    def test_create_ticket_basic(self, mock_get_client):
        """Should create ticket with basic options."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket_123",
            "ticket_number": "TKT-001",
            "subject": "Test ticket",
            "status": "open",
            "priority": "medium",
            "customer_id": "cust_123",
            "metadata": {},
            "messages": [],
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        ticket = sage.create_ticket(
            customer_email="test@example.com",
            subject="Test ticket",
            message="This is a test"
        )

        assert ticket.id == "ticket_123"
        assert ticket.ticket_number == "TKT-001"

        # Verify the payload
        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["customer_email"] == "test@example.com"
        assert payload["subject"] == "Test ticket"
        assert payload["message"] == "This is a test"
        assert payload["priority"] == "medium"

    @patch.object(Sage, '_get_sync_client')
    def test_create_ticket_with_customer_name(self, mock_get_client):
        """Should include customer_name when provided."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket_123",
            "ticket_number": "TKT-001",
            "subject": "Test",
            "status": "open",
            "priority": "medium",
            "customer_id": "cust_123",
            "customer_name": "John Doe",
            "metadata": {},
            "messages": [],
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        sage.create_ticket(
            customer_email="test@example.com",
            subject="Test",
            message="Test",
            customer_name="John Doe"
        )

        payload = mock_client.post.call_args[1]["json"]
        assert payload["customer_name"] == "John Doe"

    @patch.object(Sage, '_get_sync_client')
    def test_create_ticket_with_priority(self, mock_get_client):
        """Should use provided priority."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket_123",
            "ticket_number": "TKT-001",
            "subject": "Urgent",
            "status": "open",
            "priority": "urgent",
            "customer_id": "cust_123",
            "metadata": {},
            "messages": [],
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        sage.create_ticket(
            customer_email="test@example.com",
            subject="Urgent",
            message="This is urgent",
            priority="urgent"
        )

        payload = mock_client.post.call_args[1]["json"]
        assert payload["priority"] == "urgent"

    @patch.object(Sage, '_get_sync_client')
    def test_create_ticket_with_priority_enum(self, mock_get_client):
        """Should accept TicketPriority enum."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket_123",
            "ticket_number": "TKT-001",
            "subject": "Test",
            "status": "open",
            "priority": "high",
            "customer_id": "cust_123",
            "metadata": {},
            "messages": [],
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        sage.create_ticket(
            customer_email="test@example.com",
            subject="Test",
            message="Test",
            priority=TicketPriority.HIGH
        )

        payload = mock_client.post.call_args[1]["json"]
        assert payload["priority"] == "high"

    @patch.object(Sage, '_get_sync_client')
    def test_create_ticket_with_metadata(self, mock_get_client):
        """Should include metadata when provided."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket_123",
            "ticket_number": "TKT-001",
            "subject": "Test",
            "status": "open",
            "priority": "medium",
            "customer_id": "cust_123",
            "metadata": {"user_id": "123"},
            "messages": [],
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        sage.create_ticket(
            customer_email="test@example.com",
            subject="Test",
            message="Test",
            metadata={"user_id": "123"}
        )

        payload = mock_client.post.call_args[1]["json"]
        assert payload["metadata"] == {"user_id": "123"}

    @patch.object(Sage, '_get_sync_client')
    def test_create_ticket_merges_default_metadata(self, mock_get_client):
        """Should merge default_metadata with provided metadata."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket_123",
            "ticket_number": "TKT-001",
            "subject": "Test",
            "status": "open",
            "priority": "medium",
            "customer_id": "cust_123",
            "metadata": {"app": "test", "version": "1.0", "user_id": "123"},
            "messages": [],
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(
            api_key="sk_sage_valid_key_12345678901234567890",
            default_metadata={"app": "test", "version": "1.0"}
        )
        sage.create_ticket(
            customer_email="test@example.com",
            subject="Test",
            message="Test",
            metadata={"user_id": "123"}
        )

        payload = mock_client.post.call_args[1]["json"]
        assert payload["metadata"] == {"app": "test", "version": "1.0", "user_id": "123"}


# =============================================================================
# Async Create Ticket Tests
# =============================================================================

class TestCreateTicketAsync:
    """Tests for async create_ticket method."""

    @pytest.mark.asyncio
    @patch.object(Sage, '_get_async_client')
    async def test_create_ticket_async(self, mock_get_client):
        """Should create ticket asynchronously."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket_123",
            "ticket_number": "TKT-001",
            "subject": "Test",
            "status": "open",
            "priority": "medium",
            "customer_id": "cust_123",
            "metadata": {},
            "messages": [],
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        ticket = await sage.create_ticket_async(
            customer_email="test@example.com",
            subject="Test",
            message="Test"
        )

        assert ticket.id == "ticket_123"


# =============================================================================
# Get Ticket Tests
# =============================================================================

class TestGetTicket:
    """Tests for get_ticket method."""

    @patch.object(Sage, '_get_sync_client')
    def test_get_ticket(self, mock_get_client):
        """Should get ticket by ID."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket_123",
            "ticket_number": "TKT-001",
            "subject": "Test ticket",
            "status": "open",
            "priority": "medium",
            "customer_id": "cust_123",
            "metadata": {},
            "messages": [
                {
                    "id": "msg_1",
                    "content": "Hello",
                    "sender_type": "customer",
                    "is_internal": False,
                }
            ],
        }
        mock_client.get.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        ticket = sage.get_ticket("ticket_123")

        assert ticket.id == "ticket_123"
        assert len(ticket.messages) == 1
        assert ticket.messages[0].content == "Hello"

    @patch.object(Sage, '_get_sync_client')
    def test_get_ticket_not_found(self, mock_get_client):
        """Should raise SageAPIError for 404."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Ticket not found"}
        mock_client.get.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")

        with pytest.raises(SageAPIError) as exc_info:
            sage.get_ticket("invalid_id")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch.object(Sage, '_get_async_client')
    async def test_get_ticket_async(self, mock_get_client):
        """Should get ticket asynchronously."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket_123",
            "ticket_number": "TKT-001",
            "subject": "Test",
            "status": "open",
            "priority": "medium",
            "customer_id": "cust_123",
            "metadata": {},
            "messages": [],
        }
        mock_client.get.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        ticket = await sage.get_ticket_async("ticket_123")

        assert ticket.id == "ticket_123"


# =============================================================================
# Add Message Tests
# =============================================================================

class TestAddMessage:
    """Tests for add_message method."""

    @patch.object(Sage, '_get_sync_client')
    def test_add_message(self, mock_get_client):
        """Should add message to ticket."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket_123",
            "ticket_number": "TKT-001",
            "subject": "Test",
            "status": "open",
            "priority": "medium",
            "customer_id": "cust_123",
            "metadata": {},
            "messages": [
                {"id": "msg_1", "content": "Original", "sender_type": "customer", "is_internal": False},
                {"id": "msg_2", "content": "System update", "sender_type": "system", "is_internal": False},
            ],
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        ticket = sage.add_message("ticket_123", "System update")

        assert len(ticket.messages) == 2

        payload = mock_client.post.call_args[1]["json"]
        assert payload["content"] == "System update"
        assert payload["sender_type"] == "system"

    @patch.object(Sage, '_get_sync_client')
    def test_add_message_custom_sender_type(self, mock_get_client):
        """Should use custom sender_type."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket_123",
            "ticket_number": "TKT-001",
            "subject": "Test",
            "status": "open",
            "priority": "medium",
            "customer_id": "cust_123",
            "metadata": {},
            "messages": [],
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        sage.add_message("ticket_123", "Agent reply", sender_type="agent")

        payload = mock_client.post.call_args[1]["json"]
        assert payload["sender_type"] == "agent"

    @pytest.mark.asyncio
    @patch.object(Sage, '_get_async_client')
    async def test_add_message_async(self, mock_get_client):
        """Should add message asynchronously."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket_123",
            "ticket_number": "TKT-001",
            "subject": "Test",
            "status": "open",
            "priority": "medium",
            "customer_id": "cust_123",
            "metadata": {},
            "messages": [],
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        ticket = await sage.add_message_async("ticket_123", "Test")

        assert ticket.id == "ticket_123"


# =============================================================================
# Identify Customer Tests
# =============================================================================

class TestIdentifyCustomer:
    """Tests for identify_customer method."""

    @patch.object(Sage, '_get_sync_client')
    def test_identify_customer_basic(self, mock_get_client):
        """Should identify customer with email only."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cust_123",
            "email": "test@example.com",
            "name": None,
            "external_id": None,
            "company": None,
            "phone": None,
            "custom_data": {},
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        customer = sage.identify_customer(email="test@example.com")

        assert customer.id == "cust_123"
        assert customer.email == "test@example.com"

    @patch.object(Sage, '_get_sync_client')
    def test_identify_customer_with_all_fields(self, mock_get_client):
        """Should identify customer with all fields."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cust_123",
            "email": "test@example.com",
            "name": "John Doe",
            "external_id": "ext_123",
            "company": "Acme Inc",
            "phone": "+1234567890",
            "custom_data": {"plan": "enterprise"},
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        customer = sage.identify_customer(
            email="test@example.com",
            name="John Doe",
            external_id="ext_123",
            company="Acme Inc",
            phone="+1234567890",
            metadata={"plan": "enterprise"}
        )

        payload = mock_client.post.call_args[1]["json"]
        assert payload["email"] == "test@example.com"
        assert payload["name"] == "John Doe"
        assert payload["external_id"] == "ext_123"
        assert payload["company"] == "Acme Inc"
        assert payload["phone"] == "+1234567890"
        assert payload["custom_data"] == {"plan": "enterprise"}

        assert customer.name == "John Doe"
        assert customer.external_id == "ext_123"

    @pytest.mark.asyncio
    @patch.object(Sage, '_get_async_client')
    async def test_identify_customer_async(self, mock_get_client):
        """Should identify customer asynchronously."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cust_123",
            "email": "test@example.com",
            "custom_data": {},
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client

        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        customer = await sage.identify_customer_async(email="test@example.com")

        assert customer.id == "cust_123"


# =============================================================================
# Module-level Functions Tests
# =============================================================================

class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    def test_init(self):
        """Should initialize default instance."""
        import sage_sdk

        # Reset the default instance
        sage_sdk._default_instance = None

        instance = sage_sdk.init(api_key="sk_sage_valid_key_12345678901234567890")
        assert instance is not None
        assert sage_sdk.get_instance() is instance

    def test_get_instance_before_init(self):
        """Should return None before init."""
        import sage_sdk

        # Reset the default instance
        sage_sdk._default_instance = None

        assert sage_sdk.get_instance() is None

    def test_create_ticket_without_init(self):
        """Should raise SageError when using create_ticket without init."""
        import sage_sdk

        # Reset the default instance
        sage_sdk._default_instance = None

        with pytest.raises(SageError) as exc_info:
            sage_sdk.create_ticket(
                customer_email="test@example.com",
                subject="Test",
                message="Test"
            )

        assert "not initialized" in str(exc_info.value)

    def test_identify_customer_without_init(self):
        """Should raise SageError when using identify_customer without init."""
        import sage_sdk

        # Reset the default instance
        sage_sdk._default_instance = None

        with pytest.raises(SageError) as exc_info:
            sage_sdk.identify_customer(email="test@example.com")

        assert "not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_ticket_async_without_init(self):
        """Should raise SageError when using create_ticket_async without init."""
        import sage_sdk

        # Reset the default instance
        sage_sdk._default_instance = None

        with pytest.raises(SageError) as exc_info:
            await sage_sdk.create_ticket_async(
                customer_email="test@example.com",
                subject="Test",
                message="Test"
            )

        assert "not initialized" in str(exc_info.value)


# =============================================================================
# Client Cleanup Tests
# =============================================================================

class TestClientCleanup:
    """Tests for client cleanup methods."""

    def test_close(self):
        """Should close sync client."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")

        # Create a mock client
        mock_client = Mock()
        sage._sync_client = mock_client

        sage.close()

        mock_client.close.assert_called_once()
        assert sage._sync_client is None

    @pytest.mark.asyncio
    async def test_aclose(self):
        """Should close async client."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")

        # Create a mock async client
        mock_client = AsyncMock()
        sage._async_client = mock_client

        await sage.aclose()

        mock_client.aclose.assert_called_once()
        assert sage._async_client is None
