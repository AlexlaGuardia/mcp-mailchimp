# mcp-mailchimp

Production-grade MCP server for the [Mailchimp Marketing API](https://mailchimp.com/developer/marketing/). 71 tools covering campaigns, audiences, members, tags, segments, templates, reports, automations, webhooks, merge fields, interest groups, landing pages, batch operations, e-commerce, A/B testing, member notes, file manager, and audience analytics.

Built for Claude Desktop, Claude Code, Cursor, and any MCP-compatible client.

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

## Tools (71)

### Account (1)
| Tool | Description |
|------|-------------|
| `ping` | Validate API key and get account info |

### Campaigns (11)
| Tool | Description |
|------|-------------|
| `list_campaigns` | List campaigns with status/audience filters |
| `get_campaign` | Get campaign details (settings, tracking, recipients) |
| `create_campaign` | Create a new email campaign |
| `update_campaign` | Update campaign settings (subject, from_name, etc.) |
| `send_campaign` | Send a campaign immediately |
| `schedule_campaign` | Schedule a campaign for a specific time |
| `unschedule_campaign` | Unschedule a scheduled campaign |
| `cancel_campaign` | Cancel a campaign currently sending |
| `delete_campaign` | Permanently delete a draft campaign |
| `replicate_campaign` | Copy an existing campaign |
| `send_test_email` | Send test email to specified addresses |

### Campaign Content (2)
| Tool | Description |
|------|-------------|
| `get_campaign_content` | Get campaign HTML and plain-text content |
| `set_campaign_content` | Set content via HTML or template |

### Reports (5)
| Tool | Description |
|------|-------------|
| `get_campaign_report` | Performance report (opens, clicks, bounces, unsubscribes) |
| `get_click_report` | Click details -- which URLs were clicked and how often |
| `get_open_report` | Open details -- which subscribers opened and when |
| `get_unsubscribe_report` | Unsubscribe details -- who left and why |
| `get_sent_to_report` | Delivery details -- recipient status (sent, bounced) |

### Audiences (4)
| Tool | Description |
|------|-------------|
| `list_audiences` | List all audiences with subscriber counts |
| `get_audience` | Get audience details and stats |
| `create_audience` | Create a new audience/list |
| `update_audience` | Update audience settings |

### Audience Analytics (3)
| Tool | Description |
|------|-------------|
| `get_audience_growth` | Monthly growth history -- subscribes, unsubscribes, net change |
| `get_audience_locations` | Subscriber location breakdown by country/region |
| `get_email_client_stats` | Email domain performance -- Gmail, Outlook, Apple Mail breakdown |

### Members (8)
| Tool | Description |
|------|-------------|
| `list_members` | List/filter audience members by status |
| `get_member` | Get subscriber details by email |
| `add_or_update_member` | Add new subscriber or update existing (upsert) |
| `archive_member` | Archive (soft-delete) a subscriber |
| `delete_member_permanent` | Permanently delete a subscriber (irreversible) |
| `batch_subscribe_members` | Batch subscribe up to 500 members at once |
| `search_members` | Search members across all audiences |
| `get_member_activity` | Recent subscriber activity (opens, clicks, etc.) |

### Member Notes (2)
| Tool | Description |
|------|-------------|
| `list_member_notes` | List CRM-style notes on a subscriber |
| `add_member_note` | Add a note to a subscriber |

### Tags (2)
| Tool | Description |
|------|-------------|
| `list_tags` | List all tags for an audience |
| `manage_member_tags` | Add or remove tags on a subscriber |

### Segments (5)
| Tool | Description |
|------|-------------|
| `list_segments` | List saved segments for an audience |
| `get_segment_members` | List members in a segment |
| `create_segment` | Create a static segment from email addresses |
| `update_segment` | Update segment name or add/remove members |
| `delete_segment` | Delete a segment |

### Merge Fields (2)
| Tool | Description |
|------|-------------|
| `list_merge_fields` | List custom fields (FNAME, LNAME, custom) |
| `create_merge_field` | Create a custom merge field (text, number, date, etc.) |

### Interest Categories & Groups (2)
| Tool | Description |
|------|-------------|
| `list_interest_categories` | List interest groups (checkboxes, dropdowns, radios) |
| `list_interests` | List individual options within a category |

### Templates (4)
| Tool | Description |
|------|-------------|
| `list_templates` | List available email templates |
| `get_template` | Get template details and HTML content |
| `create_template` | Create a new template from HTML |
| `delete_template` | Delete a custom template |

### Automations (5)
| Tool | Description |
|------|-------------|
| `list_automations` | List classic automations |
| `get_automation` | Get automation details and trigger info |
| `list_automation_emails` | List all emails in an automation workflow |
| `pause_automation` | Pause all emails in a workflow |
| `start_automation` | Start all emails in a workflow |

### Webhooks (3)
| Tool | Description |
|------|-------------|
| `list_webhooks` | List webhooks for an audience |
| `create_webhook` | Create a webhook for audience events |
| `delete_webhook` | Delete a webhook |

### E-Commerce (6)
| Tool | Description |
|------|-------------|
| `list_ecommerce_stores` | List connected stores (Shopify, WooCommerce, etc.) |
| `list_store_products` | List products in a connected store |
| `list_store_orders` | List orders -- filter by campaign for revenue attribution |
| `get_ecommerce_customer` | Get customer details with order count and total spent |
| `list_store_carts` | List abandoned carts for recovery campaigns |
| `list_store_promo_codes` | List promo codes for a promo rule |

### A/B Testing (1)
| Tool | Description |
|------|-------------|
| `get_ab_test_results` | Get variate campaign results -- which combination won |

### Landing Pages (2)
| Tool | Description |
|------|-------------|
| `list_landing_pages` | List landing pages with visit/conversion stats |
| `get_landing_page` | Get landing page details and tracking data |

### File Manager (2)
| Tool | Description |
|------|-------------|
| `list_files` | List files in the Mailchimp file manager |
| `upload_file` | Upload a file (base64-encoded) |

### Batch Operations (1)
| Tool | Description |
|------|-------------|
| `create_batch_operation` | Submit up to 500 API operations in a single batch |

## Examples

**"What campaigns have I sent recently?"**
> Uses `list_campaigns` with `status=sent` to show recent campaigns with open/click stats.

**"How has my audience grown this quarter?"**
> Uses `get_audience_growth` to show monthly subscribe/unsubscribe trends.

**"Which campaign drove the most revenue?"**
> Uses `list_store_orders` with `campaign_id` to see revenue attribution per campaign.

**"Show me abandoned carts from my Shopify store"**
> Uses `list_store_carts` to find recovery opportunities.

**"Add a note to john@example.com that he called about pricing"**
> Uses `add_member_note` for CRM-style contact management.

**"What A/B test subject line won?"**
> Uses `get_ab_test_results` to see which variant performed best.

**"Where are my subscribers located?"**
> Uses `get_audience_locations` for geographic breakdown.

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
