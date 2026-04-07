---
name: {{SKILL_NAME}}
description: >
  Integrates with [API Name] to perform [specific tasks].
  Use when making API calls to [Service], fetching data from [Endpoint],
  or automating [specific workflow]. Trigger on: API integration, HTTP requests,
  REST/GraphQL calls, webhook handling.
compatibility:
  - Python 3.8+
  - requests
---

# {{SKILL_NAME}}

Integrates with [API Name] to perform [specific tasks].

## Prerequisites

1. Obtain API key from [Service Name]
2. Set environment variable: `export API_KEY=your-key`
3. Install dependencies: `pip install requests`

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `API_KEY` | Yes | Your API key |
| `API_BASE_URL` | No | Custom base URL (optional) |
| `TIMEOUT` | No | Request timeout in seconds (default: 30) |

### config.yaml

```yaml
api:
  base_url: "https://api.example.com"
  timeout: 30
  retry_count: 3
```

## Usage

### Basic Request

```python
from scripts.api_client import APIClient

client = APIClient()
result = client.get("/endpoint")
print(result)
```

### Example Tasks

- Fetch user data: `python scripts/fetch_user.py --id 123`
- List resources: `python scripts/list_resources.py`
- Create item: `python scripts/create_item.py --data '{"name":"test"}'`

## Error Handling

The API client includes automatic retry with exponential backoff.

| Error | Handling |
|-------|----------|
| Rate Limit | Wait and retry |
| Timeout | Retry up to 3 times |
| Auth Error | Check API key |

## References

- API Documentation: `references/api-docs.md`
- Examples: `references/examples.md`
