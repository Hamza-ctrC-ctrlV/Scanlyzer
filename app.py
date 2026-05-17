"""
Flask Application Entry Point

Main application server with rate limiting and API routing.

Routes:
- /api/*: API endpoints (registered via blueprints)
- /auth/*: Authentication endpoints
- /reports/<path>: Serve static reports (rate limited)

Configuration:
- Global rate limits: 200 requests/day, 50 requests/hour per IP
- CORS restricted to allowed origins
- Debug mode controlled via FLASK_DEBUG env var
"""

import os
import logging
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config.constants import (
    DEFAULT_DAILY_LIMIT,
    DEFAULT_HOURLY_LIMIT,
    REPORT_ROUTE_RATE_LIMIT,
    LOG_FORMAT,
    LOG_LEVEL,
)
from utils.helpers import load_json_file

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
# Tell Flask it is behind a proxy so that request.remote_addr gets the real client IP.
# 1 ensures it trusts the immediate upstream proxy (e.g. Nginx, ALB) for these headers.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

# ------------------------------------------------------------------
# CORS — restrict to known origins; never use allow-all in production
# ------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:3000",     # React dev server
    "http://127.0.0.1:3000",
    "http://localhost:5000",     # Flask default
    "http://127.0.0.1:5000",
    f"http://localhost:{os.getenv('FLASK_PORT', '5000')}",
    f"http://127.0.0.1:{os.getenv('FLASK_PORT', '5000')}",
]
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# ------------------------------------------------------------------
# Register API blueprints
# ------------------------------------------------------------------
try:
    from api.routes import api_bp, limiter as api_limiter
    from api.auth import auth_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp)

    # Attach the per-blueprint limiter to the Flask app
    api_limiter.init_app(app)

    logger.info("API blueprints registered successfully")
except Exception as e:
    logger.warning(f"Could not register API blueprints: {e}")

# ------------------------------------------------------------------
# Global rate limiter
# ------------------------------------------------------------------
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[
        f"{DEFAULT_DAILY_LIMIT} per day",
        f"{DEFAULT_HOURLY_LIMIT} per hour",
    ],
    storage_uri="memory://",
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


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    logger.info(f"Starting Flask app on port {port} (debug={debug})")
    app.run(debug=debug, host="0.0.0.0", port=port)