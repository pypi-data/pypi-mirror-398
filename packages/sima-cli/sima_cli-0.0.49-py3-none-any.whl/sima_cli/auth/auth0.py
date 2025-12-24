#!/usr/bin/env python3
"""
Minimal Auth0 Device Authorization Flow client with persistent tokens.

- Works in both headless and interactive (browser-available) environments.
- Stores tokens at ~/.sima-cli/tokens.json and auto-refreshes if expired.
- Welcomes the user after successful authentication (using ID token claims).
"""

import os
import sys
import time
import json
import base64
import requests
import webbrowser
import click
from typing import Dict, Optional

from sima_cli.utils.config_loader import load_resource_config

# ─────────────────────────────────────────────
# Global constants
# ─────────────────────────────────────────────
HOME_DIR = os.path.expanduser("~/.sima-cli")
TOKEN_FILE = os.path.join(HOME_DIR, ".tokens.json")

# ─────────────────────────────────────────────
# Configuration loader
# ─────────────────────────────────────────────
def get_auth_config(cfg=None):
    """
    Load and return authentication configuration based on environment.

    If USE_STAGING_DEV_PORTAL is set to true (1/true/yes),
    loads 'auth-dev' under 'public', otherwise 'auth-prod'.
    """
    if cfg is None:
        cfg = load_resource_config()

    use_staging = os.getenv("USE_STAGING_DEV_PORTAL", "false").lower() in ("1", "true", "yes")
    auth_cfg = cfg.get("public", {}).get("auth-dev" if use_staging else "auth-prod", {})

    auth0_domain = auth_cfg.get("domain")
    client_id = auth_cfg.get("client-id")
    audience = auth_cfg.get("audience")
    scopes = auth_cfg.get("scopes")

    device_code_url = f"https://{auth0_domain}/oauth/device/code" if auth0_domain else None
    token_url = f"https://{auth0_domain}/oauth/token" if auth0_domain else None

    return {
        "AUTH0_DOMAIN": auth0_domain,
        "CLIENT_ID": client_id,
        "AUDIENCE": audience,
        "SCOPES": scopes,
        "DEVICE_CODE_URL": device_code_url,
        "TOKEN_URL": token_url,
    }


# ─────────────────────────────────────────────
# Token persistence utilities
# ─────────────────────────────────────────────
def save_tokens(tokens: dict):
    """Save tokens to ~/.sima-cli/.tokens.json."""
    os.makedirs(HOME_DIR, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)


def load_tokens() -> Optional[Dict]:
    """Load tokens if available."""
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load tokens: {e}")
        return None


def is_token_valid(tokens: dict) -> bool:
    """Check if access token still valid based on expires_in field."""
    if not tokens:
        return False
    issued_at = tokens.get("timestamp", 0)
    expires_in = tokens.get("expires_in", 0)
    return (time.time() - issued_at) < (expires_in - 60)  # 1-min safety margin


