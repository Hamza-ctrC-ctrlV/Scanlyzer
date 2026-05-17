"""
Patch Generator Module - Main AI Engine Orchestrator

Reads vulnerability reports, generates AI-powered security fixes,
and produces a structured patches report.

Pipeline:
1. Load vulnerabilities.json from scanner
2. For each vulnerability:
   a. Build prompt with context
   b. Send to Gemini API
   c. Parse JSON response
   d. Enrich with metadata
3. Save comprehensive patches.json

Responsibilities:
- Coordinate AI analysis of vulnerabilities
- Implement retry logic for transient failures
- Structure and validate AI responses
- Produce standardized patch reports
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .ai_client import get_ai_client
from .prompt_builder import PromptBuilder
from config.constants import (
    MAX_RETRY_ATTEMPTS,
    SCAN_ID_PREFIX,
)
from utils.helpers import extract_json_from_text, is_retryable_error

logger = logging.getLogger(__name__)


class PatchGenerator:
    """
    Orchestrates the full patch generation pipeline.
    
    Processes vulnerability reports through the AI engine to generate
    security fixes and structured remediation guidance.
    
    Attributes:
        ai_client (AIClient): Client for Gemini API communication
        prompt_builder (PromptBuilder): Builds AI prompts from vulnerabilities
    """
    
    def __init__(self) -> None:
        """
        Initialize patch generator with AI client and prompt builder.
        
        Side Effects:
            Logs initialization message
        """
        self.ai_client = get_ai_client()
        self.prompt_builder = PromptBuilder()
        logger.info("PatchGenerator initialized")

    def generate_all_patches(
        self,
        vulnerabilities_path: Optional[str] = None,
        output_path: Optional[str] = None,
        vulnerabilities_data: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for patch generation.
        
        Reads vulnerabilities from file or in-memory data, processes each one
        through the AI engine, and saves results to patches.json file.
        
        Args:
            vulnerabilities_path (Optional[str]): Path to vulnerabilities.json from scanner
            output_path (Optional[str]): Path where patches.json will be saved
            vulnerabilities_data (Optional[Dict]): In-memory vulnerability report
                (takes precedence over vulnerabilities_path)

        Returns:
            Dict[str, Any]: Structured patches report containing:
                - scan_id: Identifier for this scan
                - generated_at: ISO timestamp of generation
                - total_patches: Count of processed vulnerabilities
                - patches: List of patch objects

        Raises:
            ValueError: If neither vulnerabilities_path nor vulnerabilities_data provided

        Side Effects:
            - Writes patches.json to output_path if provided
            - Logs progress and status messages
        """
        # Load vulnerabilities from provided source
        if vulnerabilities_data is not None:
            scan_data = vulnerabilities_data
            logger.info("Loading vulnerabilities from in-memory report data")
        else:
            if not vulnerabilities_path:
                raise ValueError("vulnerabilities_path or vulnerabilities_data is required")
            logger.info(f"Loading vulnerabilities from: {vulnerabilities_path}")
            with open(vulnerabilities_path, "r", encoding="utf-8") as f:
                scan_data = json.load(f)

        vulnerabilities = scan_data.get("vulnerabilities", [])
        scan_id = scan_data.get("scan_id", "unknown")

        # Create output directory early for empty scans
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Handle empty vulnerability list
        if not vulnerabilities:
            logger.info("No vulnerabilities found in report. Returning empty patches.")
            empty_result = {
                "scan_id": scan_id,
                "generated_at": datetime.now().isoformat(),
                "total_patches": 0,
                "patches": []
            }
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(empty_result, f, indent=2, ensure_ascii=False)
                logger.info(f"Empty patch report saved to: {output_path}")
            return empty_result

        logger.info(f"Found {len(vulnerabilities)} vulnerability(ies) to analyze")

        patches = []
        for i, vuln in enumerate(vulnerabilities):
            vuln_id = vuln.get("id", f"VULN-{i+1:03d}")
            vuln_type = vuln.get("type", "Unknown")
            file_name = vuln.get("contexte_code", {}).get("fichier", "unknown")

            logger.info(f"Processing ({i+1}/{len(vulnerabilities)}) {vuln_id} - {vuln_type} in {file_name}")

            patch = self._process_single_vulnerability(vuln, model=model)
            patches.append(patch)

            # Add small delay between API calls to respect rate limits
            if i < len(vulnerabilities) - 1:
                time.sleep(1)

        # Build final result
        result = {
            "scan_id": scan_id,
            "generated_at": datetime.now().isoformat(),
            "total_patches": len(patches),
            "patches": patches
        }

        # Save to disk if output path provided
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"Patches saved to: {output_path}")
        else:
            logger.info("Patch report kept in memory (no output path provided)")
        
        return result

    def _process_single_vulnerability(
        self,
        vuln: Dict[str, Any],
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a single vulnerability through the full patch generation pipeline.
        
        Implements retry logic with exponential backoff for transient errors.
        Falls back to default response if all retries exhausted.
        
        Pipeline:
        1. Build prompt from vulnerability context
        2. Send to Gemini API with retry logic
        3. Parse and validate JSON response
        4. Enrich with vulnerability metadata
        
        Args:
            vuln (Dict): Vulnerability object from scanner report

        Returns:
            Dict: Patch object with vulnerability + AI analysis + fixes
                - vuln_id, type, severity, file, url, field: Metadata
                - explication, solution: AI-generated analysis
                - code_vulnerable, code_corrige: Code examples
                - status: "success" or "error"
                - error_message: Only present if status="error"
        """
        vuln_id = vuln.get("id", "UNKNOWN")
        last_error = None

        # Retry loop with exponential backoff
        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                # Step 1: Build prompt
                prompt = self.prompt_builder.build(vuln)
                logger.debug(f"Prompt built for {vuln_id}: {len(prompt)} chars")

                # Step 2: Call AI (pass model when available)
                logger.info(f"Sending {vuln_id} to AI backend (attempt {attempt}/{MAX_RETRY_ATTEMPTS})")
                raw_response = self.ai_client.send_prompt(prompt, model=model)
                logger.debug(f"Response received: {len(raw_response)} chars")

                # Step 3: Parse response
                parsed = self._parse_ai_response(raw_response, vuln_id)

                # Step 4: Build final patch object
                patch = {
                    "vuln_id": vuln_id,
                    "type": vuln.get("type"),
                    "severity": vuln.get("severity"),
                    "fichier": vuln.get("contexte_code", {}).get("fichier", "unknown"),
                    "url": vuln.get("url"),
                    "champ": vuln.get("champ"),
                    "explication": parsed.get("explication", ""),
                    "solution": parsed.get("solution", ""),
                    "code_vulnerable": parsed.get("code_vulnerable", vuln.get("contexte_code", {}).get("code_vulnerable", "")),
                    "code_corrige": parsed.get("code_corrige", ""),
                    "status": "success"
                }
                logger.info(f"Successfully generated patch for {vuln_id}")
                return patch

            except Exception as e:
                last_error = e
                retryable = is_retryable_error(e)
                logger.warning(f"Attempt {attempt}/{MAX_RETRY_ATTEMPTS} failed for {vuln_id}: {str(e)} (retryable: {retryable})")

                # Retry if transient error and attempts remain
                if attempt < MAX_RETRY_ATTEMPTS and retryable:
                    backoff_time = attempt  # Simple backoff: 1s, 2s, 3s
                    time.sleep(backoff_time)
                    continue

                break

        # Fallback patch if all retries failed
        logger.error(f"Failed to generate patch for {vuln_id} after {MAX_RETRY_ATTEMPTS} attempts")
        return {
            "vuln_id": vuln_id,
            "type": vuln.get("type"),
            "severity": vuln.get("severity"),
            "fichier": vuln.get("contexte_code", {}).get("fichier", "unknown"),
            "url": vuln.get("url"),
            "champ": vuln.get("champ"),
            "explication": "AI analysis failed after retries. Please review this vulnerability manually.",
            "solution": "Refer to OWASP guidelines for remediation.",
            "code_vulnerable": vuln.get("contexte_code", {}).get("code_vulnerable", ""),
            "code_corrige": "",
            "status": "error",
            "error_message": str(last_error) if last_error else "Unknown error"
        }

    def _parse_ai_response(self, raw: str, vuln_id: str) -> Dict[str, Any]:
        """
        Parse JSON response from Gemini API.
        
        Handles various response formats including markdown code blocks
        and extra whitespace. Uses shared utility function.
        
        Args:
            raw (str): Raw response text from AI
            vuln_id (str): Vulnerability ID (for error context)

        Returns:
            Dict[str, Any]: Parsed response with keys:
                - explication: Vulnerability explanation
                - solution: Remediation guidance
                - code_vulnerable: Example vulnerable code
                - code_corrige: Example patched code

        Raises:
            ValueError: If JSON cannot be extracted or parsed
        """
        # Use shared utility to extract JSON
        parsed = extract_json_from_text(raw)
        
        if parsed is None:
            raise ValueError(f"No JSON object found in AI response for {vuln_id}")

        # Ensure all required keys are present
        required_keys = ["explication", "solution", "code_vulnerable", "code_corrige"]
        for key in required_keys:
            if key not in parsed:
                logger.warning(f"Missing field '{key}' in AI response for {vuln_id}, using placeholder")
                parsed[key] = f"[Missing field: {key}]"

        return parsed