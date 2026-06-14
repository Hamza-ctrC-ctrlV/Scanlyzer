# Scanlyzer — AI-Powered Web Vulnerability Scanner

A comprehensive, full-stack web security vulnerability scanner with AI-powered patch generation and real-time security scoring based on confirmed vulnerabilities. Built with Python (Flask) backend and React frontend.

![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask 3.1](https://img.shields.io/badge/Flask-3.1-green)
![React 19](https://img.shields.io/badge/React-19-61dafb)
![License MIT](https://img.shields.io/badge/License-MIT-yellow)

---

## Overview

Scanlyzer automatically discovers and analyzes web vulnerabilities through an intelligent multi-stage pipeline:

1. **Web Crawling** — Discover forms, input fields, and URL parameters
2. **Active Testing** — Test discovered fields with security payloads
3. **AI Classification** — Classify findings using Gemini, Groq, or a local LLM
4. **Patch Generation** — Generate secure code fixes with step-by-step guidance
5. **Security Scoring** — Track confirmed vulnerabilities with accuracy-based scoring
6. **Cloud Storage** — Store and retrieve scans via Supabase

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Features](#features)
- [Project Architecture](#project-architecture)
- [File Organization](#file-organization)
- [Key Components](#key-components)
- [Development Guide](#development-guide)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before installing Scanlyzer, ensure you have the following:

- **Python 3.9+** with pip
- **Node.js 14+** with npm
- **AI backend** — one of: Gemini API key, Groq API key, or a running local LM Studio instance
- **Supabase account** — free tier is sufficient

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd scanlyzer
```

### 2. Set Up the Python Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## Configuration

Copy the environment template and fill in your credentials:

```bash
cp env.example .env
```

### Environment Variables

```env
# AI Backend Selection
AI_BACKEND=gemini                    # Options: gemini | groq | local

# Gemini API (Free — 60 req/min)
GEMINI_API_KEY=your_key_here

# Groq API (Free — 30 req/min)
GROQ_API_KEY=your_key_here
GROQ_MODEL=meta-llama/llama-3-8b-instruct

# Local LM Studio
# AI_LOCAL_API_URL=https://your-tunnel.example.com
# AI_LOCAL_MODEL=your-model-id

# Flask Server
FLASK_PORT=5000
FLASK_DEBUG=False                    # Never True in production

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key

# Optional: Crawler Behavior
# DEFAULT_MAX_PAGES=50
# DEFAULT_MAX_DEPTH=2
# CRAWL_DELAY_SECONDS=0.5
```

### Key Configuration File — `config/constants.py`

```python
# Rate Limits
DEFAULT_DAILY_LIMIT = 200
DEFAULT_HOURLY_LIMIT = 50
SCAN_ROUTE_RATE_LIMIT = "10 per minute"

# Crawler
DEFAULT_MAX_PAGES = 50
DEFAULT_MAX_DEPTH = 2
CRAWL_DELAY_SECONDS = 0.5

# API
API_REQUEST_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3

# Vulnerability Classification
INJECTABLE_SKIP_TYPES = {"hidden", "submit", "button", ...}
```

---

## Running the Application

Start each component in a separate terminal:

```bash
# Terminal 1 — Backend
python app.py

# Terminal 2 — Frontend
cd frontend && npm start

# Terminal 3 — Test site (optional)
cd vulnerable_site && php -S localhost:8000
```

| Service      | URL                     |
|--------------|-------------------------|
| Frontend     | http://localhost:3000   |
| Backend API  | http://localhost:5000   |
| Test site    | http://localhost:8000   |

---

## Features

### Intelligent Discovery

- **Smart Crawler** — BFS crawling with configurable depth and page limits
- **Form Detection** — Automatic extraction of forms, fields, and HTTP methods
- **Parameter Discovery** — GET/POST parameter identification
- **robots.txt Compliance** — Respects crawl directives

### AI-Powered Analysis

- **Multi-Model Support** — Gemini, Groq (Llama), or local LM Studio
- **Vulnerability Classification** — SQL Injection, XSS, CSRF, CORS, and more
- **Intelligent Assessment** — Severity and confidence scoring
- **Contextual Analysis** — Code-aware vulnerability understanding

### Automated Remediation

- **Patch Generation** — AI-generated secure code fixes
- **Language Support** — PHP, Python, JavaScript code examples
- **Best Practices** — OWASP-compliant recommendations
- **Step-by-Step Guidance** — Clear, actionable fix instructions

### Security Scoring System

- **Confirmation-Based** — `Score = (confirmed_vulns / total_vulns) × 100`
- **Color Coding** — Red (high) → Orange (medium) → Green (low)
- **Real-Time Updates** — Immediate score recalculation on confirmation
- **Historical Tracking** — Compare results across scan sessions

### Authentication and Access Control

- **Rate Limiting** — Per-endpoint and global limits
- **User Authentication** — Email/password with JWT tokens
- **Domain Verification** — Prevents unauthorized scanning of external targets
- **Row-Level Security** — User data isolation via Supabase RLS

### Web Dashboard

- Real-time scan progress monitoring
- Interactive vulnerability reports with severity distribution charts
- Historical scan management
- PDF export capability

---

## Project Architecture

### System Diagram

```
+--------------------------------------------+
|         React Frontend (Port 3000)         |
|  Dashboard  |  History  |  Reports  |  Auth|
+---------------------+----------------------+
                      |  HTTP/REST
                      v
+--------------------------------------------+
|         Flask Backend API (Port 5000)      |
|   Rate Limiting  |  Auth  |  Scan Routes  |
+-----------+------------------+-------------+
            |                  |
      +-----v----+        +----v------+
      |  Scanner |        | AI Engine |
      | Crawler  |        | Classifier|
      | Exporter |        | Patcher   |
      | Tester   |        | Prompt    |
      +----------+        +-----------+
            |                  |
            +--------+---------+
                     v
          +--------------------+
          |  Supabase (Cloud)  |
          |  Database          |
          |  Auth              |
          |  Storage           |
          +--------------------+
```

### Scan Lifecycle

```
1. User initiates scan via Dashboard
         |
2. Frontend  POST /api/scan  (target URL)
         |
3. Backend validates URL and domain ownership
         |
4. Background thread starts:
   +-- Crawler discovers forms and params
   +-- Active Scanner tests each field
   +-- Exporter builds vulnerabilities.json
   +-- AI Engine generates patches.json
         |
5. Security score computed from confirmed vulns
         |
6. Results stored in Supabase
         |
7. Frontend displays report
         |
8. User saves, exports, or compares scans
```

---

## File Organization

### Backend

```
project-root/
|-- app.py                          # Flask app entry point
|-- requirements.txt                # Python dependencies
|
|-- config/
|   |-- __init__.py
|   +-- constants.py                # Rate limits, crawler defaults, classification settings
|
|-- utils/
|   |-- __init__.py
|   |-- helpers.py                  # JSON parsing, error responses, score calculation
|   |-- security.py                 # URL validation, SSRF prevention
|   +-- state.py                    # In-memory scan state management
|
|-- scanner/
|   |-- __init__.py
|   |-- crawler.py                  # BFS web crawler with robots.txt support
|   |-- active_scanner.py           # Payload injection and result testing
|   |-- exporter.py                 # Convert raw results to vulnerabilities.json
|   +-- payloads.py                 # Payload templates organized by field type
|
|-- ai_engine/
|   |-- __init__.py
|   |-- ai_client.py                # Gemini / Groq / LM Studio client wrapper
|   |-- patch_generator.py          # Patch generation orchestration
|   |-- prompt_builder.py           # Specialized prompts per vulnerability type
|   +-- supabase_client.py          # Database operations and user auth
|
|-- api/
|   |-- __init__.py
|   |-- scan_routes.py              # POST /scan, GET /scan-result, etc.
|   |-- report_routes.py            # Save and retrieve scans
|   |-- verify_routes.py            # Domain verification
|   +-- auth.py                     # Signup, login, token verification
|
|-- reports/
|   |-- vulnerabilities.json        # Detected issues (includes confirmed field)
|   +-- patches.json                # AI-generated fixes
|
|-- vulnerable_site/
|   |-- index.php
|   |-- sqli.php
|   +-- xss.php
|
+-- env.example
```

### Frontend

```
frontend/
|-- package.json
|-- public/
|   +-- index.html
|
+-- src/
    |-- index.js
    |
    |-- app/
    |   +-- App.js                  # Main app component and routing
    |
    |-- pages/
    |   |-- DashboardPage.js
    |   |-- HistoryPage.js
    |   |-- LoginPage.js
    |   |-- SignupPage.js
    |   |-- VerifyPage.js
    |   +-- index.js
    |
    |-- components/
    |   |-- ScanInput.js
    |   |-- ProgressBar.js
    |   |-- ReportViewer.js
    |   |-- VulnerabilityList.js
    |   |-- FixesList.js
    |   |-- Charts.js
    |   |-- Header.js
    |   |-- AIChat.js
    |   |-- CodeBlock.js
    |   |-- Skeleton.js
    |   |-- Icons.js
    |   +-- index.js
    |
    |-- styles/
    |   +-- index.css
    |
    |-- helpers/
    |   |-- reportHelpers.js
    |   |-- validationHelpers.js
    |   |-- historyHelpers.js
    |   |-- pdfHelper.js
    |   +-- api.js
    |
    +-- config/
        +-- constants.js
```

---

## Key Components

### Scanner Module

Crawls the target, injects payloads, and normalizes findings.

```python
# Crawl and test
results = scan_forms(target_url, max_pages=30, max_depth=2)
results = active_scan(results)

# Build standardized report
report = build_vulnerabilities_report(results, target_url)
# report.vulnerabilities[].confirmed = True / False
```

### AI Engine Module

Classifies vulnerabilities and generates remediation patches.

```python
generator = PatchGenerator()
patches_report = generator.generate_all_patches(
    vulnerabilities_data=vulnerabilities_report,
    output_path="reports/patches.json"
)
```

### Security Scoring

**Algorithm:** `score = (confirmed_vulnerabilities / total_vulnerabilities) × 100`

Backend (`utils/helpers.py`):

```python
def compute_scan_stats(patches: list) -> tuple:
    confirmed_count = sum(1 for p in patches if p.get("confirmed") is True)
    score = (confirmed_count / len(patches)) * 100 if patches else 0
    return int(round(score)), stats, len(patches)
```

Frontend (`frontend/src/helpers/reportHelpers.js`):

```javascript
export function computeScore(patches) {
  if (!patches || patches.length === 0) return 0;
  const confirmedCount = patches.filter(p => p.confirmed === true).length;
  return Math.round((confirmedCount / patches.length) * 100);
}

export function getScoreColor(score) {
  if (score > 60) return "#ff4d6d";   // red    — critical
  if (score > 30) return "#ff8c42";   // orange — medium
  return "#06d6a0";                   // green  — low
}
```

| Score Range | Color  | Meaning  |
|-------------|--------|----------|
| 0–30%       | Green  | Low exposure |
| 31–60%      | Orange | Moderate exposure |
| 61–100%     | Red    | Critical exposure |

---

## Development Guide

### Adding a New Vulnerability Type

**Step 1 — Add payload to `scanner/payloads.py`:**

```python
def choose_payload(field_type: str) -> str:
    payloads = {
        "text":     ["' OR '1'='1", "<img src=x onerror=alert(1)>"],
        "email":    ["' AND 1=1--"],
        "your_type": ["your_payload_1", "your_payload_2"],
    }
    return random.choice(payloads.get(field_type, ["test"]))
```

**Step 2 — Update `ai_engine/prompt_builder.py`:**

```python
def build_classification_prompt(self, vuln_data):
    if "your_type" in vuln_data["type"].lower():
        return f"Classify this {your_type} vulnerability..."
```

**Step 3 — Add a test case to `vulnerable_site/`:**

```php
<?php
// your_test.php — intentionally vulnerable example
?>
```

### Adding a New API Endpoint

**Step 1 — Create the route handler (`api/myroutes.py`):**

```python
from flask import Blueprint, request, jsonify
from api.auth import require_auth

my_bp = Blueprint("my", __name__, url_prefix="/api")

@my_bp.route("/myendpoint", methods=["GET"])
@require_auth
def my_endpoint():
    user_id = request.auth_user.get("user_id")
    return jsonify({"success": True, "data": ...}), 200
```

**Step 2 — Register in `app.py`:**

```python
from api.myroutes import my_bp
app.register_blueprint(my_bp)
```

**Step 3 — Add frontend helper (`frontend/src/helpers/api.js`):**

```javascript
export async function callMyEndpoint(token) {
  return fetch(`${API_URL}/myendpoint`, {
    headers: { Authorization: `Bearer ${token}` }
  }).then(r => r.json());
}
```

---

## API Reference

### Authentication

**POST /auth/signup**

```bash
curl -X POST http://localhost:5000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"securepass"}'
```

```json
{ "success": true, "user_id": "uuid", "token": "jwt_token" }
```

**POST /auth/login**

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"securepass"}'
```

```json
{ "success": true, "token": "jwt_token", "user_id": "uuid" }
```

### Scanning

**POST /api/scan** — Initiate an asynchronous scan

```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"http://localhost:8000"}'
```

```json
{ "success": true, "scan_id": "scan_1234567890", "url": "http://localhost:8000" }
```

**GET /api/scan-result** — Retrieve completed scan

```bash
curl http://localhost:5000/api/scan-result?scan_id=scan_1234567890 \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "success": true,
  "score": 45,
  "stats": { "CRITICAL": 2, "HIGH": 1 },
  "vulnerabilities_report": {},
  "patches_report": {}
}
```

**GET /api/scan-progress** — Stream real-time progress (Server-Sent Events)

```bash
curl http://localhost:5000/api/scan-progress?scan_id=scan_1234567890 \
  -H "Authorization: Bearer $TOKEN"
```

```
data: {"step":"crawling","pct":10,"msg":"..."}
data: {"step":"active_scan","pct":50,"msg":"..."}
data: {"step":"done","pct":100,"msg":"..."}
```

### Reports

| Method | Endpoint                        | Description             |
|--------|---------------------------------|-------------------------|
| POST   | /api/save-scan                  | Save scan to Supabase   |
| GET    | /api/scans                      | List user's scans       |
| DELETE | /api/delete-scan?scan_id=X      | Delete a scan           |

### Domain Verification

| Method | Endpoint                  | Description              |
|--------|---------------------------|--------------------------|
| POST   | /api/verify-domain        | Verify domain ownership  |
| GET    | /api/verified-domains     | List verified domains    |

---

## Troubleshooting

### "Domain not verified" error

Go to the Verify page and complete domain ownership verification before scanning.

### Blank report or score showing 0

Check that the `confirmed` field is present on each vulnerability. This field is set by the active scanner — if it did not run, scores will default to zero.

### AI API timeouts

Increase `API_REQUEST_TIMEOUT` in `config/constants.py` and verify your API key and remaining rate limit quota.

### Frontend cannot reach backend

- Confirm the backend is running on port 5000
- Verify CORS in `app.py` allows `http://localhost:3000`
- Check the `proxy` setting in `frontend/package.json`

### Python import errors

Ensure the virtual environment is activated and dependencies are installed:

```bash
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

### Enabling Debug Mode

```bash
export FLASK_DEBUG=True
python app.py
```

### Persisting Logs to File

Add the following to `app.py`:

```python
import logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [Supabase Documentation](https://supabase.com/docs)
- [Google Gemini API](https://ai.google.dev/)
- [Groq API](https://console.groq.com/)

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.