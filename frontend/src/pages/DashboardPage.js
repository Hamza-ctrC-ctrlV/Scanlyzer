import React, { useEffect, useState, useCallback, useRef } from "react";
import { IconBug, IconCode } from "../components/Icons";
import { validateUrl } from "../helpers/validationHelpers";
import { normalizeReport, getScoreColor, getScoreVerdict } from "../helpers/reportHelpers";
import { generatePDF } from "../helpers/pdfHelper";
import { ScanInput } from "../components/ScanInput";
import { ProgressBar } from "../components/ProgressBar";
import { MetricsSkeleton, VulnCardSkeleton } from "../components/Skeleton";
import ReportViewer from "../components/ReportViewer";
import { API_URL, SCAN_RESULT_URL, SAVE_SCAN_URL, API_BASE_URL, STEP_MAP } from "../config/constants";

/**
 * Dashboard page — scanning and report display
 *
 * Phase 1 async flow:
 *   1. POST /api/scan          → receive scan_id immediately
 *   2. SSE /api/scan-progress  → stream progress updates
 *   3. GET /api/scan-result    → fetch full report once SSE signals "done"
 *   4. POST /api/save-scan     → persist to Supabase (authenticated users only)
 */
export function DashboardPage({ authUser, onReportLoad, initialReport = null }) {
  const [url, setUrl]           = useState("");
  const [urlError, setUrlError] = useState("");
  const [apiError, setApiError] = useState("");
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stepIdx, setStepIdx]   = useState(0);
  const [scanId, setScanId]     = useState(null);   // active background scan id
  const [report, setReport]     = useState(initialReport);
  const [tab, setTab]           = useState("vulns");
  const [showSkeleton, setShowSkeleton] = useState(false);
  const [statusMsg, setStatusMsg] = useState("Initialisation...");
  const [elapsed, setElapsed] = useState(0);

  // Keep url in a ref so async callbacks always read the latest value
  const urlRef = useRef(url);
  useEffect(() => { urlRef.current = url; }, [url]);

  // Keep authUser in a ref for the same reason
  const authUserRef = useRef(authUser);
  useEffect(() => { authUserRef.current = authUser; }, [authUser]);

  // ── Load an existing report passed from parent (e.g. history view) ──
  useEffect(() => {
    if (!initialReport) return;
    setReport(initialReport);
    setUrl(initialReport.url || "");
    setTab("vulns");
  }, [initialReport]);

  // ── Fetch the full scan result once the background job finishes ──────
  const savedScansRef = useRef(new Set());

  const fetchScanResult = useCallback(async (sid, token) => {
    if (savedScansRef.current.has(sid)) return;

    try {
      const res = await fetch(`${SCAN_RESULT_URL}?scan_id=${sid}`, {
        headers: { Authorization: token ? `Bearer ${token}` : "" },
      });
      const resultData = await res.json();

      if (!res.ok || !resultData.success) {
        setApiError(resultData.error || resultData.message || "Error retrieving the report.");
        return;
      }

      const reportData = normalizeReport(resultData, urlRef.current);
      if (resultData.scan_duration_total) {
        reportData.scan_duration_total = resultData.scan_duration_total;
      }

      setReport(reportData);
      setTab("vulns");
      onReportLoad(reportData);

      // ── Save to Supabase (uses the full result, not the empty POST response) ──
      const currentAuthUser = authUserRef.current;
      if (currentAuthUser) {
        savedScansRef.current.add(sid);
        try {
          await fetch(SAVE_SCAN_URL, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: token ? `Bearer ${token}` : "",
            },
            body: JSON.stringify({
              user_id:               currentAuthUser.user_id,
              email:                 currentAuthUser.email,
              target_url:            urlRef.current.trim(),
              scan_id:               reportData.scan_id,
              vulnerabilities_count: reportData.vulnerabilities_count
                                      || resultData.vulnerabilities_report?.total_vulnerabilities
                                      || 0,
              patches_count:         reportData.total_patches
                                      || resultData.patches_report?.total_patches
                                      || 0,
              vulnerabilities_report: resultData.vulnerabilities_report,
              patches_report:         resultData.patches_report,
            }),
          });
        } catch (saveErr) {
          console.warn("Failed to save scan to Supabase:", saveErr);
        }
      }
    } catch (err) {
      console.error("fetchScanResult error:", err);
      setApiError(`Unable to fetch results — ${err.message || "unknown error"}`);
    } finally {
      setScanning(false);
      setShowSkeleton(false);
      setScanId(null);
    }
  }, [onReportLoad]);

  // ── SSE effect: opens when scanId is set, closes on cleanup ─────────
  useEffect(() => {
    if (!scanId || !scanning) return;

    const token = authUserRef.current?.token || localStorage.getItem("vulnscan_token");
    const sseUrl = `${API_BASE_URL}/api/scan-progress?scan_id=${encodeURIComponent(scanId)}${token ? `&token=${token}` : ""}`;
    const es = new EventSource(sseUrl);

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setProgress(data.pct ?? 0);
        setStepIdx(STEP_MAP[data.step] ?? 0);
        setStatusMsg(data.msg || "Scanning in progress...");
        setElapsed(data.elapsed || 0);

        if (data.step === "done") {
          es.close();
          fetchScanResult(scanId, token);
        } else if (data.step === "error") {
          es.close();
          setApiError(data.msg || "An error occurred during the scan.");
          setScanning(false);
          setShowSkeleton(false);
          setScanId(null);
          setStatusMsg("");
          setElapsed(0);
        }
      } catch {
        // ignore parse errors
      }
    };

    es.onerror = () => {
      es.close();
      // SSE disconnected — try polling result once as fallback
      const token_ = authUserRef.current?.token || localStorage.getItem("vulnscan_token");
      fetchScanResult(scanId, token_);
    };

    return () => { es.close(); };
  }, [scanId, scanning, fetchScanResult]);

  // ── Initiate scan ────────────────────────────────────────────────────
  const handleScan = useCallback(async () => {
    const err = validateUrl(url);
    if (err) { setUrlError(err); return; }

    setUrlError(""); setApiError(""); setReport(null);
    setScanning(true); setProgress(0); setStepIdx(0);
    setShowSkeleton(true); setScanId(null);

    try {
      const token = authUserRef.current?.token || localStorage.getItem("vulnscan_token");
      const res = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({ url: url.trim() }),
      });
      const data = await res.json();

      if (!res.ok) {
        setApiError(data.error || data.message || "Error launching the scan.");
        setScanning(false);
        setShowSkeleton(false);
        return;
      }

      // Background scan started — set scanId to trigger the SSE effect
      setScanId(data.scan_id);

    } catch (err) {
      console.error("Scan fetch error:", err);
      setApiError(`Unable to contact server — check if it is responding (${err.message || "unknown error"})`);
      setScanning(false);
      setShowSkeleton(false);
    }
  }, [url]);

  const handleUrlChange = useCallback((value) => {
    setUrl(value);
    setUrlError("");
    setApiError("");
  }, []);

  const scoreColor   = !report ? "#fff" : getScoreColor(report.score);
  const scoreVerdict = !report ? ""     : getScoreVerdict(report.score);

  return (
    <main className="main">
      <ScanInput
        url={url}
        onUrlChange={handleUrlChange}
        onScan={handleScan}
        urlError={urlError}
        apiError={apiError}
        scanning={scanning}
      />

      {scanning && (
        <ProgressBar
          progress={progress}
          stepIdx={stepIdx}
          statusMsg={statusMsg}
          elapsed={elapsed}
        />
      )}

      {/* Skeleton loading state */}
      {showSkeleton && !report && (
        <section className="report fade-in" style={{ marginTop: "32px" }}>
          <MetricsSkeleton />
          <VulnCardSkeleton count={3} />
        </section>
      )}

      {!report && !scanning && !showSkeleton && (
        <div className="empty-state">
          <div className="empty-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L4 6v6c0 5.5 3.8 10.7 8 12 4.2-1.3 8-6.5 8-12V6l-8-4z" fill="url(#sg)"/>
              <path d="M9 12l2 2 4-4" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              <defs><linearGradient id="sg" x1="4" y1="2" x2="20" y2="22" gradientUnits="userSpaceOnUse">
                <stop stopColor="#3b82f6"/><stop offset="1" stopColor="#0ea5e9"/>
              </linearGradient></defs>
            </svg>
          </div>
          <div className="empty-title">WAITING FOR SCAN</div>
          <p className="empty-sub">
            Enter a valid URL above and launch the analysis to see the full report.
          </p>
        </div>
      )}

      {report && <ReportViewer report={report} />}
    </main>
  );
}