def refresh_access_token(auth_cfg, refresh_token):
    """Attempt to refresh access token using the refresh token."""
    data = {
        "grant_type": "refresh_token",
        "client_id": auth_cfg["CLIENT_ID"],
        "refresh_token": refresh_token,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    resp = requests.post(auth_cfg["TOKEN_URL"], data=data, headers=headers)
    if resp.status_code == 200:
        print("🔄 Access token refreshed successfully.")
        new_tokens = resp.json()
        if "refresh_token" not in new_tokens:
            new_tokens["refresh_token"] = refresh_token
        new_tokens["timestamp"] = int(time.time())
        save_tokens(new_tokens)
        return new_tokens
    else:
        print(f"❌ Failed to refresh token: {resp.text}")
        return None


# ─────────────────────────────────────────────
# Auth0 device flow
# ─────────────────────────────────────────────
def is_browser_available():
    """Detect whether the environment can open a browser.

    Returns False if the HEADLESS_CLIENT environment variable is set to a truthy value.
    """
    # Explicitly disable browser if headless mode is requested
    if os.getenv("HEADLESS_CLIENT", "false").lower() in ("1", "true", "yes"):
        return False

    try:
        webbrowser.get()
        return True
    except webbrowser.Error:
        return False

def request_device_code(auth_cfg):
    """Step 1: Request device code from Auth0."""
    data = {
        "client_id": auth_cfg["CLIENT_ID"],
        "scope": auth_cfg["SCOPES"],
        "audience": auth_cfg["AUDIENCE"],
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    resp = requests.post(auth_cfg["DEVICE_CODE_URL"], data=data, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    return resp.json()


def poll_for_token(auth_cfg, device_code, interval):
    """Step 2: Poll for user authorization."""
    print(f"⏳ Waiting for user authorization... polling every {interval} seconds.")
    while True:
        time.sleep(interval)
        resp = requests.post(
            auth_cfg["TOKEN_URL"],
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_code,
                "client_id": auth_cfg["CLIENT_ID"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if resp.status_code == 200:
            print("✅ sima-cli authorized!")
            tokens = resp.json()
            tokens["timestamp"] = int(time.time())
            save_tokens(tokens)
            return tokens

        data = resp.json()
        error = data.get("error")
        if error == "authorization_pending":
            continue
        elif error == "slow_down":
            interval += 5
        elif error == "expired_token":
            print("❌ Device code expired — restart the flow.")
            sys.exit(1)
        else:
            print(f"❌ Error: {resp.text}")
            sys.exit(1)


def login_auth0(auth_cfg):
    """Perform Auth0 Device Authorization flow."""
    data = request_device_code(auth_cfg)

    verify_url = data["verification_uri"]
    user_code = data["user_code"]
    verify_complete = data.get("verification_uri_complete") or f"{verify_url}?user_code={user_code}"
    expires_in = data["expires_in"] // 60

    # Style the clickable or highlighted URL
    highlighted_url = click.style(verify_complete, fg="cyan", bold=True)
    highlighted_code = click.style(user_code, fg="yellow", bold=True)

    print(f"⏰ Link expires in {expires_in} minutes.\n")

    # Auto-open browser if possible
    if is_browser_available() and verify_complete:
        print(f"🌐 Opening browser for login → {highlighted_url}")
        webbrowser.open(verify_complete)
    else:
        print("🔐 Browser not available — open manually:")
        print(f"   👉 {highlighted_url}")
        print(f"   🪄  Code: {highlighted_code}")

    return poll_for_token(auth_cfg, data["device_code"], data["interval"])

# ─────────────────────────────────────────────
# Decode ID token for user info
# ─────────────────────────────────────────────
def decode_jwt_payload(id_token: str) -> dict:
    """Decode the middle (payload) section of a JWT without verifying signature."""
    try:
        parts = id_token.split(".")
        if len(parts) != 3:
            return {}
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        decoded = base64.urlsafe_b64decode(payload_b64)
        return json.loads(decoded)
    except Exception:
        return {}


def print_welcome_message(tokens: dict):
    """Print a friendly, colorful welcome message using click styling."""
    id_token = tokens.get("id_token")
    if not id_token:
        return

    claims = decode_jwt_payload(id_token)
    name = claims.get("name") or claims.get("nickname") or claims.get("email") or "developer"

    # Styled parts
    styled_name = click.style(name, fg="yellow", bold=True)
    portal_name = click.style("SiMa Developer Portal", fg="cyan", bold=True)
    emoji = click.style("🎉", fg="magenta", bold=True)

    print("\n" + click.style("═" * 60, fg="bright_black"))
    print(f"{emoji}  Welcome back, {styled_name}!  {emoji}")
    print(f"    You are now signed in to the {portal_name}.")
    print(click.style("═" * 60, fg="bright_black") + "\n")

# ─────────────────────────────────────────────
# Unified token access
# ─────────────────────────────────────────────
def get_or_refresh_tokens():
    """Get a valid access token; refresh or reauthenticate if needed."""
    auth_cfg = get_auth_config()
    tokens = load_tokens()

    if tokens and is_token_valid(tokens):
        return tokens

    if tokens and tokens.get("refresh_token"):
        refreshed = refresh_access_token(auth_cfg, tokens["refresh_token"])
        if refreshed:
            print_welcome_message(refreshed)
            return refreshed
        print("⚠️ Refresh failed, falling back to new login.")

    new_tokens = login_auth0(auth_cfg)
    print_welcome_message(new_tokens)
    return new_tokens

def get_cached_access_token():
    tokens = load_tokens()
    if tokens:
        return tokens.get('access_token')
    
    return None

# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    try:
        tokens = get_or_refresh_tokens()
        print("\n🎟️ Tokens ready for use:")
        print(json.dumps(tokens, indent=2)[:500])  # truncated for safety
    except KeyboardInterrupt:
        print("\n🛑 Aborted by user.")
