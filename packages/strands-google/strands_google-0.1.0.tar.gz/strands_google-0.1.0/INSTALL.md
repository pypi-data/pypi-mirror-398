# Installation Instructions for strands-google

## Quick Start

### 1. Install from local directory (development mode)

```bash
cd strands-google
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Or install from PyPI (once published)

```bash
pip install strands-google
```

### 3. Verify installation

```python
from strands_google import use_google, gmail_send, gmail_reply, google_auth
print("✅ strands-google installed successfully!")
```

## Authentication Setup

### OAuth 2.0 (for Gmail, Drive, Calendar)

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID (Desktop app)
3. Download JSON and save as `gmail_credentials.json`
4. Run authentication:

```bash
python -m strands_google.google_auth
```

5. Set environment variable:

```bash
export GOOGLE_OAUTH_CREDENTIALS=~/gmail_token.json
```

### Service Account (for GCP services)

```bash
export GOOGLE_APPLICATION_CREDENTIALS=~/service-account-key.json
```

### API Key (for public APIs)

```bash
export GOOGLE_API_KEY=your_api_key_here
```

## Usage with Strands Agent

```python
from strands import Agent
from strands_google import use_google, gmail_send, gmail_reply

agent = Agent(tools=[use_google, gmail_send, gmail_reply])

# Send an email
agent("Send an email to friend@example.com saying hello")

# Search Gmail
agent("Find all unread emails from last week")

# List Drive files
agent("Show me my recent Drive files")
```

## Development

### Build distribution

```bash
pip install build
python -m build
```

### Upload to PyPI

```bash
pip install twine
twine upload dist/*
```

## Testing

```bash
# Test imports
python -c "from strands_google import use_google, gmail_send; print('OK')"

# Run examples
python examples.py
```
