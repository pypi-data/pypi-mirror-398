# Canvelete Python SDK

Official Python client library for the [Canvelete](https://www.canvelete.com) API.

## Installation

```bash
pip install canvelete
```

Or install from source:

```bash
git clone https://github.com/canvelete/canvelete-python.git
cd canvelete-python
pip install -e .
```

## Quick Start

### Authentication with API Key

The simplest way to get started is with an API key:

```python
from canvelete import CanveleteClient

# Initialize client with API key
client = CanveleteClient(api_key="cvt_your_api_key_here")

# List your designs
designs = client.designs.list()
print(f"Found {len(designs['data'])} designs")

# Create a new design
canvas_data = {
    "elements": [
        {
            "type": "text",
            "text": "Hello Canvelete!",
            "x": 100,
            "y": 100,
            "fontSize": 48,
        }
    ]
}

design = client.designs.create(
    name="My First Design",
    canvas_data=canvas_data,
    width=1920,
    height=1080,
)

# Render the design
image_data = client.render.create(
    design_id=design["id"],
    format="png",
    output_file="output.png",
)
print(f"Saved render to output.png")
```

### Authentication with OAuth2

For applications that need user authorization:

```python
from canvelete import CanveleteClient

# Initialize client with OAuth2 credentials
client = CanveleteClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
)

# Authenticate (opens browser for user consent)
client.authenticate()

# Now you can make API calls
designs = client.designs.list()
```

## API Reference

### Designs

```python
# List designs with pagination
designs = client.designs.list(page=1, limit=20)

# Iterate through all designs
for design in client.designs.iterate_all():
    print(design["name"])

# Create a design
design = client.designs.create(
    name="New Design",
    canvas_data={"elements": []},
    width=1920,
    height=1080,
)

# Get a specific design
design = client.designs.get("design_id")

# Update a design
design = client.designs.update(
    "design_id",
    name="Updated Name",
    canvas_data={"elements": [...]},
)

# Delete a design
client.designs.delete("design_id")
```

### Templates

```python
# List templates
templates = client.templates.list(page=1, limit=20)

# Search templates
templates = client.templates.list(search="certificate")

# Get only your templates
my_templates = client.templates.list(my_only=True)

# Iterate through all templates
for template in client.templates.iterate_all():
    print(template["name"])

# Get a specific template
template = client.templates.get("template_id")
```

### Render

```python
# Render a design to PNG
image_data = client.render.create(
    design_id="design_id",
    format="png",
    quality=90,
    output_file="output.png",
)

# Render a template with dynamic data
image_data = client.render.create(
    template_id="template_id",
    dynamic_data={
        "name": "John Doe",
        "date": "2024-01-01",
        "company": "Acme Corp",
    },
    format="pdf",
    output_file="certificate.pdf",
)

# Custom dimensions
image_data = client.render.create(
    design_id="design_id",
    format="jpg",
    width=1200,
    height=630,
)

# List render history
renders = client.render.list(page=1, limit=20)

# Iterate through all renders
for render in client.render.iterate_all():
    print(f"Rendered at {render['createdAt']}")
```

### API Keys

```python
# List API keys (requires OAuth2)
api_keys = client.api_keys.list()

# Create a new API key
new_key = client.api_keys.create(name="Production API Key")
print(f"Save this key: {new_key['key']}")  # Shown only once!
```

## Advanced Usage

### Automatic Pagination

All list methods support automatic pagination with iterators:

```python
# Instead of manual pagination
for design in client.designs.iterate_all(limit=100):
    process_design(design)

# Instead of:
page = 1
while True:
    response = client.designs.list(page=page, limit=100)
    if not response['data']:
        break
    for design in response['data']:
        process_design(design)
    page += 1
```

### Error Handling

The SDK provides specific exceptions for different error types:

```python
from canvelete import CanveleteClient
from canvelete.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

client = CanveleteClient(api_key="cvt_your_key")

try:
    design = client.designs.get("invalid_id")
except NotFoundError:
    print("Design not found")
except AuthenticationError:
    print("Invalid API key or expired OAuth token")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ValidationError as e:
    print(f"Invalid request: {e.message}")
```

### Custom Configuration

```python
client = CanveleteClient(
    api_key="cvt_your_key",
    base_url="https://www.canvelete.com",  # Custom base URL
    timeout=60,  # Request timeout in seconds
    max_retries=5,  # Maximum retry attempts
)
```

## Environment Variables

You can also configure the client using environment variables:

```bash
export CANVELETE_API_KEY="cvt_your_api_key"
export CANVELETE_CLIENT_ID="your_client_id"
export CANVELETE_CLIENT_SECRET="your_client_secret"
export CANVELETE_BASE_URL="https://www.canvelete.com"
```

```python
import os
from canvelete import CanveleteClient

client = CanveleteClient(
    api_key=os.getenv("CANVELETE_API_KEY"),
)
```

## Examples

See the [examples](./examples) directory for complete working examples:

- `quickstart.py` - Basic usage with API key
- `oauth_flow.py` - OAuth2 authentication
- `batch_render.py` - Batch rendering multiple designs
- `template_usage.py` - Working with templates

## Requirements

- Python 3.8+
- requests >= 2.28.0
- urllib3 >= 1.26.0

## License

MIT License - see LICENSE file for details.

## Support

- **Documentation**: https://docs.canvelete.com
- **API Reference**: https://docs.canvelete.com/api
- **Issues**: https://github.com/canvelete/canvelete-python/issues
- **Email**: support@canvelete.com
