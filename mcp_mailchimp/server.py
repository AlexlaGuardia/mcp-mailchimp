"""MCP server for the Mailchimp Marketing API — 33 tools."""

import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_mailchimp.client import MailchimpClient, MailchimpError

mcp = FastMCP(
    "mcp-mailchimp",
    instructions=(
        "Production-grade MCP server for the Mailchimp Marketing API. "
        "33 tools for campaigns, audiences, members, tags, segments, "
        "templates, reports, and automations."
    ),
)

# ── Client singleton ─────────────────────────────────────────────────

_client: MailchimpClient | None = None


def get_client() -> MailchimpClient:
    global _client
    if _client is None:
        api_key = os.environ.get("MAILCHIMP_API_KEY", "")
        if not api_key or "-" not in api_key:
            raise ValueError(
                "MAILCHIMP_API_KEY environment variable required. "
                "Format: xxxxxxxxxx-usXX "
                "(get yours at https://mailchimp.com/account/api)"
            )
        _client = MailchimpClient(api_key)
    return _client


def _fmt(data: Any) -> str:
    """Format response data as indented JSON string."""
    return json.dumps(data, indent=2, default=str)


# ══════════════════════════════════════════════════════════════════════
# ACCOUNT
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def ping() -> str:
    """Validate your Mailchimp API key and get account info (name, email, total subscribers)."""
    mc = get_client()
    try:
        await mc.get("/ping")
        root = await mc.get("/")
        return _fmt({
            "status": "connected",
            "account_name": root.get("account_name", ""),
            "email": root.get("email", ""),
            "account_id": root.get("account_id", ""),
            "total_subscribers": root.get("total_subscribers", 0),
            "data_center": mc.dc,
        })
    except MailchimpError as e:
        return f"Connection failed: {e}"


# ══════════════════════════════════════════════════════════════════════
# CAMPAIGNS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_campaigns(
    status: str = "",
    list_id: str = "",
    count: int = 20,
    offset: int = 0,
) -> str:
    """List email campaigns. Filter by status (save, paused, schedule, sending, sent) or audience list_id."""
    mc = get_client()
    params: dict[str, Any] = {"count": min(count, 100), "offset": offset}
    if status:
        params["status"] = status
    if list_id:
        params["list_id"] = list_id
    data = await mc.get("/campaigns", params=params)
    campaigns = []
    for c in data.get("campaigns", []):
        s = c.get("settings", {})
        campaigns.append({
            "id": c["id"],
            "title": s.get("title", ""),
            "subject_line": s.get("subject_line", ""),
            "status": c.get("status", ""),
            "type": c.get("type", ""),
            "send_time": c.get("send_time"),
            "emails_sent": c.get("emails_sent", 0),
        })
    return _fmt({"total_items": data.get("total_items", 0), "campaigns": campaigns})


@mcp.tool()
async def get_campaign(campaign_id: str) -> str:
    """Get full details for a specific campaign including settings, tracking, and recipient info."""
    mc = get_client()
    c = await mc.get(f"/campaigns/{campaign_id}")
    s = c.get("settings", {})
    r = c.get("recipients", {})
    t = c.get("tracking", {})
    return _fmt({
        "id": c["id"],
        "type": c.get("type", ""),
        "status": c.get("status", ""),
        "title": s.get("title", ""),
        "subject_line": s.get("subject_line", ""),
        "preview_text": s.get("preview_text", ""),
        "from_name": s.get("from_name", ""),
        "reply_to": s.get("reply_to", ""),
        "list_id": r.get("list_id", ""),
        "list_name": r.get("list_name", ""),
        "recipient_count": r.get("recipient_count", 0),
        "send_time": c.get("send_time"),
        "emails_sent": c.get("emails_sent", 0),
        "opens_tracking": t.get("opens", False),
        "clicks_tracking": t.get("html_clicks", False),
        "created_at": c.get("create_time", ""),
    })


