# Vulnerability Scanner App

This project is a Flask-based vulnerability scanning platform with a React frontend. It scans a target URL, analyzes discovered forms and parameters, generates a vulnerability report, and produces AI-assisted patch suggestions.

## What It Does

- Authenticates users with Supabase.
- Scans a target URL through the Flask API.
- Crawls pages and inspects forms and parameters.
- Produces a vulnerabilities report and AI-generated patch report.
- Saves scans to Supabase for authenticated users.
- Shows scan history with local cache fallback.
- Exposes a health endpoint for backend checks.

## Tech Stack

- Backend: Flask, Flask-CORS, Flask-Limiter
- AI: Google Gemini-based client
- Data: Supabase authentication, storage, and scan history
- Frontend: React 19 with React Scripts
- Parsing and crawling: Requests, BeautifulSoup, lxml

## Project Structure

- `app.py`: Flask entry point and static file serving
- `api/`: API routes for scan, report, auth, health, and scan management
- `ai_engine/`: AI client, patch generation, and Supabase integration
- `scanner/`: Crawler and report export logic
- `frontend/`: React UI for login, signup, dashboard, and history
- `reports/`: Stored JSON reports
- `vulnerable_site/`: Local vulnerable demo site used for testing

## Environment Setup

Create a `.env` file from `env.example` and fill in the required values:

- `GEMINI_API_KEY`
- `FLASK_PORT`
- `FLASK_DEBUG`
- `TARGET_SITE_URL`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

The frontend can also use these optional environment variables if you want to override its defaults:

- `REACT_APP_API_BASE_URL`
- `REACT_APP_TARGET_SITE_URL`

## Install And Run

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

By default the Flask server runs on port 5000.

### Frontend

```bash
cd frontend
npm install
npm start
```

The frontend is configured to call the backend at `http://localhost:5000` unless you override the base URL.

## Main API Endpoints

- `POST /api/scan` - Run a scan against a target URL.
- `GET /api/report` - Fetch a specific report by `scan_id` or `user_id`.
- `POST /api/save-scan` - Save a completed scan to Supabase.
- `GET /api/scans` - List authenticated user scans.
- `DELETE /api/delete-scan` - Remove a saved scan.
- `GET /api/health` - Backend health check.
- `POST /auth/signup` - Create an account.
- `POST /auth/login` - Log in.
- `POST /auth/verify` - Verify a session token.

## Current Behavior Notes

- The dashboard validates URLs before sending them to the scan API.
- Scan history is cached in localStorage for faster reloads.
- When a user is authenticated, new scans can be persisted in Supabase.
- The app normalizes report data before rendering charts, lists, and summaries.

## Performance Considerations

- The crawler is intentionally constrained with limited depth and page counts to reduce scan time and server load.
- Rate limiting is enabled on Flask routes to prevent abuse and keep scans predictable.
- The history page uses a local cache first, then refreshes from Supabase when needed.
- Report list views use lightweight summaries instead of downloading full report payloads every time.
- AI patch generation is wrapped so the scan can still complete even if patch generation fails.

## Security Considerations

- Only scan systems you are authorized to test.
- The scan API only accepts `http` and `https` URLs.
- Authentication uses bearer tokens for protected history and report actions.
- The service role key for Supabase must stay on the server side only.
- Do not commit `.env` files or API keys to version control.
- Route-level and global rate limits are enabled to reduce abuse.
- If you enable `API_PUBLIC_KEY`, the AI proxy endpoints require an API key header or query parameter.

## Notes

- The repo currently contains both source files and built frontend assets.
- The empty `README.md` has been replaced with the current-state overview only, without historical background.
