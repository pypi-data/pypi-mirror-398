"""Flask integration for Sage SDK.

Provides utilities to integrate Sage with Flask applications.

Example:
    from flask import Flask
    from sage_sdk import Sage
    from sage_sdk.flask import init_app

    app = Flask(__name__)
    sage = Sage(api_key="sk_sage_...")
    init_app(app, sage)
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from flask import Flask, Request

from sage_sdk.client import Sage


def _build_request_context(request: "Request") -> dict[str, Any]:
    """Extract context from a Flask request."""
    # Sanitize headers
    sensitive_headers = {"authorization", "cookie", "x-api-key", "api-key"}
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in sensitive_headers
    }

    return {
        "request": {
            "method": request.method,
            "url": request.url,
            "path": request.path,
            "query": dict(request.args),
            "headers": dict(headers),
            "client_ip": request.remote_addr,
        }
    }


def init_app(
    app: "Flask",
    sage: Sage | None = None,
    *,
    create_tickets: bool = False,
    get_customer_email: Callable[[], str | None] | None = None,
) -> Sage:
    """
    Initialize Sage with a Flask application.

    Args:
        app: Flask application instance
        sage: Sage client instance (or None to create from app.config)
        create_tickets: Whether to auto-create tickets for exceptions
        get_customer_email: Function to get customer email (uses Flask's request context)

    Returns:
        The Sage client instance

    Example:
        from flask import Flask, g
        from sage_sdk import Sage
        from sage_sdk.flask import init_app

        app = Flask(__name__)
        sage = Sage(api_key="sk_sage_...")

        def get_email():
            return getattr(g, 'user_email', None)

        init_app(app, sage, create_tickets=True, get_customer_email=get_email)
    """
    if sage is None:
        # Create from app config
        api_key = app.config.get("SAGE_API_KEY")
        if not api_key:
            raise ValueError(
                "No Sage client provided and SAGE_API_KEY not found in app.config"
            )
        sage = Sage(
            api_key=api_key,
            api_url=app.config.get("SAGE_API_URL"),
            debug=app.config.get("SAGE_DEBUG", app.debug),
        )

    # Store on app for later access
    app.extensions = getattr(app, "extensions", {})
    app.extensions["sage"] = sage

    if create_tickets:
        @app.errorhandler(Exception)
        def handle_exception(error: Exception) -> Any:
            """Handle exceptions by creating tickets."""
            from flask import request

            context = _build_request_context(request)
            context["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            }

            customer_email = None
            if get_customer_email:
                try:
                    customer_email = get_customer_email()
                except Exception:
                    pass

            if customer_email:
                subject = f"[Error] {type(error).__name__}: {str(error)[:50]}"
                message = f"""An error occurred in your application:

**Error:** {type(error).__name__}
**Message:** {str(error)}

**Request:**
- Method: {request.method}
- URL: {request.url}

**Traceback:**
```
{traceback.format_exc()}
```
"""
                try:
                    sage.create_ticket(
                        customer_email=customer_email,
                        subject=subject,
                        message=message,
                        priority="high",
                        metadata=context,
                    )
                except Exception:
                    # Don't let ticket creation failures break the app
                    pass

            # Re-raise to let Flask handle the response
            raise error

    return sage


class SageFlask:
    """
    Flask extension for Sage SDK.

    Example:
        from flask import Flask
        from sage_sdk.flask import SageFlask

        sage_ext = SageFlask()

        def create_app():
            app = Flask(__name__)
            app.config["SAGE_API_KEY"] = "sk_sage_..."
            sage_ext.init_app(app)
            return app

        # Later, in views:
        from sage_sdk.flask import sage_ext
        sage_ext.sage.create_ticket(...)
    """

    def __init__(self, app: "Flask" | None = None):
        self._sage: Sage | None = None
        if app is not None:
            self.init_app(app)

    def init_app(
        self,
        app: "Flask",
        sage: Sage | None = None,
        **kwargs: Any,
    ) -> Sage:
        """Initialize with a Flask app."""
        self._sage = init_app(app, sage, **kwargs)
        return self._sage

    @property
    def sage(self) -> Sage:
        """Get the Sage client instance."""
        if self._sage is None:
            raise RuntimeError("SageFlask not initialized. Call init_app() first.")
        return self._sage

    def get_sage(self, app: "Flask") -> Sage | None:
        """Get Sage instance from a specific app."""
        return app.extensions.get("sage")
