"""
Prompt Builder Module - AI Prompt Construction

Builds context-rich prompts for the Gemini API based on vulnerability type.

Prompt quality directly impacts AI analysis quality. Each vulnerability type
receives a specialized prompt template with relevant context, instructions,
and expected output format.

Responsibilities:
- Generate patches prompts (for code fix generation)
- Generate assessment prompts (for vulnerability classification)
- Ensure consistent JSON output format
- Provide type-specific instructions and examples
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Constructs specialized prompts for the AI based on vulnerability type.

    Maintains separate prompt templates for SQL Injection, XSS, and generic
    vulnerabilities to maximize analysis quality and fix accuracy.
    """

    SYSTEM_CONTEXT = """You are a senior cybersecurity engineer and PHP developer.
Your job is to analyze a specific security vulnerability found in a PHP web application,
explain it clearly, and provide a corrected version of the code.

You must respond ONLY in the following exact JSON format, with no extra text before or after:
{
  "explication": "Plain language explanation of why the code is vulnerable and what an attacker could do",
  "solution": "One sentence describing the correct fix approach",
  "code_vulnerable": "The original vulnerable code exactly as provided",
  "code_corrige": "The fully corrected and secure version of the code"
}

Rules:
- The corrected code must be syntactically valid PHP
- Do not add markdown backticks around the JSON
- Do not add any commentary outside the JSON object
- The explanation must be understandable by a developer with no security background
- The corrected code must be complete and ready to copy-paste
"""

    ASSESSMENT_CONTEXT = """You are a senior application security analyst.
Your job is to classify a detected web input issue by severity and likely vulnerability type.

You must respond ONLY in the following exact JSON format, with no extra text before or after:
{
    "type": "Likely vulnerability class such as SQL Injection, XSS Reflected, XSS Stored, CSRF, File Upload, or Unclassified Vulnerability",
    "severity": "One of CRITICAL, HIGH, MEDIUM, LOW, or INFO",
    "confidence": "One of HIGH, MEDIUM, or LOW",
    "description": "Short plain-language summary of the security risk"
}

Rules:
- Base the assessment on the field name, method, payload, and page context
- If the signal is weak, return Unclassified Vulnerability with LOW severity
- Do not add markdown backticks around the JSON
- Do not add any commentary outside the JSON object
"""

    def build(self, vulnerability: Dict[str, Any]) -> str:
        """
        Build a patch generation prompt based on vulnerability type.

        Routes to the appropriate prompt template (SQL injection, XSS, or generic)
        based on the vulnerability type classification.

        Args:
            vulnerability (Dict): Vulnerability object containing:
                - type: Classification (SQL Injection, XSS, etc.)
                - severity: Risk level
                - url: Target URL
                - champ: Input field name
                - contexte_code: Code context with vulnerable snippet
                - method: HTTP method (GET/POST)
                - payload_used: Tested payload
                - evidence: Supporting evidence

        Returns:
            str: Complete prompt ready to send to AI
        """
        vuln_type = vulnerability.get("type", "").lower()
        logger.debug(f"Building prompt for vulnerability type: {vuln_type}")

        if "sql injection" in vuln_type or "sqli" in vuln_type:
            return self._build_sqli_prompt(vulnerability)
        if any(xss_type in vuln_type for xss_type in ["xss", "cross-site scripting"]):
            return self._build_xss_prompt(vulnerability)

        logger.debug(f"Using generic prompt for type: {vuln_type}")
        return self._build_generic_prompt(vulnerability)

    def build_assessment(self, vulnerability: Dict[str, Any]) -> str:
        """
        Build a vulnerability classification/assessment prompt.

        Asks the AI to classify an input field's security risk based on
        field characteristics, payloads tested, and code context.

        Args:
            vulnerability (Dict): Vulnerability candidate object containing:
                - url: Page URL
                - method: HTTP method
                - champ: Field name
                - payload_used: Test payload
                - contexte_code: Code context

        Returns:
            str: Assessment prompt ready for AI
        """
        code_ctx = vulnerability.get("contexte_code", {})

        return f"""{self.ASSESSMENT_CONTEXT}

--- DETECTED INPUT ---
Page URL      : {vulnerability.get('url', '')}
File          : {code_ctx.get('fichier', 'unknown')}
Method        : {vulnerability.get('method', 'GET')}
Field         : {vulnerability.get('champ', '')}
Payload used  : {vulnerability.get('payload_used', '')}
Evidence      : {vulnerability.get('evidence', '')}
Code snippet  : {code_ctx.get('code_vulnerable', 'Not available')}
"""

    def _build_sqli_prompt(self, v: Dict[str, Any]) -> str:
        """
        Build SQL Injection-specific prompt.

        Provides detailed context about SQL injection vulnerability and
        requests a fix using prepared statements/PDO.

        Args:
            v (Dict): Vulnerability object

        Returns:
            str: SQL Injection-specific prompt
        """
        code_ctx = v.get("contexte_code", {})

        return f"""{self.SYSTEM_CONTEXT}

--- VULNERABILITY REPORT ---
Type          : SQL Injection
Severity      : {v.get('severity', 'CRITICAL')}
File          : {code_ctx.get('fichier', 'unknown')}
Estimated line: {code_ctx.get('ligne_estimee', 'unknown')}
URL attacked  : {v.get('url', '')}
Input field   : {v.get('champ', '')} ({v.get('method', 'POST')} method)
Payload used  : {v.get('payload_used', '')}
Evidence found: {v.get('evidence', '')}

Vulnerable code:
{code_ctx.get('code_vulnerable', 'Not available')}

Instructions:
1. Explain why this specific code allows SQL injection
2. Rewrite the code using PDO Prepared Statements
3. Make sure the corrected code handles the same logic as the original (login check, search, etc.)
4. Add password_hash() if the code handles authentication
"""

    def _build_xss_prompt(self, v: Dict[str, Any]) -> str:
        """
        Build XSS (Reflected/Stored) specific prompt.

        Provides detailed context about XSS vulnerability, noting the
        difference between stored and reflected variants and their fixes.

        Args:
            v (Dict): Vulnerability object

        Returns:
            str: XSS-specific prompt with context
        """
        code_ctx = v.get("contexte_code", {})
        xss_subtype = v.get("type", "XSS")

        stored_note = ""
        if "stored" in xss_subtype.lower():
            stored_note = """
Note: This is a STORED XSS vulnerability. The fix must be applied in TWO places:
1. At insertion time (sanitize input before saving to the database)
2. At display time (escape output before rendering in HTML)
"""

        return f"""{self.SYSTEM_CONTEXT}

--- VULNERABILITY REPORT ---
Type          : {xss_subtype}
Severity      : {v.get('severity', 'HIGH')}
File          : {code_ctx.get('fichier', 'unknown')}
Estimated line: {code_ctx.get('ligne_estimee', 'unknown')}
URL attacked  : {v.get('url', '')}
Input field   : {v.get('champ', '')} ({v.get('method', 'GET')} method)
Payload used  : {v.get('payload_used', '')}
Evidence found: {v.get('evidence', '')}
{stored_note}
Vulnerable code:
{code_ctx.get('code_vulnerable', 'Not available')}

Instructions:
1. Explain why this specific code allows {xss_subtype}
2. Rewrite the code using htmlspecialchars() with ENT_QUOTES and UTF-8
3. For stored XSS: show both the insertion fix (strip_tags + trim) and the display fix
4. Preserve the original functionality of the code
"""

    def _build_generic_prompt(self, v: Dict[str, Any]) -> str:
        """
        Build generic/fallback prompt for unclassified vulnerabilities.

        Used when vulnerability type doesn't match SQL Injection or XSS.
        Still provides full context but with generic instructions.

        Args:
            v (Dict): Vulnerability object

        Returns:
            str: Generic vulnerability prompt
        """
        code_ctx = v.get("contexte_code", {})

        return f"""{self.SYSTEM_CONTEXT}

--- VULNERABILITY REPORT ---
Type          : {v.get('type', 'Unknown')}
Severity      : {v.get('severity', 'UNKNOWN')}
File          : {code_ctx.get('fichier', 'unknown')}
URL attacked  : {v.get('url', '')}
Input field   : {v.get('champ', '')}
Payload used  : {v.get('payload_used', '')}
Evidence found: {v.get('evidence', '')}

Vulnerable code:
{code_ctx.get('code_vulnerable', 'Not available')}

Instructions:
1. Explain why this code is vulnerable
2. Provide the corrected and secure version
3. Follow PHP security best practices
"""