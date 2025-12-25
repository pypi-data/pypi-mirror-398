# strands-google

🌐 **Google API integration for Strands Agents**

Access 200+ Google APIs (Gmail, Drive, Calendar, YouTube, etc.) directly from your Strands agent with simple, powerful tools.

## Features

- ✅ **Universal Google API Access** - Gmail, Drive, Calendar, YouTube, Sheets, Docs, and 200+ more
- 🔐 **Flexible Authentication** - OAuth 2.0, Service Accounts, and API Keys
- 📧 **Gmail Helpers** - Easy email sending and replying with automatic encoding
- 🎯 **Dynamic Scopes** - Configure OAuth scopes on-the-fly

## Installation

```bash
pip install strands-google
```

## Quick Start

### 1. Authentication Setup

#### OAuth 2.0 (Recommended for Gmail/Drive/Calendar)

```bash
python -m strands_google.google_auth
```

This will:
1. Open your browser for Google sign-in
2. Generate `gmail_token.json` with your credentials
3. Grant access to selected Google APIs

Set the environment variable:
```bash
export GOOGLE_OAUTH_CREDENTIALS=~/gmail_token.json
```

#### Service Account (For GCP services)

```bash
export GOOGLE_APPLICATION_CREDENTIALS=~/service-account-key.json
```

#### API Key (For public APIs)

```bash
export GOOGLE_API_KEY=your_api_key_here
```

### 2. Use with Strands Agents

```python
from strands import Agent
from strands_google import use_google, gmail_send, gmail_reply

agent = Agent(tools=[use_google, gmail_send, gmail_reply])

# Send an email
agent("Send an email to friend@example.com saying hello")

# Search Gmail
agent("Find all unread emails from last week")

# List Google Drive files
agent("Show me my recent Drive files")
```

## Available Tools

### `use_google` - Universal Google API Access

Access any Google API operation:

```python
# Gmail: List messages
agent.tool.use_google(
    service="gmail",
    version="v1",
    resource="users.messages",
    method="list",
    parameters={"userId": "me", "maxResults": 10}
)

# Drive: List files
agent.tool.use_google(
    service="drive",
    version="v3",
    resource="files",
    method="list",
    parameters={"pageSize": 10}
)

# Calendar: List events
agent.tool.use_google(
    service="calendar",
    version="v3",
    resource="events",
    method="list",
    parameters={"calendarId": "primary"}
)

# YouTube: Search videos
agent.tool.use_google(
    service="youtube",
    version="v3",
    resource="search",
    method="list",
    parameters={"part": "snippet", "q": "python", "maxResults": 5},
    credential_type="api_key"
)
```

### `gmail_send` - Easy Email Sending

Send emails without dealing with base64 encoding:

```python
# Simple email
agent.tool.gmail_send(
    to="friend@example.com",
    subject="Hello!",
    body="This is a test email."
)

# With CC/BCC
agent.tool.gmail_send(
    to="friend@example.com",
    subject="Team Update",
    body="Meeting at 3pm",
    cc=["boss@example.com"],
    bcc=["archive@example.com"]
)

# HTML email
agent.tool.gmail_send(
    to="friend@example.com",
    subject="Newsletter",
    body="<h1>Hello!</h1><p>This is <b>HTML</b> content.</p>",
    html=True
)
```

### `gmail_reply` - Reply to Emails

Reply to existing messages automatically:

```python
agent.tool.gmail_reply(
    message_id="19b1ff0cf255af0d",
    body="Thanks! I'll get back to you soon."
)
```

### `google_auth` - OAuth Authentication Tool

Authenticate and generate OAuth tokens with custom scopes:

```python
from strands_google import google_auth

# Authenticate with default scopes
google_auth(
    credentials_file="gmail_credentials.json",
    token_file="gmail_token.json"
)

# Authenticate with custom scopes
google_auth(
    credentials_file="gmail_credentials.json",
    token_file="gmail_token.json",
    scopes=[
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
)
```

## Advanced Usage

