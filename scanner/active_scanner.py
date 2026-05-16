"""
Active Scanner Module - Payload Injection & Verification

Actually submits payloads to discovered forms/parameters and analyzes
the server response to confirm whether a vulnerability is exploitable.

Pipeline:
1. Receive crawler results (forms, fields, payloads)
2. For each injectable field, submit the payload via HTTP
3. Analyze the response for evidence of exploitation
4. Return enriched results with evidence and confirmed status

This module turns Scanlyzer from a passive form-discoverer into
an active vulnerability tester.
"""

import re
import logging
import requests
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin, urlencode

from .payloads import XSS_PAYLOADS, SQLI_PAYLOADS
from config.constants import INJECTABLE_SKIP_TYPES

logger = logging.getLogger(__name__)

# Signatures that indicate a successful SQL injection
SQL_ERROR_SIGNATURES = [
    # MySQL
    "you have an error in your sql syntax",
    "mysql_fetch_array",
    "mysql_num_rows",
    "mysql_query",
    "warning: mysql",
    # PostgreSQL
    "postgresql error",
    "pg_query",
    "pg_exec",
    # SQLite
    "sqlite3::query",
    "sqlite_error",
    # MSSQL
    "microsoft sql server",
    "unclosed quotation mark",
    # Generic
    "sql syntax",
    "syntax error",
    "odbc drivers",
    "pdoexception",
    # Evidence of query reflection (our test site does this)
    "select * from",
    "where id =",
    "where name =",
    "where email =",
]

# Patterns that indicate the payload was reflected without sanitization
XSS_REFLECTION_PATTERNS = [
    "<script>alert(",
    "<img src=x onerror=alert(",
    "<svg onload=alert(",
    "onerror=alert(",
    "onload=alert(",
    "javascript:alert(",
]


def test_xss(
    url: str,
    method: str,
    field_name: str,
    form_action: str,
    all_fields: List[Dict[str, Any]],
) -> Tuple[bool, str, str]:
    """
    Test a single field for reflected XSS by submitting payloads
    and checking if they appear unescaped in the response.

    Args:
        url: Page URL where the form was found
        method: HTTP method (GET/POST)
        field_name: Name of the field to test
        form_action: The form's action URL (where data is submitted)
        all_fields: All fields in the form (to fill required fields)

    Returns:
        Tuple of (is_vulnerable, evidence, payload_used)
    """
    target_url = form_action or url

    for payload in XSS_PAYLOADS[:4]:  # Test first 4 payloads
        # Build form data with payload in target field, defaults for others
        form_data = {}
        for f in all_fields:
            name = f.get("name", "")
            if not name:
                continue
            if name == field_name:
                form_data[name] = payload
            else:
                form_data[name] = "test"  # Fill other fields with safe data

        try:
            if method.upper() == "POST":
                response = requests.post(target_url, data=form_data, timeout=5, allow_redirects=True)
            else:
                response = requests.get(target_url, params=form_data, timeout=5, allow_redirects=True)

            response_text = response.text

            # Check if the exact payload appears in the response body
            if payload in response_text:
                evidence = f"Payload reflected in response: '{payload}' found in HTML body"
                logger.info(f"✓ XSS CONFIRMED on field '{field_name}' at {target_url}")
                return True, evidence, payload

            # Check for partial reflection patterns
            for pattern in XSS_REFLECTION_PATTERNS:
                if pattern.lower() in response_text.lower():
                    evidence = f"XSS pattern detected: '{pattern}' found in response"
                    logger.info(f"✓ XSS CONFIRMED (pattern) on field '{field_name}' at {target_url}")
                    return True, evidence, payload

        except requests.RequestException as e:
            logger.debug(f"Request failed for XSS test on {field_name}: {e}")
            continue

    return False, "", ""


