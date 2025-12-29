"""Async Pigeon client for sending emails."""

from __future__ import annotations

from typing import Any

import httpx

from .exceptions import PigeonAPIError, PigeonConfigError, PigeonValidationError
from .types import Email, EmailList, SendResult, Template, TemplateList


class Pigeon:
    """
    Async Pigeon client for sending emails.

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
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.pigeon.roselabs.io",
        timeout: float = 30.0,
    ):
        """
        Initialize the Pigeon client.

        Args:
            api_key: Your Pigeon API key (starts with pk_)
            base_url: Pigeon API URL (defaults to https://api.pigeon.roselabs.io)
            timeout: Request timeout in seconds (defaults to 30.0)

        Raises:
            PigeonConfigError: If configuration is invalid
        """
        if not api_key:
            raise PigeonConfigError("api_key is required")
        if not isinstance(api_key, str):
            raise PigeonConfigError("api_key must be a string")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the Pigeon API."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method,
                f"{self.base_url}{path}",
                headers=self._headers(),
                json=json,
                params=params,
            )

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    message = error_data.get("detail", str(error_data))
                except Exception:
                    message = response.text or "Unknown error"
                raise PigeonAPIError(response.status_code, message)

            if response.status_code == 204:
                return {}
            return response.json()

    async def send(
        self,
        to: str | list[str],
        *,
        template_name: str | None = None,
        template_id: str | None = None,
        variables: dict[str, Any] | None = None,
        subject: str | None = None,
        html: str | None = None,
        text: str | None = None,
        from_name: str | None = None,
        reply_to: str | None = None,
        scheduled_for: str | None = None,
    ) -> SendResult:
        """
        Send an email.

        Use template_name/template_id + variables for template emails,
        or subject + html/text for raw emails.

        Args:
            to: Recipient email(s)
            template_name: Template name to use
            template_id: Template ID to use
            variables: Template variables
            subject: Email subject (for raw emails)
            html: HTML content (for raw emails)
            text: Plain text content (for raw emails)
            from_name: Sender name override
            reply_to: Reply-to email address
            scheduled_for: ISO 8601 datetime for scheduled sending

        Returns:
            SendResult with email ID and status

        Raises:
            PigeonValidationError: If required parameters are missing
            PigeonAPIError: If the API returns an error
        """
        # Validate inputs
        if not template_name and not template_id and not subject:
            raise PigeonValidationError(
                "Either template_name/template_id or subject is required"
            )

        if (subject and not html and not text) or (not subject and (html or text)):
            if not template_name and not template_id:
                raise PigeonValidationError(
                    "For raw emails, both subject and html/text are required"
                )

        # Build payload
        payload: dict[str, Any] = {
            "to": to if isinstance(to, list) else [to],
        }

        if template_name:
            payload["template_name"] = template_name
        if template_id:
            payload["template_id"] = template_id
        if variables:
            payload["variables"] = variables
        if subject:
            payload["subject"] = subject
        if html:
            payload["html"] = html
        if text:
            payload["text"] = text
        if from_name:
            payload["from_name"] = from_name
        if reply_to:
            payload["reply_to"] = reply_to
        if scheduled_for:
            payload["scheduled_for"] = scheduled_for

        data = await self._request("POST", "/v1/send", json=payload)
        return SendResult.from_dict(data)

    async def list_templates(self) -> list[Template]:
        """
        List all templates for this team.

        Returns:
            List of Template objects
        """
        data = await self._request("GET", "/v1/templates")
        return TemplateList.from_dict(data).templates

    async def get_template(self, template_id: str) -> Template:
        """
        Get a template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template object
        """
        data = await self._request("GET", f"/v1/templates/{template_id}")
        return Template.from_dict(data)

    async def get_template_by_name(self, name: str) -> Template:
        """
        Get a template by name.

        Args:
            name: Template name

        Returns:
            Template object
        """
        data = await self._request("GET", f"/v1/templates/name/{name}")
        return Template.from_dict(data)

    async def list_emails(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
    ) -> EmailList:
        """
        List sent emails.

        Args:
            page: Page number (default: 1)
            page_size: Number of emails per page (default: 50)
            status: Filter by status

        Returns:
            EmailList with paginated results
        """
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        if status:
            params["status"] = status

        data = await self._request("GET", "/v1/emails", params=params)
        return EmailList.from_dict(data)

    async def get_email(self, email_id: str) -> Email:
        """
        Get an email by ID.

        Args:
            email_id: Email ID

        Returns:
            Email object
        """
        data = await self._request("GET", f"/v1/emails/{email_id}")
        return Email.from_dict(data)
