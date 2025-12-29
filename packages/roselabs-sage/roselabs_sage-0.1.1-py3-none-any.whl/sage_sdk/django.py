"""Django integration for Sage SDK.

Provides middleware and utilities for Django applications.

Setup:
    # settings.py
    SAGE_API_KEY = "sk_sage_..."

    MIDDLEWARE = [
        ...
        'sage_sdk.django.SageMiddleware',
    ]

    # Optional settings
    SAGE_API_URL = "https://api.sage.roselabs.io"  # Custom API URL
    SAGE_CREATE_TICKETS = False  # Auto-create tickets for exceptions
    SAGE_DEBUG = False  # Enable debug logging
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

from sage_sdk.client import Sage

# Global Sage instance
_sage: Sage | None = None


def get_sage() -> Sage:
    """
    Get the global Sage instance.

    Must be called after Django has loaded settings.
    """
    global _sage

    if _sage is None:
        from django.conf import settings

        api_key = getattr(settings, "SAGE_API_KEY", None)
        if not api_key:
            raise ValueError("SAGE_API_KEY not found in Django settings")

        _sage = Sage(
            api_key=api_key,
            api_url=getattr(settings, "SAGE_API_URL", None),
            debug=getattr(settings, "SAGE_DEBUG", False),
        )

    return _sage


def _build_request_context(request: "HttpRequest") -> dict[str, Any]:
    """Extract context from a Django request."""
    # Sanitize headers
    sensitive_headers = {"authorization", "cookie", "x-api-key", "api-key"}
    headers = {}
    for key, value in request.META.items():
        if key.startswith("HTTP_"):
            header_name = key[5:].lower().replace("_", "-")
            if header_name not in sensitive_headers:
                headers[header_name] = value

    return {
        "request": {
            "method": request.method,
            "url": request.build_absolute_uri(),
            "path": request.path,
            "query": dict(request.GET),
            "headers": headers,
            "client_ip": _get_client_ip(request),
        }
    }


def _get_client_ip(request: "HttpRequest") -> str | None:
    """Get client IP from request, handling proxies."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class SageMiddleware:
    """
    Django middleware that captures unhandled exceptions.

    Add to MIDDLEWARE in settings.py:
        MIDDLEWARE = [
            ...
            'sage_sdk.django.SageMiddleware',
        ]

    Configuration in settings.py:
        SAGE_API_KEY = "sk_sage_..."
        SAGE_CREATE_TICKETS = True  # Optional: auto-create tickets
    """

    def __init__(self, get_response: Callable[["HttpRequest"], "HttpResponse"]):
        self.get_response = get_response
        self._sage: Sage | None = None

    @property
    def sage(self) -> Sage:
        if self._sage is None:
            self._sage = get_sage()
        return self._sage

    def __call__(self, request: "HttpRequest") -> "HttpResponse":
        return self.get_response(request)

    def process_exception(
        self,
        request: "HttpRequest",
        exception: Exception,
    ) -> None:
        """Process an unhandled exception."""
        from django.conf import settings

        context = _build_request_context(request)
        context["error"] = {
            "type": type(exception).__name__,
            "message": str(exception),
            "traceback": traceback.format_exc(),
        }

        # Check if we should create tickets
        create_tickets = getattr(settings, "SAGE_CREATE_TICKETS", False)
        if not create_tickets:
            return None

        # Try to get customer email
        customer_email = self._get_customer_email(request)
        if not customer_email:
            return None

        subject = f"[Error] {type(exception).__name__}: {str(exception)[:50]}"
        message = f"""An error occurred in your application:

**Error:** {type(exception).__name__}
**Message:** {str(exception)}

**Request:**
- Method: {request.method}
- URL: {request.build_absolute_uri()}

**Traceback:**
```
{traceback.format_exc()}
```
"""

        try:
            self.sage.create_ticket(
                customer_email=customer_email,
                subject=subject,
                message=message,
                priority="high",
                metadata=context,
            )
        except Exception:
            # Don't let ticket creation failures break the app
            pass

        return None

    def _get_customer_email(self, request: "HttpRequest") -> str | None:
        """Try to get customer email from request."""
        # Check for authenticated user
        if hasattr(request, "user") and request.user.is_authenticated:
            return getattr(request.user, "email", None)

        # Could be extended to check session, etc.
        return None
