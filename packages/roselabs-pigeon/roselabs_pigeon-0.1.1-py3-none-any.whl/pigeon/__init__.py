"""
Pigeon Email SDK for Python.

Simple, reliable transactional email sending for your Python applications.

Example:
    >>> from pigeon import Pigeon
    >>>
    >>> pigeon = Pigeon(api_key="pk_xxx")
    >>>
    >>> # Send using a template
    >>> result = await pigeon.send(
    ...     to="user@example.com",
    ...     template_name="welcome-email",
    ...     variables={"name": "John", "company_name": "Acme Inc"},
    ... )
    >>>
    >>> # Send raw email
    >>> result = await pigeon.send(
    ...     to="user@example.com",
    ...     subject="Hello!",
    ...     html="<h1>Welcome</h1>",
    ... )

For synchronous usage:
    >>> from pigeon import PigeonSync
    >>>
    >>> with PigeonSync(api_key="pk_xxx") as pigeon:
    ...     result = pigeon.send(
    ...         to="user@example.com",
    ...         template_name="welcome-email",
    ...         variables={"name": "John"},
    ...     )
"""

from __future__ import annotations

from .client import Pigeon
from .sync_client import PigeonSync
from .types import Email, EmailList, SendResult, Template, TemplateList
from .exceptions import (
    PigeonError,
    PigeonAPIError,
    PigeonConfigError,
    PigeonValidationError,
)

__version__ = "0.1.0"
__all__ = [
    # Clients
    "Pigeon",
    "PigeonSync",
    # Types
    "SendResult",
    "Template",
    "TemplateList",
    "Email",
    "EmailList",
    # Exceptions
    "PigeonError",
    "PigeonAPIError",
    "PigeonConfigError",
    "PigeonValidationError",
]
