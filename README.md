# Vulnerability Scanner - AI-Powered Web Security Analysis

A comprehensive Python-based web security vulnerability scanner with AI-powered patch generation. Automatically discover security issues and receive intelligent remediation guidance.

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-green)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-Powered-61dafb)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## Quick Overview

This application performs automated security analysis on web applications by:

1. **Crawling** target websites to discover forms and input parameters
2. **Classifying** detected vulnerabilities using AI (SQL Injection, XSS, CSRF, etc.)
3. **Generating** secure code patches with detailed remediation guidance
4. **Storing** results in a cloud database for historical tracking and reporting

##   Table of Contents

- [Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
  - [First Scan](#first-scan)
- [Features](#-features)
- [Architecture](#-architecture)
  - [System Overview](#system-overview)
  - [Detailed Architecture](#-detailed-architecture)
    - [Directory Structure](#directory-structure)
  - [Key Components](#key-components)
    - [1. Web Crawler](#1-web-crawler-scannercrawlerpy)
    - [2. Vulnerability Analysis](#2-vulnerability-analysis-scannerexporterpy)
    - [3. AI Patch Generation](#3-ai-patch-generation-ai_engine)
    - [4. REST API](#4-rest-api-apiroutespy)
    - [5. Configuration Management](#5-configuration-management-configconstantspy)
    - [6. Shared Utilities](#6-shared-utilities-utilshelperspy)
  - [Data Flow](#data-flow)
  - [Error Handling Strategy](#error-handling-strategy)
  - [Logging](#logging)
- [API Reference](#-api-reference)
  - [Core Endpoints](#core-endpoints)
  - [POST /api/scan](#post-apiscan)
  - [Error Responses](#error-responses)
- [Development](#-development)
  - [Project Structure Overview](#project-structure-overview)
  - [Adding New Vulnerability Types](#adding-new-vulnerability-types)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Cloudflare Tunnel Setup for LM Studio](#cloudflare-tunnel-setup-for-lm-studio)
  - [Customizing Constants](#customizing-constants)
  - [Type Hints](#type-hints)
  - [Documentation Standards](#documentation-standards)
  - [Performance Considerations](#performance-considerations)
  - [Security Considerations](#security-considerations)
  - [Maintenance & Operations](#maintenance--operations)
  - [Future Enhancements](#future-enhancements)
- [Troubleshooting](#-troubleshooting)
  - [Common Issues](#common-issues)
  - [Debug Mode](#debug-mode)
  - [Viewing Logs](#viewing-logs)
- [FAQ](#-faq)
- [Getting Help](#-getting-help)
- [References](#-references)
- [Acknowledgments](#-acknowledgments)
- [License](#-license)

##  🚀 Quick Start

### Prerequisites

- **Python 3.9+** with pip
- **Node.js 14+** and npm
- **Git** for version control
- API keys (Gemini API)
- Supabase (for the backend)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Hamza-ctrC-ctrlV/secuscan.git
cd secuscan
```

2. **Set up Python environment**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Install frontend dependencies**
```bash
cd frontend
npm install
cd ..
```

5. **Configure environment**
Create `.env` file in project root:

**Option A: Using Google Gemini API (recommended)**
```env
GEMINI_API_KEY=your_api_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
PORT=5000
```

**Option B: Using Local LM Studio with Cloudflare Tunnel**
```env
AI_BACKEND=local
AI_LOCAL_API_URL=https://your-tunnel-domain.example.com
AI_LOCAL_MODELS_PATH=/v1/models
AI_LOCAL_GENERATE_PATH=/v1/chat/completions
AI_LOCAL_DEFAULT_MODEL=your-model-id
API_PUBLIC_KEY=some-strong-shared-token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
PORT=5000
```

### Running the Application

**Terminal 1: Start Flask backend**
```bash
# Make sure virtual environment is activated
python app.py
# Backend runs on http://localhost:5000
```

**Terminal 2: Start React frontend**
```bash
cd frontend
npm start
# Frontend opens at http://localhost:3000
```

**Terminal 3: Start the vulnerable site**
```bash
cd vulnerable_site
php -S localhost:8000
# site opens at http://localhost:8000
```


### First Scan

1. Open http://localhost:3000 in your browser
2. Enter a target URL (e.g., `http://localhost:8080`)
3. Click "Scan" and monitor progress
4. View vulnerabilities and AI-generated patches
5. Optionally save scan results to database
6. Optionally export scan as a **.pdf**

## 📋 Features

- **Intelligent Web Crawler**
  - Breadth-first search with configurable depth/limits
  - Form and input parameter discovery
  - Request throttling to avoid overload

- **AI-Powered Vulnerability Classification**
  - SQL Injection detection and analysis
  - XSS (Cross-Site Scripting) identification
  - CSRF vulnerabilities
  - CORS misconfiguration
  - Security header validation
  - And more...

- **Automated Patch Generation**
  - Language-aware fix recommendations
  - Code examples with secure patterns
  - Severity-based prioritization
  - Confidence scoring

- **Web Dashboard**
  - Intuitive scan interface
  - Real-time scan progress
  - Interactive vulnerability reports
  - Historical scan tracking
  - Export capabilities

- **Rate Limiting & Security**
  - Per-endpoint rate limits
  - User authentication support
  - Sensitive data masking in logs
  - Input validation on all endpoints

## 📊 Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   React Web Frontend                        │
│         (Dashboard, History, Vulnerability Reports)         │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST
                           ↓
┌────────────────────────────────────────────────────────────┐
│                      Flask Backend API                     │
│  ┌───────────────┐  ┌──────────┐  ┌─────────────────────┐  │
│  │ Rate Limiting │  │   Auth   │  │  Request Handlers   │  │
│  └───────────────┘  └──────────┘  └─────────────────────┘  │
└──────────┬──────────────────────────┬──────────────────────┘
           │                          │
           ↓                          ↓
    ┌──────────────┐         ┌─────────────────────┐
    │   Scanner    │         │   AI Engine         │
    │ ┌──────────┐ │         │ ┌──────────────────┐│
    │ │ Crawler  │ │         │ │ Patch Generator  ││
    │ ├──────────┤ │         │ ├──────────────────┤│
    │ │ Exporter │ │         │ │ Prompt Builder   ││
    │ └──────────┘ │         │ ├──────────────────┤│
    │              │         │ │    AI Client     ││
    │              │         │ │    (Gemini/LM    ||
    |              |         | |     Studio)      ││
    │              │         │ │                  ││
    │              │         │ └──────────────────┘|
    └──────────────┘         └─────────────────────┘
           │                        │
           └────────────┬───────────┘
                        ↓
              ┌───────────────────┐
              │   Supabase DB     │     
              └───────────────────┘
```

## 🏗️ Detailed Architecture

### Directory Structure

```
.
├── app.py                          # Flask application entry point
├── requirements.txt                # Python dependencies
├── config/                         # Configuration & constants
│   ├── __init__.py
│   └── constants.py                # Centralized configuration values
├── utils/                          # Shared utilities & helpers
│   ├── __init__.py
│   └── helpers.py                  # JSON extraction, error handling, validation
├── ai_engine/                      # AI analysis & patch generation
│   ├── __init__.py
│   ├── ai_client.py                # Google Gemini / LM Studio client wrapper
│   ├── patch_generator.py          # Orchestrates patch generation pipeline
│   ├── prompt_builder.py           # Specializes prompts by vulnerability type
│   └── supabase_client.py          # Database & authentication
├── api/                            # REST API endpoints
│   ├── __init__.py
│   ├── routes.py                   # Scan, report, and management endpoints
│   └── auth.py                     # User authentication endpoints
├── scanner/                        # Web crawling & discovery
│   ├── __init__.py
│   ├── crawler.py                  # Breadth-first web crawler
│   ├── exporter.py                 # Converts crawler output to vulnerabilities schema
│   ├── payloads.py                 # Security test payloads
│   ├── test_scanner.py             # Unit tests
│   └── test_integration.py         # Integration tests
├── frontend/                       # Web UI
│   ├── package.json
│   ├── build/
│   │   ├── asset-manifest.json
│   │   ├── index.html
│   │   ├── manifest.json
│   │   ├── robots.txt
│   │   └── static/
│   │       ├── css/
│   │       │   └── main.e8ee3074.css
│   │       └── js/
│   │           ├── main.fc98bc1f.js
│   │           └── main.fc98bc1f.js.LICENSE.txt
│   ├── public/
│   │   ├── index.html
│   │   ├── manifest.json
│   │   └── robots.txt
│   └── src/
│       ├── index.js
│       ├── app/
│       │   ├── App.css
│       │   └── App.js
│       ├── components/
│       │   ├── Charts.js
│       │   ├── CodeBlock.js
│       │   ├── FixesList.js
│       │   ├── Header.js
│       │   ├── Icons.js
│       │   ├── index.js
│       │   ├── ProgressBar.js
│       │   ├── ReportCharts.js
│       │   ├── ReportMetrics.js
│       │   ├── ScanInput.js
│       │   ├── SeverityBadge.js
│       │   └── VulnerabilityList.js
│       ├── config/
│       │   └── constants.js
│       ├── helpers/
│       │   ├── historyHelpers.js
│       │   ├── reportHelpers.js
│       │   └── validationHelpers.js
│       ├── pages/
│       │   ├── DashboardPage.js
│       │   ├── HistoryPage.js
│       │   ├── index.js
│       │   ├── LoginPage.js
│       │   └── SignupPage.js
│       └── styles/
│           └── index.css
├── reports/                        # Output directory
│   ├── patches.json
│   └── vulnerabilities.json
├── vulnerable_site/                # Test target with intentional vulnerabilities
│   ├── Atlasbank.sql
│   ├── config.php
│   ├── form_handler.php
│   ├── index.php
│   └── style.css
└── README.md                       # Project documentation
```

## Key Components

### 1. Web Crawler (`scanner/crawler.py`)

**Responsibilities**:
- Discover web application pages, forms, and input parameters
- Extract field attributes (type, name, validation rules)
- Generate appropriate test payloads
- Respect robots.txt and crawl limits

**Features**:
- Breadth-first search with configurable depth and page limits
- Robots.txt compliance
- Domain boundary enforcement
- Request throttling (0.5s delay between requests)
- GET parameter extraction
- HTML form parsing with field enumeration

**Configuration**:
```python
DEFAULT_MAX_PAGES = 50      # Maximum pages to crawl
DEFAULT_MAX_DEPTH = 2       # Maximum link depth to follow
CRAWL_DELAY_SECONDS = 0.5   # Delay between requests
```

### 2. Vulnerability Analysis (`scanner/exporter.py`)

**Responsibilities**:
- Convert raw crawler output to standardized vulnerability schema
- Use AI to classify each finding (severity, type, confidence)
- Generate unique vulnerability identifiers
- Produce structured JSON reports

**Output Schema**:
```json
{
  "scan_id": "scan_20240106_120000",
  "total_vulnerabilities": 5,
  "vulnerabilities": [
    {
      "id": "VULN-001",
      "type": "SQL Injection",
      "severity": "CRITICAL",
      "url": "http://target.com/login",
      "champ": "username",
      "contexte_code": {
        "fichier": "login.php",
        "code_vulnerable": "..."
      }
    }
  ]
}
```

### 3. AI Patch Generation (`ai_engine/`)

**Pipeline**:
1. **Prompt Builder** (`prompt_builder.py`)
   - Creates specialized prompts based on vulnerability type
   - SQL Injection → PDO prepared statement fixes
   - XSS → htmlspecialchars() and escaping fixes
   - Generic → General security best practices

2. **AI Client** (`ai_client.py`)
   - Wraps Google Gemini API
   - Implements rate limiting (14 requests/minute free tier)
   - Handles exponential backoff retries
   - Masks API keys in logs

3. **Patch Generator** (`patch_generator.py`)
   - Orchestrates full pipeline
   - Retry logic for transient errors
   - Graceful fallback responses
   - Batch processing with progress logging

**Output Schema**:
```json
{
  "scan_id": "scan_20240106_120000",
  "total_patches": 5,
  "patches": [
    {
      "vuln_id": "VULN-001",
      "type": "SQL Injection",
      "severity": "CRITICAL",
      "explication": "Dynamic query construction...",
      "solution": "Use PDO prepared statements",
      "code_vulnerable": "...",
      "code_corrige": "...",
      "status": "success"
    }
  ]
}
```

### 4. REST API (`api/routes.py`)

#### Endpoints

| Method | Endpoint      | Rate Limit | Description | Auth Required |
|--------|---------------|-----------|-------------|---------------|
| POST   | `/api/scan` | 10/min | Run complete scan pipeline | Yes |
| POST   | `/api/save-scan` | 20/min | Save scan to database | Yes |
| GET    | `/api/scans` | 30/min | List user's scans | Yes |
| GET    | `/api/report` | 30/min | Retrieve scan report | Yes |
| DELETE | `/api/delete-scan` | 15/min | Remove scan (ownership required) | Yes |
| GET    | `/api/health` | Unlimited | Health check | No |

#### Example: POST `/api/scan`
```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"url": "http://target.com"}'
```

**Response**:
```json
{
  "success": true,
  "vulnerabilities_report": {...},
  "patches_report": {...}
}
```

### 5. Configuration Management (`config/constants.py`)

All magic numbers and configuration strings centralized:

**Rate Limiting**:
- `DEFAULT_DAILY_LIMIT = 200` (app global)
- `DEFAULT_HOURLY_LIMIT = 50` (app global)
- `SCAN_ROUTE_RATE_LIMIT = "10 per minute"`
- `GEMINI_FREE_TIER_RATE_LIMIT = 14` (API requests/minute)

**Crawler Settings**:
- `DEFAULT_MAX_PAGES = 50`
- `DEFAULT_MAX_DEPTH = 2`
- `CRAWL_DELAY_SECONDS = 0.5`
- `INJECTABLE_SKIP_TYPES = {"submit", "button", "reset", ...}`

**API Settings**:
- `GEMINI_MODEL_ID = "models/gemini-4-31b-it"`
- `API_REQUEST_TIMEOUT = 30`
- `MAX_RETRY_ATTEMPTS = 3`

### 6. Shared Utilities (`utils/helpers.py`)

Reusable functions eliminating code duplication:

| Function | Purpose |
|----------|---------|
| `extract_json_from_text()` | Extract JSON from markdown-wrapped text |
| `standardize_error_response()` | Create consistent API error responses |
| `mask_sensitive_value()` | Safe logging for secrets |
| `validate_api_key_format()` | API key format validation |
| `is_retryable_error()` | Categorize transient vs permanent errors |
| `merge_dicts()` | Deep dictionary merging |
| `safe_get()` | Nested dict access with dot notation |

## Data Flow

### Scan Pipeline
```
1. User submits target URL via /api/scan
   ↓
2. Web Crawler scans target
   - Discovers pages, forms, parameters
   ↓
3. Exporter converts to vulnerability schema
   - Classifies findings with AI
   ↓
4. Patch Generator processes each vulnerability
   - Builds specialized prompts
   - Calls Gemini API
   - Parses and validates responses
   ↓
5. Results returned to user
   - Raw crawler results
   - Standardized vulnerability report
   - AI-generated patches with fixes
   ↓
6. User can save to database
   - Stored in Supabase with reports
   - Can be retrieved later
```

## Error Handling Strategy

### Hierarchical Error Handling
1. **Input Validation** (400 Bad Request)
   - Missing required fields
   - Invalid URL format
   - Type mismatches

2. **Transient Errors** (retry with exponential backoff)
   - Timeouts (429, 503, 504)
   - Network connection issues
   - Service temporarily unavailable

3. **Permanent Errors** (fail immediately)
   - Authentication failures (401)
   - Authorization failures (403)
   - Not found (404)

### Graceful Degradation
- If AI unavailable: Still return vulnerability report
- If patch generation fails: Return vulnerability with error status
- If database unavailable: Still perform scan

## Logging

All modules use Python's logging module:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Important event")      # Information
logger.warning("Recoverable issue") # Warnings
logger.error("Serious problem")     # Errors
logger.debug("Detailed info")       # Debug
```

Sensitive data (API keys) automatically masked in logs.

## 📡 API Reference

### Core Endpoints

| Method | Endpoint | Rate Limit | Authentication | Description |
|--------|----------|-----------|-----------------|-------------|
| POST | `/api/scan` | 10/min | Required | Run complete scan pipeline |
| POST | `/api/save-scan` | 20/min | Required | Save scan to database |
| GET | `/api/scans` | 30/min | Required | List user's scans |
| GET | `/api/report` | 30/min | Required | Retrieve scan report |
| DELETE | `/api/delete-scan` | 15/min | Required | Remove scan (ownership required) |
| GET | `/api/health` | Unlimited | No | Health check |
| POST | `/auth/login` | 5/min | No | User login |
| POST | `/auth/signup` | 5/min | No | User registration |

### POST /api/scan

**Request**:
```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://target.com",
    "max_pages": 50,
    "max_depth": 2,
    "timeout": 30
  }'
```

**Response**:
```json
{
  "success": true,
  "vulnerabilities_report": {
    "scan_id": "scan_20240114_143022",
    "total_vulnerabilities": 5,
    "vulnerabilities": [
      {
        "id": "VULN-001",
        "type": "SQL Injection",
        "severity": "CRITICAL",
        "url": "http://target.com/login",
        "champ": "username"
      }
    ]
  },
  "patches_report": {
    "scan_id": "scan_20240114_143022",
    "total_patches": 5,
    "patches": [
      {
        "vuln_id": "VULN-001",
        "type": "SQL Injection",
        "solution": "Use PDO prepared statements",
        "code_corrige": "..."
      }
    ]
  }
}
```

### Error Responses

**400 Bad Request**:
```json
{
  "error": "Invalid URL format",
  "status": 400
}
```

**429 Too Many Requests**:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60,
  "status": 429
}
```

## 🛠️ Development

### Project Structure Overview

```
Backend (Flask):
  app.py                 # Entry point with rate limiting & CORS
  config/                # Centralized configuration
  api/                   # REST endpoints & authentication
  scanner/               # Web crawling & vulnerability detection
  ai_engine/             # AI analysis & patch generation
  utils/                 # Shared utilities & helpers

Frontend (React):
  src/
    components/          # Reusable UI components
    pages/               # Full-page views
    helpers/             # Business logic & data processing
    styles/              # Global styling
```

### Adding New Vulnerability Types

1. Update `config/constants.py`:
```python
VULNERABILITY_TYPES = [..., "NEW_TYPE"]
```

2. Create handler in `ai_engine/prompt_builder.py`:
```python
def _build_new_type_prompt(self, vulnerability: Dict) -> str:
    """Build prompt for NEW_TYPE vulnerability."""
    # Implementation
```

3. Test with sample vulnerable code
4. Update frontend constants if needed



## Configuration

### Environment Variables

Create `.env` file in project root:
```env
GEMINI_API_KEY=your_api_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DATABASE_URL=postgresql://...
PORT=5000
```

If you are using LM Studio through Cloudflare Tunnel, add these values instead of the Gemini ones for AI generation:
```env
AI_BACKEND=local
AI_LOCAL_API_URL=https://your-tunnel-domain.example.com
AI_LOCAL_MODELS_PATH=/v1/models
AI_LOCAL_GENERATE_PATH=/v1/chat/completions
AI_LOCAL_DEFAULT_MODEL=your-model-id
API_PUBLIC_KEY=some-strong-shared-token
```

### Cloudflare Tunnel Setup for LM Studio

Use Cloudflare Tunnel if your LM Studio server runs at home and you want to access it from anywhere without exposing your router directly.

1. Install `cloudflared` on the home machine that runs LM Studio.
2. Start LM Studio's local server and make sure it listens on a reachable interface, not only `127.0.0.1`.
3. Create a tunnel that forwards to the LM Studio port, usually `1234`:
```bash
cloudflared tunnel --url http://localhost:1234
```
4. Cloudflare will give you a public `https://...` URL. Put that URL in `AI_LOCAL_API_URL`.
5. Verify the API works:
```bash
curl https://your-tunnel-domain.example.com/v1/models
```
6. Open the app and choose a model from the dropdown. The app calls the tunneled LM Studio server through the same OpenAI-compatible API shape used by Gemini-style generation.

Recommended security settings:
- Protect your own Flask app with `API_PUBLIC_KEY` if you expose it outside your LAN.
- Prefer a Cloudflare Access policy or another auth layer in front of the tunnel if the AI endpoint is public.
- Do not expose LM Studio's port directly with router forwarding unless you also add authentication.

### Customizing Constants

Edit `config/constants.py` to adjust:
- Rate limits
- Crawler behavior
- AI model settings
- Error messages
- Timeouts

## Type Hints

The codebase uses comprehensive type hints for better IDE support and clarity:

```python
def build_vulnerabilities_report(
    results: List[Dict[str, Any]],
    target_url: str,
    output_path: Optional[str] = None,
    scan_duration_seconds: float = 0
) -> Dict[str, Any]:
    """Convert scanner results into vulnerabilities report."""
```

## Documentation Standards

All modules, classes, and functions have comprehensive docstrings:

```python
def function_name(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief one-line description.
    
    More detailed explanation of what the function does,
    including any important behavior or side effects.
    
    Args:
        param1 (str): Description with type
        param2 (int): Another parameter
        
    Returns:
        Dict[str, Any]: Description of return value structure
        
    Raises:
        ValueError: When validation fails
        
    Side Effects:
        - Logs information at info level
        - Makes HTTP requests to external services
    """
```

## Performance Considerations

### Crawler Optimization
- Robots.txt parsed once per crawl (not per URL)
- Domain boundary checking prevents off-domain crawling
- Request throttling respects server load (0.5s delay)
- Breadth-first search prevents getting stuck on deep paths

### API Rate Limiting
- 14 requests/minute Gemini free tier limit
- 1-second delay between vulnerability processing
- Exponential backoff for transient errors

### Database
- Indexes on frequently queried fields (user_id, scan_id)
- Report compression for large payloads
- Storage integration for large files

## Security Considerations

### API Security
✓ Strict CORS policies restricting origins
✓ Rate limiting on all endpoints, including Server-Sent Events
✓ Global `@require_auth` decorator verifying JWT tokens
✓ Ownership verification (IDOR prevention) using tokens instead of payload data
✓ Input validation on all endpoints
✓ Error messages don't leak sensitive info

### Data Security
✓ No hardcoded secrets (using `.env` exclusively)
✓ API keys masked in logs
✓ Sensitive values use safe masking function
✓ Token-based authentication
✓ Database access limited to necessary operations

### Scanning Security
✓ Respects robots.txt
✓ Configurable crawl limits prevent abuse
✓ User-agent identification
✓ Timeout prevention

## Maintenance & Operations

### Adding New Vulnerability Types
1. Add type name to `constants.py`
2. Create `_build_<type>_prompt()` in `prompt_builder.py`
3. Test with sample vulnerabilities
4. Update documentation

### Adjusting Rate Limits
Edit `config/constants.py` without changing code:
```python
SCAN_ROUTE_RATE_LIMIT = "5 per minute"  # More restrictive
```

### Changing Error Messages
Centralized in `config.constants`:
```python
ERROR_INVALID_API_KEY = "Custom error message"
```

### Adding Logging
```python
logger = logging.getLogger(__name__)
logger.info("Event description")
```

## Future Enhancements

Potential improvements not yet implemented:
- Background job processing for scans
- Multiple crawler strategies (JavaScript rendering, etc.)
- Custom payload libraries
- Machine learning classification
- Real-time scan progress updates
- Report comparison/trending
- Automated remediation
- Integration with other security tools

## 🚨 Troubleshooting

### Common Issues

**Issue: "ModuleNotFoundError: No module named 'flask'"**
- Solution: Activate virtual environment and run `pip install -r requirements.txt`

**Issue: "GEMINI_API_KEY not found"**
- Solution: Create `.env` file in project root with required keys. See Configuration section.

**Issue: "Connection refused" when accessing http://localhost:5000**
- Solution: Ensure Flask backend is running with `python app.py`
- Check if port 5000 is already in use: Change `PORT=5000` in `.env`

**Issue: Frontend not loading / showing blank page**
- Solution: 
  1. Clear browser cache (Ctrl+Shift+Delete)
  2. Ensure npm dev server is running (`npm start` in frontend/)
  3. Check browser console for errors (F12)

**Issue: Scans timing out**
- Solution: Increase `API_REQUEST_TIMEOUT` in `.env` or reduce `DEFAULT_MAX_PAGES` in `config/constants.py`

**Issue: AI generation fails with rate limit error**
- Solution: Gemini free tier has 14 requests/minute limit. Wait 60 seconds or use LM Studio for unlimited requests.

**Issue: "CORS error" or "blocked by CORS policy"**
- Solution: CORS is enabled, but if running custom frontend URL, add it to `CORS(app)` in `app.py`

### Debug Mode

Run Flask in debug mode for detailed error messages:
```bash
FLASK_ENV=development FLASK_DEBUG=1 python app.py
```

### Viewing Logs

Logs are written to console. For persistent logging:
```python
# Add to app.py after logger setup
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## ❓ FAQ

**Q: Can I scan multiple URLs in parallel?**
A: The `/api/scan` endpoint processes one URL at a time. For batch scanning, make multiple requests with appropriate rate limiting (10 requests/min).

**Q: How long does a scan typically take?**
A: 
- Crawling: 10-60 seconds (depends on site size)
- AI classification: 1-3 seconds per vulnerability
- Total: Usually 30 seconds to 5 minutes

**Q: What happens if a vulnerability is found on multiple pages?**
A: Each instance is reported separately with its specific URL and context.

**Q: Can I disable the AI patch generation?**
A: Yes, modify `patch_generator.py` to return early or skip the AI call. The vulnerability report will still be generated.

**Q: Is the scanner safe to use on production sites?**
A: The scanner is non-destructive and reads-only. However, always get explicit permission before scanning any site you don't own. Use responsibly.

**Q: What types of vulnerabilities are detected?**
A: SQL Injection, XSS, CSRF, Command Injection, Path Traversal, and more. See `config/constants.py` for complete list.

**Q: Can I use this with my own AI model?**
A: Yes! Set `AI_BACKEND=local` and configure `AI_LOCAL_API_URL` to point to your model's OpenAI-compatible API endpoint.

**Q: How do I export scan results?**
A: Scan results are automatically saved as JSON in `reports/` directory and can be downloaded from the web interface.

**Q: What database is required?**
A: Supabase (PostgreSQL) is optional for storing historical scans. Scans work entirely offline if database is unavailable.


## 💬 Getting Help

### Resources

- **Documentation**: See [Detailed Architecture](#-detailed-architecture) section
- **Issues**: [GitHub Issues](https://github.com/your-username/PFA/issues)
- **Discussions**: Check existing issues before creating a new one
- **Email**: Contact project maintainers

### Common Questions

Check the [FAQ](#-faq) section for common questions and troubleshooting steps.

## 📚 References

### APIs & Frameworks
- [Google Gemini API](https://ai.google.dev/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Supabase Documentation](https://supabase.io/docs)
- [React Documentation](https://react.dev/)
- [LM Studio](https://lmstudio.ai/)

### Security Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [PHP Security Best Practices](https://owasp.org/www-community/attacks/SQL_Injection)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)

### Python Best Practices
- [PEP 8 - Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [PEP 257 - Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)

### Web Security Testing
- [OWASP WebGoat](https://owasp.org/www-project-webgoat/)
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)
- [DVWA - Damn Vulnerable Web App](http://www.dvwa.co.uk/)

## 🙏 Acknowledgments

- **Security Community**: OWASP, security researchers, and contributors
- **Open Source**: Built on Flask, React, BeautifulSoup, and many other great libraries
- **Testing Infrastructure**: Thanks to all contributors and bug reporters

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### License Summary

```
MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

**Happy scanning! 🔒** If you find this project helpful, please consider:

    
