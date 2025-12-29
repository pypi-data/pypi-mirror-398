# SendPost Python SDK

[![PyPI version](https://badge.fury.io/py/sendpost-python-sdk.svg)](https://badge.fury.io/py/sendpost-python-sdk)

The official Python SDK for SendPost - a powerful email API service for sending transactional and marketing emails with advanced tracking and analytics.

**Installation**: `pip install sendpost-python-sdk`

## Features

- Send transactional and marketing emails
- Track email opens and clicks
- View detailed statistics and analytics
- Manage domains and sub-accounts
- Handle webhooks for real-time event notifications
- Full Python type hints support

## Requirements

- Python 3.9 or higher
- pip (Python package installer)

## Installation

### Install from PyPI (Recommended)

The easiest way to install the SendPost Python SDK is using pip:

```bash
pip install sendpost-python-sdk
```

If you're using Python 3, you may need to use `pip3`:

```bash
pip3 install sendpost-python-sdk
```

For a specific version:

```bash
pip install sendpost-python-sdk==2.0.0
```

### Alternative Installation Methods

#### Install from GitHub

If you need the latest development version, install directly from the GitHub repository:

```bash
pip install git+https://github.com/sendpost/sendpost-python-sdk.git
```

#### Install from Source

1. Clone the repository:
```bash
git clone https://github.com/sendpost/sendpost-python-sdk.git
cd sendpost-python-sdk
```

2. Install using setuptools:
```bash
python setup.py install --user
```

Or install for all users:
```bash
sudo python setup.py install
```

### Verify Installation

To verify the installation, run:

```python
python -c "import sendpost_python_sdk; print('SendPost SDK installed successfully!')"
```

## Quick Start

### 1. Get Your API Keys

Before you begin, you'll need API keys from SendPost:

1. Sign up at [SendPost](https://app.sendpost.io/register) if you haven't already
2. Log in to your [SendPost dashboard](https://app.sendpost.io)
3. Navigate to your account settings to get your API keys:
   - **Sub-Account API Key** (`X-SubAccount-ApiKey`) - Used for sending emails and managing domains
   - **Account API Key** (`X-Account-ApiKey`) - Used for managing sub-accounts and account-level operations

### 2. Configure Authentication

Set your API key as an environment variable (recommended):

```bash
export SENDPOST_SUB_ACCOUNT_API_KEY="your-sub-account-api-key-here"
export SENDPOST_ACCOUNT_API_KEY="your-account-api-key-here"
```

Or set it directly in your code:

```python
import os
import sendpost_python_sdk

# Configure the SDK
configuration = sendpost_python_sdk.Configuration(
    host="https://api.sendpost.io/api/v1"
)

# Set your API key
configuration.api_key['subAccountAuth'] = "your-sub-account-api-key-here"
```

### 3. Send Your First Email

Here's a simple example to send an email:

```python
import os
import sendpost_python_sdk
from sendpost_python_sdk.api import EmailApi
from sendpost_python_sdk.models import EmailMessageObject, EmailAddress, Recipient

# Configure authentication
configuration = sendpost_python_sdk.Configuration(
    host="https://api.sendpost.io/api/v1"
)
configuration.api_key['subAccountAuth'] = os.getenv("SENDPOST_SUB_ACCOUNT_API_KEY")

# Create the API client
with sendpost_python_sdk.ApiClient(configuration) as api_client:
    # Initialize the Email API
    email_api = EmailApi(api_client)
    
    # Create the email message
    email_message = EmailMessageObject()
    
    # Set the sender
    from_addr = EmailAddress()
    from_addr.email = "sender@yourdomain.com"  # Use your verified domain
    from_addr.name = "Your Name"
    email_message.var_from = from_addr
    
    # Set the recipient
    recipient = Recipient()
    recipient.email = "recipient@example.com"
    recipient.name = "Recipient Name"
    email_message.to = [recipient]
    
    # Set email content
    email_message.subject = "Hello from SendPost!"
    email_message.html_body = "<h1>Welcome!</h1><p>This is your first email sent with SendPost.</p>"
    email_message.text_body = "Welcome! This is your first email sent with SendPost."
    
    # Enable tracking
    email_message.track_opens = True
    email_message.track_clicks = True
    
    # Send the email
    try:
        responses = email_api.send_email(email_message)
        if responses:
            response = responses[0]
            print(f"Email sent successfully! Message ID: {response.message_id}")
    except sendpost_python_sdk.exceptions.ApiException as e:
        print(f"Error sending email: {e.status} - {e.body}")
```

## Common Use Cases

### Send a Transactional Email

```python
import sendpost_python_sdk
from sendpost_python_sdk.api import EmailApi
from sendpost_python_sdk.models import EmailMessageObject, EmailAddress, Recipient

configuration = sendpost_python_sdk.Configuration(
    host="https://api.sendpost.io/api/v1"
)
configuration.api_key['subAccountAuth'] = "your-sub-account-api-key"

with sendpost_python_sdk.ApiClient(configuration) as api_client:
    email_api = EmailApi(api_client)
    
    email = EmailMessageObject()
    
    # Set sender
    from_addr = EmailAddress()
    from_addr.email = "noreply@yourdomain.com"
    from_addr.name = "Your Company"
    email.var_from = from_addr
    
    # Set recipient
    recipient = Recipient()
    recipient.email = "customer@example.com"
    recipient.name = "Customer"
    email.to = [recipient]
    
    # Email content
    email.subject = "Order Confirmation"
    email.html_body = "<h1>Thank you for your order!</h1><p>Order #12345 has been confirmed.</p>"
    email.text_body = "Thank you for your order! Order #12345 has been confirmed."
    
    # Add custom data
    recipient.custom_fields = {
        "order_id": "12345",
        "order_total": "99.99"
    }
    
    # Send
    responses = email_api.send_email(email)
    print(f"Sent: {responses[0].message_id}")
```

### List Your Domains

```python
import sendpost_python_sdk
from sendpost_python_sdk.api import DomainApi

configuration = sendpost_python_sdk.Configuration(
    host="https://api.sendpost.io/api/v1"
)
configuration.api_key['subAccountAuth'] = "your-sub-account-api-key"

with sendpost_python_sdk.ApiClient(configuration) as api_client:
    domain_api = DomainApi(api_client)
    
    domains = domain_api.get_all_domains()
    
    for domain in domains:
        print(f"Domain: {domain.name}, Verified: {domain.verified}")
```

### Get Email Statistics

```python
import sendpost_python_sdk
from sendpost_python_sdk.api import StatsApi
from datetime import datetime, timedelta

configuration = sendpost_python_sdk.Configuration(
    host="https://api.sendpost.io/api/v1"
)
configuration.api_key['accountAuth'] = "your-account-api-key"

with sendpost_python_sdk.ApiClient(configuration) as api_client:
    stats_api = StatsApi(api_client)
    
    # Get stats for the last 7 days
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=7)
    subaccount_id = 123  # Your sub-account ID
    
    stats = stats_api.account_subaccount_stat_subaccount_id_get(
        from_date, to_date, subaccount_id
    )
    
    for stat in stats:
        print(f"Date: {stat.date}")
        if stat.stats:
            print(f"  Processed: {stat.stats.processed}")
            print(f"  Delivered: {stat.stats.delivered}")
            print(f"  Opened: {stat.stats.opened}")
            print(f"  Clicked: {stat.stats.clicked}")
```

## API Reference

### Available APIs

| API Class | Description |
|-----------|-------------|
| `EmailApi` | Send emails and manage email templates |
| `DomainApi` | Manage sending domains |
| `SubAccountApi` | Create and manage sub-accounts |
| `StatsApi` | Retrieve email statistics and analytics |
| `WebhookApi` | Manage webhooks for event notifications |
| `SuppressionApi` | Manage suppression lists |
| `IPApi` | Manage IP addresses |
| `IPPoolsApi` | Manage IP pools |
| `MessageApi` | Retrieve message details |

### Authentication

SendPost uses API keys for authentication. There are two types of API keys:

- **Sub-Account API Key** (`X-SubAccount-ApiKey`): Used for sending emails, managing domains, and retrieving sub-account statistics
- **Account API Key** (`X-Account-ApiKey`): Used for managing sub-accounts, IPs, and account-level operations

Set the appropriate API key based on the operation you're performing:

```python
# For sub-account operations (sending emails, managing domains)
configuration.api_key['subAccountAuth'] = "your-sub-account-api-key"

# For account operations (managing sub-accounts, IPs)
configuration.api_key['accountAuth'] = "your-account-api-key"
```

### Error Handling

The SDK raises `ApiException` for API errors. Always wrap API calls in try-except blocks:

```python
from sendpost_python_sdk.exceptions import ApiException

try:
    response = email_api.send_email(email_message)
except ApiException as e:
    print(f"API Error: {e.status}")
    print(f"Error message: {e.body}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Examples

For more comprehensive examples, check out the [example directory](../example-sdk-python/ESPExample.py) which includes:

- Creating sub-accounts
- Setting up webhooks
- Adding and verifying domains
- Sending transactional and marketing emails
- Retrieving message details
- Getting statistics
- Managing IP pools

## Testing

Run the test suite:

```bash
pytest
```

## Documentation

For detailed API documentation, visit:
- [PyPI Package](https://pypi.org/project/sendpost-python-sdk/)
- [Full API Reference](docs/)
- [SendPost API Documentation](https://docs.sendpost.io)

## Support

- **Email**: hello@sendpost.io
- **Website**: [https://sendpost.io](https://sendpost.io)
- **Documentation**: [https://docs.sendpost.io](https://docs.sendpost.io)

## License

This SDK is licensed under the MIT License.

## Version

- **SDK Version**: 2.0.0
- **API Version**: 1.0.0
- **Python**: 3.9+

---

**Note**: Make sure your sending domain is verified in SendPost before sending emails. You can add and verify domains using the `DomainApi`.
