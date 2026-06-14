from urllib.parse import urlparse
import re


def extract_domain(raw):
    """
    Takes any input the user might paste — full URL, bare domain,
    with or without www — and returns a clean lowercase domain.

    Examples:
        "https://www.example.com/products"  →  "example.com"
        "http://blog.example.com"           →  "blog.example.com"
        "example.com"                       →  "example.com"
        "  EXAMPLE.COM  "                   →  "example.com"
    """
    raw = raw.strip()

    if not raw.startswith("http"):
        raw = "https://" + raw

    parsed = urlparse(raw)
    host = parsed.netloc

    # Strip www. from the start but leave other subdomains intact
    host = re.sub(r"^www\.", "", host)

    return host.lower()