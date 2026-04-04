"""MCP server for the Mailchimp Marketing API — 71 tools."""

import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_mailchimp.client import MailchimpClient, MailchimpError

mcp = FastMCP(
    "mcp-mailchimp",
    instructions=(
        "Production-grade MCP server for the Mailchimp Marketing API. "
        "71 tools for campaigns, audiences, members, tags, segments, "
        "templates, reports, automations, webhooks, merge fields, "
        "interest groups, landing pages, batch operations, e-commerce, "
        "A/B testing, member notes, file manager, and audience analytics."
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


@mcp.tool()
async def get_automation(workflow_id: str) -> str:
    """Get details for a specific automation including trigger, recipients, and stats."""
    mc = get_client()
    a = await mc.get(f"/automations/{workflow_id}")
    s = a.get("settings", {})
    r = a.get("recipients", {})
    t = a.get("trigger_settings", {})
    return _fmt({
        "id": a["id"],
        "title": s.get("title", ""),
        "status": a.get("status", ""),
        "emails_sent": a.get("emails_sent", 0),
        "list_id": r.get("list_id", ""),
        "list_name": r.get("list_name", ""),
        "trigger_type": t.get("workflow_type", ""),
        "start_time": a.get("start_time", ""),
        "created_at": a.get("create_time", ""),
    })


@mcp.tool()
async def list_automation_emails(workflow_id: str) -> str:
    """List all emails in an automation workflow with their status, delay, and position."""
    mc = get_client()
    data = await mc.get(f"/automations/{workflow_id}/emails")
    emails = []
    for e in data.get("emails", []):
        s = e.get("settings", {})
        emails.append({
            "id": e.get("id", ""),
            "position": e.get("position", 0),
            "status": e.get("status", ""),
            "subject_line": s.get("subject_line", ""),
            "from_name": s.get("from_name", ""),
            "delay": e.get("delay", {}),
            "emails_sent": e.get("emails_sent", 0),
            "send_time": e.get("send_time", ""),
        })
    return _fmt({"workflow_id": workflow_id, "total_emails": len(emails), "emails": emails})


# ══════════════════════════════════════════════════════════════════════
# CAMPAIGN OPS (delete, unschedule, cancel)
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def delete_campaign(campaign_id: str) -> str:
    """Permanently delete a campaign. Only works on campaigns that haven't been sent."""
    mc = get_client()
    await mc.delete(f"/campaigns/{campaign_id}")
    return _fmt({"campaign_id": campaign_id, "message": "Campaign deleted permanently."})


@mcp.tool()
async def unschedule_campaign(campaign_id: str) -> str:
    """Unschedule a scheduled campaign, returning it to 'save' status."""
    mc = get_client()
    await mc.post(f"/campaigns/{campaign_id}/actions/unschedule")
    return _fmt({"campaign_id": campaign_id, "message": "Campaign unscheduled."})


@mcp.tool()
async def cancel_campaign(campaign_id: str) -> str:
    """Cancel a campaign that is currently sending. Only works during the send window."""
    mc = get_client()
    await mc.post(f"/campaigns/{campaign_id}/actions/cancel-send")
    return _fmt({"campaign_id": campaign_id, "message": "Campaign send cancelled."})


# ══════════════════════════════════════════════════════════════════════
# AUDIENCE OPS (update, batch subscribe)
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def update_audience(
    list_id: str,
    name: str = "",
    from_email: str = "",
    from_name: str = "",
    permission_reminder: str = "",
) -> str:
    """Update audience settings. Only provide fields you want to change."""
    mc = get_client()
    body: dict[str, Any] = {}
    if name:
        body["name"] = name
    if permission_reminder:
        body["permission_reminder"] = permission_reminder
    defaults: dict[str, str] = {}
    if from_email:
        defaults["from_email"] = from_email
    if from_name:
        defaults["from_name"] = from_name
    if defaults:
        body["campaign_defaults"] = defaults
    if not body:
        return "No fields provided to update."
    a = await mc.patch(f"/lists/{list_id}", json=body)
    return _fmt({
        "id": a["id"],
        "name": a.get("name", ""),
        "message": "Audience updated.",
    })


@mcp.tool()
async def batch_subscribe_members(
    list_id: str,
    emails: str,
    status: str = "subscribed",
) -> str:
    """Batch subscribe multiple members at once. emails: comma-separated list (max 500)."""
    mc = get_client()
    members = []
    for email in emails.split(","):
        email = email.strip()
        if email:
            members.append({
                "email_address": email.lower(),
                "status": status,
            })
    if not members:
        return "No valid email addresses provided."
    data = await mc.post(f"/lists/{list_id}", json={
        "members": members[:500],
        "update_existing": False,
    })
    return _fmt({
        "new_members": data.get("new_members", 0) if isinstance(data.get("new_members"), int) else len(data.get("new_members", [])),
        "updated_members": data.get("updated_members", 0) if isinstance(data.get("updated_members"), int) else len(data.get("updated_members", [])),
        "error_count": data.get("error_count", 0),
        "errors": [e.get("email_address", "") for e in data.get("errors", [])[:10]],
        "message": "Batch subscribe complete.",
    })


# ══════════════════════════════════════════════════════════════════════
# MEMBER OPS (permanent delete)
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def delete_member_permanent(list_id: str, email: str) -> str:
    """Permanently delete a subscriber. Cannot be undone — the contact cannot be re-imported."""
    mc = get_client()
    h = mc.subscriber_hash(email)
    await mc.post(f"/lists/{list_id}/members/{h}/actions/delete-permanent")
    return _fmt({"email": email, "message": "Member permanently deleted."})


# ══════════════════════════════════════════════════════════════════════
# MERGE FIELDS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_merge_fields(list_id: str, count: int = 50) -> str:
    """List merge fields (custom fields) for an audience — FNAME, LNAME, plus any custom ones."""
    mc = get_client()
    data = await mc.get(
        f"/lists/{list_id}/merge-fields",
        params={"count": min(count, 100)},
    )
    fields = []
    for f in data.get("merge_fields", []):
        fields.append({
            "merge_id": f.get("merge_id", ""),
            "tag": f.get("tag", ""),
            "name": f.get("name", ""),
            "type": f.get("type", ""),
            "required": f.get("required", False),
            "default_value": f.get("default_value", ""),
            "public": f.get("public", False),
        })
    return _fmt({"total_items": data.get("total_items", 0), "merge_fields": fields})


@mcp.tool()
async def create_merge_field(
    list_id: str,
    name: str,
    field_type: str = "text",
    tag: str = "",
    required: bool = False,
    default_value: str = "",
) -> str:
    """Create a custom merge field. field_type: text, number, address, phone, date, url, dropdown, radio, birthday."""
    mc = get_client()
    body: dict[str, Any] = {
        "name": name,
        "type": field_type,
        "required": required,
    }
    if tag:
        body["tag"] = tag.upper()
    if default_value:
        body["default_value"] = default_value
    f = await mc.post(f"/lists/{list_id}/merge-fields", json=body)
    return _fmt({
        "merge_id": f.get("merge_id", ""),
        "tag": f.get("tag", ""),
        "name": f.get("name", ""),
        "type": f.get("type", ""),
        "message": "Merge field created.",
    })


# ══════════════════════════════════════════════════════════════════════
# INTEREST CATEGORIES & GROUPS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_interest_categories(list_id: str) -> str:
    """List interest categories (groups) for an audience — checkboxes, dropdowns, radio buttons, etc."""
    mc = get_client()
    data = await mc.get(f"/lists/{list_id}/interest-categories")
    categories = []
    for c in data.get("categories", []):
        categories.append({
            "id": c.get("id", ""),
            "title": c.get("title", ""),
            "type": c.get("type", ""),
            "display_order": c.get("display_order", 0),
        })
    return _fmt({"total_items": data.get("total_items", 0), "categories": categories})


@mcp.tool()
async def list_interests(list_id: str, category_id: str, count: int = 50) -> str:
    """List interests (individual options) within a category — the actual checkbox/radio items."""
    mc = get_client()
    data = await mc.get(
        f"/lists/{list_id}/interest-categories/{category_id}/interests",
        params={"count": min(count, 100)},
    )
    interests = []
    for i in data.get("interests", []):
        interests.append({
            "id": i.get("id", ""),
            "name": i.get("name", ""),
            "subscriber_count": i.get("subscriber_count", 0),
            "display_order": i.get("display_order", 0),
        })
    return _fmt({"total_items": data.get("total_items", 0), "interests": interests})


# ══════════════════════════════════════════════════════════════════════
# TEMPLATE OPS (create, delete)
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def create_template(name: str, html: str) -> str:
    """Create a new email template from HTML content."""
    mc = get_client()
    t = await mc.post("/templates", json={"name": name, "html": html})
    return _fmt({
        "id": t.get("id", ""),
        "name": t.get("name", ""),
        "type": t.get("type", ""),
        "message": "Template created.",
    })


@mcp.tool()
async def delete_template(template_id: int) -> str:
    """Delete a custom email template. Cannot delete Mailchimp's built-in templates."""
    mc = get_client()
    await mc.delete(f"/templates/{template_id}")
    return _fmt({"template_id": template_id, "message": "Template deleted."})


# ══════════════════════════════════════════════════════════════════════
# SEGMENT OPS (update, delete)
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def update_segment(
    list_id: str,
    segment_id: str,
    name: str = "",
    emails_to_add: str = "",
    emails_to_remove: str = "",
) -> str:
    """Update a static segment — rename or add/remove members. emails: comma-separated."""
    mc = get_client()
    body: dict[str, Any] = {}
    if name:
        body["name"] = name
    if emails_to_add:
        body["members_to_add"] = [e.strip() for e in emails_to_add.split(",") if e.strip()]
    if emails_to_remove:
        body["members_to_remove"] = [e.strip() for e in emails_to_remove.split(",") if e.strip()]
    if not body:
        return "Provide name, emails_to_add, or emails_to_remove."
    s = await mc.patch(f"/lists/{list_id}/segments/{segment_id}", json=body)
    return _fmt({
        "id": s.get("id", ""),
        "name": s.get("name", ""),
        "member_count": s.get("member_count", 0),
        "message": "Segment updated.",
    })


@mcp.tool()
async def delete_segment(list_id: str, segment_id: str) -> str:
    """Delete a segment from an audience."""
    mc = get_client()
    await mc.delete(f"/lists/{list_id}/segments/{segment_id}")
    return _fmt({"segment_id": segment_id, "message": "Segment deleted."})


# ══════════════════════════════════════════════════════════════════════
# WEBHOOKS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_webhooks(list_id: str) -> str:
    """List webhooks configured for an audience."""
    mc = get_client()
    data = await mc.get(f"/lists/{list_id}/webhooks")
    hooks = []
    for w in data.get("webhooks", []):
        hooks.append({
            "id": w.get("id", ""),
            "url": w.get("url", ""),
            "events": w.get("events", {}),
            "sources": w.get("sources", {}),
        })
    return _fmt({"total_items": len(hooks), "webhooks": hooks})


@mcp.tool()
async def create_webhook(
    list_id: str,
    url: str,
    subscribe: bool = True,
    unsubscribe: bool = True,
    profile: bool = True,
    cleaned: bool = True,
    campaign: bool = False,
) -> str:
    """Create a webhook for audience events. Configure which events trigger the callback."""
    mc = get_client()
    body = {
        "url": url,
        "events": {
            "subscribe": subscribe,
            "unsubscribe": unsubscribe,
            "profile": profile,
            "cleaned": cleaned,
            "campaign": campaign,
        },
        "sources": {"user": True, "admin": True, "api": True},
    }
    w = await mc.post(f"/lists/{list_id}/webhooks", json=body)
    return _fmt({
        "id": w.get("id", ""),
        "url": w.get("url", ""),
        "message": "Webhook created.",
    })


@mcp.tool()
async def delete_webhook(list_id: str, webhook_id: str) -> str:
    """Delete a webhook from an audience."""
    mc = get_client()
    await mc.delete(f"/lists/{list_id}/webhooks/{webhook_id}")
    return _fmt({"webhook_id": webhook_id, "message": "Webhook deleted."})


# ══════════════════════════════════════════════════════════════════════
# REPORTS (unsubscribes, sent-to)
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_unsubscribe_report(campaign_id: str, count: int = 20, offset: int = 0) -> str:
    """Get unsubscribe details for a campaign — who unsubscribed and why."""
    mc = get_client()
    data = await mc.get(
        f"/reports/{campaign_id}/unsubscribed",
        params={"count": min(count, 100), "offset": offset},
    )
    unsubs = []
    for u in data.get("unsubscribes", []):
        unsubs.append({
            "email": u.get("email_address", ""),
            "reason": u.get("reason", ""),
            "timestamp": u.get("timestamp", ""),
            "campaign_id": u.get("campaign_id", ""),
        })
    return _fmt({
        "campaign_id": campaign_id,
        "total_items": data.get("total_items", 0),
        "unsubscribes": unsubs,
    })


@mcp.tool()
async def get_sent_to_report(campaign_id: str, status: str = "", count: int = 20, offset: int = 0) -> str:
    """Get delivery details — which members received the email and their status (sent, hard, soft)."""
    mc = get_client()
    params: dict[str, Any] = {"count": min(count, 100), "offset": offset}
    if status:
        params["status"] = status
    data = await mc.get(f"/reports/{campaign_id}/sent-to", params=params)
    recipients = []
    for r in data.get("sent_to", []):
        recipients.append({
            "email": r.get("email_address", ""),
            "status": r.get("status", ""),
            "open_count": r.get("open_count", 0),
            "last_open": r.get("last_open", ""),
        })
    return _fmt({
        "campaign_id": campaign_id,
        "total_items": data.get("total_items", 0),
        "recipients": recipients,
    })


# ══════════════════════════════════════════════════════════════════════
# LANDING PAGES
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_landing_pages(count: int = 20) -> str:
    """List landing pages with their status, visits, and conversion stats."""
    mc = get_client()
    data = await mc.get("/landing-pages", params={"count": min(count, 100)})
    pages = []
    for p in data.get("landing_pages", []):
        pages.append({
            "id": p.get("id", ""),
            "name": p.get("name", ""),
            "title": p.get("title", ""),
            "status": p.get("status", ""),
            "url": p.get("url", ""),
            "list_id": p.get("list_id", ""),
            "visits": p.get("tracking", {}).get("visits", 0),
            "unique_visits": p.get("tracking", {}).get("unique_visits", 0),
            "subscribes": p.get("tracking", {}).get("subscribes", 0),
            "published_at": p.get("published_at", ""),
        })
    return _fmt({"total_items": len(pages), "landing_pages": pages})


@mcp.tool()
async def get_landing_page(page_id: str) -> str:
    """Get details for a specific landing page including tracking stats."""
    mc = get_client()
    p = await mc.get(f"/landing-pages/{page_id}")
    t = p.get("tracking", {})
    return _fmt({
        "id": p.get("id", ""),
        "name": p.get("name", ""),
        "title": p.get("title", ""),
        "status": p.get("status", ""),
        "url": p.get("url", ""),
        "list_id": p.get("list_id", ""),
        "visits": t.get("visits", 0),
        "unique_visits": t.get("unique_visits", 0),
        "subscribes": t.get("subscribes", 0),
        "clicks": t.get("clicks", 0),
        "published_at": p.get("published_at", ""),
        "created_at": p.get("created_at", ""),
        "updated_at": p.get("updated_at", ""),
    })


# ══════════════════════════════════════════════════════════════════════
# BATCH OPERATIONS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def create_batch_operation(operations: str) -> str:
    """Submit a batch of API operations. operations: JSON array of {method, path, body} objects. Max 500 ops."""
    mc = get_client()
    import json as _json
    try:
        ops = _json.loads(operations)
    except _json.JSONDecodeError:
        return "Invalid JSON. Provide an array of {method, path, body} objects."
    if not isinstance(ops, list):
        return "operations must be a JSON array."
    data = await mc.post("/batches", json={"operations": ops[:500]})
    return _fmt({
        "batch_id": data.get("id", ""),
        "status": data.get("status", ""),
        "total_operations": data.get("total_operations", 0),
        "submitted_at": data.get("submitted_at", ""),
        "message": "Batch submitted. Check status with the batch ID.",
    })


# ══════════════════════════════════════════════════════════════════════
# E-COMMERCE (stores, products, orders, carts, customers, promo codes)
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_ecommerce_stores(count: int = 20) -> str:
    """List connected e-commerce stores (Shopify, WooCommerce, etc.) with revenue stats."""
    mc = get_client()
    data = await mc.get("/ecommerce/stores", params={"count": min(count, 100)})
    stores = []
    for s in data.get("stores", []):
        stores.append({
            "id": s.get("id", ""),
            "name": s.get("name", ""),
            "platform": s.get("platform", ""),
            "domain": s.get("domain", ""),
            "list_id": s.get("list_id", ""),
            "currency_code": s.get("currency_code", ""),
            "money_format": s.get("money_format", ""),
            "is_syncing": s.get("is_syncing", False),
            "created_at": s.get("created_at", ""),
        })
    return _fmt({"total_items": data.get("total_items", 0), "stores": stores})


@mcp.tool()
async def list_store_products(store_id: str, count: int = 20, offset: int = 0) -> str:
    """List products in a connected e-commerce store."""
    mc = get_client()
    data = await mc.get(
        f"/ecommerce/stores/{store_id}/products",
        params={"count": min(count, 100), "offset": offset},
    )
    products = []
    for p in data.get("products", []):
        products.append({
            "id": p.get("id", ""),
            "title": p.get("title", ""),
            "handle": p.get("handle", ""),
            "url": p.get("url", ""),
            "type": p.get("type", ""),
            "vendor": p.get("vendor", ""),
            "image_url": p.get("image_url", ""),
            "variants": len(p.get("variants", [])),
            "published_at": p.get("published_at_foreign", ""),
        })
    return _fmt({"total_items": data.get("total_items", 0), "products": products})


@mcp.tool()
async def list_store_orders(
    store_id: str,
    count: int = 20,
    offset: int = 0,
    campaign_id: str = "",
) -> str:
    """List orders from a connected store. Optionally filter by campaign_id to see revenue attribution."""
    mc = get_client()
    params: dict[str, Any] = {"count": min(count, 100), "offset": offset}
    if campaign_id:
        params["campaign_id"] = campaign_id
    data = await mc.get(f"/ecommerce/stores/{store_id}/orders", params=params)
    orders = []
    for o in data.get("orders", []):
        orders.append({
            "id": o.get("id", ""),
            "customer": o.get("customer", {}).get("email_address", ""),
            "financial_status": o.get("financial_status", ""),
            "fulfillment_status": o.get("fulfillment_status", ""),
            "order_total": o.get("order_total", 0),
            "currency_code": o.get("currency_code", ""),
            "lines_count": len(o.get("lines", [])),
            "campaign_id": o.get("campaign_id", ""),
            "landing_site": o.get("landing_site", ""),
            "processed_at": o.get("processed_at_foreign", ""),
        })
    return _fmt({"total_items": data.get("total_items", 0), "orders": orders})


@mcp.tool()
async def get_ecommerce_customer(store_id: str, customer_id: str) -> str:
    """Get e-commerce customer details including order count and total spent."""
    mc = get_client()
    c = await mc.get(f"/ecommerce/stores/{store_id}/customers/{customer_id}")
    return _fmt({
        "id": c.get("id", ""),
        "email": c.get("email_address", ""),
        "first_name": c.get("first_name", ""),
        "last_name": c.get("last_name", ""),
        "opt_in_status": c.get("opt_in_status", False),
        "orders_count": c.get("orders_count", 0),
        "total_spent": c.get("total_spent", 0),
        "currency_code": c.get("currency_code", ""),
        "created_at": c.get("created_at", ""),
        "updated_at": c.get("updated_at", ""),
    })


@mcp.tool()
async def list_store_carts(store_id: str, count: int = 20) -> str:
    """List abandoned carts from a connected store — useful for abandoned cart recovery campaigns."""
    mc = get_client()
    data = await mc.get(
        f"/ecommerce/stores/{store_id}/carts",
        params={"count": min(count, 100)},
    )
    carts = []
    for c in data.get("carts", []):
        carts.append({
            "id": c.get("id", ""),
            "customer_email": c.get("customer", {}).get("email_address", ""),
            "order_total": c.get("order_total", 0),
            "currency_code": c.get("currency_code", ""),
            "lines_count": len(c.get("lines", [])),
            "checkout_url": c.get("checkout_url", ""),
            "created_at": c.get("created_at", ""),
            "updated_at": c.get("updated_at", ""),
        })
    return _fmt({"total_items": data.get("total_items", 0), "carts": carts})


@mcp.tool()
async def list_store_promo_codes(store_id: str, promo_rule_id: str, count: int = 20) -> str:
    """List promo codes for a specific promo rule in a connected store."""
    mc = get_client()
    data = await mc.get(
        f"/ecommerce/stores/{store_id}/promo-rules/{promo_rule_id}/promo-codes",
        params={"count": min(count, 100)},
    )
    codes = []
    for c in data.get("promo_codes", []):
        codes.append({
            "id": c.get("id", ""),
            "code": c.get("code", ""),
            "redemption_url": c.get("redemption_url", ""),
            "usage_count": c.get("usage_count", 0),
            "enabled": c.get("enabled", True),
            "created_at": c.get("created_at_foreign", ""),
            "updated_at": c.get("updated_at_foreign", ""),
        })
    return _fmt({"total_items": data.get("total_items", 0), "promo_codes": codes})


# ══════════════════════════════════════════════════════════════════════
# AUDIENCE ANALYTICS (growth, locations, email clients)
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_audience_growth(list_id: str, count: int = 12) -> str:
    """Get monthly audience growth history — subscribes, unsubscribes, and net change over time."""
    mc = get_client()
    data = await mc.get(
        f"/lists/{list_id}/growth-history",
        params={"count": min(count, 100), "sort_field": "month", "sort_dir": "DESC"},
    )
    history = []
    for h in data.get("history", []):
        history.append({
            "month": h.get("month", ""),
            "existing": h.get("existing", 0),
            "imports": h.get("imports", 0),
            "optins": h.get("optins", 0),
        })
    return _fmt({"list_id": list_id, "total_items": data.get("total_items", 0), "history": history})


@mcp.tool()
async def get_audience_locations(list_id: str, count: int = 20) -> str:
    """Get subscriber location breakdown by country/region — where your audience lives."""
    mc = get_client()
    data = await mc.get(
        f"/lists/{list_id}/locations",
        params={"count": min(count, 100)},
    )
    locations = []
    for loc in data.get("locations", []):
        locations.append({
            "country": loc.get("country", ""),
            "cc": loc.get("cc", ""),
            "percent": loc.get("percent", 0),
            "total": loc.get("total", 0),
        })
    return _fmt({"list_id": list_id, "locations": locations})


@mcp.tool()
async def get_email_client_stats(campaign_id: str) -> str:
    """Get email client usage for a campaign — Gmail, Apple Mail, Outlook breakdown."""
    mc = get_client()
    data = await mc.get(f"/reports/{campaign_id}/domain-performance")
    domains = []
    for d in data.get("domains", []):
        domains.append({
            "domain": d.get("domain", ""),
            "emails_sent": d.get("emails_sent", 0),
            "bounces": d.get("bounces", 0),
            "opens": d.get("opens", 0),
            "clicks": d.get("clicks", 0),
            "unsubs": d.get("unsubs", 0),
            "delivered": d.get("delivered", 0),
            "emails_pct": d.get("emails_pct", 0),
            "bounces_pct": d.get("bounces_pct", 0),
            "opens_pct": d.get("opens_pct", 0),
            "clicks_pct": d.get("clicks_pct", 0),
        })
    return _fmt({
        "campaign_id": campaign_id,
        "total_domains": len(domains),
        "domains": domains,
    })


# ══════════════════════════════════════════════════════════════════════
# A/B TESTING (variate campaign results)
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_ab_test_results(campaign_id: str) -> str:
    """Get A/B test (variate) results for a campaign — which combination won and performance of each."""
    mc = get_client()
    c = await mc.get(f"/campaigns/{campaign_id}")
    v = c.get("variate_settings", {})
    if not v:
        return _fmt({"error": "This campaign is not an A/B test (variate) campaign."})
    # Get the report for full performance data
    r = await mc.get(f"/reports/{campaign_id}")
    return _fmt({
        "campaign_id": campaign_id,
        "test_type": v.get("test_size", ""),
        "winning_criteria": v.get("winner_criteria", ""),
        "wait_time": v.get("wait_time", 0),
        "winner_campaign_id": v.get("winning_campaign_id", ""),
        "winner_combination_id": v.get("winning_combination_id", ""),
        "combinations": v.get("combinations", []),
        "subject_lines": v.get("subject_lines", []),
        "from_names": v.get("from_names", []),
        "send_times": v.get("send_times", []),
        "report": {
            "emails_sent": r.get("emails_sent", 0),
            "opens": r.get("opens", {}).get("unique_opens", 0),
            "open_rate": r.get("opens", {}).get("open_rate", 0),
            "clicks": r.get("clicks", {}).get("unique_clicks", 0),
            "click_rate": r.get("clicks", {}).get("click_rate", 0),
        },
    })


# ══════════════════════════════════════════════════════════════════════
# MEMBER NOTES
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_member_notes(list_id: str, email: str, count: int = 20) -> str:
    """List notes on a subscriber — internal CRM-style notes attached to a contact."""
    mc = get_client()
    h = mc.subscriber_hash(email)
    data = await mc.get(
        f"/lists/{list_id}/members/{h}/notes",
        params={"count": min(count, 100)},
    )
    notes = []
    for n in data.get("notes", []):
        notes.append({
            "id": n.get("note_id", ""),
            "note": n.get("note", ""),
            "created_at": n.get("created_at", ""),
            "created_by": n.get("created_by", ""),
            "updated_at": n.get("updated_at", ""),
        })
    return _fmt({"email": email, "total_items": data.get("total_items", 0), "notes": notes})


@mcp.tool()
async def add_member_note(list_id: str, email: str, note: str) -> str:
    """Add a note to a subscriber — useful for CRM-style contact management."""
    mc = get_client()
    h = mc.subscriber_hash(email)
    n = await mc.post(
        f"/lists/{list_id}/members/{h}/notes",
        json={"note": note},
    )
    return _fmt({
        "note_id": n.get("note_id", ""),
        "email": email,
        "note": n.get("note", ""),
        "created_at": n.get("created_at", ""),
        "message": "Note added.",
    })


# ══════════════════════════════════════════════════════════════════════
# FILE MANAGER
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_files(count: int = 20, offset: int = 0, file_type: str = "") -> str:
    """List files in the Mailchimp file manager. Filter by file_type: image, file."""
    mc = get_client()
    params: dict[str, Any] = {"count": min(count, 100), "offset": offset}
    if file_type:
        params["type"] = file_type
    data = await mc.get("/file-manager/files", params=params)
    files = []
    for f in data.get("files", []):
        files.append({
            "id": f.get("id", ""),
            "name": f.get("name", ""),
            "type": f.get("type", ""),
            "size": f.get("size", 0),
            "full_size_url": f.get("full_size_url", ""),
            "thumbnail_url": f.get("thumbnail_url", ""),
            "folder_id": f.get("folder_id", 0),
            "created_at": f.get("created_at", ""),
        })
    return _fmt({"total_items": data.get("total_items", 0), "files": files})


@mcp.tool()
async def upload_file(name: str, file_data_base64: str, folder_id: int = 0) -> str:
    """Upload a file to the Mailchimp file manager. file_data_base64: base64-encoded file content."""
    mc = get_client()
    body: dict[str, Any] = {
        "name": name,
        "file_data": file_data_base64,
    }
    if folder_id:
        body["folder_id"] = folder_id
    f = await mc.post("/file-manager/files", json=body)
    return _fmt({
        "id": f.get("id", ""),
        "name": f.get("name", ""),
        "type": f.get("type", ""),
        "full_size_url": f.get("full_size_url", ""),
        "size": f.get("size", 0),
        "message": "File uploaded.",
    })


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
