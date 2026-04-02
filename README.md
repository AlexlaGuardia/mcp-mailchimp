# mcp-mailchimp
[![MCPize](https://mcpize.com/badge/@AlexlaGuardia/mailchimp)](https://mcpize.com/mcp/mailchimp)

Production-grade MCP server for the [Mailchimp Marketing API](https://mailchimp.com/developer/marketing/). 33 tools covering campaigns, audiences, members, tags, segments, templates, reports, and automations.

Built for Claude Desktop, Claude Code, Cursor, and any MCP-compatible client.

## Connect via MCPize

Use this MCP server instantly with no local installation:

```bash
npx -y mcpize connect @AlexlaGuardia/mailchimp --client claude
```

Or connect at: **https://mcpize.com/mcp/mailchimp**

## Quick Start

### 1. Install

```bash
pip install mcp-mailchimp
```

Or from source:

```bash
git clone https://github.com/AlexlaGuardia/mcp-mailchimp.git
cd mcp-mailchimp
pip install .
```

### 2. Get Your API Key

1. Log in to [Mailchimp](https://mailchimp.com)
2. Go to **Account & Billing** > **Extras** > **API Keys**
3. Click **Create A Key**
4. Copy the key (format: `xxxxxxxxxx-usXX`)

### 3. Configure Your Client

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mailchimp": {
      "command": "mcp-mailchimp",
      "env": {
        "MAILCHIMP_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Claude Code:**

```bash
claude mcp add mailchimp -- env MAILCHIMP_API_KEY=your-key mcp-mailchimp
```

**Cursor** (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "mailchimp": {
      "command": "mcp-mailchimp",
      "env": {
        "MAILCHIMP_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Or run directly:

```bash
MAILCHIMP_API_KEY=your-key mcp-mailchimp
```

## Tools (33)

### Account
| Tool | Description |
|------|-------------|
| `ping` | Validate API key and get account info |

### Campaigns
| Tool | Description |
|------|-------------|
| `list_campaigns` | List campaigns with status/audience filters |
| `get_campaign` | Get campaign details (settings, tracking, recipients) |
| `create_campaign` | Create a new email campaign |
| `update_campaign` | Update campaign settings (subject, from_name, etc.) |
| `send_campaign` | Send a campaign immediately |
| `schedule_campaign` | Schedule a campaign for a specific time |
| `replicate_campaign` | Copy an existing campaign |
| `send_test_email` | Send test email to specified addresses |

### Campaign Content
| Tool | Description |
|------|-------------|
| `get_campaign_content` | Get campaign HTML and plain-text content |
| `set_campaign_content` | Set content via HTML or template |

### Reports
| Tool | Description |
|------|-------------|
| `get_campaign_report` | Performance report (opens, clicks, bounces, unsubscribes) |
| `get_click_report` | Click details — which URLs were clicked and how often |
| `get_open_report` | Open details — which subscribers opened and when |

### Audiences
| Tool | Description |
|------|-------------|
| `list_audiences` | List all audiences with subscriber counts |
| `get_audience` | Get audience details and stats |
| `create_audience` | Create a new audience/list |

### Members
| Tool | Description |
|------|-------------|
| `list_members` | List/filter audience members by status |
| `get_member` | Get subscriber details by email |
| `add_or_update_member` | Add new subscriber or update existing (upsert) |
| `archive_member` | Archive (soft-delete) a subscriber |
| `search_members` | Search members across all audiences |
| `get_member_activity` | Recent subscriber activity (opens, clicks, etc.) |

### Tags
| Tool | Description |
|------|-------------|
| `list_tags` | List all tags for an audience |
| `manage_member_tags` | Add or remove tags on a subscriber |

### Segments
| Tool | Description |
|------|-------------|
| `list_segments` | List saved segments for an audience |
| `get_segment_members` | List members in a segment |
| `create_segment` | Create a static segment from email addresses |

### Templates
| Tool | Description |
|------|-------------|
| `list_templates` | List available email templates |
| `get_template` | Get template details and HTML content |

### Automations
| Tool | Description |
|------|-------------|
| `list_automations` | List classic automations |
| `pause_automation` | Pause all emails in a workflow |
| `start_automation` | Start all emails in a workflow |

## Examples

**"What campaigns have I sent recently?"**
> Uses `list_campaigns` with `status=sent` to show recent campaigns with open/click stats.

**"Add john@example.com to my newsletter list and tag them as VIP"**
> Uses `add_or_update_member` then `manage_member_tags` to subscribe and tag in one flow.

**"How did my last campaign perform?"**
> Uses `list_campaigns` to find the latest, then `get_campaign_report` for opens, clicks, bounces.

**"Send a test of my draft campaign to my email"**
> Uses `send_test_email` to send a preview before the real send.

## Requirements

- Python 3.10+
- Mailchimp account with API key
- MCP-compatible client (Claude Desktop, Claude Code, Cursor, etc.)

## Development

```bash
git clone https://github.com/AlexlaGuardia/mcp-mailchimp.git
cd mcp-mailchimp
pip install -e ".[dev]"
pytest
```

## License

MIT