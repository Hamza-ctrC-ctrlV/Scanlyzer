"""
Configuration constants for the vulnerability scanner application.

This module centralizes all hardcoded values including rate limits,
API settings, crawler parameters, and other configuration values.
"""

# ==============================================================================
# RATE LIMITING CONFIGURATION
# ==============================================================================

# Flask app global rate limits
DEFAULT_DAILY_LIMIT = 200  # Scans per day
DEFAULT_HOURLY_LIMIT = 50  # Scans per hour

# Route-specific rate limits
SCAN_ROUTE_RATE_LIMIT = "10 per minute"  # /scan endpoint
SAVE_SCAN_RATE_LIMIT = "20 per minute"  # /save-scan endpoint
REPORT_ROUTE_RATE_LIMIT = "30 per minute"  # /report endpoint
DELETE_SCAN_RATE_LIMIT = "50 per minute"  # /delete-scan endpoint
AUTH_ROUTE_RATE_LIMIT = "5 per minute"  # Auth endpoints

# Gemini API rate limiting
GEMINI_FREE_TIER_RATE_LIMIT = 14  # Requests per minute
RATE_LIMIT_WINDOW_SECONDS = 60

# ==============================================================================
# API CONFIGURATION
# ==============================================================================

GEMINI_MODEL_ID = "models/gemma-4-31b-it"
GROQ_MODEL_ID = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_KEYS_LINK = "https://console.groq.com/keys"
API_REQUEST_TIMEOUT = 30  # seconds
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff multiplier

# ==============================================================================
# CRAWLER CONFIGURATION
# ==============================================================================

DEFAULT_MAX_PAGES = 50
DEFAULT_MAX_DEPTH = 2
CRAWL_DELAY_SECONDS = 0.5  # Delay between requests to respect server load
ROBOTS_TXT_TIMEOUT = 5  # seconds

# Field types to skip during scanning
INJECTABLE_SKIP_TYPES = {
    "hidden",
    "submit",
    "button",
    "reset",
    "image",
    "file",
    "csrf_token",
}

# ==============================================================================
# DATABASE/STORAGE CONFIGURATION
# ==============================================================================

SCAN_ID_PREFIX = "scan_"
REPORTS_BUCKET_NAME = "reports"
STORAGE_RETRY_ATTEMPTS = 2

# ==============================================================================
# VULNERABILITY CLASSIFICATION
# ==============================================================================

# Default fallback response for vulnerability assessment
DEFAULT_VULNERABILITY_ASSESSMENT = {
    "type": "unknown",
    "severity": "medium",
    "description": "Could not automatically classify vulnerability. Manual review recommended.",
    "recommendation": "Review the vulnerable code pattern and apply input validation/escaping.",
}

# ==============================================================================
# PROMPT CONFIGURATION
# ==============================================================================

# Prompt prefixes for AI model
PROMPT_SYSTEM_CONTEXT_PREFIX = "You are a security expert analyzing web application vulnerabilities."
PROMPT_ASSESSMENT_PREFIX = "Classify this vulnerability and provide recommendations:"
PROMPT_FIX_PREFIX = "Generate a secure code fix for this vulnerability:"

# ==============================================================================
# ERROR MESSAGES
# ==============================================================================

ERROR_INVALID_API_KEY = "Invalid Gemini API key format"
ERROR_RATE_LIMIT_EXCEEDED = "Rate limit exceeded. Please try again later."
ERROR_API_TIMEOUT = "API request timeout. Please try again."
ERROR_INVALID_JSON_RESPONSE = "Failed to parse AI response as JSON"
ERROR_DATABASE_CONNECTION = "Database connection error"
ERROR_STORAGE_UPLOAD = "Failed to upload report to storage"
ERROR_UNAUTHORIZED = "Unauthorized. Please log in."
ERROR_SCAN_NOT_FOUND = "Scan not found"
ERROR_PERMISSION_DENIED = "Permission denied"

# ==============================================================================
# SUCCESS MESSAGES
# ==============================================================================

SUCCESS_SCAN_SAVED = "Scan saved successfully"
SUCCESS_SCAN_DELETED = "Scan deleted successfully"
SUCCESS_REPORT_GENERATED = "Report generated successfully"

# ==============================================================================
# AUTHENTICATION
# ==============================================================================

TOKEN_EXPIRATION_HOURS = 24
SESSION_TIMEOUT_MINUTES = 30

# ==============================================================================
# LOGGING
# ==============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# API Key masking for logs
API_KEY_VISIBLE_CHARS = 4  # Show first 4 characters only
