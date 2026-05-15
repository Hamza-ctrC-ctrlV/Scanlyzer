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
from typing import Dict, Tuple, Any
from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from urllib.parse import urlparse
import json as json_lib
import time
import os
from functools import wraps

from scanner.crawler import scan_forms
from scanner.exporter import build_vulnerabilities_report
from ai_engine.patch_generator import PatchGenerator
from ai_engine.ai_client import get_ai_client
from config.constants import (
    SCAN_ROUTE_RATE_LIMIT,
    SAVE_SCAN_RATE_LIMIT,
    REPORT_ROUTE_RATE_LIMIT,
    DELETE_SCAN_RATE_LIMIT,
)
from utils.helpers import standardize_error_response

logger = logging.getLogger(__name__)

api_bp = Blueprint("api_bp", __name__)

# Lightweight per-process limiter for API endpoints
limiter = Limiter(key_func=get_remote_address)


def _parse_report_value(raw_value: Any) -> Any:
    """Parse a stored report from dict, JSON string, or storage URL/path."""
    if not raw_value:
        return None


def _severity_score_points(severity: str | None) -> int:
    mapping = {
        "CRITICAL": 25,
        "HIGH": 15,
        "MEDIUM": 8,
        "LOW": 3,
        "INFO": 1,
    }
    return mapping.get((severity or "").upper(), 0)


def _build_scan_summary_light(scan_row: dict) -> dict:
    """Build a lightweight scan summary for list views (no report downloads).
    
    Only includes metadata and counts from database, avoiding expensive storage downloads.
    """
    target_url = scan_row.get("target_url") or scan_row.get("url") or ""
    generated_at = scan_row.get("scan_date") or scan_row.get("created_at")
    
    # Use database counts directly - no parsing
    vulnerabilities_count = scan_row.get("vulnerabilities_count", 0)
    patches_count = scan_row.get("patches_count", 0)
    
    # Estimate score from severity distribution (we don't have the full data)
    # Conservative estimate: assume moderate distribution
    estimated_score = max(0, 100 - (patches_count * 3))  # Rough estimate
    
    # Parse stats from database if available, otherwise estimate
    stats = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    
    return {
        "scan_id": scan_row.get("scan_id"),
        "url": target_url,
        "target_url": target_url,
        "generated_at": generated_at,
        "score": estimated_score,
        "stats": stats,
        "total_patches": patches_count,
        "vulnerabilities_count": vulnerabilities_count,
        "patches_count": patches_count,
        # Don't include full reports in list view
    }


def _build_scan_summary(scan_row: dict) -> dict:
    """Build a frontend-friendly scan summary from a database row with full reports.
    
    This downloads full reports from storage - only use for detail views.
    """
    vulnerabilities_report = _parse_report_value(scan_row.get("file_path_vulnerabilities")) or {}
    patches_report = _parse_report_value(scan_row.get("file_path_patches")) or {}
    patches = patches_report.get("patches", []) if isinstance(patches_report, dict) else []

    total_points = sum(_severity_score_points(patch.get("severity")) for patch in patches if isinstance(patch, dict))
    score = max(0, 100 - total_points)

    stats = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for patch in patches:
        if not isinstance(patch, dict):
            continue
        severity = (patch.get("severity") or "").upper()
        if severity in stats:
            stats[severity] += 1

    target_url = scan_row.get("target_url") or scan_row.get("url") or ""
    generated_at = scan_row.get("scan_date") or scan_row.get("created_at")

    return {
        "scan_id": scan_row.get("scan_id"),
        "url": target_url,
        "target_url": target_url,
        "generated_at": generated_at,
        "score": score,
        "stats": stats,
        "total_patches": scan_row.get("patches_count", len(patches)),
        "vulnerabilities_count": scan_row.get("vulnerabilities_count", len((vulnerabilities_report or {}).get("vulnerabilities", []))),
        "patches_count": scan_row.get("patches_count", len(patches)),
        "vulnerabilities_report": vulnerabilities_report,
        "patches_report": patches_report,
        "patches": patches,
        "vulnerabilities": (vulnerabilities_report or {}).get("vulnerabilities", []),
    }

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

        # Check Authorization header
        auth = request.headers.get("Authorization", "")
        token = None
        if auth.startswith("Bearer "):
            token = auth.split(None, 1)[1].strip()

        # Fallback to query param
        if not token:
            token = request.args.get("api_key") or request.form.get("api_key")

        if not token or token != api_key:
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        return f(*args, **kwargs)

    return wrapped


