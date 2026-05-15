import React, { useEffect, useState, useCallback } from "react";
import { IconBug, IconCode } from "../components/Icons";
import { validateUrl } from "../helpers/validationHelpers";
import { normalizeReport, getScoreColor, getScoreVerdict } from "../helpers/reportHelpers";
import { addToHistory } from "../helpers/historyHelpers";
import { ScanInput } from "../components/ScanInput";
import { ProgressBar } from "../components/ProgressBar";
import ReportMetrics from "../components/ReportMetrics";
import ReportCharts from "../components/ReportCharts";
import VulnerabilityList from "../components/VulnerabilityList";
import FixesList from "../components/FixesList";
import { API_URL } from "../config/constants";

const SAVE_SCAN_URL = `${API_URL.replace('/api/scan', '')}/api/save-scan`;

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

    const animSteps = async () => {
      const targets = [12, 30, 52, 74, 92];
      for (let i = 0; i < targets.length; i++) {
        setStepIdx(i);
        await new Promise(r=>setTimeout(r,700));
        setProgress(targets[i]);
      }
    };
    const anim = animSteps();

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });
      const data = await res.json();
      await anim;
      setProgress(100);

      if (!res.ok) {
        setApiError(data.error || data.message || "Erreur lors du scan.");
        setScanning(false);
        return;
      }

      const reportData = normalizeReport(data, url);
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

    } catch {
      await anim;
      setApiError(`Impossible de contacter Flask — vérifiez que le serveur répond`);
    }
    setScanning(false);
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

      {scanning && <ProgressBar progress={progress} stepIdx={stepIdx} />}

      {!report && !scanning && (
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
            </div>
          </div>

          <ReportMetrics report={report} scoreColor={scoreColor} scoreVerdict={scoreVerdict} />
          <ReportCharts report={report} />

          <div className="tabs">
            <button className={`tab-btn ${tab==="vulns"?"active":""}`} onClick={()=>setTab("vulns")}>
              <IconBug/> Vulnérabilités ({report.total_patches})
            </button>
            <button className={`tab-btn ${tab==="fixes"?"active":""}`} onClick={()=>setTab("fixes")}>
              <IconCode/> Correctifs IA
            </button>
          </div>

          {tab==="vulns" && <VulnerabilityList patches={report.patches} />}
          {tab==="fixes" && <FixesList patches={report.patches} />}
        </section>
      )}
    </main>
  );
}
