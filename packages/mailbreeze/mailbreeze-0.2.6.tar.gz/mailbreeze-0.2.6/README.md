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
    async with MailBreeze(api_key="sk_live_xxx") as client:
        # Send an email
        result = await client.emails.send(
            from_="hello@yourdomain.com",
            to="user@example.com",
            subject="Welcome!",
            html="<h1>Welcome to our platform!</h1>",
        )
        print(result.message_id)  # msg_xxx

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
print(result.message_id)  # msg_xxx

# Send with a template
result = await client.emails.send(
    from_="hello@yourdomain.com",
    to=["user1@example.com", "user2@example.com"],
    template_id="welcome-template",
    variables={"name": "John", "plan": "Pro"},
)

# Send with attachments
result = await client.emails.send(
    from_="hello@yourdomain.com",
    to="user@example.com",
    subject="Document attached",
    html="<p>Please find the attachment.</p>",
    attachment_ids=["att_xxx"],
)

# List emails
emails = await client.emails.list(status="delivered", page=1, limit=20)
for email in emails.data:
    print(email.id, email.status)

# Get email details
email = await client.emails.get("email_xxx")
print(email.status, email.delivered_at)

# Get statistics
stats = await client.emails.stats()
print(stats.success_rate)  # 98.5
print(stats.total)  # 1500
```

### Contact Lists

```python
# Create a list
list_ = await client.lists.create(
    name="Newsletter Subscribers",
    description="Weekly newsletter recipients",
)
print(list_.id)

# List all lists
lists = await client.lists.list()
for lst in lists.data:
    print(lst.name)

# Get a list
list_ = await client.lists.get("list_xxx")

# Update a list
list_ = await client.lists.update("list_xxx", name="Updated Name")

# Get list stats
stats = await client.lists.stats("list_xxx")
print(stats.total_contacts)
print(stats.active_contacts)

# Delete a list
await client.lists.delete("list_xxx")
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
print(contact.id)

# List contacts
result = await contacts.list(status="active", page=1, limit=50)
for contact in result.data:
    print(contact.email)

# Get a contact
contact = await contacts.get("contact_xxx")

# Update a contact
updated = await contacts.update("contact_xxx", first_name="Jane")

# Suppress a contact (opt-out)
await contacts.suppress("contact_xxx", reason="unsubscribed")

# Delete a contact
await contacts.delete("contact_xxx")
```

### Email Verification

```python
# Verify a single email
result = await client.verification.verify({"email": "user@example.com"})
print(result.is_valid)  # True
print(result.is_deliverable)  # True

# Batch verification (async processing)
batch = await client.verification.batch(["user1@example.com", "user2@example.com"])
print(batch.verification_id)  # ver_xxx
print(batch.status)  # "processing"

# Check batch status
status = await client.verification.get(batch.verification_id)
print(status.status)  # "completed"
print(status.results)

# List all verifications
verifications = await client.verification.list()

# Get verification statistics
stats = await client.verification.stats()
print(stats.total_valid)
print(stats.valid_percentage)
```

### Attachments

```python
# Create a pre-signed upload URL
upload = await client.attachments.create_upload(
    filename="document.pdf",
    content_type="application/pdf",
    size=1024000,  # bytes
)
print(upload.attachment_id)  # att_xxx
print(upload.upload_url)  # Pre-signed URL

# Upload the file to the pre-signed URL (use your preferred HTTP client)
# httpx.put(upload.upload_url, content=file_bytes)

# Confirm the upload
attachment = await client.attachments.confirm(upload.attachment_id)
print(attachment.status)  # "ready"
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
    result = await client.emails.send(
        from_="hello@yourdomain.com",
        to="user@example.com",
        subject="Hello",
        html="<p>Hello</p>",
    )
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

## Configuration

```python
from mailbreeze import MailBreeze

client = MailBreeze(
    api_key="sk_live_xxx",
    base_url="https://api.mailbreeze.com/api/v1",  # Optional
    timeout=30.0,  # Request timeout in seconds
    max_retries=3,  # Retry attempts for retryable errors
)
```

## Requirements

- Python 3.10 or higher
- A MailBreeze API key ([get one here](https://console.mailbreeze.com))

## License

MIT
