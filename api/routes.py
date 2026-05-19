"""
API Routes Module - Main Endpoint Handlers

RESTful endpoints for vulnerability scanning, report management, and authentication.

Endpoints:
- POST /scan: Run crawler + analysis on target URL
- GET /scans: List user's saved scans
- GET /report: Retrieve specific scan report
- DELETE /delete-scan: Remove scan from database
- GET /health: Health check endpoint

All endpoints include rate limiting and error handling.
"""

import logging
from typing import Dict, Any
from flask import Blueprint, request, jsonify, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from urllib.parse import urlparse, parse_qs
import json as json_lib
import time
import os
import uuid
import threading
from functools import wraps

from scanner.crawler import scan_forms
from scanner.active_scanner import active_scan
from scanner.exporter import build_vulnerabilities_report
from ai_engine.patch_generator import PatchGenerator
from ai_engine.ai_client import get_ai_client
from config.constants import (
    SCAN_ROUTE_RATE_LIMIT,
    SAVE_SCAN_RATE_LIMIT,
    REPORT_ROUTE_RATE_LIMIT,
    DELETE_SCAN_RATE_LIMIT,
)
from utils.helpers import standardize_error_response, compute_scan_stats, EMPTY_STATS
from utils.state import set_scan_progress, get_scan_progress, set_scan_result, get_scan_result as get_state_scan_result
from utils.security import is_safe_url

logger = logging.getLogger(__name__)

api_bp = Blueprint("api_bp", __name__)

# Lightweight per-process limiter for API endpoints
limiter = Limiter(key_func=get_remote_address)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")

# Shared helpers (DRY — used by both list and detail views)
# ======================================================================

def _parse_report_value(raw_value: Any) -> Any:
    """Parse a stored report from dict, JSON string, or storage URL/path."""
    if not raw_value:
        return None

    if isinstance(raw_value, (dict, list)):
        return raw_value

    try:
        return json_lib.loads(raw_value)
    except Exception:
        try:
            from ai_engine.supabase_client import download_report_from_storage

            dl = download_report_from_storage(raw_value)
            if dl.get("success"):
                return dl.get("data")
        except Exception as exc:
            logger.warning(f"Could not download report from storage: {exc}")
        return None


def _build_scan_base(scan_row: dict) -> dict:
    """Build the base fields shared by both list and detail scan summaries."""
    target_url = scan_row.get("target_url") or scan_row.get("url") or ""
    generated_at = scan_row.get("scan_date") or scan_row.get("created_at")

    return {
        "scan_id": scan_row.get("scan_id"),
        "url": target_url,
        "target_url": target_url,
        "generated_at": generated_at,
    }


def _build_scan_summary_light(scan_row: dict) -> dict:
    """Build a scan summary for list views.

    Parses score and stats from query parameters stored in file_path_patches.
    Falls back to estimates if not found.
    """
    base = _build_scan_base(scan_row)
    patches_count = scan_row.get("patches_count", 0)

    score = max(0, 100 - (patches_count * 3))  # Fallback estimate
    stats = dict(EMPTY_STATS)
    scan_duration_total = None

    try:
        file_path_patches = scan_row.get("file_path_patches", "")
        
        # If the file path is actually a raw JSON string (fallback mechanism)
        if file_path_patches.startswith("{"):
            patches_report = json_lib.loads(file_path_patches)
            scan_duration_total = patches_report.get("scan_duration_total")
            patches = patches_report.get("patches", [])
            if patches:
                score, stats, patches_count = compute_scan_stats(patches)
                
        # If the file path contains query parameters (new mechanism)
        elif "?" in file_path_patches:
            path_part, query_part = file_path_patches.split("?", 1)
            qs = parse_qs(query_part)
            if "score" in qs:
                score = int(qs.get("score")[0])
            if "stats" in qs:
                stats = json_lib.loads(qs.get("stats")[0])
            if "duration" in qs:
                scan_duration_total = float(qs.get("duration")[0])
    except Exception as e:
        logger.error(f"Error extracting metadata from file_path_patches: {e}")

    return {
        **base,
        "score": score,
        "stats": stats,
        "total_patches": patches_count,
        "vulnerabilities_count": scan_row.get("vulnerabilities_count", 0),
        "patches_count": patches_count,
        "scan_duration_total": scan_duration_total,
    }