@mcp.tool()
async def create_campaign(
    list_id: str,
    subject_line: str,
    from_name: str,
    reply_to: str,
    title: str = "",
    preview_text: str = "",
    campaign_type: str = "regular",
) -> str:
    """Create a new email campaign. Returns the campaign ID. Type: regular, plaintext, absplit, rss."""
    mc = get_client()
    body: dict[str, Any] = {
        "type": campaign_type,
        "recipients": {"list_id": list_id},
        "settings": {
            "subject_line": subject_line,
            "from_name": from_name,
            "reply_to": reply_to,
            "title": title or subject_line,
        },
    }
    if preview_text:
        body["settings"]["preview_text"] = preview_text
    c = await mc.post("/campaigns", json=body)
    return _fmt({
        "id": c["id"],
        "status": c.get("status", ""),
        "title": c.get("settings", {}).get("title", ""),
        "message": "Campaign created successfully.",
    })


@mcp.tool()
async def update_campaign(
    campaign_id: str,
    subject_line: str = "",
    from_name: str = "",
    reply_to: str = "",
    title: str = "",
    preview_text: str = "",
) -> str:
    """Update campaign settings. Only provide fields you want to change."""
    mc = get_client()
    settings: dict[str, str] = {}
    if subject_line:
        settings["subject_line"] = subject_line
    if from_name:
        settings["from_name"] = from_name
    if reply_to:
        settings["reply_to"] = reply_to
    if title:
        settings["title"] = title
    if preview_text:
        settings["preview_text"] = preview_text
    if not settings:
        return "No fields provided to update."
    c = await mc.patch(f"/campaigns/{campaign_id}", json={"settings": settings})
    return _fmt({
        "id": c["id"],
        "status": c.get("status", ""),
        "updated_fields": list(settings.keys()),
        "message": "Campaign updated.",
    })


@mcp.tool()
async def send_campaign(campaign_id: str) -> str:
    """Send a campaign immediately. The campaign must be in 'save' status with content set."""
    mc = get_client()
    await mc.post(f"/campaigns/{campaign_id}/actions/send")
    return _fmt({"campaign_id": campaign_id, "message": "Campaign is sending."})


@mcp.tool()
async def schedule_campaign(campaign_id: str, schedule_time: str) -> str:
    """Schedule a campaign. schedule_time must be ISO 8601 UTC (e.g. '2026-04-01T14:00:00+00:00')."""
    mc = get_client()
    await mc.post(
        f"/campaigns/{campaign_id}/actions/schedule",
        json={"schedule_time": schedule_time},
    )
    return _fmt({
        "campaign_id": campaign_id,
        "scheduled_for": schedule_time,
        "message": "Campaign scheduled.",
    })


@mcp.tool()
async def replicate_campaign(campaign_id: str) -> str:
    """Create a copy of an existing campaign. Returns the new campaign ID."""
    mc = get_client()
    c = await mc.post(f"/campaigns/{campaign_id}/actions/replicate")
    return _fmt({
        "new_campaign_id": c["id"],
        "original_campaign_id": campaign_id,
        "status": c.get("status", ""),
        "message": "Campaign replicated.",
    })


@mcp.tool()
async def send_test_email(campaign_id: str, test_emails: str) -> str:
    """Send a test email for a campaign. test_emails: comma-separated addresses (max 5)."""
    mc = get_client()
    emails = [e.strip() for e in test_emails.split(",") if e.strip()]
    await mc.post(
        f"/campaigns/{campaign_id}/actions/test",
        json={"test_emails": emails[:5], "send_type": "html"},
    )
    return _fmt({
        "campaign_id": campaign_id,
        "sent_to": emails[:5],
        "message": "Test email sent.",
    })


# ══════════════════════════════════════════════════════════════════════
# CAMPAIGN CONTENT
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_campaign_content(campaign_id: str) -> str:
    """Get the HTML and plain-text content of a campaign."""
    mc = get_client()
    data = await mc.get(f"/campaigns/{campaign_id}/content")
    return _fmt({
        "campaign_id": campaign_id,
        "plain_text": data.get("plain_text", "")[:2000],
        "html_preview": data.get("html", "")[:3000],
        "archive_html": data.get("archive_html", "")[:500],
    })


@mcp.tool()
async def set_campaign_content(
    campaign_id: str,
    html: str = "",
    plain_text: str = "",
    template_id: int = 0,
) -> str:
    """Set campaign content. Provide html for custom content, or template_id to use a template."""
    mc = get_client()
    body: dict[str, Any] = {}
    if html:
        body["html"] = html
    if plain_text:
        body["plain_text"] = plain_text
    if template_id:
        body["template"] = {"id": template_id}
    if not body:
        return "Provide html, plain_text, or template_id."
    await mc.put(f"/campaigns/{campaign_id}/content", json=body)
    return _fmt({
        "campaign_id": campaign_id,
        "content_type": "template" if template_id else "custom_html",
        "message": "Campaign content set.",
    })


