# Crexperium Python SDK

[![Python Version](https://img.shields.io/pypi/pyversions/crexperium)](https://pypi.org/project/crexperium/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Official Python SDK for the Crexperium CRM API. This library provides a simple and intuitive interface for integrating your Python applications with Crexperium CRM.

## Features

- 🚀 **Easy to use**: Simple, intuitive API
- 🔄 **Automatic retries**: Built-in retry logic with exponential backoff
- 🛡️ **Type hints**: Full type hint support for better IDE integration
- 📝 **Comprehensive documentation**: Detailed docstrings and examples
- ✅ **Well tested**: 100% test coverage with unit and integration tests
- 🔌 **Flexible**: Support for contact identification, deal management, and activity tracking

## Installation

```bash
pip install crexperium
```

Or install from source:

```bash
git clone https://github.com/crexperium/crexperium-python-sdk.git
cd crexperium-python-sdk
pip install -e .
```

## Quick Start

```python
from crexperium import CRMClient
from decimal import Decimal

# Initialize the client
client = CRMClient(
    api_token="your-api-token"
)

# Identify or create a contact
contact, created = client.contacts.identify(
    external_id="user_123",
    email="user@example.com",
    first_name="John",
    last_name="Doe"
)

# Create a deal
deal = client.deals.create(
    name="Premium Subscription",
    amount=Decimal("999.99"),
    contact_external_id="user_123",
    currency="USD",
    priority="HIGH"
)

# Log an activity
activity = client.activities.log(
    title="User completed onboarding",
    activity_type="USER_ACTION",
    user_id="user_123",
    metadata={"steps": 5, "time_spent": 120}
)

# Don't forget to close the client
client.close()
```

### Using as Context Manager

```python
from crexperium import CRMClient

with CRMClient(api_token="your-token") as client:
    contact, _ = client.contacts.identify(
        external_id="user_123",
        email="user@example.com"
    )
    # Client is automatically closed when exiting the context
```

## Core Concepts

### Authentication

The SDK uses API token authentication. You can generate an API token from your Crexperium dashboard.

```python
from crexperium import CRMClient

client = CRMClient(
    api_token="your-api-token",
    timeout=30,  # Request timeout in seconds
    max_retries=3,  # Maximum retry attempts
    retry_delay=1.0,  # Initial retry delay in seconds
)
```

### Error Handling

The SDK provides specific exception classes for different error types:

```python
from crexperium import CRMClient
from crexperium.exceptions import (
    AuthenticationError,
    ResourceNotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    NetworkError,
)

client = CRMClient(api_token="your-token")

try:
    contact = client.contacts.get("contact-id")
except AuthenticationError:
    print("Invalid API token")
except ResourceNotFoundError:
    print("Contact not found")
except ValidationError as e:
    print(f"Validation failed: {e.errors}")
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}")
except ServerError:
    print("Server error occurred")
except NetworkError:
    print("Network error occurred")
```

## API Reference

### Contacts

#### `identify(external_id, email, first_name, last_name, **kwargs)`

Identify or create a contact. This is the primary method for SDK user identification.

```python
contact, created = client.contacts.identify(
    external_id="user_123",
    email="user@example.com",
    first_name="John",
    last_name="Doe",
    phone="+1234567890",
    title="Software Engineer"
)
```

#### `lookup(external_id, email)`

Lookup a contact without creating if not found.

```python
contact = client.contacts.lookup(external_id="user_123")
if contact:
    print(f"Found: {contact.full_name}")
else:
    print("Contact not found")
```

#### `create(email, first_name, last_name, **kwargs)`

Create a new contact.

```python
contact = client.contacts.create(
    email="user@example.com",
    first_name="John",
    last_name="Doe"
)
```

#### `get(contact_id)`

Get a contact by ID.

```python
contact = client.contacts.get("contact-uuid")
```

#### `update(contact_id, **kwargs)`

Update a contact.

```python
contact = client.contacts.update(
    "contact-uuid",
    first_name="Jane",
    title="Senior Engineer"
)
```

#### `list(**filters)`

List contacts with optional filters.

```python
contacts = client.contacts.list(status="CUSTOMER")
```

#### `mark_contacted(contact_id)`

Mark contact as contacted.

```python
contact = client.contacts.mark_contacted("contact-uuid")
```

#### `update_status(contact_id, status)`

Update contact status.

```python
contact = client.contacts.update_status("contact-uuid", "CUSTOMER")
```

### Deals

#### `create(name, amount, contact_id, **kwargs)`

Create a deal with flexible contact identification.

```python
from decimal import Decimal

deal = client.deals.create(
    name="Premium Subscription",
    amount=Decimal("999.99"),
    contact_external_id="user_123",  # Or use contact_id or contact_email
    currency="USD",
    pipeline="Sales Pipeline",  # Optional: pipeline name or ID
    stage="Prospecting",  # Optional: stage name or ID
    priority="HIGH",
    tags=["premium", "annual"],
    custom_fields={"source": "website"}
)
```

#### `get(deal_id)`

Get a deal by ID.

```python
deal = client.deals.get("deal-uuid")
```

#### `update(deal_id, **kwargs)`

Update a deal.

```python
deal = client.deals.update(
    "deal-uuid",
    amount=Decimal("1499.99"),
    priority="URGENT"
)
```

#### `list(**filters)`

List deals with optional filters.

```python
deals = client.deals.list(status="OPEN", priority="HIGH")
```

#### `move_stage(deal_id, stage_id, notes)`

Move deal to a new stage.

```python
deal = client.deals.move_stage(
    "deal-uuid",
    "stage-uuid",
    notes="Customer requested demo"
)
```

#### `get_history(deal_id)`

Get stage history for a deal.

```python
history = client.deals.get_history("deal-uuid")
```

#### `by_stage(pipeline_id, **filters)`

Get deals grouped by stage (for kanban view).

```python
stages = client.deals.by_stage("pipeline-uuid", status="OPEN")
```

### Activities

#### `log(title, activity_type, user_id, email, **kwargs)`

Log an activity from your backend system.

```python
activity = client.activities.log(
    title="User completed onboarding",
    activity_type="USER_ACTION",
    user_id="user_123",  # external_id
    email="user@example.com",  # Fallback if user_id not found
    description="User finished all onboarding steps",
    metadata={
        "steps_completed": 5,
        "time_spent_seconds": 120,
        "completion_rate": 100
    }
)
```

#### `create(title, activity_type, **kwargs)`

Create an activity (generic endpoint).

```python
activity = client.activities.create(
    title="Meeting scheduled",
    activity_type="MEETING",
    description="Initial discovery call"
)
```

#### `get(activity_id)`

Get an activity by ID.

```python
activity = client.activities.get("activity-uuid")
```

#### `list(**filters)`

List activities with optional filters.

```python
activities = client.activities.list(activity_type="USER_ACTION")
```

#### `timeline(related_to_type, related_to_id)`

Get activity timeline for a specific entity.

```python
timeline = client.activities.timeline("contact", "contact-uuid")
```

#### `recent(activity_type)`

Get recent activities (last 30 days).

```python
recent = client.activities.recent(activity_type="DEAL_CREATED")
```

## Complete Example

Here's a complete example showing a typical integration workflow:

```python
from crexperium import CRMClient
from decimal import Decimal

# Initialize client
with CRMClient(api_token="your-api-token") as client:
    # 1. User signs up in your app
    contact, created = client.contacts.identify(
        external_id="user_12345",
        email="john.doe@example.com",
        first_name="John",
        last_name="Doe",
        phone="+1234567890"
    )

    if created:
        print(f"New contact created: {contact.full_name}")
    else:
        print(f"Existing contact found: {contact.full_name}")

    # 2. Log signup activity
    client.activities.log(
        title="User signed up",
        activity_type="USER_ACTION",
        user_id="user_12345",
        metadata={"source": "website", "plan": "free"}
    )

    # 3. User upgrades to premium
    client.activities.log(
        title="User upgraded to premium",
        activity_type="USER_ACTION",
        user_id="user_12345",
        metadata={"plan": "premium", "amount": 99.99}
    )

    # 4. Create a deal for the upgrade
    deal = client.deals.create(
        name=f"Premium Upgrade - {contact.full_name}",
        amount=Decimal("99.99"),
        contact_external_id="user_12345",
        currency="USD",
        priority="MEDIUM",
        tags=["upgrade", "premium"],
        custom_fields={
            "previous_plan": "free",
            "upgrade_date": "2024-01-15"
        }
    )

    print(f"Deal created: {deal.name} - ${deal.amount}")

    # 5. Move deal through stages as user completes onboarding
    # (Assuming you have the stage IDs)
    deal = client.deals.move_stage(
        deal.id,
        "qualification-stage-uuid",
        notes="User completed profile setup"
    )

    # 6. Get complete activity timeline for the contact
    timeline = client.activities.timeline("contact", contact.id)
    print(f"Total activities: {len(timeline)}")
```

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/crexperium/crexperium-python-sdk.git
cd crexperium-python-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=crexperium --cov-report=html

# Run integration tests (requires API token)
export CREXPERIUM_API_TOKEN="your-api-token"
export CREXPERIUM_BASE_URL="http://localhost:8000"
pytest tests/test_integration.py -v
```

### Code Formatting

```bash
# Format code with black
black crexperium/ tests/

# Check with flake8
flake8 crexperium/ tests/

# Type checking with mypy
mypy crexperium/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- 📧 Email: support@crexperium.com
- 📚 Documentation: https://docs.crexperium.com
- 🐛 Bug Reports: https://github.com/crexperium/crexperium-python-sdk/issues

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### Version 1.0.0 (2025-01-01)

- Initial release
- Contact management (identify, lookup, create, update, list)
- Deal management (create, update, move through stages)
- Activity logging and tracking
- Comprehensive error handling
- Automatic retries with exponential backoff
- Full test coverage
