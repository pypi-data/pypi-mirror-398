# SafeComms Python SDK

Official Python client for the SafeComms API.

SafeComms is a powerful content moderation platform designed to keep your digital communities safe. It provides real-time analysis of text to detect and filter harmful content, including hate speech, harassment, and spam.

**Get Started for Free:**
We offer a generous **Free Tier** for all users, with **no credit card required**. Sign up today and start protecting your community immediately.

## Documentation

For full API documentation and integration guides, visit [https://safecomms.dev/docs](https://safecomms.dev/docs).

## Installation

```bash
pip install safecomms
```

## Usage

```python
from safecomms import SafeCommsClient

client = SafeCommsClient(api_key="your-api-key")

# Moderate text
result = client.moderate_text(
    content="Some text to check",
    language="en",
    replace=True
)
print(result)

# Get usage
usage = client.get_usage()
print(usage)
```