# ══════════════════════════════════════════════════════════════════════
# REPORTS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_campaign_report(campaign_id: str) -> str:
    """Get performance report for a sent campaign — opens, clicks, bounces, unsubscribes, and more."""
    mc = get_client()
    r = await mc.get(f"/reports/{campaign_id}")
    return _fmt({
        "campaign_id": campaign_id,
        "subject_line": r.get("subject_line", ""),
        "emails_sent": r.get("emails_sent", 0),
        "opens": {
            "total": r.get("opens", {}).get("opens_total", 0),
            "unique": r.get("opens", {}).get("unique_opens", 0),
            "rate": r.get("opens", {}).get("open_rate", 0),
        },
        "clicks": {
            "total": r.get("clicks", {}).get("clicks_total", 0),
            "unique": r.get("clicks", {}).get("unique_clicks", 0),
            "rate": r.get("clicks", {}).get("click_rate", 0),
        },
        "bounces": {
            "hard": r.get("bounces", {}).get("hard_bounces", 0),
            "soft": r.get("bounces", {}).get("soft_bounces", 0),
        },
        "unsubscribes": r.get("unsubscribed", 0),
        "abuse_reports": r.get("abuse_reports", 0),
        "send_time": r.get("send_time", ""),
    })


@mcp.tool()
async def get_click_report(campaign_id: str, count: int = 20) -> str:
    """Get click details for a campaign — which URLs were clicked and how many times."""
    mc = get_client()
    data = await mc.get(
        f"/reports/{campaign_id}/click-details",
        params={"count": min(count, 100)},
    )
    urls = []
    for u in data.get("urls_clicked", []):
        urls.append({
            "url": u.get("url", ""),
            "total_clicks": u.get("total_clicks", 0),
            "unique_clicks": u.get("unique_clicks", 0),
            "click_percentage": u.get("click_percentage", 0),
            "last_click": u.get("last_click", ""),
        })
    return _fmt({"campaign_id": campaign_id, "total_urls": len(urls), "urls": urls})


@mcp.tool()
async def get_open_report(campaign_id: str, count: int = 20, offset: int = 0) -> str:
    """Get open details for a campaign — which subscribers opened and when."""
    mc = get_client()
    data = await mc.get(
        f"/reports/{campaign_id}/open-details",
        params={"count": min(count, 100), "offset": offset},
    )
    members = []
    for m in data.get("members", []):
        members.append({
            "email": m.get("email_address", ""),
            "opens_count": m.get("opens_count", 0),
            "first_open": m.get("first_open", ""),
            "last_open": m.get("last_open", ""),
        })
    return _fmt({
        "campaign_id": campaign_id,
        "total_opens": data.get("total_opens", 0),
        "total_items": data.get("total_items", 0),
        "members": members,
    })


# ══════════════════════════════════════════════════════════════════════
# AUDIENCES (LISTS)
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_audiences(count: int = 20, offset: int = 0) -> str:
    """List all audiences (mailing lists) with subscriber counts and stats."""
    mc = get_client()
    data = await mc.get("/lists", params={"count": min(count, 100), "offset": offset})
    audiences = []
    for a in data.get("lists", []):
        stats = a.get("stats", {})
        audiences.append({
            "id": a["id"],
            "name": a.get("name", ""),
            "member_count": stats.get("member_count", 0),
            "unsubscribe_count": stats.get("unsubscribe_count", 0),
            "open_rate": stats.get("open_rate", 0),
            "click_rate": stats.get("click_rate", 0),
            "created_at": a.get("date_created", ""),
        })
    return _fmt({"total_items": data.get("total_items", 0), "audiences": audiences})


