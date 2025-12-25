# Neuroute

**Private Beta Python SDK for rate-limited Claude API access**

> 📍 **Coming back to this project?** See [STATUS.md](STATUS.md) for current progress and next steps.

This is a Python SDK that provides controlled access to Claude AI for authorized users. It's designed for a small group of friends/users with strict rate limiting to keep costs manageable.

## ⚠️ Private Beta Notice

This SDK is **not** a public service. It's a private beta for a limited number of authorized users (max 10). Access requires an API key distributed by the service administrator.

## Installation

```bash
pip install neuroute
```

## Quick Start

```python
from neuroute import ClaudeClient

# Initialize client with your API key
client = ClaudeClient(api_key="csk_your_api_key_here")

# Query Claude
response = client.query("What is Python?")
print(response)
```

## Rate Limits & Constraints

- **1 query per hour** per user
- **100 character maximum** per query
- **150 tokens maximum** output (enforced server-side)

## Error Handling

```python
from neuroute import (
    ClaudeClient,
    RateLimitExceededError,
    QueryTooLongError,
    InvalidAPIKeyError,
    ServiceDisabledError
)

client = ClaudeClient(api_key="your_key")

try:
    response = client.query("Explain recursion")
    print(response)

except RateLimitExceededError as e:
    print(f"Rate limit hit! Wait {e.retry_after_seconds} seconds")

except QueryTooLongError:
    print("Query too long (max 100 characters)")

except InvalidAPIKeyError:
    print("Invalid or inactive API key")

except ServiceDisabledError:
    print("Service temporarily disabled")
```

## API Key Security

**IMPORTANT:** Treat your API key like a password:

- ✅ Store it in environment variables
- ✅ Never commit it to git
- ✅ Never share it publicly
- ❌ Don't hardcode it in your scripts

**Best practice:**

```python
import os
from neuroute import ClaudeClient

api_key = os.getenv("NEUROUTE_API_KEY")
client = ClaudeClient(api_key=api_key)
```

## Example Use Cases

### Simple Query

```python
client = ClaudeClient(api_key="your_key")
answer = client.query("What is recursion?")
print(answer)
```

### With Retry Logic

```python
import time
from neuroute import ClaudeClient, RateLimitExceededError

client = ClaudeClient(api_key="your_key")

def query_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.query(prompt)
        except RateLimitExceededError as e:
            if attempt < max_retries - 1:
                print(f"Rate limited. Waiting {e.retry_after_seconds} seconds...")
                time.sleep(e.retry_after_seconds)
            else:
                raise

response = query_with_retry("What is Python?")
print(response)
```

## Limitations

- Single query per hour (3600 seconds)
- Query length capped at 100 characters
- Output capped at 150 tokens (~100-120 words)
- Service may be disabled temporarily for maintenance
- This is a **private beta** - service can be terminated anytime

## Getting an API Key

API keys are manually distributed by the service administrator. If you don't have a key, contact the administrator directly.

Each key is limited to **1 query per hour** and can be revoked at any time.

## Support

Since this is a private beta for friends:
- Contact the administrator directly for support
- Check the GitHub repository for documentation
- Report issues privately to the administrator

## License

MIT License - See LICENSE file for details

---

**Note:** This SDK is a wrapper around the Anthropic Claude API. It's designed for personal/educational use with strict rate limits. For production use, consider using the official Anthropic API directly.
