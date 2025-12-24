import requests
import logging
import socket
from typing import Optional, Tuple

def exchange_identity_token(
    identity_token: str,
    exchange_url: str,
    expires_in: int = 604800,
    scope: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Exchange an identity token for a short-lived access token.

    Args:
        identity_token (str): Long-lived identity token.
        exchange_url (str): Artifactory /api/security/token endpoint.
        expires_in (int): Access token lifetime in seconds (default: 7 days).
        scope (Optional[str]): Optional scope string (e.g. 'member-of-groups:readers').

    Returns:
        Tuple: (access_token, username) if successful, or (None, None) on failure.
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {identity_token}"  # Assuming token is passed in header
    }
    data = {
        "grant_type": "client_credentials",  # Adjust based on Artifactory's requirements
        "expires_in": str(expires_in)
    }
    if scope:
        data["scope"] = scope

    try:
        response = requests.post(exchange_url, headers=headers, data=data)
        response.raise_for_status()
        result = response.json()
        access_token = result.get("access_token")
        username = result.get("username") or result.get("sub")
        return access_token, username
    except requests.RequestException as e:
        logging.error(f"Token exchange failed: {e}")
        return None, None

def validate_token(token: str, validate_url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a token by calling a lightweight Artifactory-protected endpoint.

    Args:
        token (str): Access token to validate.
        validate_url (str): Endpoint such as /api/security/users/$self.

    Returns:
        Tuple: (True, username) if valid, or (False, None) if invalid or unauthorized.
    """
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(validate_url, headers=headers)
        response.raise_for_status()
        data = response.json() if "application/json" in response.headers.get("Content-Type", "") else {}
        return True, data.get("name")  # Assumes /api/security/users/$self
    except requests.RequestException as e:
        logging.error(f"Token validation failed: {e}")
        return False, None


def check_artifactory_reachability(host="artifacts.eng.sima.ai", port=443, timeout=3) -> bool:
    """
    Probe whether the SiMa Artifactory server is reachable.
    Returns True if reachable, False otherwise.
    """
    try:
        socket.setdefaulttimeout(timeout)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False
