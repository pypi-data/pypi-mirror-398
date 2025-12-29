"""Tests for Sage FastAPI integration."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from sage_sdk import Sage
from sage_sdk.fastapi import SageMiddleware, instrument_fastapi, _build_request_context


# =============================================================================
# Request Context Tests
# =============================================================================

class TestBuildRequestContext:
    """Tests for _build_request_context function."""

    def test_basic_request_context(self):
        """Should extract basic request information."""
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url = Mock()
        mock_request.url.__str__ = lambda self: "https://example.com/api/users?page=1"
        mock_request.url.path = "/api/users"
        mock_request.query_params = {"page": "1"}
        mock_request.headers = {"content-type": "application/json", "accept": "application/json"}
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"

        context = _build_request_context(mock_request)

        assert context["request"]["method"] == "GET"
        assert context["request"]["url"] == "https://example.com/api/users?page=1"
        assert context["request"]["path"] == "/api/users"
        assert context["request"]["query"] == {"page": "1"}
        assert context["request"]["client_ip"] == "192.168.1.1"

    def test_sanitize_sensitive_headers(self):
        """Should remove sensitive headers."""
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url = Mock()
        mock_request.url.__str__ = lambda self: "https://example.com/api/login"
        mock_request.url.path = "/api/login"
        mock_request.query_params = {}
        mock_request.headers = {
            "authorization": "Bearer secret-token",
            "cookie": "session=abc123",
            "x-api-key": "api-key-value",
            "api-key": "another-key",
            "content-type": "application/json",
        }
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        context = _build_request_context(mock_request)

        # Sensitive headers should not be included
        assert "authorization" not in context["request"]["headers"]
        assert "cookie" not in context["request"]["headers"]
        assert "x-api-key" not in context["request"]["headers"]
        assert "api-key" not in context["request"]["headers"]
        # Non-sensitive headers should be included
        assert context["request"]["headers"]["content-type"] == "application/json"

    def test_no_client(self):
        """Should handle missing client."""
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url = Mock()
        mock_request.url.__str__ = lambda self: "https://example.com/test"
        mock_request.url.path = "/test"
        mock_request.query_params = {}
        mock_request.headers = {}
        mock_request.client = None

        context = _build_request_context(mock_request)

        assert context["request"]["client_ip"] is None


# =============================================================================
# SageMiddleware Tests
# =============================================================================

class TestSageMiddleware:
    """Tests for SageMiddleware class."""

    def test_init(self):
        """Should initialize with correct options."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        app = Mock()

        middleware = SageMiddleware(
            app,
            sage,
            capture_exceptions=True,
            create_tickets=True,
            ticket_subject_prefix="[Bug] ",
            get_customer_email=lambda req: "test@example.com",
        )

        assert middleware.app is app
        assert middleware.sage is sage
        assert middleware.capture_exceptions is True
        assert middleware.create_tickets is True
        assert middleware.ticket_subject_prefix == "[Bug] "

    @pytest.mark.asyncio
    async def test_passthrough_non_http(self):
        """Should pass through non-http requests."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        app = AsyncMock()

        middleware = SageMiddleware(app, sage)

        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_passthrough_successful_request(self):
        """Should pass through successful HTTP requests."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        app = AsyncMock()

        middleware = SageMiddleware(app, sage)

        scope = {"type": "http", "method": "GET", "path": "/test"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_reraises_exception(self):
        """Should reraise exception after handling."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")

        async def raise_error(*args):
            raise ValueError("Test error")

        app = AsyncMock(side_effect=raise_error)

        middleware = SageMiddleware(app, sage, capture_exceptions=True)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "server": ("localhost", 8000),
        }
        receive = AsyncMock()
        send = AsyncMock()

        with pytest.raises(ValueError) as exc_info:
            await middleware(scope, receive, send)

        assert str(exc_info.value) == "Test error"

    @pytest.mark.asyncio
    async def test_no_capture_when_disabled(self):
        """Should not capture exceptions when disabled."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")

        async def raise_error(*args):
            raise ValueError("Test error")

        app = AsyncMock(side_effect=raise_error)

        middleware = SageMiddleware(app, sage, capture_exceptions=False)

        scope = {"type": "http"}
        receive = AsyncMock()
        send = AsyncMock()

        with pytest.raises(ValueError):
            await middleware(scope, receive, send)

    @pytest.mark.asyncio
    @patch.object(Sage, 'create_ticket_async')
    async def test_create_ticket_on_error(self, mock_create_ticket):
        """Should create ticket when enabled and email available."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        mock_create_ticket.return_value = Mock()

        async def raise_error(*args):
            raise ValueError("Test error")

        app = AsyncMock(side_effect=raise_error)

        middleware = SageMiddleware(
            app,
            sage,
            create_tickets=True,
            get_customer_email=lambda req: "test@example.com",
        )

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/users",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "server": ("localhost", 8000),
        }
        receive = AsyncMock()
        send = AsyncMock()

        with pytest.raises(ValueError):
            await middleware(scope, receive, send)

        mock_create_ticket.assert_called_once()
        call_kwargs = mock_create_ticket.call_args[1]
        assert call_kwargs["customer_email"] == "test@example.com"
        assert call_kwargs["priority"] == "high"
        assert "ValueError" in call_kwargs["subject"]

    @pytest.mark.asyncio
    @patch.object(Sage, 'create_ticket_async')
    async def test_no_ticket_without_email(self, mock_create_ticket):
        """Should not create ticket when no email available."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")

        async def raise_error(*args):
            raise ValueError("Test error")

        app = AsyncMock(side_effect=raise_error)

        middleware = SageMiddleware(
            app,
            sage,
            create_tickets=True,
            get_customer_email=lambda req: None,
        )

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "server": ("localhost", 8000),
        }
        receive = AsyncMock()
        send = AsyncMock()

        with pytest.raises(ValueError):
            await middleware(scope, receive, send)

        mock_create_ticket.assert_not_called()

    @pytest.mark.asyncio
    @patch.object(Sage, 'create_ticket_async')
    async def test_email_extraction_failure(self, mock_create_ticket):
        """Should handle email extraction failure gracefully."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")

        async def raise_error(*args):
            raise ValueError("Test error")

        app = AsyncMock(side_effect=raise_error)

        def bad_email_getter(req):
            raise Exception("Email extraction failed")

        middleware = SageMiddleware(
            app,
            sage,
            create_tickets=True,
            get_customer_email=bad_email_getter,
        )

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "server": ("localhost", 8000),
        }
        receive = AsyncMock()
        send = AsyncMock()

        with pytest.raises(ValueError):
            await middleware(scope, receive, send)

        mock_create_ticket.assert_not_called()

    @pytest.mark.asyncio
    @patch.object(Sage, 'create_ticket_async')
    async def test_ticket_creation_failure_ignored(self, mock_create_ticket):
        """Should ignore ticket creation failures."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        mock_create_ticket.side_effect = Exception("Ticket creation failed")

        async def raise_error(*args):
            raise ValueError("Test error")

        app = AsyncMock(side_effect=raise_error)

        middleware = SageMiddleware(
            app,
            sage,
            create_tickets=True,
            get_customer_email=lambda req: "test@example.com",
        )

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "server": ("localhost", 8000),
        }
        receive = AsyncMock()
        send = AsyncMock()

        # Should raise the original error, not the ticket creation error
        with pytest.raises(ValueError) as exc_info:
            await middleware(scope, receive, send)

        assert str(exc_info.value) == "Test error"

    @pytest.mark.asyncio
    @patch.object(Sage, 'create_ticket_async')
    async def test_custom_subject_prefix(self, mock_create_ticket):
        """Should use custom subject prefix."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        mock_create_ticket.return_value = Mock()

        async def raise_error(*args):
            raise TypeError("Type mismatch")

        app = AsyncMock(side_effect=raise_error)

        middleware = SageMiddleware(
            app,
            sage,
            create_tickets=True,
            ticket_subject_prefix="[Critical Bug] ",
            get_customer_email=lambda req: "test@example.com",
        )

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "server": ("localhost", 8000),
        }
        receive = AsyncMock()
        send = AsyncMock()

        with pytest.raises(TypeError):
            await middleware(scope, receive, send)

        call_kwargs = mock_create_ticket.call_args[1]
        assert call_kwargs["subject"].startswith("[Critical Bug] ")


# =============================================================================
# Instrument FastAPI Tests
# =============================================================================

class TestInstrumentFastAPI:
    """Tests for instrument_fastapi function."""

    def test_adds_middleware(self):
        """Should add SageMiddleware to app."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        app = Mock()

        instrument_fastapi(app, sage)

        app.add_middleware.assert_called_once()
        call_args = app.add_middleware.call_args
        assert call_args[0][0] == SageMiddleware
        assert call_args[1]["sage"] is sage

    def test_with_create_tickets(self):
        """Should pass create_tickets option."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        app = Mock()

        instrument_fastapi(app, sage, create_tickets=True)

        call_kwargs = app.add_middleware.call_args[1]
        assert call_kwargs["create_tickets"] is True

    def test_with_get_customer_email(self):
        """Should pass get_customer_email function."""
        sage = Sage(api_key="sk_sage_valid_key_12345678901234567890")
        app = Mock()

        def email_getter(req):
            return req.state.user.email

        instrument_fastapi(app, sage, get_customer_email=email_getter)

        call_kwargs = app.add_middleware.call_args[1]
        assert call_kwargs["get_customer_email"] is email_getter
