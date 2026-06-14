from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from .verify import create_verification, check_html_file, check_meta_tag
from ai_engine.supabase_client import _get_supabase_admin_client
from .utils import extract_domain
import functools

# Blueprint — register this in your main app.py  with:
# from routes.verify_routes import verify_bp
# app.register_blueprint(verify_bp)
verify_bp = Blueprint("verify", __name__)


from api.routes import require_auth


@verify_bp.route("/verify/start", methods=["POST"])
@require_auth
def start_verification():
    """
    Called when the user submits a domain they want to verify.
    Generates a token and returns the verification file details for the UI.

    Expects JSON body: { "url": "https://example.com" }
    Returns: { "domain": "...", "file_url": "...", "file_contents": "..." }
    """
    data = request.get_json()
    raw_url = data.get("url", "")
    domain = extract_domain(raw_url)

    if not domain:
        return jsonify({"error": "Invalid URL provided"}), 400

    # Always get user_id from the session — never trust the request body
    user_id = request.auth_user.get("user_id")

    # Check for existing verification records to avoid unique constraint errors
    supabase = _get_supabase_admin_client()
    existing = supabase.table("domain_verifications").select("verified").eq("user_id", user_id).eq("domain", domain).execute()
    
    if existing.data:
        if existing.data[0].get("verified"):
            return jsonify({"error": f"{domain} est déjà vérifié."}), 400
        else:
            # Delete the pending verification so we can generate a fresh one
            supabase.table("domain_verifications").delete().eq("user_id", user_id).eq("domain", domain).execute()

    # Generate fresh token and store in Supabase
    token = create_verification(user_id, domain)

    # Return everything the frontend needs to show the verification instructions
    return jsonify({
        "domain":        domain,
        "file_url":      f"https://{domain}/scanner-verify.html",
        "file_contents": f"scanner-verify={token}",
        "meta_tag":     f"<meta name=\"scanlyzer-verify\" content=\"scanner-verify={token}\">"
    })


@verify_bp.route("/verify/check", methods=["POST"])
@require_auth
def check_verification():
    """
    Called when the user clicks "Check Now".
    Fetches the verification file and marks the domain as verified if found.

    Expects JSON body: { "domain": "example.com" }
    Returns: { "verified": true/false, "message": "..." }
    """
    data = request.get_json()
    domain = data.get("domain", "")
    user_id = request.auth_user.get("user_id")

    if not domain:
        return jsonify({"error": "Domain is required"}), 400

    # Look up the pending verification row in Supabase
    supabase = _get_supabase_admin_client()
    result = (
        supabase.table("domain_verifications")
        .select("*")
        .eq("user_id", user_id)
        .eq("domain", domain)
        .eq("verified", False)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        return jsonify({"error": "No pending verification found. Please start again."}), 404

    record = result.data[0]

    # Check if the token has expired (older than 24 hours)
    expiry = datetime.fromisoformat(record["expires_at"])
    if datetime.now(timezone.utc) > expiry:
        return jsonify({"error": "Token expired. Please start the verification again."}), 400

    # Do the actual ownership verification by checking either
    # the verification file or the homepage meta tag.
    verified_by_file = check_html_file(domain, record["token"])
    verified_by_meta = check_meta_tag(domain, record["token"])

    if not (verified_by_file or verified_by_meta):
        return jsonify({
            "verified": False,
            "message": "Verification not found yet. Create /scanner-verify.html or add the meta tag to your homepage and try again."
        })

    success_message = (
        "Domain verified via /scanner-verify.html file."
        if verified_by_file
        else "Domain verified via homepage meta tag."
    )

    # Domain verification succeeded — mark the domain as verified in Supabase
    supabase.table("domain_verifications").update({
        "verified":    True,
        "verified_at": datetime.now(timezone.utc).isoformat()
    }).eq("user_id", user_id).eq("domain", domain).execute()

    return jsonify({
        "verified": True,
        "message":  success_message
    })

@verify_bp.route("/verify/list", methods=["GET"])
@require_auth
def list_verifications():
    """
    Returns a list of all verified domains for the authenticated user.
    """
    user_id = request.auth_user.get("user_id")
    supabase = _get_supabase_admin_client()
    
    result = (
        supabase.table("domain_verifications")
        .select("domain, verified_at, created_at")
        .eq("user_id", user_id)
        .eq("verified", True)
        .order("created_at", desc=True)
        .execute()
    )
    
    # deduplicate domains (in case they verified the same domain twice somehow)
    seen = set()
    unique_domains = []
    for row in result.data:
        if row["domain"] not in seen:
            seen.add(row["domain"])
            unique_domains.append(row)
            
    return jsonify({"verifications": unique_domains})