@mcp.tool()
async def get_audience(list_id: str) -> str:
    """Get detailed info and stats for a specific audience."""
    mc = get_client()
    a = await mc.get(f"/lists/{list_id}")
    stats = a.get("stats", {})
    return _fmt({
        "id": a["id"],
        "name": a.get("name", ""),
        "permission_reminder": a.get("permission_reminder", ""),
        "member_count": stats.get("member_count", 0),
        "unsubscribe_count": stats.get("unsubscribe_count", 0),
        "cleaned_count": stats.get("cleaned_count", 0),
        "campaign_count": stats.get("campaign_count", 0),
        "open_rate": stats.get("open_rate", 0),
        "click_rate": stats.get("click_rate", 0),
        "last_campaign_sent": stats.get("campaign_last_sent", ""),
        "created_at": a.get("date_created", ""),
    })


@mcp.tool()
async def create_audience(
    name: str,
    from_email: str,
    company: str,
    permission_reminder: str = "You signed up on our website.",
    from_name: str = "",
    country: str = "US",
) -> str:
    """Create a new audience/list. Requires name, sender email, and company name."""
    mc = get_client()
    body = {
        "name": name,
        "permission_reminder": permission_reminder,
        "email_type_option": True,
        "contact": {
            "company": company,
            "address1": "",
            "city": "",
            "state": "",
            "zip": "",
            "country": country,
        },
        "campaign_defaults": {
            "from_name": from_name or company,
            "from_email": from_email,
            "subject": "",
            "language": "en",
        },
    }
    a = await mc.post("/lists", json=body)
    return _fmt({
        "id": a["id"],
        "name": a.get("name", ""),
        "message": "Audience created.",
    })


# ══════════════════════════════════════════════════════════════════════
# MEMBERS / SUBSCRIBERS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_members(
    list_id: str,
    status: str = "",
    count: int = 20,
    offset: int = 0,
) -> str:
    """List members of an audience. Filter by status: subscribed, unsubscribed, cleaned, pending, transactional."""
    mc = get_client()
    params: dict[str, Any] = {"count": min(count, 100), "offset": offset}
    if status:
        params["status"] = status
    data = await mc.get(f"/lists/{list_id}/members", params=params)
    members = []
    for m in data.get("members", []):
        members.append({
            "email": m.get("email_address", ""),
            "status": m.get("status", ""),
            "full_name": m.get("full_name", ""),
            "tags_count": m.get("tags_count", 0),
            "rating": m.get("member_rating", 0),
            "last_changed": m.get("last_changed", ""),
            "id": m.get("id", ""),
        })
    return _fmt({"total_items": data.get("total_items", 0), "members": members})


@mcp.tool()
async def get_member(list_id: str, email: str) -> str:
    """Get details for a specific subscriber by email address."""
    mc = get_client()
    h = mc.subscriber_hash(email)
    m = await mc.get(f"/lists/{list_id}/members/{h}")
    merge = m.get("merge_fields", {})
    return _fmt({
        "email": m.get("email_address", ""),
        "status": m.get("status", ""),
        "full_name": m.get("full_name", ""),
        "first_name": merge.get("FNAME", ""),
        "last_name": merge.get("LNAME", ""),
        "rating": m.get("member_rating", 0),
        "tags_count": m.get("tags_count", 0),
        "vip": m.get("vip", False),
        "source": m.get("source", ""),
        "ip_signup": m.get("ip_signup", ""),
        "language": m.get("language", ""),
        "location": m.get("location", {}),
        "subscribed_at": m.get("timestamp_opt", ""),
        "last_changed": m.get("last_changed", ""),
        "id": m.get("id", ""),
    })


