import React, { useState } from "react";
import { IconBug, IconCode } from "./Icons";
import { generatePDF } from "../helpers/pdfHelper";
import { getScoreColor, getScoreVerdict } from "../helpers/reportHelpers";
import ReportMetrics from "./ReportMetrics";
import ReportCharts from "./ReportCharts";
import VulnerabilityList from "./VulnerabilityList";
import FixesList from "./FixesList";

/**
 * Reusable component to view a full scan report.
 * Provides tabs for vulnerabilities and AI fixes, charts, and metrics.
 */
export function ReportViewer({ report, hideTopbar = false }) {
  const [tab, setTab] = useState("vulns");

  if (!report) return null;

  const scoreColor = getScoreColor(report.score);
  const scoreVerdict = getScoreVerdict(report.score);

  return (
    <section className="report fade-in">
      {!hideTopbar && (
        <div className="report-topbar">
          <div>
            <div className="rtb-lbl">Scanned URL · {report.scan_id}</div>
            <div className="rtb-url">{report.url}</div>
          </div>
          <div className="rtb-right">
            <div className="rtb-lbl">Generated on</div>
            <div className="rtb-time">
              {report.generated_at
                ? new Date(report.generated_at).toLocaleString("en-US")
                : new Date().toLocaleString("en-US")}
            </div>
            {report.scan_duration_total && (
              <div className="rtb-duration">⏱ {report.scan_duration_total}s (total)</div>
            )}
          </div>
        </div>
      )}

      <ReportMetrics report={report} scoreColor={scoreColor} scoreVerdict={scoreVerdict} />
      <ReportCharts report={report} />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div className="tabs" style={{ marginBottom: 0 }}>
          <button className={`tab-btn ${tab==="vulns"?"active":""}`} onClick={()=>setTab("vulns")}>
            <IconBug/> Vulnerabilities ({report.total_patches})
          </button>
          <button className={`tab-btn ${tab==="fixes"?"active":""}`} onClick={()=>setTab("fixes")}>
            <IconCode/> AI Fixes
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
          Export PDF
        </button>
      </div>

      {tab==="vulns" && <VulnerabilityList patches={report.patches} />}
      {tab==="fixes" && <FixesList patches={report.patches} />}
    </section>
  );
}

export default ReportViewer;