def _build_scan_summary(scan_row: dict) -> dict:
    """Build a frontend-friendly scan summary from a database row with full reports.

    This downloads full reports from storage - only use for detail views.
    """
    base = _build_scan_base(scan_row)

    vulnerabilities_report = _parse_report_value(scan_row.get("file_path_vulnerabilities")) or {}
    patches_report = _parse_report_value(scan_row.get("file_path_patches")) or {}
    patches = patches_report.get("patches", []) if isinstance(patches_report, dict) else []

    score, stats, _ = compute_scan_stats(patches)

    return {
        **base,
        "score": score,
        "stats": stats,
        "total_patches": scan_row.get("patches_count", len(patches)),
        "vulnerabilities_count": scan_row.get(
            "vulnerabilities_count",
            len((vulnerabilities_report or {}).get("vulnerabilities", [])),
        ),
        "patches_count": scan_row.get("patches_count", len(patches)),
        "vulnerabilities_report": vulnerabilities_report,
        "patches_report": patches_report,
        "patches": patches,
        "vulnerabilities": (vulnerabilities_report or {}).get("vulnerabilities", []),
    }


# ======================================================================
# Authentication decorators
# ======================================================================

def _extract_token() -> str | None:
    """Extract Bearer token from the Authorization header or query parameter."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(None, 1)[1].strip()
        
    # Fallback for EventSource (SSE) which cannot send custom headers natively
    token_param = request.args.get("token")
    if token_param:
        return token_param
        
    return None


def _verify_user(token: str) -> dict | None:
    """Verify a JWT token and return user info dict, or None on failure."""
    from ai_engine.supabase_client import verify_token
    result = verify_token(token)
    if result.get("success"):
        return result
    return None


def require_auth(f):
    """Decorator that verifies the user's JWT token and injects `auth_user`
    into the request context via `request.auth_user`.

    Returns 401 if token is missing or invalid.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify(standardize_error_response(
                False,
                "Missing or invalid Authorization header",
                error_code="UNAUTHORIZED"
            )), 401

        user_info = _verify_user(token)
        if not user_info:
            return jsonify(standardize_error_response(
                False,
                "Invalid or expired token",
                error_code="UNAUTHORIZED"
            )), 401

        # Attach verified user info to the request
        request.auth_user = user_info
        return f(*args, **kwargs)

    return wrapped


