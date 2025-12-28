# humanticclient

Python client for [Humantic AI](https://humantic.ai) API - Analyze LinkedIn profiles for sales and hiring insights.

## Features

- **Get or Create Pattern** - Automatically creates profile analysis if it doesn't exist
- **Sales & Hiring Personas** - Get insights tailored for sales outreach or hiring evaluations
- **CLI Tool** - Command-line interface for quick analysis
- **Python Library** - Use as a library in your Python projects
- **JSON Output** - Output to stdout or save to file

## Installation

```bash
pip install humanticclient
```

## Configuration

Set your API key via environment variable or `.env` file:

```bash
export HUMANTIC_API_KEY=your_api_key_here
```

Or create a `.env` file:

```
HUMANTIC_API_KEY=your_api_key_here
```

## CLI Usage

```bash
# Print JSON to stdout
humantic "https://www.linkedin.com/in/username/"

# Save to file
humantic "https://www.linkedin.com/in/username/" -o output.json

# Specify persona (sales or hiring)
humantic "https://www.linkedin.com/in/username/" -p hiring -o output.json

# Pass API key directly
humantic "https://www.linkedin.com/in/username/" --api-key YOUR_KEY
```

### CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Save output to JSON file |
| `--persona` | `-p` | Persona: `sales` (default) or `hiring` |
| `--api-key` | | API key (overrides env var) |

## Python Library Usage

```python
from humantic import HumanticClient

# Initialize client (reads HUMANTIC_API_KEY from env)
with HumanticClient() as client:
    # Get or create profile analysis
    result = client.get_or_create_profile(
        "https://www.linkedin.com/in/username/",
        persona="sales"
    )
    print(result)
```

### API Methods

```python
from humantic import HumanticClient

client = HumanticClient(api_key="your_key")

# Create a new profile analysis
client.create_profile("https://www.linkedin.com/in/username/")

# Fetch existing profile
result = client.fetch_profile("https://www.linkedin.com/in/username/", persona="sales")

# Get or create (waits for analysis to complete)
result = client.get_or_create_profile("https://www.linkedin.com/in/username/", persona="sales")
```

## Response Structure

```json
{
  "status": "200",
  "message": "Success",
  "results": {
    "first_name": "John",
    "last_name": "Doe",
    "display_name": "John Doe",
    "user_description": "...",
    "personality_analysis": {
      "disc_assessment": {...},
      "ocean_assessment": {...}
    },
    "persona": {
      "sales": {
        "email_personalization": {...},
        "cold_calling_advice": {...},
        "communication_advice": {...}
      }
    }
  },
  "metadata": {
    "status": "FOUND",
    "analysis_status": "COMPLETE"
  }
}
```

## Development

```bash
# Install with dev dependencies
pip install -e .

# Run CLI directly
python -m humantic.cli "https://www.linkedin.com/in/username/"
```

## License

MIT License

## Links

- [Humantic AI Documentation](https://api.humantic.ai/docs)
- [GitHub Repository](https://github.com/ifightcode/Humantic-Client)