@mcp.tool()
async def add_or_update_member(
    list_id: str,
    email: str,
    status: str = "subscribed",
    first_name: str = "",
    last_name: str = "",
    tags: str = "",
) -> str:
    """Add a new subscriber or update if exists (upsert). Status: subscribed, pending, unsubscribed. Tags: comma-separated."""
    mc = get_client()
    h = mc.subscriber_hash(email)
    body: dict[str, Any] = {
        "email_address": email.lower().strip(),
        "status_if_new": status,
    }
    merge_fields: dict[str, str] = {}
    if first_name:
        merge_fields["FNAME"] = first_name
    if last_name:
        merge_fields["LNAME"] = last_name
    if merge_fields:
        body["merge_fields"] = merge_fields
    if tags:
        body["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    m = await mc.put(f"/lists/{list_id}/members/{h}", json=body)
    return _fmt({
        "email": m.get("email_address", ""),
        "status": m.get("status", ""),
        "id": m.get("id", ""),
        "message": "Member added/updated.",
    })


@mcp.tool()
async def archive_member(list_id: str, email: str) -> str:
    """Archive (soft-delete) a subscriber. They can be re-added later via add_or_update_member."""
    mc = get_client()
    h = mc.subscriber_hash(email)
    await mc.delete(f"/lists/{list_id}/members/{h}")
    return _fmt({"email": email, "message": "Member archived."})


@mcp.tool()
async def search_members(query: str, list_id: str = "") -> str:
    """Search for members by email or name across all audiences (or a specific one)."""
    mc = get_client()
    params: dict[str, str] = {"query": query}
    if list_id:
        params["list_id"] = list_id
    data = await mc.get("/search-members", params=params)
    results = []
    for match in data.get("exact_matches", {}).get("members", []):
        results.append({
            "email": match.get("email_address", ""),
            "full_name": match.get("full_name", ""),
            "status": match.get("status", ""),
            "list_id": match.get("list_id", ""),
        })
    for match in data.get("full_search", {}).get("members", []):
        email = match.get("email_address", "")
        if not any(r["email"] == email for r in results):
            results.append({
                "email": email,
                "full_name": match.get("full_name", ""),
                "status": match.get("status", ""),
                "list_id": match.get("list_id", ""),
            })
    return _fmt({"total_results": len(results), "members": results[:50]})


@mcp.tool()
async def get_member_activity(list_id: str, email: str, count: int = 20) -> str:
    """Get recent activity for a subscriber — opens, clicks, bounces, etc."""
    mc = get_client()
    h = mc.subscriber_hash(email)
    data = await mc.get(
        f"/lists/{list_id}/members/{h}/activity-feed",
        params={"count": min(count, 50)},
    )
    activities = []
    for a in data.get("activity", []):
        activities.append({
            "action": a.get("action", ""),
            "title": a.get("title", ""),
            "timestamp": a.get("timestamp", ""),
            "campaign_id": a.get("campaign_id", ""),
        })
    return _fmt({"email": email, "activities": activities})


# ══════════════════════════════════════════════════════════════════════
# TAGS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_tags(list_id: str) -> str:
    """List all tags for an audience."""
    mc = get_client()
    data = await mc.get(f"/lists/{list_id}/tag-search", params={"name": ""})
    tags = [
        {"id": t.get("id", ""), "name": t.get("name", "")}
        for t in data.get("tags", [])
    ]
    return _fmt({"total": len(tags), "tags": tags})


@mcp.tool()
async def manage_member_tags(
    list_id: str,
    email: str,
    add_tags: str = "",
    remove_tags: str = "",
) -> str:
    """Add or remove tags on a subscriber. Provide comma-separated tag names for add_tags and/or remove_tags."""
    mc = get_client()
    h = mc.subscriber_hash(email)
    tag_list = []
    if add_tags:
        for t in add_tags.split(","):
            if t.strip():
                tag_list.append({"name": t.strip(), "status": "active"})
    if remove_tags:
        for t in remove_tags.split(","):
            if t.strip():
                tag_list.append({"name": t.strip(), "status": "inactive"})
    if not tag_list:
        return "Provide add_tags or remove_tags (comma-separated names)."
    await mc.post(
        f"/lists/{list_id}/members/{h}/tags",
        json={"tags": tag_list, "is_syncing": False},
    )
    return _fmt({
        "email": email,
        "added": [t["name"] for t in tag_list if t["status"] == "active"],
        "removed": [t["name"] for t in tag_list if t["status"] == "inactive"],
        "message": "Tags updated.",
    })


# ══════════════════════════════════════════════════════════════════════
# SEGMENTS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_segments(list_id: str, count: int = 20, offset: int = 0) -> str:
    """List saved segments for an audience."""
    mc = get_client()
    data = await mc.get(
        f"/lists/{list_id}/segments",
        params={"count": min(count, 100), "offset": offset},
    )
    segments = []
    for s in data.get("segments", []):
        segments.append({
            "id": s.get("id", ""),
            "name": s.get("name", ""),
            "member_count": s.get("member_count", 0),
            "type": s.get("type", ""),
            "created_at": s.get("created_at", ""),
            "updated_at": s.get("updated_at", ""),
        })
    return _fmt({"total_items": data.get("total_items", 0), "segments": segments})


@mcp.tool()
async def get_segment_members(
    list_id: str,
    segment_id: str,
    count: int = 20,
    offset: int = 0,
) -> str:
    """List members in a specific segment."""
    mc = get_client()
    data = await mc.get(
        f"/lists/{list_id}/segments/{segment_id}/members",
        params={"count": min(count, 100), "offset": offset},
    )
    members = []
    for m in data.get("members", []):
        members.append({
            "email": m.get("email_address", ""),
            "full_name": m.get("full_name", ""),
            "status": m.get("status", ""),
        })
    return _fmt({"total_items": data.get("total_items", 0), "members": members})


@mcp.tool()
async def create_segment(
    list_id: str,
    name: str,
    emails: str = "",
) -> str:
    """Create a static segment from email addresses. emails: comma-separated list."""
    mc = get_client()
    body: dict[str, Any] = {"name": name}
    if emails:
        body["static_segment"] = [e.strip() for e in emails.split(",") if e.strip()]
    s = await mc.post(f"/lists/{list_id}/segments", json=body)
    return _fmt({
        "id": s.get("id", ""),
        "name": s.get("name", ""),
        "member_count": s.get("member_count", 0),
        "message": "Segment created.",
    })


# ══════════════════════════════════════════════════════════════════════
# TEMPLATES
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_templates(count: int = 20, offset: int = 0) -> str:
    """List available email templates."""
    mc = get_client()
    data = await mc.get(
        "/templates",
        params={"count": min(count, 100), "offset": offset},
    )
    templates = []
    for t in data.get("templates", []):
        templates.append({
            "id": t.get("id", ""),
            "name": t.get("name", ""),
            "type": t.get("type", ""),
            "category": t.get("category", ""),
            "active": t.get("active", False),
            "created_at": t.get("date_created", ""),
        })
    return _fmt({"total_items": data.get("total_items", 0), "templates": templates})


@mcp.tool()
async def get_template(template_id: int) -> str:
    """Get a template's details and HTML content."""
    mc = get_client()
    t = await mc.get(f"/templates/{template_id}")
    return _fmt({
        "id": t.get("id", ""),
        "name": t.get("name", ""),
        "type": t.get("type", ""),
        "active": t.get("active", False),
        "html": t.get("html", "")[:5000],
        "created_at": t.get("date_created", ""),
        "edited_at": t.get("date_edited", ""),
    })


# ══════════════════════════════════════════════════════════════════════
# AUTOMATIONS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_automations(count: int = 20, offset: int = 0) -> str:
    """List classic automations with status and stats."""
    mc = get_client()
    data = await mc.get(
        "/automations",
        params={"count": min(count, 100), "offset": offset},
    )
    automations = []
    for a in data.get("automations", []):
        automations.append({
            "id": a.get("id", ""),
            "title": a.get("settings", {}).get("title", ""),
            "status": a.get("status", ""),
            "emails_sent": a.get("emails_sent", 0),
            "list_id": a.get("recipients", {}).get("list_id", ""),
            "start_time": a.get("start_time", ""),
            "created_at": a.get("create_time", ""),
        })
    return _fmt({
        "total_items": data.get("total_items", 0),
        "automations": automations,
    })


@mcp.tool()
async def pause_automation(workflow_id: str) -> str:
    """Pause all emails in a classic automation workflow."""
    mc = get_client()
    await mc.post(f"/automations/{workflow_id}/actions/pause-all-emails")
    return _fmt({"workflow_id": workflow_id, "message": "Automation paused."})


@mcp.tool()
async def start_automation(workflow_id: str) -> str:
    """Start all emails in a classic automation workflow."""
    mc = get_client()
    await mc.post(f"/automations/{workflow_id}/actions/start-all-emails")
    return _fmt({"workflow_id": workflow_id, "message": "Automation started."})


# ══════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════


def main() -> None:
    standby_port = os.environ.get("ACTOR_STANDBY_PORT")
    if standby_port:
        # Running on Apify — use Streamable HTTP transport
        os.environ.setdefault("FASTMCP_HOST", "0.0.0.0")
        os.environ.setdefault("FASTMCP_PORT", standby_port)
        os.environ.setdefault("FASTMCP_STREAMABLE_HTTP_PATH", "/mcp")
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
