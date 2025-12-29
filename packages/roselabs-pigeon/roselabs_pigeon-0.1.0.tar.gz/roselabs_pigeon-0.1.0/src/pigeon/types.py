"""Type definitions for the Pigeon SDK."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class SendResult:
    """Result of sending an email."""

    id: str
    status: str
    to: list[str]
    subject: str
    sent_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SendResult":
        """Create SendResult from API response dict."""
        sent_at = None
        if data.get("sent_at"):
            sent_at = datetime.fromisoformat(data["sent_at"].replace("Z", "+00:00"))
        return cls(
            id=data["id"],
            status=data["status"],
            to=data["to"],
            subject=data["subject"],
            sent_at=sent_at,
        )


@dataclass
class Template:
    """Email template."""

    id: str
    name: str
    subject: str
    created_at: datetime
    updated_at: datetime
    html_content: str | None = None
    text_content: str | None = None
    variables: list[dict[str, Any]] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Template":
        """Create Template from API response dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            subject=data["subject"],
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            html_content=data.get("html_content"),
            text_content=data.get("text_content"),
            variables=data.get("variables"),
        )


@dataclass
class Email:
    """Email record."""

    id: str
    to: list[str]
    subject: str
    status: str
    sent_at: datetime | None = None
    template_id: str | None = None
    template_name: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Email":
        """Create Email from API response dict."""
        sent_at = None
        if data.get("sent_at"):
            sent_at = datetime.fromisoformat(data["sent_at"].replace("Z", "+00:00"))
        return cls(
            id=data["id"],
            to=data["to"],
            subject=data["subject"],
            status=data["status"],
            sent_at=sent_at,
            template_id=data.get("template_id"),
            template_name=data.get("template_name"),
        )


@dataclass
class EmailList:
    """Paginated list of emails."""

    emails: list[Email]
    total: int
    page: int
    page_size: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmailList":
        """Create EmailList from API response dict."""
        return cls(
            emails=[Email.from_dict(e) for e in data.get("emails", [])],
            total=data.get("total", 0),
            page=data.get("page", 1),
            page_size=data.get("page_size", 50),
        )


@dataclass
class TemplateList:
    """List of templates."""

    templates: list[Template]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TemplateList":
        """Create TemplateList from API response dict."""
        return cls(
            templates=[Template.from_dict(t) for t in data.get("templates", [])],
        )