def require_api_key(f):
    """Decorator to require an API key if `API_PUBLIC_KEY` is set.

    If `API_PUBLIC_KEY` is not set, the decorator is a no-op (keeps backwards compatibility).
    Clients may send the key as `Authorization: Bearer <key>` header or `api_key` query param.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        api_key = os.getenv("API_PUBLIC_KEY")
        if not api_key:
            return f(*args, **kwargs)

        # Reuse shared token extraction (Bearer header + query param)
        token = _extract_token()

        # Also accept api_key form param (legacy support)
        if not token:
            token = request.args.get("api_key") or request.form.get("api_key")

        if not token or token != api_key:
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        return f(*args, **kwargs)

    return wrapped


# ======================================================================
# Scan endpoints
# ======================================================================

@api_bp.route("/scan", methods=["POST"])
@limiter.limit(SCAN_ROUTE_RATE_LIMIT)
@require_auth
def run_scan():
    """
    Run a security scan against a target URL.

    Performs complete scan pipeline:
    1. Web crawling (forms and parameters discovery)
    2. Active vulnerability testing
    3. Vulnerability classification
    4. AI-powered patch generation

    Request JSON:
        {
            "url": "http://target.com"  # Target URL to scan
        }

    Returns:
        JSON with initial success status and scan_id:
        - success: True
        - scan_id: unique ID for tracking progress

    Status Codes:
        200: Scan initiated successfully
        400: Invalid request (missing URL, invalid format)
        401: Unauthorized
        500: Internal server error
    """
    target = None
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "url" not in data:
            return jsonify(standardize_error_response(
                False,
                "Missing 'url' in request body",
                error_code="INVALID_REQUEST"
            )), 400

        target = data["url"].strip()

        # Validate URL format and prevent SSRF
        parsed = urlparse(target)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return jsonify(standardize_error_response(
                False,
                "Invalid URL format",
                error_code="INVALID_URL"
            )), 400
            
        if not is_safe_url(target):
            return jsonify(standardize_error_response(
                False,
                "Security Policy Violation: Scanning internal or private IP addresses is prohibited.",
                error_code="SSRF_PREVENTED"
            )), 400

        scan_id = f"scan_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        user_info = request.auth_user
        user_id = user_info.get("user_id", "anonymous")

        logger.info(f"Initiating background scan {scan_id} for {target}")
        set_scan_progress(scan_id, user_id, {"step": "waiting", "pct": 0, "msg": "Initialisation du scan...", "elapsed": 0})

        # Spawn background thread
        thread = threading.Thread(
            target=_background_scan_task,
            args=(scan_id, target, data, user_info)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            "success": True,
            "scan_id": scan_id,
            "url": target,
        }), 200

    except Exception as e:
        logger.error(f"Scan initialization error: {e}", exc_info=True)
        return jsonify(standardize_error_response(
            False,
            f"Failed to initiate scan: {str(e)}",
            error_code="INIT_ERROR"
        )), 500


def _background_scan_task(scan_id: str, target: str, data: dict, user_info: dict):
    """Background worker for executing the scan pipeline."""
    user_id = user_info.get("user_id", "anonymous")
    try:
        started_at = time.time()
        set_scan_progress(scan_id, user_id, {"step": "crawling", "pct": 5, "msg": "Crawling du site...", "elapsed": 0})

        # Step 1: Run web crawler
        results = scan_forms(target, max_pages=30, max_depth=2)
        crawl_duration = round(time.time() - started_at, 2)
        logger.info(f"[{scan_id}] Crawling complete in {crawl_duration}s, found {len(results)} forms/parameters")
        set_scan_progress(scan_id, user_id, {"step": "active_scan", "pct": 25, "msg": f"Test actif de {len(results)} formulaire(s)...", "elapsed": crawl_duration})

        # Step 2: Active scanning
        logger.info(f"[{scan_id}] Starting active vulnerability testing...")
        results = active_scan(results)
        active_duration = round(time.time() - started_at, 2)
        logger.info(f"[{scan_id}] Active scan complete in {active_duration}s")
        set_scan_progress(scan_id, user_id, {"step": "classification", "pct": 50, "msg": "Classification des vulnérabilités...", "elapsed": active_duration})

        # Step 3: Build vulnerability report from enriched results
        vulnerabilities_report = build_vulnerabilities_report(
            results,
            target_url=target,
            output_path=os.path.join(REPORTS_DIR, "vulnerabilities.json"),
            scan_duration_seconds=active_duration,
        )
        vuln_count = vulnerabilities_report.get("total_vulnerabilities", 0)
        classify_duration = round(time.time() - started_at, 2)
        set_scan_progress(scan_id, user_id, {"step": "ai_patches", "pct": 70, "msg": f"Génération IA pour {vuln_count} vulnérabilité(s)...", "elapsed": classify_duration})

        # Step 4: Generate patches using AI (with graceful fallback)
        patches_report = None
        try:
            patch_generator = PatchGenerator()
            # Allow caller to request a specific model for AI generation
            requested_model = data.get("model")
            patches_report = patch_generator.generate_all_patches(
                vulnerabilities_data=vulnerabilities_report,
                output_path=os.path.join(REPORTS_DIR, "patches.json"),
                model=requested_model,
            )
            logger.info(f"[{scan_id}] Generated patches for {vuln_count} vulnerabilities")
        except ValueError as ai_error:
            logger.warning(f"[{scan_id}] AI patch generation failed: {ai_error}")
            # Still return vulnerabilities report, but with warning about patches
            patches_report = {
                "scan_id": vulnerabilities_report["scan_id"],
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "total_patches": 0,
                "patches": [],
                "warning": str(ai_error),
            }

        total_duration = round(time.time() - started_at, 2)
        vulnerabilities_report["scan_duration_total"] = total_duration
        if patches_report:
            patches_report["scan_duration_total"] = total_duration

        # Store final results
        set_scan_result(scan_id, user_id, {
            "success": True,
            "results": results,
            "vulnerabilities_report": vulnerabilities_report,
            "patches_report": patches_report,
            "scan_duration_total": total_duration,
        })
        
        set_scan_progress(scan_id, user_id, {"step": "done", "pct": 100, "msg": "Scan terminé !", "elapsed": total_duration})

    except Exception as e:
        logger.error(f"[{scan_id}] Scan endpoint background error: {e}", exc_info=True)
        set_scan_result(scan_id, user_id, {
            "success": False,
            "error": str(e),
            "error_code": "SCAN_ERROR"
        })
        set_scan_progress(scan_id, user_id, {"step": "error", "pct": 100, "msg": f"Erreur: {str(e)}", "elapsed": 0})


@api_bp.route("/scan-result", methods=["GET"])
@limiter.limit("60 per minute")
@require_auth
def get_scan_result():
    """Fetch the result of a completed background scan."""
    scan_id = request.args.get("scan_id")
    if not scan_id:
        return jsonify(standardize_error_response(False, "Missing scan_id", error_code="MISSING_PARAM")), 400
        
    result_entry = get_state_scan_result(scan_id)
    if not result_entry:
        # Check if it's still running
        if get_scan_progress(scan_id):
            return jsonify({"success": False, "status": "running"}), 202
        return jsonify(standardize_error_response(False, "Scan not found or expired", error_code="NOT_FOUND")), 404
        
    # Verify BOLA / IDOR ownership
    if result_entry.get("user_id") != request.auth_user.get("user_id"):
        return jsonify(standardize_error_response(False, "Unauthorized to access this scan", error_code="UNAUTHORIZED")), 403
    
    return jsonify(result_entry["data"]), 200


@api_bp.route("/scan-progress", methods=["GET"])
@limiter.limit("30 per minute")
@require_auth
def scan_progress_sse():
    """
    SSE endpoint — streams real-time scan progress to the frontend.
    Query parameter: scan_id (the unique background task ID)
    """
    scan_id = request.args.get("scan_id")
    target = request.args.get("url")
    
    key = scan_id if scan_id else target
    user_id = request.auth_user.get("user_id")

    def generate():
        last_pct = -1
        timeout = 0
        while timeout < 600:  # 10 minute max
            progress = get_scan_progress(key) or {"step": "waiting", "pct": 0, "msg": "En attente...", "elapsed": 0}
            if progress["pct"] != last_pct:
                last_pct = progress["pct"]
                yield f"data: {json_lib.dumps(progress)}\n\n"
            if progress.get("step") in ("done", "error"):
                break
            time.sleep(0.5)
            timeout += 1

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


# ======================================================================
# Health & AI endpoints
# ======================================================================

@api_bp.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint.

    Returns:
        JSON: {"status": "ok"} if service is up
    """
    return jsonify({"status": "ok"}), 200


