# UsageFlow Core

> ⚠️ **Beta Notice**: This package is currently in beta. While we strive to maintain stability, there may be breaking changes as we continue to improve the API.

The core package of UsageFlow provides the fundamental functionality for API usage tracking and management. It contains the base client implementation and shared utilities used by framework-specific packages.

## Installation

```bash
pip install usageflow-core
```

## Features

- Base client implementation

## Usage

While you typically won't use this package directly (instead using framework-specific packages like `usageflow-flask` or `usageflow-fastapi`), here's how you can use the core client:

```python
from usageflow.core import UsageFlowClient

client = UsageFlowClient(api_key="your_api_key_here")

# Track a request
client.track_request(
    method="GET",
    path="/api/v1/users",
    identity="user123",
    metadata={"user_agent": "Mozilla/5.0"}
)
```

## Development

To contribute to the project:

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run tests:
   ```bash
   pytest
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
