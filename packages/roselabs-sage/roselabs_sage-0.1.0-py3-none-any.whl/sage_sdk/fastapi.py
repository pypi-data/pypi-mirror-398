"""FastAPI integration for Sage SDK.

Provides middleware and utilities to automatically capture exceptions
and create support tickets from your FastAPI application.

Example:
    from fastapi import FastAPI
    from sage_sdk import Sage
    from sage_sdk.fastapi import SageMiddleware

    sage = Sage(api_key="sk_sage_...")
    app = FastAPI()

    # Add middleware to capture unhandled exceptions
    app.add_middleware(SageMiddleware, sage=sage)
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
    from starlette.requests import Request
    from starlette.responses import Response

from sage_sdk.client import Sage


def _build_request_context(request: "Request") -> dict[str, Any]:
    """Extract context from a Starlette/FastAPI request."""
    # Sanitize headers - remove sensitive ones
    sensitive_headers = {"authorization", "cookie", "x-api-key", "api-key"}
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in sensitive_headers
    }

    return {
        "request": {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query": dict(request.query_params),
            "headers": headers,
            "client_ip": request.client.host if request.client else None,
        }
    }


class SageMiddleware:
    """
    ASGI middleware that captures unhandled exceptions and creates tickets.

    Usage:
        from sage_sdk import Sage
        from sage_sdk.fastapi import SageMiddleware

        sage = Sage(api_key="sk_sage_...")
        app = FastAPI()
        app.add_middleware(SageMiddleware, sage=sage)

    Options:
        sage: Sage client instance
        capture_exceptions: Whether to capture exceptions (default: True)
        create_tickets: Whether to auto-create tickets (default: False)
        ticket_subject_prefix: Prefix for auto-created ticket subjects
        get_customer_email: Callable to extract customer email from request
    """

    def __init__(
        self,
        app: Any,
        sage: Sage,
        *,
        capture_exceptions: bool = True,
        create_tickets: bool = False,
        ticket_subject_prefix: str = "[Error] ",
        get_customer_email: Callable[["Request"], str | None] | None = None,
    ):
        self.app = app
        self.sage = sage
        self.capture_exceptions = capture_exceptions
        self.create_tickets = create_tickets
        self.ticket_subject_prefix = ticket_subject_prefix
        self.get_customer_email = get_customer_email

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            if self.capture_exceptions:
                await self._handle_exception(scope, exc)
            raise

    async def _handle_exception(self, scope: dict, exc: Exception) -> None:
        """Handle an exception by optionally creating a ticket."""
        from starlette.requests import Request

        # Build a minimal request object from scope
        request = Request(scope)
        context = _build_request_context(request)
        context["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }

        if self.create_tickets:
            customer_email = None
            if self.get_customer_email:
                try:
                    customer_email = self.get_customer_email(request)
                except Exception:
                    pass

            if customer_email:
                subject = f"{self.ticket_subject_prefix}{type(exc).__name__}: {str(exc)[:50]}"
                message = f"""An error occurred in your application:

**Error:** {type(exc).__name__}
**Message:** {str(exc)}

**Request:**
- Method: {request.method}
- URL: {request.url}

**Traceback:**
```
{traceback.format_exc()}
```
"""
                try:
                    await self.sage.create_ticket_async(
                        customer_email=customer_email,
                        subject=subject,
                        message=message,
                        priority="high",
                        metadata=context,
                    )
                except Exception:
                    # Don't let ticket creation failures break the app
                    pass


def instrument_fastapi(
    app: Any,
    sage: Sage,
    *,
    create_tickets: bool = False,
    get_customer_email: Callable[["Request"], str | None] | None = None,
) -> None:
    """
    Convenience function to instrument a FastAPI app with Sage.

    Args:
        app: FastAPI application instance
        sage: Sage client instance
        create_tickets: Whether to auto-create tickets for exceptions
        get_customer_email: Function to extract customer email from request

    Example:
        from fastapi import FastAPI
        from sage_sdk import Sage
        from sage_sdk.fastapi import instrument_fastapi

        sage = Sage(api_key="sk_sage_...")
        app = FastAPI()

        def get_email(request):
            # Extract from JWT, session, etc.
            return request.state.user.email

        instrument_fastapi(app, sage, create_tickets=True, get_customer_email=get_email)
    """
    app.add_middleware(
        SageMiddleware,
        sage=sage,
        create_tickets=create_tickets,
        get_customer_email=get_customer_email,
    )
