# FullEnrich Client

Python client for the [FullEnrich API](https://fullenrich.com) - Enrich LinkedIn profiles with contact information (emails and phone numbers).

## Installation

```bash
pip install fullenrichclient
```

## Quick Start

```python
from fullenrich import FullEnrich

# Initialize with API key (or set FULLENRICH_API_KEY env var)
client = FullEnrich(api_key="your-api-key")

# Enrich a single LinkedIn profile
response = client.enrich("https://www.linkedin.com/in/username/")
print(f"Enrichment ID: {response.enrichment_id}")

# Wait for results
result = client.wait_for_enrichment(response.enrichment_id)
print(result.results)
```

## Usage

### Environment Variables

Set your API key via environment variable (supports `.env` files):

```bash
export FULLENRICH_API_KEY=your-api-key
```

Then use without passing the key:

```python
client = FullEnrich()
```

### Check Credit Balance

```python
credits = client.get_credits()
print(f"Balance: {credits.balance}")
```

### Enrich Single Profile

```python
response = client.enrich("https://www.linkedin.com/in/username/")
```

### Enrich Multiple Profiles

```python
urls = [
    "https://www.linkedin.com/in/user1/",
    "https://www.linkedin.com/in/user2/",
    "https://www.linkedin.com/in/user3/",
]

response = client.enrich(urls)
```

### With Webhook

```python
response = client.enrich(
    linkedin_urls="https://www.linkedin.com/in/username/",
    webhook_url="https://your-webhook.com/callback"
)
```

### Select Specific Fields

```python
from fullenrich import FullEnrich, EnrichField

client = FullEnrich()

# Using enum
response = client.enrich(
    "https://www.linkedin.com/in/username/",
    enrich_fields=[EnrichField.EMAILS]
)

# Using strings
response = client.enrich(
    "https://www.linkedin.com/in/username/",
    enrich_fields=["contact.emails", "contact.personal_emails"]
)
```

Available fields:
- `EnrichField.EMAILS` / `"contact.emails"` - Work emails
- `EnrichField.PERSONAL_EMAILS` / `"contact.personal_emails"` - Personal emails
- `EnrichField.PHONES` / `"contact.phones"` - Phone numbers

### Enrich by Name/Domain (Without LinkedIn URL)

```python
from fullenrich import FullEnrich, EnrichmentRequest, EnrichField

client = FullEnrich()

requests = [
    EnrichmentRequest(
        firstname="John",
        lastname="Doe",
        domain="example.com",
        enrich_fields=[EnrichField.EMAILS, EnrichField.PHONES],
    ),
    EnrichmentRequest(
        firstname="Jane",
        lastname="Smith",
        company_name="Acme Inc",
    ),
]

response = client.enrich_batch(requests)
```

### With Custom Data (for CRM integration)

```python
response = client.enrich(
    "https://www.linkedin.com/in/username/",
    custom={"crm_contact_id": "123", "user_id": "456"}
)

# Or with enrich_batch for per-person custom data
requests = [
    EnrichmentRequest(
        linkedin_url="https://www.linkedin.com/in/user1/",
        custom={"crm_id": "001"}
    ),
    EnrichmentRequest(
        linkedin_url="https://www.linkedin.com/in/user2/",
        custom={"crm_id": "002"}
    ),
]
response = client.enrich_batch(requests)
```

### Enrich and Wait (Convenience Method)

```python
# Start enrichment and wait for results in one call
result = client.enrich_and_wait(
    "https://www.linkedin.com/in/username/",
    max_attempts=30,
    poll_interval=10
)
print(result.results)
```

### Check Enrichment Status

```python
result = client.get_enrichment("enrichment-id")
print(f"Status: {result.status}")
```

### Reverse Email Lookup

Find LinkedIn profiles from email addresses:

```python
# Single email
response = client.reverse_lookup("john@example.com")

# Multiple emails
response = client.reverse_lookup([
    "john@example.com",
    "jane@example.com"
])

# With webhook
response = client.reverse_lookup(
    "john@example.com",
    webhook_url="https://your-webhook.com/callback"
)

# Wait for results
result = client.wait_for_reverse_lookup(response.reverse_id)
print(result.datas)

# Or use the convenience method
result = client.reverse_lookup_and_wait("john@example.com")
```

### Context Manager

```python
with FullEnrich() as client:
    result = client.enrich_and_wait("https://www.linkedin.com/in/username/")
    print(result.results)
```

## API Reference

### FullEnrich

Main client class.

**Constructor:**
- `api_key` (str, optional): API key. Defaults to `FULLENRICH_API_KEY` env var.
- `base_url` (str, optional): Custom API base URL.
- `timeout` (float, optional): Request timeout in seconds. Default: 30.0

**Account Methods:**
- `get_credits()` - Get current credit balance

**Enrichment Methods:**
- `enrich(linkedin_urls, enrich_fields, name, webhook_url, custom)` - Start enrichment by LinkedIn URL
- `enrich_batch(requests, name, webhook_url)` - Start enrichment with full control (name/domain lookup, custom data)
- `get_enrichment(enrichment_id)` - Get enrichment status/results
- `wait_for_enrichment(enrichment_id, max_attempts, poll_interval)` - Poll until complete
- `enrich_and_wait(...)` - Convenience method combining enrich + wait

**Reverse Lookup Methods:**
- `reverse_lookup(emails, name, webhook_url)` - Find LinkedIn profiles from emails
- `get_reverse_lookup(reverse_id)` - Get reverse lookup status/results
- `wait_for_reverse_lookup(reverse_id, max_attempts, poll_interval)` - Poll until complete
- `reverse_lookup_and_wait(...)` - Convenience method combining reverse_lookup + wait

### EnrichmentRequest

For advanced enrichment requests:
- `linkedin_url` - LinkedIn profile URL
- `firstname` - First name (for name/domain lookup)
- `lastname` - Last name (for name/domain lookup)
- `domain` - Company domain (for name/domain lookup)
- `company_name` - Company name (for name/domain lookup)
- `enrich_fields` - List of fields to enrich
- `custom` - Custom data dict (max 20 string entries)

### EnrichField

Enum of available fields:
- `EnrichField.EMAILS` - Work emails
- `EnrichField.PERSONAL_EMAILS` - Personal emails
- `EnrichField.PHONES` - Phone numbers

### EnrichmentStatus

- `PENDING`, `PROCESSING`, `FINISHED`, `FAILED`

### ReverseStatus

- `CREATED`, `IN_PROGRESS`, `CANCELED`, `CREDITS_INSUFFICIENT`, `FINISHED`, `RATE_LIMIT`, `UNKNOWN`

## License

MIT
