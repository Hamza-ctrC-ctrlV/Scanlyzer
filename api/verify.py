import secrets
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from ai_engine.supabase_client import ensure_user_profile, _get_supabase_admin_client


def _supabase():
    return _get_supabase_admin_client()


def create_verification(user_id, domain):
    """
    Generates a random token and stores it in Supabase.
    Called when the user submits a domain they want to verify.
    Returns the token so the Flask route can send it to the frontend.
    """

    # Generate a secure random 64-character hex token
    # e.g. "a3f9bc2d1e4f..." — impossible to guess
    token = secrets.token_hex(32)

    # Token expires in 24 hours from now (always in UTC)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    # Ensure the user exists in the Supabase users table before inserting
    # the verification row, which references users.id via a foreign key.
    ensure_user_profile(user_id=user_id)

    # Store the verification attempt in Supabase
    _supabase().table("domain_verifications").insert({
        "user_id":    user_id,
        "domain":     domain,
        "token":      token,
        "verified":   False,
        "expires_at": expires_at.isoformat()
    }).execute()

    return token


def check_html_file(domain, expected_token):
    """
    Verifies ownership by fetching a root-level HTML file from the target domain.
    The user must place a file at /scanner-verify.html containing the exact
    verification text. Returns True if verified, False otherwise.
    """

    expected_value = f"scanner-verify={expected_token}"
    urls = [
        f"https://{domain}/scanner-verify.html",
        f"http://{domain}/scanner-verify.html",
    ]

    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue
            body = response.text.strip()
            if expected_value in body:
                return True
        except requests.RequestException:
            continue

    return False


def check_meta_tag(domain, expected_token):
    """
    Verifies ownership by checking the homepage for a
    <meta name="scanlyzer-verify" content="scanner-verify=..."> tag.
    """

    expected_value = f"scanner-verify={expected_token}"

    for scheme in ["https", "http"]:
        try:
            url = f"{scheme}://{domain}"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            tag = soup.find("meta", {"name": "scanlyzer-verify"})
            if tag and tag.get("content", "").strip() == expected_value:
                return True
        except requests.RequestException:
            continue

    return False