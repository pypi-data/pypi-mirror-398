# Slotix MCP Server

MCP (Model Context Protocol) server for [Slotix](https://slotix.it) - AI-powered appointment management.

This server allows AI assistants like **Claude Desktop** and **ChatGPT** to manage your Slotix appointments, clients, and notifications directly through natural conversation.

## Features

- **Appointments**: View, create, update, cancel, and reschedule appointments
- **Clients**: Search and view client information and history
- **Availability**: Check available time slots for booking
- **Statistics**: Get business insights (revenue, appointments, clients)
- **Notifications**: Send messages to clients via Telegram or WhatsApp
- **Coupons**: Create and send discount coupons with QR codes to clients

## Prerequisites

- A [Slotix](https://slotix.it) account with an active subscription
- An API key (generate one in Slotix Settings > API & Integrations)

## Installation

### Claude Desktop

1. Install using `uvx`:

```bash
uvx slotixmcp
```

2. Configure Claude Desktop by editing `claude_desktop_config.json`:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "slotix": {
      "command": "uvx",
      "args": ["slotixmcp"],
      "env": {
        "SLOTIX_API_KEY": "sk_slotix_your_api_key_here"
      }
    }
  }
}
```

3. Restart Claude Desktop

### ChatGPT (Developer Mode)

1. Enable Developer Mode in ChatGPT settings (requires Plus/Pro)
2. Go to Settings → Connectors → Advanced Settings → Developer Mode
3. Add the MCP server with your API key

### Direct Installation (pip)

```bash
pip install slotixmcp
```

## Configuration

Set the following environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `SLOTIX_API_KEY` | Yes | Your Slotix API key (starts with `sk_slotix_`) |
| `SLOTIX_API_URL` | No | API URL (default: `https://api.slotix.it`) |

## Available Tools

| Tool | Description |
|------|-------------|
| `get_profile` | Get your professional profile information |
| `get_appointments` | Get appointments with optional date range and status filter |
| `get_today_appointments` | Get today's appointments |
| `get_week_appointments` | Get this week's appointments |
| `get_appointment` | Get details of a specific appointment |
| `create_appointment` | Create a new appointment |
| `update_appointment` | Update an existing appointment |
| `cancel_appointment` | Cancel an appointment |
| `reschedule_appointment` | Reschedule and optionally notify the client |
| `get_clients` | Get list of clients with optional search |
| `get_client` | Get detailed client information |
| `get_availability` | Get available time slots |
| `get_stats` | Get business statistics |
| `send_notification` | Send a message to a client |
| `create_coupon` | Create and send a discount coupon to a client |

## Example Conversations

**Get today's schedule:**
> "What appointments do I have today?"

**Reschedule an appointment:**
> "Move Mario Rossi's appointment to tomorrow at 3pm and let him know"

**Check client history:**
> "Show me the appointment history for client Maria Bianchi"

**Get business stats:**
> "How was my month? Show me the statistics"

**Find available slots:**
> "When am I free next week?"

**Send a discount coupon:**
> "Create a 10% discount coupon for client Mario Rossi"

**Send a fixed amount coupon:**
> "Send a €5 coupon to the client with ID 42"

## Development

### Local Development

```bash
# Clone the repository
git clone https://github.com/slotix/SlotixMCP.git
cd SlotixMCP

# Install dependencies
pip install -e .

# Run the server
SLOTIX_API_KEY=your_key python -m slotixmcp.server
```

### Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uvx slotixmcp
```

---

## Publishing to MCP Stores

### PyPI (Required for `uvx` installation)

1. **Build the package:**
```bash
pip install build twine
python -m build
```

2. **Upload to PyPI:**
```bash
# Test upload first
twine upload --repository testpypi dist/*

# Production upload
twine upload dist/*
```

Or using `uv`:
```bash
uv build
uv publish
```

### MCP.so (Community Registry)

1. Go to [mcp.so](https://mcp.so)
2. Click "Submit Server"
3. Fill in the form with:
   - Name: `Slotix`
   - Repository: `https://github.com/slotix/SlotixMCP`
   - Description: AI-powered appointment management for professionals

Or submit via GitHub issue on their repository.

### Smithery.ai

1. Visit [smithery.ai](https://smithery.ai)
2. Sign in with GitHub
3. Submit your MCP server repository
4. Fill in the metadata and examples

### Glama.ai

1. Go to [glama.ai/mcp/servers](https://glama.ai/mcp/servers)
2. Click "Submit Server"
3. Provide repository URL and documentation

### Anthropic MCP Directory (Official)

**Requirements:**
- Privacy policy accessible from your website
- Verified contact information
- Technical support availability
- OAuth 2.0 with valid certificates (for remote servers)
- 3+ working example use cases
- Compliance with [Anthropic MCP Directory Policy](https://support.anthropic.com/en/articles/11697096-anthropic-mcp-directory-policy)

**Process:**
1. Ensure your server meets all security and privacy requirements
2. Prepare test account with sample data
3. Submit via [Claude Partners](https://claude.com/partners/mcp)
4. Wait for review (can take several weeks)

---

## Security

- Never share your API key publicly
- The API key provides full access to your Slotix account
- Revoke and regenerate keys if compromised
- Use environment variables, not hardcoded keys

## Support

- **Documentation**: [docs.slotix.it](https://docs.slotix.it)
- **Issues**: [GitHub Issues](https://github.com/slotix/SlotixMCP/issues)
- **Email**: support@slotix.it

## License

MIT License - see [LICENSE](LICENSE) for details.
