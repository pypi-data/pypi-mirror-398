# ATX - Aiello ToolX

Build standalone, LLM-ready tools from Python functions. Package your tools as portable executables that can be distributed and deployed anywhere.

## What is ATX?

ATX (Aiello ToolX) is a framework for creating function tools that Large Language Models can discover and execute. It transforms Python functions into:

- **Standalone executables** - Single binary files with no external dependencies
- **LLM-compatible** - Self-describing tools with JSON schema definitions
- **Distributable** - Share tools across teams and environments
- **Version-controlled** - Manage multiple versions of the same tool

## Quick Start

### Installation

```bash
pip install atx-py
```

### Create Your First Tool

Create a file `my_tool.py`:

```python
from atx import AielloToolx
from typing import Any, Optional

class GreetTool(AielloToolx):
    def name(self) -> str:
        return "greet_user"

    def description(self, context: Optional[str] = None) -> str:
        return "Greets a user by name"

    def parameters(self, context: Optional[str] = None) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the person to greet"
                }
            },
            "required": ["name"]
        }

    def run(
        self, arguments: Optional[str] = None, context: Optional[str] = None
    ) -> str:
        import json
        args = json.loads(arguments) if arguments else {}
        name = args.get("name", "stranger")
        return f"Hello, {name}!"
```

### Build the Tool

```bash
atx build my_tool.py \
  --tool-name greet_user \
  --tool-version 1 \
  --output-dir ./dist
```

### Run the Tool

```bash
./dist/greet_user/1/tool --arguments '{"name": "Alice"}'
```

Output:

```plaintext
Hello, Alice!
```

## Features

### Type-Safe Parameters

Define parameters using JSON Schema with full type safety:

```python
def parameters(self, context: Optional[str] = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "location": {"type": "string"},
            "days": {"type": "integer", "enum": [1, 5, 10]}
        },
        "required": ["location"]
    }
```

### Environment Variable Support

Securely handle API keys and sensitive data:

```python
import os

def run(self, arguments: Optional[str] = None, context: Optional[str] = None) -> str:
    api_key = os.getenv("MY_API_KEY")
    if not api_key:
        raise ValueError("MY_API_KEY environment variable is required")
    # Use api_key...
```

### Versioned Deployment

Deploy multiple versions side-by-side:

```plaintext
dist/
├── my_tool/
│   ├── 1/
│   │   └── tool
│   └── 2/
│       └── tool
```

## Documentation

For comprehensive documentation, see:

- [Documentation Home](docs/index.md) - Complete documentation index
- [Getting Started Guide](docs/getting-started/quick-start.md) - Detailed tutorial
- [Core Concepts](docs/core-concepts/aiellotoolx-class.md) - Understanding the framework
- [API Reference](docs/api-reference/aiellotoolx.md) - Complete API documentation

## Examples

The project includes several prebuilt examples:

- **[hello_world](atx/prebuilds/hello_world.py)** - Minimal example
- **[get_maps_geocode](atx/prebuilds/get_maps_geocode.py)** - Google Maps geocoding
- **[get_weather_forecast_daily](atx/prebuilds/get_weather_forecast_daily.py)** - Weather forecasts

Build and run examples:

```bash
# Build hello world
atx build atx/prebuilds/hello_world.py --tool-name hello_world --tool-version 1

# Run it
./dist/hello_world/1/tool
```

## Development

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd atx

# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
```

### Running Tests

```bash
poetry run pytest
```

## License

Private - Aiello Inc.

## Contributing

This is a private project. For questions or contributions, please contact the Aiello development team.
