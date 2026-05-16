import React, { useEffect, useState, useCallback } from "react";
import { IconBug, IconCode } from "../components/Icons";
import { validateUrl } from "../helpers/validationHelpers";
import { normalizeReport, getScoreColor, getScoreVerdict } from "../helpers/reportHelpers";
import { addToHistory } from "../helpers/historyHelpers";
import { generatePDF } from "../helpers/pdfHelper";
import { ScanInput } from "../components/ScanInput";
import { ProgressBar } from "../components/ProgressBar";
import { MetricsSkeleton, VulnCardSkeleton } from "../components/Skeleton";
import ReportMetrics from "../components/ReportMetrics";
import ReportCharts from "../components/ReportCharts";
import VulnerabilityList from "../components/VulnerabilityList";
import FixesList from "../components/FixesList";
import { API_URL, SAVE_SCAN_URL } from "../config/constants";

/**
 * Dashboard page — scanning and report display
 */
export function DashboardPage({ authUser, onReportLoad, initialReport = null }) {
  const [url, setUrl] = useState("");
  const [urlError, setUrlError] = useState("");
  const [apiError, setApiError] = useState("");
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stepIdx, setStepIdx] = useState(0);
  const [report, setReport] = useState(initialReport);
  const [tab, setTab] = useState("vulns");
  const [showSkeleton, setShowSkeleton] = useState(false);

  useEffect(() => {
    if (!initialReport) return;
    setReport(initialReport);
    setUrl(initialReport.url || "");
    setTab("vulns");
  }, [initialReport]);

  const handleScan = useCallback(async () => {
    const err = validateUrl(url);
    if (err) { setUrlError(err); return; }
    setUrlError(""); setApiError(""); setReport(null);
    setScanning(true); setProgress(0); setStepIdx(0);

    // Show skeleton as placeholder while scanning
    setShowSkeleton(true);

    try {
      const token = authUser?.token || localStorage.getItem("vulnscan_token");
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({ url: url.trim() }),
      });
      const data = await res.json();
      setProgress(100);

      if (!res.ok) {
        setApiError(data.error || data.message || "Erreur lors du scan.");
        setScanning(false);
        setShowSkeleton(false);
        return;
      }

      const reportData = normalizeReport(data, url);

      // Add total_duration from backend
      if (data.scan_duration_total) {
        reportData.scan_duration_total = data.scan_duration_total;
      }

      setReport(reportData);
      setTab("vulns");
      addToHistory(reportData);
      onReportLoad(reportData);

      // Save scan to Supabase if authenticated
      if (authUser) {
        try {
          const token = authUser.token || localStorage.getItem("vulnscan_token");
          await fetch(SAVE_SCAN_URL, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: token ? `Bearer ${token}` : "",
            },
            body: JSON.stringify({
              user_id: authUser.user_id,
              email: authUser.email,
              target_url: url.trim(),
              scan_id: reportData.scan_id,
              vulnerabilities_count: reportData.vulnerabilities_count || data.vulnerabilities_report?.total_vulnerabilities || 0,
              patches_count: reportData.total_patches || data.patches_report?.total_patches || 0,
              vulnerabilities_report: data.vulnerabilities_report,
              patches_report: data.patches_report,
            }),
          });
        } catch (saveErr) {
          console.warn("Failed to save scan to Supabase:", saveErr);
        }
      }

    } catch (err) {
      console.error("Scan fetch error:", err);
      setApiError(`Impossible de contacter Flask — vérifiez que le serveur répond (${err.message || "erreur inconnue"})`);
    }
    setScanning(false);
    setShowSkeleton(false);
  }, [url, authUser, onReportLoad]);

  const handleUrlChange = useCallback((value) => {
    setUrl(value);
    setUrlError("");
    setApiError("");
  }, []);

  const scoreColor = !report ? "#fff" : getScoreColor(report.score);
  const scoreVerdict = !report ? "" : getScoreVerdict(report.score);

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

      {scanning && <ProgressBar progress={progress} stepIdx={stepIdx} targetUrl={url.trim()} scanning={scanning} />}

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
            <button className="btn-outline" onClick={() => generatePDF(report)} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
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
