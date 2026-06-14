import logging
import json as json_lib
import time
import os
import uuid
import threading
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config.constants import REPORT_ROUTE_RATE_LIMIT, SAVE_SCAN_RATE_LIMIT, DELETE_SCAN_RATE_LIMIT
from utils.helpers import standardize_error_response, _build_scan_summary_light, _parse_report_value
from api.auth import require_auth

logger = logging.getLogger(__name__)

report_bp = Blueprint("report_bp", __name__)
report_limiter = Limiter(key_func=get_remote_address)


@report_bp.route("/save-scan", methods=["POST"])
@report_limiter.limit(SAVE_SCAN_RATE_LIMIT)
@require_auth
def save_scan_route():
    try:
        from ai_engine.supabase_client import save_scan

        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify(standardize_error_response(
                False,
                "Missing request body",
                error_code="INVALID_REQUEST"
            )), 400

        user_id = request.auth_user.get("user_id")
        email = request.auth_user.get("email")

        target_url = data.get("target_url")
        vulnerabilities_count = data.get("vulnerabilities_count", 0)
        patches_count = data.get("patches_count", 0)
        vulnerabilities_report = data.get("vulnerabilities_report")
        patches_report = data.get("patches_report")
        scan_id = data.get("scan_id")

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


@report_bp.route("/scans", methods=["GET"])
@report_limiter.limit(REPORT_ROUTE_RATE_LIMIT)
@require_auth
def get_scans_route():
    try:
        from ai_engine.supabase_client import get_user_scans

        user_id = request.auth_user.get("user_id")
        logger.info(f"Fetching scans for authenticated user {user_id}")
        result = get_user_scans(user_id)

        if result["success"]:
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


@report_bp.route("/report", methods=["GET"])
@report_limiter.limit(REPORT_ROUTE_RATE_LIMIT)
@require_auth
def get_report_route():
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


@report_bp.route("/delete-scan", methods=["DELETE", "POST"])
@report_limiter.limit(DELETE_SCAN_RATE_LIMIT)
@require_auth
def delete_scan_route():
    try:
        from ai_engine.supabase_client import supabase_admin, _get_supabase_admin_client

        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify(standardize_error_response(
                False,
                "Missing request body",
                error_code="INVALID_REQUEST"
            )), 400

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
