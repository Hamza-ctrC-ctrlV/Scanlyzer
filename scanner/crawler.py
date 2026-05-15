"""
Web Crawler Module - Form and Parameter Discovery

Crawls websites to discover forms, input fields, and URL parameters
for security analysis.

Features:
- Respects robots.txt to avoid crawling restricted areas
- Extracts form data (action, method, fields, attributes)
- Identifies GET parameters from URLs
- Generates appropriate payloads for each field type
- Avoids infinite loops and excessive crawling

Responsibilities:
- Perform breadth-first search crawl of website
- Extract and structure form and parameter information
- Respect crawl limits (max pages, max depth, domain boundaries)
- Apply intelligent payload selection to fields
"""

import os
import requests
import time
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from urllib.robotparser import RobotFileParser
from collections import deque
import json
from typing import List, Dict, Any

from .payloads import choose_payload
from config.constants import (
    DEFAULT_MAX_PAGES,
    DEFAULT_MAX_DEPTH,
    CRAWL_DELAY_SECONDS,
    ROBOTS_TXT_TIMEOUT,
    INJECTABLE_SKIP_TYPES,
)

logger = logging.getLogger(__name__)


def summarize_crawl_results(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """Return simple counts for CLI output and tests."""
    return {
        "pages": len({row["page_url"] for row in results}),
        "forms": sum(1 for row in results if row.get("form_id") != "url_params"),
        "params": sum(1 for row in results if row.get("form_id") == "url_params"),
        "total": len(results),
    }


def save_forms_report(results: List[Dict[str, Any]], output_path: str) -> None:
    """Persist crawl results to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file_handle:
        json.dump(results, file_handle, indent=2)


def build_robot_parser(seed_url: str) -> RobotFileParser:
    """
    Fetch and parse robots.txt for a domain.
    
    Creates a single RobotFileParser instance that can be reused
    for multiple URL checks within the same crawl (optimization).
    
    Args:
        seed_url (str): Base URL to extract domain from
        
    Returns:
        RobotFileParser: Initialized parser (may be empty if robots.txt unavailable)
        
    Side Effects:
        Logs failures to fetch robots.txt
    """
    parsed = urlparse(seed_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    
    rp = RobotFileParser()
    rp.set_url(robots_url)
    
    try:
        rp.read()
        logger.debug(f"Successfully parsed robots.txt from {robots_url}")
    except Exception as e:
        logger.debug(f"Could not fetch robots.txt from {robots_url}: {e}")
        # Continue anyway - allow everything if robots.txt unavailable
    
    return rp


def scan_forms(
    seed_url: str,
    max_pages: int = DEFAULT_MAX_PAGES,
    max_depth: int = DEFAULT_MAX_DEPTH
) -> List[Dict[str, Any]]:
    """
    Crawl a website and extract forms and URL parameters.
    
    Performs breadth-first crawl starting from seed_url, respecting robots.txt
    and crawl limits (max pages, depth, domain boundaries).
    
    For each discovered page:
    1. Extract all HTML forms with field details
    2. Extract GET parameters from URL
    3. Generate appropriate payloads for injection testing
    
    Crawl Limits:
    - max_pages: Stop after discovering this many unique URLs
    - max_depth: Stop following links deeper than this level
    - Domain: Only crawl same domain as seed_url
    - robots.txt: Respect disallow directives
    
    Args:
        seed_url (str): Starting URL for crawl
        max_pages (int): Maximum pages to crawl (default: 50)
        max_depth (int): Maximum link depth to follow (default: 2)

    Returns:
        List[Dict]: Results containing:
            - page_url: URL page was found on
            - form_action: Form submission target URL
            - method: HTTP method (GET/POST)
            - form_id: HTML form id attribute
            - enctype: Form encoding type
            - field_count: Number of fields
            - fields: List of field objects with full details

    Side Effects:
        - Makes HTTP requests to seed_url and discovered links
        - Logs crawl progress and errors
        - Respects CRAWL_DELAY_SECONDS between requests
    """
    base_domain = urlparse(seed_url).netloc
    visited = set()
    queue = deque([(seed_url, 0)])  # (url, depth)
    results = []

    # Parse robots.txt once and reuse
    rp = build_robot_parser(seed_url)
    logger.info(f"Starting crawl from {seed_url}")

    while queue:
        url, depth = queue.popleft()

        # Skip if: already visited, too deep, off-domain, or max pages reached
        if url in visited or depth > max_depth or len(visited) >= max_pages:
            continue
        
        if urlparse(url).netloc != base_domain:
            logger.debug(f"Skipping off-domain URL: {url}")
            continue

        # Check robots.txt
        if not rp.can_fetch("*", url):
            logger.debug(f"Blocked by robots.txt: {url}")
            continue

        visited.add(url)
        logger.info(f"Crawling ({len(visited)}/{max_pages}): {url}")

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract GET parameters from URL query string
        parsed_url = urlparse(url)
        if parsed_url.query:
            get_params = parse_qs(parsed_url.query)
            results.append({
                "page_url":    url,
                "form_action": url,
                "method":      "GET",
                "form_id":     "url_params",
                "enctype":     "",
                "field_count": len(get_params),
                "fields": [
                    {
                        "id":           "",
                        "tag":          "url_param",
                        "type":         "text",
                        "name":         k,
                        "label":        "",
                        "placeholder":  "",
                        "value":        v[0],
                        "options":      [],
                        "required":     False,
                        "minlength":    "",
                        "maxlength":    "",
                        "pattern":      "",
                        "autocomplete": "",
                        "disabled":     False,
                        "readonly":     False,
                        "severity":     "",
                        "payload":      "",
                        "champ":        "",
                        "code_vulnerable": f"GET parameter in URL: {url}",
                    }
                    for k, v in get_params.items()
                ],
            })

        # Extract HTML forms
        for form in soup.find_all("form"):
            fields = []
            
            for tag in form.find_all(["input", "textarea", "select", "button"]):
                # Collect dropdown options
                options = []
                if tag.name == "select":
                    options = [opt.get_text(strip=True) for opt in tag.find_all("option")]

                # Find associated label text
                label_text = ""
                field_id = tag.get("id", "")
                if field_id:
                    label = soup.find("label", {"for": field_id})
                    if label:
                        label_text = label.get_text(strip=True)

                # Generate appropriate payload for field
                payload = choose_payload(tag.get("name", ""), tag.get("type", "text"))

                fields.append({
                    "id":           field_id,
                    "tag":          tag.name,
                    "type":         tag.get("type", "text"),
                    "name":         tag.get("name", ""),
                    "label":        label_text,
                    "placeholder":  tag.get("placeholder", ""),
                    "value":        tag.get("value", ""),
                    "options":      options,
                    "required":     tag.has_attr("required"),
                    "minlength":    tag.get("minlength", ""),
                    "maxlength":    tag.get("maxlength", ""),
                    "pattern":      tag.get("pattern", ""),
                    "autocomplete": tag.get("autocomplete", ""),
                    "disabled":     tag.has_attr("disabled"),
                    "readonly":     tag.has_attr("readonly"),
                    "severity":     "",
                    "payload":      payload,
                    "champ":        "",
                    "code_vulnerable": str(form),
                })

            results.append({
                "page_url":    url,
                "form_action": urljoin(url, form.get("action", "")),
                "method":      form.get("method", "get").upper(),
                "form_id":     form.get("id", ""),
                "enctype":     form.get("enctype", ""),
                "field_count": len(fields),
                "fields":      fields,
            })

        # Queue new links, stripping fragments but keeping query strings
        for a_tag in soup.find_all("a", href=True):
            next_url = urljoin(url, a_tag["href"])
            # Remove fragment but keep query string
            next_url = urlparse(next_url)._replace(fragment="").geturl()
            if next_url not in visited:
                queue.append((next_url, depth + 1))

        # Respect server load with delay
        time.sleep(CRAWL_DELAY_SECONDS)

    logger.info(f"Crawl complete: {len(visited)} pages, {len(results)} forms/parameters")
    return results


def get_injectable_fields(form: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filter form fields to only those suitable for injection testing.
    
    Skips non-injectable field types (buttons, disabled, readonly).
    Includes hidden fields intentionally - developers often forget to
    validate them server-side, making them common injection points.
    
    Args:
        form (Dict): Form object containing 'fields' list

    Returns:
        List[Dict]: Filtered list of injectable field objects
    """
    return [
        f for f in form["fields"]
        if not f["disabled"]
        and not f["readonly"]
        and f["type"] not in INJECTABLE_SKIP_TYPES
        and f["name"]  # Skip fields with no name
    ]


if __name__ == "__main__":
    data = scan_forms("http://localhost/vuln_site/", max_pages=30, max_depth=2)
    summary = summarize_crawl_results(data)

    print(f"\n✓ Crawl complete")
    print(f"  Pages scanned : {summary['pages']}")
    print(f"  Forms found   : {summary['forms']}")
    print(f"  GET param sets: {summary['params']}")
    print(f"  Total entries : {summary['total']}")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(project_root, "reports", "forms_report.json")
    save_forms_report(data, output_path)
    print(f"\n  Report saved → {output_path}")