def test_sqli(
    url: str,
    method: str,
    field_name: str,
    form_action: str,
    all_fields: List[Dict[str, Any]],
) -> Tuple[bool, str, str]:
    """
    Test a single field for SQL injection by submitting payloads
    and checking for SQL error messages or query reflection in the response.

    Args:
        url: Page URL where the form was found
        method: HTTP method (GET/POST)
        field_name: Name of the field to test
        form_action: The form's action URL
        all_fields: All fields in the form

    Returns:
        Tuple of (is_vulnerable, evidence, payload_used)
    """
    target_url = form_action or url

    for payload in SQLI_PAYLOADS[:5]:  # Test first 5 payloads
        form_data = {}
        for f in all_fields:
            name = f.get("name", "")
            if not name:
                continue
            if name == field_name:
                form_data[name] = payload
            else:
                form_data[name] = "test"

        try:
            if method.upper() == "POST":
                response = requests.post(target_url, data=form_data, timeout=5, allow_redirects=True)
            else:
                response = requests.get(target_url, params=form_data, timeout=5, allow_redirects=True)

            response_lower = response.text.lower()

            # Check if the SQL payload is reflected in a query context
            if payload.lower() in response_lower:
                # Check if it's reflected inside what looks like a SQL query
                for sig in SQL_ERROR_SIGNATURES:
                    if sig in response_lower:
                        evidence = f"SQL payload reflected in query context. Payload '{payload}' and SQL signature '{sig}' found in response."
                        logger.info(f"✓ SQLi CONFIRMED on field '{field_name}' at {target_url}")
                        return True, evidence, payload

            # Check for SQL error messages alone (even without payload reflection)
            for sig in SQL_ERROR_SIGNATURES:
                if sig in response_lower:
                    evidence = f"SQL error detected after injection: '{sig}' found in server response"
                    logger.info(f"✓ SQLi CONFIRMED (error) on field '{field_name}' at {target_url}")
                    return True, evidence, payload

        except requests.RequestException as e:
            logger.debug(f"Request failed for SQLi test on {field_name}: {e}")
            continue

    return False, "", ""


def test_field(
    url: str,
    method: str,
    field_name: str,
    field_payload_hint: str,
    form_action: str,
    all_fields: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Run all relevant tests on a single field.

    Uses the payload hint from the crawler to decide which tests to run first,
    but also tries other attack types for completeness.

    Args:
        url: Page URL
        method: HTTP method
        field_name: Field name to test
        field_payload_hint: Suggested payload from crawler (used to prioritize)
        form_action: Form action URL
        all_fields: All fields in the form

    Returns:
        Dict with keys: confirmed, vuln_type, evidence, payload_used
    """
    result = {
        "confirmed": False,
        "vuln_type": "",
        "evidence": "",
        "payload_used": "",
    }

    # Decide test order based on payload hint
    is_sqli_hint = any(p in field_payload_hint for p in ["'", "OR", "UNION", "--"])
    is_xss_hint = any(p in field_payload_hint for p in ["<script>", "<img", "<svg"])

    tests = []
    if is_sqli_hint:
        tests = [("SQL Injection", test_sqli), ("XSS Reflected", test_xss)]
    elif is_xss_hint:
        tests = [("XSS Reflected", test_xss), ("SQL Injection", test_sqli)]
    else:
        tests = [("XSS Reflected", test_xss), ("SQL Injection", test_sqli)]

    for vuln_type, test_fn in tests:
        confirmed, evidence, payload_used = test_fn(
            url, method, field_name, form_action, all_fields
        )
        if confirmed:
            result["confirmed"] = True
            result["vuln_type"] = vuln_type
            result["evidence"] = evidence
            result["payload_used"] = payload_used
            return result

    return result


def active_scan(crawler_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run active scanning on all crawler results.

    Takes the output of the crawler (forms and fields) and actually
    submits payloads to test each injectable field.

    Args:
        crawler_results: Output from scanner.crawler.scan_forms()

    Returns:
        Enriched crawler results with added 'confirmed', 'evidence',
        and 'active_vuln_type' keys on each field.
    """
    total_fields = 0
    confirmed_count = 0

    for entry in crawler_results:
        url = entry.get("page_url", "")
        method = entry.get("method", "GET")
        form_action = entry.get("form_action", url)
        fields = entry.get("fields", [])

        for field in fields:
            field_name = field.get("name", "")
            field_type = field.get("type", "")

            # Skip non-injectable fields
            if not field_name or field_type in INJECTABLE_SKIP_TYPES:
                continue

            total_fields += 1
            payload_hint = field.get("payload", "")

            logger.info(f"Active testing: {field_name} ({method}) → {form_action}")

            result = test_field(
                url=url,
                method=method,
                field_name=field_name,
                field_payload_hint=payload_hint,
                form_action=form_action,
                all_fields=fields,
            )

            # Enrich the field with active scan results
            field["confirmed"] = result["confirmed"]
            field["evidence"] = result["evidence"]
            field["active_vuln_type"] = result["vuln_type"]
            if result["payload_used"]:
                field["payload"] = result["payload_used"]

            if result["confirmed"]:
                confirmed_count += 1
                logger.info(f"  ✓ VULNERABLE: {result['vuln_type']} — {result['evidence'][:80]}")
            else:
                logger.info(f"  ✗ Not confirmed for {field_name}")

    logger.info(f"Active scan complete: {confirmed_count}/{total_fields} fields confirmed vulnerable")
    return crawler_results
