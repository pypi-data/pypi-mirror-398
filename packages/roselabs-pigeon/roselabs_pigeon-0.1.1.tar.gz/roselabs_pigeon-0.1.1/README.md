# Pigeon Python SDK

Official Python SDK for [Pigeon](https://pigeon.roselabs.io) - Transactional email made simple.

## Installation

```bash
pip install roselabs-pigeon
```

## Quick Start

### Async Usage (Recommended)

```python
from pigeon import Pigeon

pigeon = Pigeon(api_key="pk_xxx")

# Send using a template
result = await pigeon.send(
    to="user@example.com",
    template_name="welcome-email",
    variables={
        "name": "John",
        "company_name": "Acme Inc",
    },
)

print(f"Email sent! ID: {result.id}")
```

### Sync Usage

```python
from pigeon import PigeonSync

with PigeonSync(api_key="pk_xxx") as pigeon:
    result = pigeon.send(
        to="user@example.com",
        template_name="welcome-email",
        variables={
            "name": "John",
            "company_name": "Acme Inc",
        },
    )

print(f"Email sent! ID: {result.id}")
```

## Sending Emails

### Using Templates

```python
# Single recipient
result = await pigeon.send(
    to="user@example.com",
    template_name="order-confirmation",
    variables={
        "order_id": "12345",
        "total": "$99.00",
    },
)

# Multiple recipients
result = await pigeon.send(
    to=["user1@example.com", "user2@example.com"],
    template_name="announcement",
    variables={"message": "Big news!"},
)
```

### Raw Emails

```python
result = await pigeon.send(
    to="user@example.com",
    subject="Hello from Pigeon!",
    html="<h1>Welcome!</h1><p>Thanks for signing up.</p>",
    text="Welcome! Thanks for signing up.",
)
```

### With Options

```python
result = await pigeon.send(
    to="user@example.com",
    template_name="welcome-email",
    variables={"name": "John"},
    from_name="Support Team",
    reply_to="support@yourcompany.com",
)
```

## Managing Templates

```python
# List all templates
templates = await pigeon.list_templates()
for template in templates:
    print(f"{template.name}: {template.subject}")

# Get a specific template
template = await pigeon.get_template_by_name("welcome-email")
print(template.html_content)
```

## Viewing Sent Emails

```python
# List recent emails
emails = await pigeon.list_emails(page=1, page_size=50)
for email in emails.emails:
    print(f"{email.id}: {email.subject} -> {email.to}")

# Get specific email
email = await pigeon.get_email("email-uuid")
print(email.status)
```

## Error Handling

```python
from pigeon import Pigeon, PigeonAPIError, PigeonValidationError

pigeon = Pigeon(api_key="pk_xxx")

try:
    result = await pigeon.send(
        to="user@example.com",
        template_name="nonexistent-template",
        variables={},
    )
except PigeonAPIError as e:
    print(f"API error: {e.status_code} - {e.message}")
except PigeonValidationError as e:
    print(f"Validation error: {e}")
```

## Configuration

```python
pigeon = Pigeon(
    api_key="pk_xxx",
    base_url="https://api.pigeon.roselabs.io",  # Default
    timeout=30.0,  # Request timeout in seconds
)
```

## API Reference

### `Pigeon` (Async Client)

- `send()` - Send an email
- `list_templates()` - List all templates
- `get_template(id)` - Get template by ID
- `get_template_by_name(name)` - Get template by name
- `list_emails()` - List sent emails
- `get_email(id)` - Get email by ID

### `PigeonSync` (Sync Client)

Same methods as `Pigeon`, but synchronous. Use as a context manager:

```python
with PigeonSync(api_key="pk_xxx") as pigeon:
    result = pigeon.send(...)
```

## License

MIT
