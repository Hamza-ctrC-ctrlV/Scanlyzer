import React, { useEffect, useState, useCallback, useRef } from "react";
import { IconBug, IconCode } from "../components/Icons";
import { validateUrl } from "../helpers/validationHelpers";
import { normalizeReport, getScoreColor, getScoreVerdict } from "../helpers/reportHelpers";
import { generatePDF } from "../helpers/pdfHelper";
import { ScanInput } from "../components/ScanInput";
import { ProgressBar } from "../components/ProgressBar";
import { MetricsSkeleton, VulnCardSkeleton } from "../components/Skeleton";
import ReportMetrics from "../components/ReportMetrics";
import ReportCharts from "../components/ReportCharts";
import VulnerabilityList from "../components/VulnerabilityList";
import FixesList from "../components/FixesList";
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
        setApiError(resultData.error || resultData.message || "Erreur lors de la récupération du rapport.");
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
      setApiError(`Impossible de récupérer les résultats — ${err.message || "erreur inconnue"}`);
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
        setStatusMsg(data.msg || "Analyse en cours...");
        setElapsed(data.elapsed || 0);

        if (data.step === "done") {
          es.close();
          fetchScanResult(scanId, token);
        } else if (data.step === "error") {
          es.close();
          setApiError(data.msg || "Une erreur est survenue pendant le scan.");
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
        setApiError(data.error || data.message || "Erreur lors du lancement du scan.");
        setScanning(false);
        setShowSkeleton(false);
        return;
      }

      // Background scan started — set scanId to trigger the SSE effect
      setScanId(data.scan_id);

    } catch (err) {
      console.error("Scan fetch error:", err);
      setApiError(`Impossible de contacter Flask — vérifiez que le serveur répond (${err.message || "erreur inconnue"})`);
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
          <div className="empty-title">EN ATTENTE DE SCAN</div>
          <p className="empty-sub">
            Entrez une URL valide ci-dessus et lancez l'analyse pour voir le rapport complet.
          </p>
        </div>
      )}

      {report && (
        <section className="report fade-in">
          <div className="report-topbar">
            <div>
              <div className="rtb-lbl">URL analysée · {report.scan_id}</div>
              <div className="rtb-url">{report.url}</div>
            </div>
            <div className="rtb-right">
              <div className="rtb-lbl">Généré le</div>
              <div className="rtb-time">
                {report.generated_at
                  ? new Date(report.generated_at).toLocaleString("fr-FR")
                  : new Date().toLocaleString("fr-FR")}
              </div>
              {report.scan_duration_total && (
                <div className="rtb-duration">⏱ {report.scan_duration_total}s (total)</div>
              )}
            </div>
          </div>

          <ReportMetrics report={report} scoreColor={scoreColor} scoreVerdict={scoreVerdict} />
          <ReportCharts report={report} />

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div className="tabs" style={{ marginBottom: 0 }}>
              <button className={`tab-btn ${tab==="vulns"?"active":""}`} onClick={()=>setTab("vulns")}>
                <IconBug/> Vulnérabilités ({report.total_patches})
              </button>
              <button className={`tab-btn ${tab==="fixes"?"active":""}`} onClick={()=>setTab("fixes")}>
                <IconCode/> Correctifs IA
              </button>
            </div>
            <button
              className="btn-outline"
              onClick={() => generatePDF(report)}
              style={{ display: "flex", alignItems: "center", gap: "8px" }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
              Exporter PDF
            </button>
          </div>

          {tab==="vulns" && <VulnerabilityList patches={report.patches} />}
          {tab==="fixes" && <FixesList patches={report.patches} />}
        </section>
      )}
    </main>
  );
}
