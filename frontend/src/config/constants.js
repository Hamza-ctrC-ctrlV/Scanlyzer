/**
 * Constants — App configuration, severity mapping, API endpoints
 */

export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "";
export const API_URL = `${API_BASE_URL}/api/scan`;
export const SCANS_URL = `${API_BASE_URL}/api/scans`;
export const REPORT_URL = `${API_BASE_URL}/api/report`;
export const SCAN_RESULT_URL = `${API_BASE_URL}/api/scan-result`;
export const HEALTH_URL = `${API_BASE_URL}/api/health`;
export const SAVE_SCAN_URL = `${API_BASE_URL}/api/save-scan`;
export const CHAT_URL = `${API_BASE_URL}/api/chat`;
export const DEFAULT_TARGET_URL = process.env.REACT_APP_TARGET_SITE_URL || "http://localhost:8000/";

export const SEV = {
  CRITICAL: { color: "#ff4d6d", bg: "rgba(255,77,109,0.1)",  glow: "rgba(255,77,109,0.3)",  label: "CRITICAL" },
  HIGH:     { color: "#ff8c42", bg: "rgba(255,140,66,0.1)",  glow: "rgba(255,140,66,0.25)", label: "HIGH"     },
  MEDIUM:   { color: "#ffd166", bg: "rgba(255,209,102,0.1)", glow: "rgba(255,209,102,0.2)", label: "MEDIUM"   },
  LOW:      { color: "#06d6a0", bg: "rgba(6,214,160,0.1)",   glow: "rgba(6,214,160,0.2)",   label: "LOW"      },
  INFO:     { color: "#4cc9f0", bg: "rgba(76,201,240,0.1)",  glow: "rgba(76,201,240,0.2)",  label: "INFO"     },
};

export const SCAN_STEPS = ["Connexion","Crawling","Détection","Analyse IA","Rapport"];

/** Maps backend step names to SCAN_STEPS index for the progress bar */
export const STEP_MAP = {
  waiting: 0,
  crawling: 1,
  active_scan: 2,
  classification: 3,
  ai_patches: 3,
  done: 4,
};