# Scout SDK Package

Helper python package to interact with the Scout platform.

## Installation

```bash
pip install scoutsdk
```

## Usage

```python
from scoutsdk import ScoutAPI

scout = ScoutAPI(base_url="your_scout_base_url", api_access_token="you_api_access_token")
```

## Retry Logic

The SDK automatically retries failed API requests with exponential backoff to handle transient failures. This improves reliability when dealing with network issues or temporary server problems.

### Default Behavior

- **Max attempts**: 3 (initial request + 2 retries)
- **Wait time**: Exponential backoff with multiplier=1, min=4s, max=10s
- **Retry on**:
  - Rate limiting (429)
  - Server errors (500, 502, 503, 504)
  - Network errors (ConnectionError, Timeout)
- **Does NOT retry on**:
  - Client errors (400, 401, 403, 404, etc.)
  - Successful responses

### How It Works

All HTTP methods (GET, POST, PUT, DELETE, PATCH) in the SDK automatically retry on transient failures:

```python
from scoutsdk import ScoutAPI

scout = ScoutAPI(base_url="your_url", api_access_token="your_token")

# This request will automatically retry up to 3 times on 5xx errors
response = scout.chat.completion(messages="Hello!")
```

The retry logic is transparent - you don't need to change your code. If a request fails with a retryable error, the SDK will:
1. Wait with exponential backoff (4s, then 8s, then 10s max)
2. Retry the request
3. Return the result if successful, or raise the exception after exhausting retries