@api_bp.route("/scan", methods=["POST"])
@limiter.limit(SCAN_ROUTE_RATE_LIMIT)
def run_scan():
    """
    Run a security scan against a target URL.
    
    Performs complete scan pipeline:
    1. Web crawling (forms and parameters discovery)
    2. Vulnerability classification
    3. AI-powered patch generation
    
    Request JSON:
        {
            "url": "http://target.com"  # Target URL to scan
        }
    
    Returns:
        JSON with scan results including:
        - results: Raw crawler findings (forms, parameters, fields)
        - vulnerabilities_report: Standardized vulnerability schema
        - patches_report: AI-generated fixes and remediation guidance
        
    Status Codes:
        200: Scan completed (even if vulnerabilities found)
        400: Invalid request (missing URL, invalid format)
        500: Internal server error
    
    Side Effects:
        - Makes HTTP requests to target and discovered URLs
        - Calls Gemini API for each vulnerability
        - Respects rate limiting on both crawler and API
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "url" not in data:
            return jsonify(standardize_error_response(
                False,
                "Missing 'url' in request body",
                error_code="INVALID_REQUEST"
            )), 400

        target = data["url"].strip()

        # Validate URL format
        parsed = urlparse(target)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return jsonify(standardize_error_response(
                False,
                "Invalid URL format",
                error_code="INVALID_URL"
            )), 400

        logger.info(f"Starting scan for {target}")
        started_at = time.time()

        # Step 1: Run web crawler
        results = scan_forms(target, max_pages=30, max_depth=2)
        scan_duration = round(time.time() - started_at, 2)
        logger.info(f"Crawling complete in {scan_duration}s, found {len(results)} forms/parameters")

        # Step 2: Build vulnerability report from crawler results
        vulnerabilities_report = build_vulnerabilities_report(
            results,
            target_url=target,
            output_path=None,
            scan_duration_seconds=scan_duration,
        )

        # Step 3: Generate patches using AI (with graceful fallback)
        patches_report = None
        try:
            patch_generator = PatchGenerator()
            # Allow caller to request a specific model for AI generation
            requested_model = data.get("model")
            patches_report = patch_generator.generate_all_patches(
                vulnerabilities_data=vulnerabilities_report,
                output_path=None,
                model=requested_model,
            )
            logger.info(f"Generated patches for {vulnerabilities_report.get('total_vulnerabilities', 0)} vulnerabilities")
        except ValueError as ai_error:
            logger.warning(f"AI patch generation failed: {ai_error}")
            # Still return vulnerabilities report, but with warning about patches
            patches_report = {
                "scan_id": vulnerabilities_report["scan_id"],
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "total_patches": 0,
                "patches": [],
                "warning": str(ai_error),
            }

        return jsonify({
            "success": True,
            "results": results,
            "vulnerabilities_report": vulnerabilities_report,
            "patches_report": patches_report,
        }), 200

    except Exception as e:
        logger.error(f"Scan endpoint error: {e}", exc_info=True)
        return jsonify(standardize_error_response(
            False,
            f"Scan failed: {str(e)}",
            error_code="SCAN_ERROR"
        )), 500


@api_bp.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint.
    
    Returns:
        JSON: {"status": "ok"} if service is up
    """
    return jsonify({"status": "ok"}), 200


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


