# MailBreeze Python SDK

The official Python SDK for the MailBreeze email platform.

## Features

- **Full async support** - Built on `httpx` for modern async/await patterns
- **Type-safe** - Complete type hints with Pydantic models
- **Automatic retries** - Built-in retry logic with exponential backoff
- **Python 3.10+** - Modern Python with native type syntax

## Installation

```bash
pip install mailbreeze
```

## Quick Start

```python
import asyncio
from mailbreeze import MailBreeze

async def main():
    client = MailBreeze(api_key="sk_live_xxx")

    # Send an email
    result = await client.emails.send(
        from_="hello@yourdomain.com",
        to="user@example.com",
        subject="Welcome!",
        html="<h1>Welcome to our platform!</h1>",
    )
    print(result.id)

asyncio.run(main())
```

## Resources

### Emails

```python
# Send an email
result = await client.emails.send(
    from_="hello@yourdomain.com",
    to="user@example.com",
    subject="Hello",
    html="<p>Hello World!</p>",
)

# Send with a template
result = await client.emails.send(
    from_="hello@yourdomain.com",
    to=["user1@example.com", "user2@example.com"],
    template_id="welcome-template",
    variables={"name": "John", "plan": "Pro"},
)

# List emails
emails = await client.emails.list(status="delivered", page=1, limit=20)

# Get email details
email = await client.emails.get("email_xxx")

# Get statistics
stats = await client.emails.stats()
```

### Contact Lists

```python
# Create a list
list_ = await client.lists.create(
    name="Newsletter Subscribers",
    description="Weekly newsletter recipients",
)

# List all lists
lists = await client.lists.list()

# Get list stats
stats = await client.lists.stats("list_xxx")
```

### Contacts

```python
# Get contacts for a list
contacts = client.contacts("list_xxx")

# Create a contact
contact = await contacts.create(
    email="user@example.com",
    first_name="John",
    last_name="Doe",
    custom_fields={"company": "Acme Inc"},
)

# List contacts
result = await contacts.list(status="active", page=1, limit=50)

# Update a contact
updated = await contacts.update("contact_xxx", first_name="Jane")

# Delete a contact
await contacts.delete("contact_xxx")
```

### Email Verification

```python
# Verify a single email
result = await client.verification.verify("user@example.com")
print(result.is_valid)  # True

# Batch verification
batch = await client.verification.batch(
    emails=["user1@example.com", "user2@example.com"]
)

# Check batch status
status = await client.verification.get(batch.verification_id)
```

### Automations

```python
# Enroll a contact
enrollment = await client.automations.enroll(
    automation_id="auto_welcome",
    contact_id="contact_xxx",
    variables={"coupon_code": "WELCOME10"},
)

# List enrollments
enrollments = await client.automations.enrollments.list(status="active")

# Cancel an enrollment
await client.automations.enrollments.cancel("enroll_xxx")
```

## Error Handling

```python
from mailbreeze import (
    MailBreeze,
    MailBreezeError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

try:
    await client.emails.send(...)
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Details: {e.details}")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except NotFoundError:
    print("Resource not found")
except ServerError as e:
    print(f"Server error: {e.status_code}")
except MailBreezeError as e:
    print(f"API error: {e.code} - {e.message}")
```

## Requirements

- Python 3.10 or higher
- A MailBreeze API key ([get one here](https://console.mailbreeze.com))

## License

MIT
