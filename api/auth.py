"""
Authentication routes for user signup, login, and token verification.

All endpoints are rate-limited to prevent brute-force attacks.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from ai_engine.supabase_client import signup, login, verify_token, ensure_user_profile
from config.constants import AUTH_ROUTE_RATE_LIMIT

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
auth_limiter = Limiter(key_func=get_remote_address)


def _validate_email(email: str) -> bool:
    """Basic email format validation."""
    return bool(email and "@" in email and "." in email.split("@")[-1])


def _validate_password(password: str) -> str | None:
    """Validate password strength. Returns error message or None if valid."""
    if not password:
        return "Password is required"
    if len(password) < 6:
        return "Password must be at least 6 characters"
    return None


@auth_bp.route("/signup", methods=["POST"])
@auth_limiter.limit(AUTH_ROUTE_RATE_LIMIT)
def signup_route():
    """Register a new user with email and password."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    if not _validate_email(email):
        return jsonify({"success": False, "error": "Valid email is required"}), 400

    password_error = _validate_password(password)
    if password_error:
        return jsonify({"success": False, "error": password_error}), 400

    result = signup(email, password)
    if result["success"]:
        profile_result = ensure_user_profile(result["user_id"], email)
        if not profile_result["success"]:
            logger.warning(f"Profile creation failed for {email}: {profile_result.get('error')}")
            return jsonify(profile_result), 400

        return jsonify(result), 201
    else:
        return jsonify(result), 400


@auth_bp.route("/login", methods=["POST"])
@auth_limiter.limit(AUTH_ROUTE_RATE_LIMIT)
def login_route():
    """Login user with email and password."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password required"}), 400

    result = login(email, password)
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 401


@auth_bp.route("/verify", methods=["POST"])
@auth_limiter.limit("20 per minute")
def verify_route():
    """Verify JWT token and return user info."""
    data = request.get_json(silent=True) or {}
    token = data.get("token")

    if not token:
        return jsonify({"success": False, "error": "Token required"}), 400

    result = verify_token(token)
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 401
