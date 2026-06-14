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

from scanner.crawler import scan_forms
from scanner.active_scanner import active_scan
from scanner.exporter import build_vulnerabilities_report
from ai_engine.patch_generator import PatchGenerator
from ai_engine.ai_client import get_ai_client
from config.constants import SCAN_ROUTE_RATE_LIMIT
from utils.helpers import standardize_error_response, compute_scan_stats
from utils.state import set_scan_progress, get_scan_progress, set_scan_result, get_scan_result as get_state_scan_result
from utils.security import is_safe_url
from api.auth import require_auth, require_api_key

logger = logging.getLogger(__name__)

scan_bp = Blueprint("scan_bp", __name__)
scan_limiter = Limiter(key_func=get_remote_address)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")

@scan_bp.route("/scan", methods=["POST"])
@scan_limiter.limit(SCAN_ROUTE_RATE_LIMIT)
@require_auth
def run_scan():
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

        # ── Domain verification gate ────────────────────────────────
        # Users must verify ownership of a domain before scanning it.
        user_info = request.auth_user
        user_id = user_info.get("user_id", "anonymous")

        from utils.helpers import extract_domain
        from ai_engine.supabase_client import _get_supabase_admin_client
        target_domain = extract_domain(target)

        if target_domain:
            supabase = _get_supabase_admin_client()
            verification = (
                supabase.table("domain_verifications")
                .select("verified")
                .eq("user_id", user_id)
                .eq("domain", target_domain)
                .eq("verified", True)
                .limit(1)
                .execute()
            )
            if not verification.data:
                return jsonify(standardize_error_response(
                    False,
                    f"Domain not verified. Please verify ownership of \"{target_domain}\" before scanning. "
                    f"Go to the Verify page to complete domain verification.",
                    error_code="DOMAIN_NOT_VERIFIED"
                )), 403

        scan_id = f"scan_{int(time.time())}_{uuid.uuid4().hex[:8]}"

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

        # Compute security score and stats from vulnerabilities (has confirmed field)
        score = 0
        stats = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        patches_count = 0
        
        if vulnerabilities_report and "vulnerabilities" in vulnerabilities_report:
            score, stats, patches_count = compute_scan_stats(vulnerabilities_report["vulnerabilities"])
        elif patches_report and "patches" in patches_report:
            # Fallback to patches if vulnerabilities not available
            score, stats, patches_count = compute_scan_stats(patches_report["patches"])

        # Store final results
        set_scan_result(scan_id, user_id, {
            "success": True,
            "results": results,
            "vulnerabilities_report": vulnerabilities_report,
            "patches_report": patches_report,
            "scan_duration_total": total_duration,
            "score": score,
            "stats": stats,
            "patches_count": patches_count,
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


@scan_bp.route("/scan-result", methods=["GET"])
@scan_limiter.limit("60 per minute")
@require_auth
def get_scan_result():
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


@scan_bp.route("/scan-progress", methods=["GET"])
@scan_limiter.limit("30 per minute")
@require_auth
def scan_progress_sse():
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


@scan_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@scan_bp.route("/chat", methods=["POST"])
@scan_limiter.limit(SCAN_ROUTE_RATE_LIMIT)
@require_auth
def ai_chat():
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

        prompt_parts = [system_prompt, "\n\n=== CONVERSATION ==="]
        for msg in messages:
            role    = msg.get("role", "user")
            content = msg.get("content", "")
            label   = "User" if role == "user" else "Scanlyzer AI"
            prompt_parts.append(f"\n{label}: {content}")
        prompt_parts.append("\nScanlyzer AI:")

        full_prompt = "".join(prompt_parts)

        client = get_ai_client()
        if hasattr(client, "client") and hasattr(client.client, "chat"):
            from groq import Groq as _Groq
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


@scan_bp.route("/ai/models", methods=["GET"])
@require_api_key
def list_ai_models():
    try:
        client = get_ai_client()
        models = []
        if hasattr(client, "list_models"):
            models = client.list_models() or []
        return jsonify({"success": True, "models": models}), 200
    except Exception as e:
        logger.error(f"Error listing AI models: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@scan_bp.route("/ai/generate", methods=["POST"])
@scan_limiter.limit(SCAN_ROUTE_RATE_LIMIT)
@require_api_key
def ai_generate():
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
