from _typeshed import Incomplete
from starlette.types import ASGIApp as ASGIApp, Receive as Receive, Scope as Scope, Send as Send

class ApiKeyToAuthorizationMiddleware:
    """Middleware that transforms X-Api-Key into Authorization header.

    This enables BOSA's legacy authentication format (X-Api-Key: api-key:jwt-token)
    to work with FastMCP's OAuth-based authentication which requires Authorization header.
    """
    app: Incomplete
    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application to wrap.
        """
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process the request and inject Authorization header if needed.

        Args:
            scope: ASGI scope containing request information.
            receive: ASGI receive callable.
            send: ASGI send callable.
        """
