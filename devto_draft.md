---
title: "33 Tools for Mailchimp in One MCP Server — Here's How I Built It"
published: false
description: "33 tools for the Mailchimp Marketing API, built with Python and the official MCP SDK. Free, open-source, and ready for Claude Desktop, Cursor, and any MCP client."
tags: mcp, ai, python, mailchimp
cover_image:
---

I wanted to manage my Mailchimp campaigns from Claude without copy-pasting data between tabs. The existing MCP servers for Mailchimp were either read-only, incomplete, or abandoned weekend projects with 3-5 tools.

So I built one with 33 tools that actually covers the full API — campaigns, audiences, members, segments, templates, automations, and reports. Read and write.

## What It Does

[MCP](https://modelcontextprotocol.io/) lets AI assistants interact with external tools directly. With this server installed, instead of tab-switching between Claude and Mailchimp, you just ask:

**Before (manual):**
1. Open Mailchimp
2. Navigate to Campaigns → Reports
3. Find last campaign
4. Copy the stats
5. Paste into Claude
6. Ask for analysis

**After (with mcp-mailchimp):**
> "How did my last campaign perform? Compare the open rate to my previous 5 campaigns."

Claude calls `list_campaigns`, then `get_campaign_report` for each, and gives you the analysis — all in one shot.

## 33 Tools, Full Read/Write

Not just listing data — you can actually do things:

- **Campaigns** (8): Create, send, schedule, replicate, test, update
- **Content** (2): Get and set campaign HTML/templates
- **Reports** (3): Performance stats, click-level details, open tracking
- **Audiences** (3): List, get details, create new lists
- **Members** (6): Add, update, upsert, archive, search, activity history
- **Tags** (2): List and manage member tags
- **Segments** (3): List, view members, create from emails
- **Templates** (2): List and view template HTML
- **Automations** (3): List, pause, start classic workflows
- **Account** (1): Validate API key and get account info

## Technical Decisions Worth Sharing

### The Subscriber Hash Gotcha

Mailchimp doesn't identify members by email or UUID. It uses an MD5 hash of the lowercased email. Get this wrong and you get silent 404s — no error message, just empty responses.

```python
@staticmethod
def subscriber_hash(email: str) -> str:
    return hashlib.md5(email.lower().strip().encode()).hexdigest()
```

Every Mailchimp integration learns this the hard way. My client handles it automatically so the tools just accept plain email addresses.

### Upsert Over Separate Create/Update

Instead of separate "add" and "update" tools, I use Mailchimp's PUT endpoint for member management (`add_or_update_member`). It's a safe upsert — exists? update. New? create.

The critical detail: it uses `status_if_new` so it won't accidentally resubscribe someone who previously unsubscribed. That's a compliance landmine most implementations miss.

### Formatted Responses, Not API Dumps

Mailchimp's API responses are verbose — nested `_links`, redundant metadata, fields nobody needs. Every tool extracts just the useful fields:

```python
@mcp.tool()
async def get_campaign_report(campaign_id: str) -> str:
    """Get performance report for a sent campaign."""
    mc = get_client()
    r = await mc.get(f"/reports/{campaign_id}")
    return _fmt({
        "emails_sent": r.get("emails_sent", 0),
        "opens": {
            "unique": r.get("opens", {}).get("unique_opens", 0),
            "rate": r.get("opens", {}).get("open_rate", 0),
        },
        "clicks": {
            "unique": r.get("clicks", {}).get("unique_clicks", 0),
            "rate": r.get("clicks", {}).get("click_rate", 0),
        },
        "bounces": {
            "hard": r.get("bounces", {}).get("hard_bounces", 0),
            "soft": r.get("bounces", {}).get("soft_bounces", 0),
        },
        "unsubscribes": r.get("unsubscribed", 0),
    })
```

The AI gets clean data it can reason about. No parsing gymnastics.

### FastMCP Makes Tool Definition Trivial

The official `mcp` Python SDK with `FastMCP` generates JSON Schema from type hints and docstrings automatically. A tool is just an async function:

```python
@mcp.tool()
async def list_campaigns(
    status: str = "",
    list_id: str = "",
    count: int = 20,
    offset: int = 0,
) -> str:
    """List email campaigns. Filter by status or audience."""
    # ... implementation
```

No schema files, no registration boilerplate. Type hints become parameter descriptions. Docstrings become tool descriptions. It just works.

## Get Started in 2 Minutes

### Install

```bash
pip install mcp-mailchimp
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mailchimp": {
      "command": "mcp-mailchimp",
      "env": {
        "MAILCHIMP_API_KEY": "your-key-us21"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add mailchimp -- env MAILCHIMP_API_KEY=your-key mcp-mailchimp
```

### Cursor

Same JSON config as Claude Desktop in `.cursor/mcp.json`.

## What I'd Do Differently

**Start with fewer tools.** 33 tools gives comprehensive coverage, but 15-20 would handle 95% of use cases. The automation and segment tools are niche — campaigns and members are where the value is.

**Test with real data sooner.** Mailchimp's free tier is now just 250 contacts and 500 sends/month. I developed mostly against the API docs, which meant some edge cases only showed up during real testing.

## Lessons for MCP Server Builders

If you're building MCP servers, here's what Mailchimp specifically taught me:

1. **Watch for silent identity schemes.** Mailchimp uses MD5 hashes of lowercased emails as member IDs — no error if you get it wrong, just empty responses. If your target API has non-obvious ID formats, abstract them away.
2. **Prefer upsert over create+update.** Mailchimp's PUT endpoint does a safe upsert with `status_if_new`, so it won't accidentally resubscribe someone. Idempotent operations are always safer when an AI is making the calls.
3. **Strip verbose responses.** Mailchimp returns `_links`, nested metadata, and redundant fields in every response. Extract only what the AI needs to reason about — the fewer tokens, the better the analysis.
4. **Write copy-paste configs.** Claude Desktop, Claude Code, Cursor — give people the exact JSON block. Every friction point between install and first use loses a user.

## Links

- **GitHub**: [AlexlaGuardia/mcp-mailchimp](https://github.com/AlexlaGuardia/mcp-mailchimp)
- **PyPI**: [mcp-mailchimp](https://pypi.org/project/mcp-mailchimp/)
- **License**: MIT

---

*This is part of a series of production-grade MCP servers I'm building for underserved SaaS platforms. Also available: [WooCommerce](https://github.com/AlexlaGuardia/mcp-woocommerce), [FreshBooks](https://github.com/AlexlaGuardia/mcp-freshbooks), [ActiveCampaign](https://github.com/AlexlaGuardia/mcp-activecampaign). Follow me here or on [GitHub](https://github.com/AlexlaGuardia) to catch the next one.*
