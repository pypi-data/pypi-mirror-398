"""MailBreeze Python SDK.

Official Python SDK for the MailBreeze email platform.

Example:
    >>> from mailbreeze import MailBreeze
    >>> client = MailBreeze(api_key="sk_live_xxx")
    >>> result = await client.emails.send(
    ...     from_="hello@yourdomain.com",
    ...     to="user@example.com",
    ...     subject="Welcome!",
    ...     html="<h1>Welcome!</h1>",
    ... )
"""

from mailbreeze.client import MailBreeze
from mailbreeze.errors import (
    AuthenticationError,
    MailBreezeError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

__version__ = "0.1.0"

__all__ = [
    "MailBreeze",
    "MailBreezeError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "__version__",
]