### Custom OAuth Scopes

Pass custom scopes for specific API access:

```python
agent.tool.use_google(
    service="gmail",
    version="v1",
    resource="users.messages",
    method="list",
    parameters={"userId": "me"},
    scopes=[
        "https://www.googleapis.com/auth/gmail.readonly"
    ]
)
```

### Force Credential Type

Override auto-detection:

```python
# Force OAuth even if service account is set
agent.tool.use_google(
    service="gmail",
    version="v1",
    resource="users.messages",
    method="list",
    parameters={"userId": "me"},
    credential_type="oauth"
)

# Force API key for public APIs
agent.tool.use_google(
    service="youtube",
    version="v3",
    resource="search",
    method="list",
    parameters={"part": "snippet", "q": "ai"},
    credential_type="api_key"
)
```

### Custom HTTP Headers

Some APIs require custom headers:

```python
# Places API with field mask
agent.tool.use_google(
    service="places",
    version="v1",
    resource="places",
    method="searchText",
    parameters={"body": {"textQuery": "restaurants in NYC"}},
    headers={"X-Goog-FieldMask": "places.displayName,places.formattedAddress"}
)
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_OAUTH_CREDENTIALS` | Path to OAuth token JSON | `~/gmail_token.json` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | `~/service-key.json` |
| `GOOGLE_API_KEY` | API key for public APIs | `AIzaSy...` |
| `GOOGLE_API_SCOPES` | Default OAuth scopes (comma-separated) | `gmail.readonly,drive.file` |
| `BYPASS_TOOL_CONSENT` | Skip confirmation prompts | `true` |

## Supported Google APIs

This package supports **ALL** Google APIs via the Discovery API, including:

- 📧 **Gmail** - Email operations
- 📁 **Drive** - File storage and management
- 📅 **Calendar** - Event scheduling
- 📺 **YouTube** - Video operations
- 📊 **Sheets** - Spreadsheet operations
- 📝 **Docs** - Document operations
- 🎨 **Slides** - Presentation operations
- 📸 **Photos** - Photo library management
- ✅ **Tasks** - Task management
- 👥 **Contacts** - Contact management
- ☁️ **Cloud Platform** - GCP services
- 📊 **Analytics** - Web analytics
- 🎓 **Classroom** - Education platform
- 📝 **Forms** - Form responses
- 🗺️ **Maps/Places** - Location services
- And 180+ more!

## Security & Safety

- **Confirmation Prompts**: Mutative operations (create, delete, modify) require confirmation
- **Bypass Option**: Set `BYPASS_TOOL_CONSENT=true` to skip prompts (be careful!)
- **Dynamic Scopes**: Only request the permissions you need
- **Credential Isolation**: Separate OAuth and service account credentials

## Development

```bash
# Clone the repo
git clone https://github.com/cagataycali/strands-google
cd strands-google

# Install in development mode
pip install -e .

# Run authentication helper
python -m strands_google.google_auth
```

## Troubleshooting

### "Permission denied" errors

Your OAuth token doesn't have the required scope. Re-authenticate with broader scopes:

```bash
python -m strands_google.google_auth
```

### "Quota exceeded" errors

You've hit API rate limits. Wait a few minutes and try again, or check your quota in Google Cloud Console.

### "Credentials not found" errors

Ensure you've set the appropriate environment variable:
- `GOOGLE_OAUTH_CREDENTIALS` for OAuth
- `GOOGLE_APPLICATION_CREDENTIALS` for service accounts
- `GOOGLE_API_KEY` for API keys

## Contributing

Contributions welcome! Please open an issue or PR on GitHub.

## License

Apache 2 License - see LICENSE file for details

## Links

- [Documentation](https://github.com/cagataycali/strands-google#readme)
- [Strands Agents](https://github.com/strands-agents/sdk-python)
- [Google API Client Library](https://github.com/googleapis/google-api-python-client)

---

Built with ❤️ for the [Strands Agents](https://github.com/strands-agents/sdk-python) community
