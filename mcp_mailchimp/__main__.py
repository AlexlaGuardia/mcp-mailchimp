"""Allow running as: python -m mcp_mailchimp"""

import os


def _load_apify_input() -> None:
    """Load API key from Apify actor input when running on the platform."""
    token = os.environ.get("APIFY_TOKEN", "")
    store_id = os.environ.get("APIFY_DEFAULT_KEY_VALUE_STORE_ID", "")
    if not (token and store_id):
        return

    import httpx

    try:
        resp = httpx.get(
            f"https://api.apify.com/v2/key-value-stores/{store_id}/records/INPUT",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            api_key = data.get("mailchimpApiKey", "")
            if api_key:
                os.environ["MAILCHIMP_API_KEY"] = api_key
    except Exception:
        pass


if os.environ.get("ACTOR_STANDBY_PORT"):
    _load_apify_input()

from mcp_mailchimp.server import main

main()
