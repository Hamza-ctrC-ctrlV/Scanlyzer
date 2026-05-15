"""
Authentication routes for user signup, login, logout
"""
from flask import Blueprint, request, jsonify
from ai_engine.supabase_client import signup, login, verify_token, ensure_user_profile

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/signup", methods=["POST"])
def signup_route():
    """Register a new user"""
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password required"}), 400

    result = signup(email, password)
    if result["success"]:
        profile_result = ensure_user_profile(result["user_id"], email)
        if not profile_result["success"]:
            return jsonify(profile_result), 400
        
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@auth_bp.route("/login", methods=["POST"])
def login_route():
    """Login user"""
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password required"}), 400

    result = login(email, password)
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 401


@auth_bp.route("/verify", methods=["POST"])
def verify_route():
    """Verify JWT token"""
    data = request.get_json(silent=True) or {}
    token = data.get("token")

    if not token:
        return jsonify({"success": False, "error": "Token required"}), 400

    result = verify_token(token)
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 401
