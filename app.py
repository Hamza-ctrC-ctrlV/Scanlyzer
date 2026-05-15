"""
Flask Application Entry Point

Main application server with static file serving and rate limiting.

Routes:
- /: Redirect to login page
- /frontend/<path>: Serve frontend HTML files
- /reports/<path>: Serve static reports (rate limited)
- /api/*: API endpoints (registered via blueprints)

Configuration:
- Global rate limits: 200 requests/day, 50 requests/hour per IP
- CORS enabled for cross-origin requests
- Static folder serves current directory for compatibility
"""

import os
import logging
from flask import Flask, jsonify, send_from_directory, redirect
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config.constants import (
    DEFAULT_DAILY_LIMIT,
    DEFAULT_HOURLY_LIMIT,
    REPORT_ROUTE_RATE_LIMIT,
)
from utils.helpers import load_json_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=".")
CORS(app)

# Register API blueprints
try:
    from api.routes import api_bp
    from api.auth import auth_bp
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp)
    logger.info("API blueprints registered successfully")
except Exception as e:
    logger.warning(f"Could not register API blueprints: {e}")
    # Blueprints optional during tests or when api package missing

# Initialize rate limiter with global limits
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[
        f"{DEFAULT_DAILY_LIMIT} per day",
        f"{DEFAULT_HOURLY_LIMIT} per hour"
    ],
    storage_uri="memory://"
)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


@app.route("/reports/<path:filename>")
@limiter.limit(REPORT_ROUTE_RATE_LIMIT)
def report_file(filename: str):
    """
    Serve static report files with rate limiting.
    
    Args:
        filename (str): Relative path within reports directory
        
    Returns:
        File download or 404 if not found
    """
    logger.info(f"Serving report file: {filename}")
    return send_from_directory(REPORTS_DIR, filename)


@app.route("/")
def index():
    """
    Root route - redirects to login page.
    
    Authentication is handled in frontend with token-based auth.
    """
    logger.debug("Redirecting to login page")
    return redirect("/frontend/login.html")


@app.route("/frontend/<path:filename>")
def frontend_file(filename: str):
    """
    Serve frontend HTML and assets.
    
    Args:
        filename (str): Relative path within frontend directory
        
    Returns:
        Static file or 404 if not found
    """
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    logger.debug(f"Serving frontend file: {filename}")
    return send_from_directory(frontend_dir, filename)


@app.route("/api/report")
@limiter.limit(REPORT_ROUTE_RATE_LIMIT)
def get_report():
    """
    Get latest vulnerability report.
    
    Returns:
        JSON: Complete patches/vulnerabilities report
        404: If report not found
    """
    logger.info("Fetching latest report")
    patches = load_json_file(os.path.join(REPORTS_DIR, "patches.json"))

    if not patches:
        logger.warning("patches.json not found")
        return jsonify({"error": "patches.json not found in reports/"}), 404

    return jsonify(patches)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(debug=True, host="0.0.0.0", port=port)