@api_bp.route("/chat", methods=["POST"])
@limiter.limit(SCAN_ROUTE_RATE_LIMIT)
@require_auth
def ai_chat():
    """
    Interactive AI chat endpoint for discussing specific vulnerabilities.

    Accepts a conversation history and vulnerability context, then responds
    via the configured AI backend (Gemini / Groq / Local).

    Request JSON:
        {
            "messages": [
                {"role": "user" | "assistant", "content": "..."}
            ],
            "context": {
                "type":             "SQL Injection",
                "severity":         "HIGH",
                "explication":      "...",
                "solution":         "...",
                "code_vulnerable":  "...",
                "url":              "http://target/page"
            }
        }

    Returns:
        JSON: {"success": true, "reply": "<AI response text>"}

    Status Codes:
        200: Reply generated successfully
        400: Missing or invalid request body
        401: Unauthorized
        500: AI backend error
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        messages = data.get("messages", [])
        context  = data.get("context", {})

        if not messages:
            return jsonify(standardize_error_response(
                False,
                "Missing 'messages' in request body",
                error_code="INVALID_REQUEST"
            )), 400

        # ── Build system prompt ──────────────────────────────────────────
        vuln_type   = context.get("type", "Unknown vulnerability")
        severity    = context.get("severity", "UNKNOWN")
        explication = context.get("explication", "")
        solution    = context.get("solution", "")
        code_vuln   = context.get("code_vulnerable", "")
        target_url  = context.get("url", "")

        system_prompt = (
            "You are Scanlyzer AI, an expert cybersecurity assistant specializing in "
            "web application security. You help developers understand and remediate "
            "vulnerabilities found during security scans. You are knowledgeable, "
            "precise, and educational — you explain not just *what* to fix but *why* "
            "it is dangerous and *how* the fix prevents the attack.\n\n"
            "=== VULNERABILITY CONTEXT ===\n"
            f"Type      : {vuln_type}\n"
            f"Severity  : {severity}\n"
            f"Target URL: {target_url}\n"
        )
        if explication:
            system_prompt += f"Explanation: {explication}\n"
        if solution:
            system_prompt += f"Proposed fix: {solution}\n"
        if code_vuln:
            system_prompt += f"\nVulnerable code snippet:\n```\n{code_vuln}\n```\n"
        system_prompt += (
            "\nAnswer the user's latest question directly. If the user greets you or asks a general question, "
            "respond naturally to it before diving into the vulnerability. Use markdown for code blocks "
            "when showing code. Use the vulnerability context to inform your answers, but do not ignore the user's input."
        )

        # ── Assemble the full prompt (system + history) ──────────────────
        prompt_parts = [system_prompt, "\n\n=== CONVERSATION ==="]
        for msg in messages:
            role    = msg.get("role", "user")
            content = msg.get("content", "")
            label   = "User" if role == "user" else "Scanlyzer AI"
            prompt_parts.append(f"\n{label}: {content}")
        prompt_parts.append("\nScanlyzer AI:")

        full_prompt = "".join(prompt_parts)

        # ── Call AI backend ───────────────────────────────────────────────
        client = get_ai_client()

        # GroqAIClient forces JSON mode — we need free-form text for chat.
        # We call the underlying groq client directly in text mode when detected.
        if hasattr(client, "client") and hasattr(client.client, "chat"):
            # Groq client — bypass JSON mode
            from groq import Groq as _Groq  # noqa: F401 (import check)
            chat_completion = client.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    *[
                        {"role": m.get("role", "user"), "content": m.get("content", "")}
                        for m in messages
                    ],
                ],
                model=client.model,
                timeout=60,
            )
            reply = chat_completion.choices[0].message.content
        else:
            # Gemini / Local clients — use standard send_prompt
            reply = client.send_prompt(full_prompt)

        logger.info(f"[chat] Generated reply ({len(reply)} chars) for {vuln_type}")
        return jsonify({"success": True, "reply": reply}), 200

    except Exception as e:
        logger.error(f"AI chat endpoint error: {e}", exc_info=True)
        return jsonify(standardize_error_response(
            False,
            f"AI chat error: {str(e)}",
            error_code="CHAT_ERROR"
        )), 500




@api_bp.route("/ai/models", methods=["GET"])
@require_api_key
def list_ai_models():
    """List available models from the configured AI backend.

    Returns a JSON list of model names. For local backends this will
    try HTTP discovery and fall back to a local models directory if configured.
    """
    try:
        client = get_ai_client()
        models = []
        # Some clients implement list_models
        if hasattr(client, "list_models"):
            models = client.list_models() or []
        return jsonify({"success": True, "models": models}), 200
    except Exception as e:
        logger.error(f"Error listing AI models: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/ai/generate", methods=["POST"])
@limiter.limit(SCAN_ROUTE_RATE_LIMIT)
@require_api_key
def ai_generate():
    """Proxy an AI generation request to the configured backend.

    Request JSON: {"prompt": "...", "model": "optional-model-name"}
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        prompt = data.get("prompt")
        model = data.get("model")

        if not prompt:
            return jsonify({"success": False, "error": "Missing 'prompt' in request"}), 400

        client = get_ai_client()
        if hasattr(client, "send_prompt"):
            result = client.send_prompt(prompt, model=model)
        else:
            return jsonify({"success": False, "error": "AI client does not support generation"}), 500

        return jsonify({"success": True, "output": result}), 200
    except Exception as e:
        logger.error(f"AI generate error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ======================================================================
# Scan persistence endpoints (all require auth)
# ======================================================================

@api_bp.route("/save-scan", methods=["POST"])
@limiter.limit(SAVE_SCAN_RATE_LIMIT)
@require_auth
def save_scan_route():
    """
    Save completed scan to database.

    Stores scan metadata and reports in Supabase for later retrieval.
    Reports are uploaded to Supabase Storage if configured.

    The user_id is taken from the verified JWT token, NOT from the request body,
    to prevent IDOR attacks.

    Returns:
        JSON: Save result with scan metadata

    Status Codes:
        201: Scan successfully saved
        400: Invalid request or validation error
        401: Unauthorized
        500: Database error
    """
    try:
        from ai_engine.supabase_client import save_scan

        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify(standardize_error_response(
                False,
                "Missing request body",
                error_code="INVALID_REQUEST"
            )), 400

        # Use verified user_id from token (prevents IDOR)
        user_id = request.auth_user.get("user_id")
        email = request.auth_user.get("email")

        target_url = data.get("target_url")
        vulnerabilities_count = data.get("vulnerabilities_count", 0)
        patches_count = data.get("patches_count", 0)
        vulnerabilities_report = data.get("vulnerabilities_report")
        patches_report = data.get("patches_report")
        scan_id = data.get("scan_id")

        # Validate required fields
        if not all([target_url, scan_id]):
            return jsonify(standardize_error_response(
                False,
                "Missing required fields: target_url, scan_id",
                error_code="MISSING_FIELDS"
            )), 400

        if not vulnerabilities_report:
            return jsonify(standardize_error_response(
                False,
                "Missing vulnerabilities_report",
                error_code="MISSING_REPORT"
            )), 400

        logger.info(f"Saving scan {scan_id} for user {user_id}")

        # Save to database
        result = save_scan(
            user_id=user_id,
            email=email,
            target_url=target_url,
            vulnerabilities_count=vulnerabilities_count,
            patches_count=patches_count,
            file_path_vulnerabilities="",
            file_path_patches="",
            scan_id=scan_id,
            vulnerabilities_report=vulnerabilities_report,
            patches_report=patches_report,
        )

        if result["success"]:
            logger.info(f"Scan {scan_id} saved successfully")
            return jsonify(result), 201
        else:
            logger.warning(f"Failed to save scan {scan_id}: {result.get('message')}")
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Save scan endpoint error: {e}", exc_info=True)
        return jsonify(standardize_error_response(
            False,
            f"Failed to save scan: {str(e)}",
            error_code="SAVE_ERROR"
        )), 500


@api_bp.route("/scans", methods=["GET"])
@limiter.limit(REPORT_ROUTE_RATE_LIMIT)
@require_auth
def get_scans_route():
    """
    Get all scans for authenticated user.

    Returns list of user's past scans with metadata (date, target URL, findings count).
    User ID is extracted from the verified JWT token.

    Returns:
        JSON: List of scan objects with metadata

    Status Codes:
        200: Successfully retrieved scan list
        401: Missing or invalid token
        400: Database error
    """
    try:
        from ai_engine.supabase_client import get_user_scans

        user_id = request.auth_user.get("user_id")
        logger.info(f"Fetching scans for authenticated user {user_id}")
        result = get_user_scans(user_id)

        if result["success"]:
            # Use lightweight summaries for list view (no storage downloads)
            scans = [_build_scan_summary_light(scan) for scan in result["data"]]
            return jsonify({"success": True, "scans": scans}), 200
        else:
            logger.warning(f"Failed to fetch scans")
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Get scans endpoint error: {e}", exc_info=True)
        return jsonify(standardize_error_response(
            False,
            f"Failed to retrieve scans: {str(e)}",
            error_code="FETCH_ERROR"
        )), 500


@api_bp.route("/report", methods=["GET"])
@limiter.limit(REPORT_ROUTE_RATE_LIMIT)
@require_auth
def get_report_route():
    """
    Retrieve a specific scan report.

    Returns complete vulnerability and patch reports for a scan.
    Only returns reports owned by the authenticated user.

    Query Parameters:
        scan_id (required): UUID of specific scan

    Returns:
        JSON: Scan metadata + vulnerabilities_report + patches_report

    Status Codes:
        200: Report retrieved successfully
        400: Invalid parameters or database error
        401: Unauthorized
        404: Scan not found
    """
    try:
        from ai_engine.supabase_client import get_scan_by_id

        scan_id = request.args.get("scan_id")
        user_id = request.auth_user.get("user_id")

        if not scan_id:
            return jsonify(standardize_error_response(
                False,
                "Missing required parameter: scan_id",
                error_code="MISSING_PARAMETER"
            )), 400

        logger.info(f"Fetching scan {scan_id} for user {user_id}")
        result = get_scan_by_id(scan_id)
        if not result.get("success"):
            return jsonify(result), 400

        scan_row = result["data"]

        # Verify ownership — user can only access their own scans
        if scan_row.get("user_id") != user_id:
            return jsonify(standardize_error_response(
                False,
                "Scan not found",
                error_code="NOT_FOUND"
            )), 404

        vulnerabilities_report = _parse_report_value(scan_row.get("file_path_vulnerabilities"))
        patches_report = _parse_report_value(scan_row.get("file_path_patches"))

        return jsonify({
            "success": True,
            "scan": scan_row,
            "scan_id": scan_row.get("scan_id"),
            "vulnerabilities_report": vulnerabilities_report,
            "patches_report": patches_report,
            "patches": (patches_report or {}).get("patches", []),
            "vulnerabilities": (vulnerabilities_report or {}).get("vulnerabilities", []),
        }), 200

    except Exception as e:
        logger.error(f"Get report endpoint error: {e}", exc_info=True)
        return jsonify(standardize_error_response(
            False,
            f"Internal server error: {str(e)}",
            error_code="INTERNAL_ERROR"
        )), 500


@api_bp.route("/delete-scan", methods=["DELETE", "POST"])
@limiter.limit(DELETE_SCAN_RATE_LIMIT)
@require_auth
def delete_scan_route():
    """
    Delete a scan from the database.

    Removes scan record and associated reports from Supabase.
    User ID is taken from the verified JWT token to enforce ownership.

    Request JSON:
        {
            "scan_id": "scan_xxx"   # UUID of scan to delete
        }

    Returns:
        JSON: Deletion result

    Status Codes:
        200: Scan successfully deleted
        400: Invalid request
        403: Unauthorized (not scan owner)
        404: Scan not found
        500: Database error
    """
    try:
        from ai_engine.supabase_client import supabase_admin, _get_supabase_admin_client

        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify(standardize_error_response(
                False,
                "Missing request body",
                error_code="INVALID_REQUEST"
            )), 400

        # Use verified user_id from token (prevents IDOR)
        user_id = request.auth_user.get("user_id")
        scan_id = data.get("scan_id")

        if not scan_id:
            return jsonify(standardize_error_response(
                False,
                "Missing scan_id",
                error_code="MISSING_FIELDS"
            )), 400

        admin_client = _get_supabase_admin_client()

        logger.info(f"Deleting scan {scan_id} for user {user_id}")

        # Verify scan ownership using the authenticated user_id
        result = admin_client.table("scans").select("user_id").eq("scan_id", scan_id).execute()
        if not result.data:
            return jsonify(standardize_error_response(
                False,
                "Scan not found",
                error_code="NOT_FOUND"
            )), 404

        if result.data[0]["user_id"] != user_id:
            logger.warning(f"Unauthorized delete attempt: user {user_id} tried to delete scan owned by {result.data[0]['user_id']}")
            return jsonify(standardize_error_response(
                False,
                "Unauthorized",
                error_code="UNAUTHORIZED"
            )), 403

        # Delete the scan
        admin_client.table("scans").delete().eq("scan_id", scan_id).execute()
        logger.info(f"Scan {scan_id} deleted successfully")

        return jsonify(standardize_error_response(
            True,
            f"Scan {scan_id} deleted",
            data={"scan_id": scan_id}
        )), 200

    except Exception as e:
        logger.error(f"Delete scan endpoint error: {e}", exc_info=True)
        return jsonify(standardize_error_response(
            False,
            f"Failed to delete scan: {str(e)}",
            error_code="DELETE_ERROR"
        )), 500