@api_bp.route("/save-scan", methods=["POST"])
@limiter.limit(SAVE_SCAN_RATE_LIMIT)
def save_scan_route():
    """
    Save completed scan to database.
    
    Stores scan metadata and reports in Supabase for later retrieval.
    Reports are uploaded to Supabase Storage if configured.
    
    Request JSON:
        {
            "user_id": "uuid",
            "email": "user@example.com",
            "target_url": "http://target.com",
            "scan_id": "scan_20240101_120000",
            "vulnerabilities_count": 5,
            "patches_count": 5,
            "vulnerabilities_report": {...},  # Full report object
            "patches_report": {...}           # Full report object
        }
    
    Returns:
        JSON: Save result with scan metadata
        
    Status Codes:
        201: Scan successfully saved
        400: Invalid request or validation error
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

        user_id = data.get("user_id")
        email = data.get("email")
        target_url = data.get("target_url")
        vulnerabilities_count = data.get("vulnerabilities_count", 0)
        patches_count = data.get("patches_count", 0)
        vulnerabilities_report = data.get("vulnerabilities_report")
        patches_report = data.get("patches_report")
        scan_id = data.get("scan_id")

        # Validate required fields
        if not all([user_id, target_url, scan_id]):
            return jsonify(standardize_error_response(
                False,
                "Missing required fields: user_id, target_url, scan_id",
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
def get_scans_route():
    """
    Get all scans for authenticated user.
    
    Returns list of user's past scans with metadata (date, target URL, findings count).
    
    Headers:
        Authorization: Bearer <token> (required for security - validates user ownership)
    
    Returns:
        JSON: List of scan objects with metadata
        
    Status Codes:
        200: Successfully retrieved scan list
        401: Missing or invalid token
        400: Database error
    """
    try:
        from ai_engine.supabase_client import get_user_scans, verify_token

        # Get token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify(standardize_error_response(
                False,
                "Missing or invalid Authorization header",
                error_code="UNAUTHORIZED"
            )), 401

        token = auth_header.split(None, 1)[1].strip()
        
        # Verify token to get authenticated user_id
        verify_result = verify_token(token)
        if not verify_result.get("success"):
            return jsonify(standardize_error_response(
                False,
                "Invalid token",
                error_code="UNAUTHORIZED"
            )), 401
        
        user_id = verify_result.get("user_id")
        logger.info(f"Fetching scans for authenticated user {user_id}")
        result = get_user_scans(user_id)

        if result["success"]:
            # Use lightweight summaries for list view (no storage downloads)
            scans = [_build_scan_summary_light(scan) for scan in result["data"]]
            return jsonify({"success": True, "scans": scans}), 200
        else:
            logger.warning(f"Failed to fetch scans for user {user_id}")
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
def get_report_route():
    """
    Retrieve a specific scan report.
    
    Returns complete vulnerability and patch reports for a scan.
    Can fetch by scan_id or user_id (returns latest).
    
    Query Parameters:
        scan_id (optional): UUID of specific scan
        user_id (optional): UUID of user (returns latest scan)
        
    Returns:
        JSON: Scan metadata + vulnerabilities_report + patches_report
        
    Status Codes:
        200: Report retrieved successfully
        400: Invalid parameters or database error
        404: Scan not found
    
    Note:
        Either scan_id or user_id must be provided.
        If both provided, scan_id takes precedence.
    """
    try:
        from ai_engine.supabase_client import get_scan_by_id, get_user_scans

        scan_id = request.args.get("scan_id")
        user_id = request.args.get("user_id")

        scan_row = None

        if scan_id:
            logger.info(f"Fetching scan {scan_id}")
            result = get_scan_by_id(scan_id)
            if not result.get("success"):
                return jsonify(result), 400
            scan_row = result["data"]

        elif user_id:
            logger.info(f"Fetching latest scan for user {user_id}")
            result = get_user_scans(user_id)
            if not result.get("success"):
                return jsonify(result), 400

            scans = result.get("data", [])
            if not scans:
                return jsonify(standardize_error_response(
                    False,
                    "No scans found for this user",
                    error_code="NOT_FOUND"
                )), 404

            # Find first scan with report data, fallback to most recent
            scan_row = None
            for scan in scans:
                if scan.get("file_path_vulnerabilities") or scan.get("file_path_patches"):
                    scan_row = scan
                    break
            if not scan_row:
                scan_row = scans[0]
        else:
            return jsonify(standardize_error_response(
                False,
                "Missing required parameter: scan_id or user_id",
                error_code="MISSING_PARAMETER"
            )), 400

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
def delete_scan_route():
    """
    Delete a scan from the database.
    
    Removes scan record and associated reports from Supabase.
    Requires user ownership verification - users can only delete their own scans.
    
    Request JSON:
        {
            "user_id": "uuid",      # Requester's UUID
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
        from ai_engine.supabase_client import supabase_admin

        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify(standardize_error_response(
                False,
                "Missing request body",
                error_code="INVALID_REQUEST"
            )), 400

        user_id = data.get("user_id")
        scan_id = data.get("scan_id")

        if not user_id or not scan_id:
            return jsonify(standardize_error_response(
                False,
                "Missing user_id or scan_id",
                error_code="MISSING_FIELDS"
            )), 400

        if not supabase_admin:
            logger.error("Supabase service role key not configured")
            return jsonify(standardize_error_response(
                False,
                "Database not configured",
                error_code="CONFIG_ERROR"
            )), 500

        logger.info(f"Deleting scan {scan_id} for user {user_id}")

        # Verify scan ownership
        result = supabase_admin.table("scans").select("user_id").eq("scan_id", scan_id).execute()
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
        supabase_admin.table("scans").delete().eq("scan_id", scan_id).execute()
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
