"""
Scanner Exporter Module - Format Conversion

Converts scanner crawler output into standardized vulnerability report format.

Pipeline:
1. Receive raw crawler results (forms, fields, payloads)
2. Group into potential vulnerabilities
3. Use AI to classify each finding (type, severity)
4. Produce vulnerabilities.json report

Responsibilities:
- Map crawler findings to vulnerability schema
- Perform AI-based classification (with fallback)
- Generate unique vulnerability IDs
- Write standardized vulnerability reports
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from ai_engine.ai_client import get_ai_client
from ai_engine.prompt_builder import PromptBuilder
from config.constants import (
    SCAN_ID_PREFIX,
    INJECTABLE_SKIP_TYPES,
    DEFAULT_VULNERABILITY_ASSESSMENT,
)
from utils.helpers import extract_json_from_text

logger = logging.getLogger(__name__)


def build_vulnerabilities_report(
    results: List[Dict[str, Any]],
    target_url: str,
    output_path: Optional[str] = None,
    scan_duration_seconds: float = 0
) -> Dict[str, Any]:
    """
    Convert scanner results into standardized vulnerabilities.json report.
    
    Processes crawler output (forms and parameters) and converts each injectable
    field into a vulnerability entry. Uses AI to classify each finding.
    
    Pipeline:
    1. Iterate through crawler results
    2. Extract injectable fields from forms
    3. Generate AI classification for each field
    4. Build vulnerability schema entries
    5. Save to disk if output_path provided
    
    Args:
        results (List[Dict]): Raw crawler results from scanner
            Each dict should contain: page_url, method, form_id, fields
        target_url (str): Base URL that was scanned
        output_path (Optional[str]): Path to save vulnerabilities.json
        scan_duration_seconds (float): Duration of scanning in seconds

    Returns:
        Dict[str, Any]: Complete vulnerability report containing:
            - scan_id: Unique identifier for this scan
            - target_url: Base URL scanned
            - scan_date: ISO timestamp of scan
            - scan_duration_seconds: Total scan duration
            - pages_crawled: Count of unique pages visited
            - forms_found: Count of forms discovered
            - total_vulnerabilities: Count of potential vulnerabilities
            - vulnerabilities: List of vulnerability objects

    Side Effects:
        - Creates output directory if output_path provided
        - Writes vulnerabilities.json to disk
        - Logs classification progress and errors
    """
    vulnerabilities = []
    vuln_id_counter = 1
    pages = set()
    form_count = 0
    
    # Initialize AI client for classification (optional - fallback if unavailable)
    ai_client = None
    prompt_builder = PromptBuilder()
    try:
        ai_client = get_ai_client()
        logger.info("AI client initialized for vulnerability classification")
    except Exception as e:
        logger.warning(f"AI client initialization failed, will use fallback assessment: {e}")
        ai_client = None

    # Process each crawler result
    for entry in results:
        pages.add(entry.get('page_url'))
        
        # Count forms (URL parameters are indexed differently)
        if entry.get('form_id') != 'url_params':
            form_count += 1
        
        # Process each field in the result
        for field in entry.get('fields', []):
            # Skip fields with no name
            if not field.get('name'):
                continue
            
            # Skip non-injectable field types
            if field.get('type') in INJECTABLE_SKIP_TYPES:
                continue

            # If active scanning was run and field was NOT confirmed, skip it
            is_confirmed = field.get('confirmed', None)
            if is_confirmed is False:
                logger.debug(f"Skipping unconfirmed field: {field.get('name')}")
                continue

            vid = f"VULN-{vuln_id_counter:03d}"
            vuln_id_counter += 1

            code_vulnerable = field.get('code_vulnerable', '')
            active_evidence = field.get('evidence', '')
            active_vuln_type = field.get('active_vuln_type', '')

            # If active scan confirmed the vulnerability, use its type directly
            # Otherwise fall back to AI classification
            if active_vuln_type:
                assessment = {
                    'type': active_vuln_type,
                    'severity': 'CRITICAL' if 'SQL' in active_vuln_type else 'HIGH',
                    'confidence': 'HIGH',
                    'description': active_evidence or f'Confirmed {active_vuln_type} via active testing.',
                }
                logger.info(f"Using active scan result for {vid}: {active_vuln_type}")
            else:
                # Classify vulnerability using AI or fallback
                assessment = _assess_vulnerability(ai_client, prompt_builder, {
                    'id': vid,
                    'url': entry.get('page_url'),
                    'method': entry.get('method', 'GET'),
                    'champ': field.get('name'),
                    'payload_used': field.get('payload', ''),
                    'evidence': active_evidence,
                    'contexte_code': {
                        'fichier': os.path.basename(entry.get('page_url') or ''),
                        'ligne_estimee': 0,
                        'code_vulnerable': code_vulnerable
                    }
                })

            # Build vulnerability object
            vuln = {
                'id': vid,
                'type': assessment.get('type', 'Unclassified Vulnerability'),
                'severity': assessment.get('severity', 'UNKNOWN'),
                'url': entry.get('page_url'),
                'method': entry.get('method', 'GET'),
                'champ': field.get('name'),
                'payload_used': field.get('payload', ''),
                'evidence': active_evidence or '',
                'confidence': assessment.get('confidence', 'LOW'),
                'confirmed': bool(is_confirmed),
                'contexte_code': {
                    'fichier': os.path.basename(entry.get('page_url') or ''),
                    'ligne_estimee': 0,
                    'code_vulnerable': code_vulnerable
                },
                'description': assessment.get('description', 'Automatically detected security finding.')
            }
            vulnerabilities.append(vuln)
            status = "✓ CONFIRMED" if is_confirmed else "? unverified"
            logger.info(f"[{status}] {vuln['type']} in {field.get('name')} at {entry.get('page_url')}")

    # Build final report
    report = {
        'scan_id': f"{SCAN_ID_PREFIX}{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        'target_url': target_url,
        'scan_date': datetime.utcnow().isoformat(),
        'scan_duration_seconds': scan_duration_seconds,
        'pages_crawled': len(pages),
        'forms_found': form_count,
        'total_vulnerabilities': len(vulnerabilities),
        'vulnerabilities': vulnerabilities
    }

    # Save to disk if output path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Vulnerability report saved to {output_path}")

    return report


def _assess_vulnerability(
    ai_client: Optional[object],
    prompt_builder: PromptBuilder,
    vulnerability: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Classify a vulnerability using AI or return safe fallback.
    
    Attempts to use AI to classify the vulnerability type, severity, and
    confidence. If AI is unavailable or fails, returns the default fallback
    assessment.
    
    Args:
        ai_client (Optional[AIClient]): Initialized AI client, or None to skip AI
        prompt_builder (PromptBuilder): Prompt builder for classification
        vulnerability (Dict): Vulnerability object to classify

    Returns:
        Dict[str, Any]: Classification result with keys:
            - type: Vulnerability type (SQL Injection, XSS, etc.)
            - severity: Risk level (HIGH, MEDIUM, LOW, UNKNOWN)
            - confidence: Assessment confidence (HIGH, MEDIUM, LOW)
            - description: Human-readable explanation

    Side Effects:
        Logs failures and fallback usage
    """
    fallback = DEFAULT_VULNERABILITY_ASSESSMENT.copy()

    # Use fallback if AI client not available
    if not ai_client:
        logger.debug("No AI client available, using fallback assessment")
        return fallback

    try:
        # Build and send classification prompt
        prompt = prompt_builder.build_assessment(vulnerability)
        logger.debug(f"Sending assessment prompt for {vulnerability.get('id')}")
        
        raw = ai_client.send_prompt(prompt)
        
        # Parse AI response
        parsed_json = extract_json_from_text(raw)
        if parsed_json is None:
            logger.warning(f"Failed to extract JSON from assessment response, using fallback")
            return fallback
        
        # Validate all required keys are present
        for key in ('type', 'severity', 'confidence', 'description'):
            if key not in parsed_json or not parsed_json[key]:
                parsed_json[key] = fallback[key]
        
        logger.debug(f"Successfully classified {vulnerability.get('id')} as {parsed_json.get('type')}")
        return parsed_json
        
    except Exception as e:
        logger.warning(f"Failed to assess vulnerability {vulnerability.get('id')}: {e}, using fallback")
        return fallback
