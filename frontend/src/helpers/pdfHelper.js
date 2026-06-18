import { jsPDF } from "jspdf";

/**
 * Draws a horizontal bar chart of vulnerability counts by severity into a jsPDF document.
 *
 * Replaces the old dot+number list with proportional bars, so the reader can
 * compare severities visually instead of just reading numbers.
 *
 * @param {jsPDF} doc      - the jsPDF document instance
 * @param {object} scan    - object with a `.stats` map, e.g. { critical: 4, high: 9, ... }
 * @param {object} sevMeta - ordered map of severity key -> { label, col: [r,g,b] }
 * @param {number} MARGIN  - left margin (matches your existing layout)
 * @param {number} y       - starting y position; returns the new y after drawing
 * @returns {number} the y position after the chart, so you can continue laying out content below it
 */
export function drawVulnerabilityChart(doc, scan, sevMeta, MARGIN, CW, y) {
  const entries = Object.entries(sevMeta);
  const counts = entries.map(([k]) => scan.stats?.[k] || 0);
  const maxCount = Math.max(...counts, 1); // avoid divide-by-zero when all counts are 0

  const chartWidth = 130;      // max pixel width a full bar can take
  const barHeight = 5.5;
  const barGap = 4;            // vertical gap between bars
  const labelWidth = 28;       // reserved space for severity labels on the left
  const barStartX = MARGIN + labelWidth;

  doc.setFillColor(240,244,255); doc.rect(MARGIN, y, CW, 8, "F");
  doc.setFillColor(26,60,140);   doc.rect(MARGIN, y, 3, 8, "F");
  doc.setFontSize(9); doc.setFont("helvetica","bold"); doc.setTextColor(26,60,140);
  doc.text("Vulnerability distribution".toUpperCase(), MARGIN + 7, y + 5.5);
  y += 14;

  entries.forEach(([k, meta], i) => {
    const count = counts[i];
    const barLength = (count / maxCount) * chartWidth;

    // Severity label, right-aligned against the bar start
    doc.setFontSize(8.5);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(60, 60, 60);
    doc.text(meta.label, barStartX - 3, y + barHeight - 1.5, { align: "right" });

    // Track (light background) so short bars still show full scale context
    doc.setFillColor(235, 235, 235);
    doc.roundedRect(barStartX, y, chartWidth, barHeight, 1, 1, "F");

    // Actual bar, proportional to count
    if (barLength > 0) {
      doc.setFillColor(...meta.col);
      doc.roundedRect(barStartX, y, Math.max(barLength, 2), barHeight, 1, 1, "F");
    }

    // Count, placed just after the bar (or inside track start if bar is 0)
    doc.setFontSize(8.5);
    doc.setFont("helvetica", "bold");
    doc.setTextColor(...meta.col);
    doc.text(`${count}`, barStartX + chartWidth + 4, y + barHeight - 1.5);

    y += barHeight + barGap;
  });

  return y + 2; // small trailing gap before whatever content comes next
}

/* ════════════════════════════════════════════════════════════
   PDF GENERATION (jsPDF)
   → Professional white-paper layout
   → Page 1: cover + metadata + score
   → Page 2: executive summary + vulnerability summary table
   → Following pages: one vulnerability per page with
     entry point (red) and AI-generated fix (green)
════════════════════════════════════════════════════════════ */
function parseReportValue(value) {
  if (!value) return undefined;
  if (typeof value === "string") {
    try {
      return JSON.parse(value);
    } catch {
      return undefined;
    }
  }
  if (typeof value === "object") return value;
  return undefined;
}

export function generatePDF(scan) {
  const doc = new jsPDF();
  const patchesReport = parseReportValue(scan.patches_report);
  const patches = scan.patches || patchesReport?.patches || [];
  const totalVulnerabilities = scan.total_patches ?? patches.length;
  const W = doc.internal.pageSize.getWidth();
  const MARGIN = 18;
  const CW = W - MARGIN * 2;

  const score = typeof scan.score === "number" ? scan.score : 0;
  const scoreCol = score < 40 ? [192,0,0] : score < 70 ? [180,95,0] : [0,128,80];
  const verdict = score < 40 ? "GOOD" : score < 70 ? "MODERATE" : "CRITICAL";

  const sevMeta = {
    CRITICAL: { label: "Critical", col: [192,0,0]   },
    HIGH:     { label: "High",     col: [180,95,0]  },
    MEDIUM:   { label: "Medium",   col: [160,130,0] },
    LOW:      { label: "Low",      col: [0,128,80]  },
    INFO:     { label: "Info",     col: [30,80,180] },
  };

  let pageNum = 0;

  const newPage = () => {
    if (pageNum > 0) doc.addPage();
    pageNum++;
    doc.setFillColor(255,255,255); doc.rect(0, 0, W, 297, "F");
    doc.setFillColor(26,60,140);   doc.rect(0, 0, W, 10, "F");
    doc.setFontSize(8); doc.setTextColor(255,255,255); doc.setFont("helvetica","normal");
    doc.text(`Page ${pageNum}`, W - MARGIN, 7, { align: "right" });
    doc.setDrawColor(200,200,200); doc.setLineWidth(0.3);
    doc.line(MARGIN, 284, W - MARGIN, 284);
    doc.setFontSize(7.5); doc.setTextColor(150,150,150);
    doc.text("Scanlyzer AI — Confidential Security Analysis Report", MARGIN, 290);
    doc.text(new Date().toLocaleDateString("en-US"), W - MARGIN, 290, { align: "right" });
    return 20;
  };

  const checkY = (y, needed = 20) => {
    if (y + needed > 278) {
      y = newPage();
      doc.setFontSize(8); doc.setTextColor(150,150,150);
      doc.text("(continued)", MARGIN, y); y += 8;
    }
    return y;
  };

  const sectionTitle = (y, text) => {
    doc.setFillColor(240,244,255); doc.rect(MARGIN, y, CW, 8, "F");
    doc.setFillColor(26,60,140);   doc.rect(MARGIN, y, 3, 8, "F");
    doc.setFontSize(9); doc.setFont("helvetica","bold"); doc.setTextColor(26,60,140);
    doc.text(text.toUpperCase(), MARGIN + 7, y + 5.5);
    return y + 14;
  };

  const labelVal = (y, key, value) => {
    doc.setFontSize(9); doc.setFont("helvetica","bold"); doc.setTextColor(80,80,80);
    doc.text(key, MARGIN, y);
    doc.setFont("helvetica","normal"); doc.setTextColor(20,20,20);
    const lines = doc.splitTextToSize(value || "—", CW - 45);
    doc.text(lines, MARGIN + 45, y);
    return y + lines.length * 5 + 3;
  };

  const codeBlock = (y, code, borderCol) => {
    const lines = doc.splitTextToSize(code, CW - 10);
    const boxH  = lines.length * 4.8 + 8;
    y = checkY(y, boxH + 6);
    doc.setFillColor(248,249,250); doc.roundedRect(MARGIN, y, CW, boxH, 1, 1, "F");
    doc.setDrawColor(...borderCol); doc.setLineWidth(0.6);
    doc.line(MARGIN, y, MARGIN, y + boxH);
    doc.setLineWidth(0.2); doc.setDrawColor(220,220,220);
    doc.roundedRect(MARGIN, y, CW, boxH, 1, 1, "S");
    doc.setFont("courier","normal"); doc.setFontSize(7.5); doc.setTextColor(40,40,40);
    doc.text(lines, MARGIN + 5, y + 6);
    return y + boxH + 6;
  };

  // PAGE 1 : COVER
  let y = newPage();
  doc.setFontSize(22); doc.setFont("helvetica","bold"); doc.setTextColor(20,20,20);
  doc.text("Web Security Analysis Report", MARGIN, y + 12);
  doc.setFontSize(11); doc.setFont("helvetica","normal"); doc.setTextColor(100,100,100);
  doc.text("Generated automatically by Scanlyzer AI", MARGIN, y + 20);
  doc.setDrawColor(26,60,140); doc.setLineWidth(1);
  doc.line(MARGIN, y + 26, W - MARGIN, y + 26);
  y += 34;

  const infoRows = [
    ["Target URL",      scan.url || "—"],
    ["Scan Date",       scan.generated_at ? new Date(scan.generated_at).toLocaleString("en-US") : new Date().toLocaleString("en-US")],
    ["Scan ID",         scan.scan_id || "—"],
    ["Vulnerabilities", `Total vulnerabilities found: ${totalVulnerabilities}`],
    ["Pages crawled",   scan.pages_crawled != null ? String(scan.pages_crawled) : "—"],
    ["Scan duration",   scan.scan_duration_total != null ? `${scan.scan_duration_total}s` : "—"],
  ];
  infoRows.forEach(([k, v], i) => {
    if (i % 2 === 0) { doc.setFillColor(248,249,252); doc.rect(MARGIN, y - 3, CW, 11, "F"); }
    doc.setFontSize(9); doc.setFont("helvetica","bold"); doc.setTextColor(80,80,80);
    doc.text(k, MARGIN + 3, y + 4);
    doc.setFont("helvetica","normal"); doc.setTextColor(20,20,20);
    doc.text(doc.splitTextToSize(v, CW - 60), MARGIN + 58, y + 4);
    y += 12;
  });
  y += 10;

  doc.setDrawColor(220,220,220); doc.setLineWidth(0.3); doc.rect(MARGIN, y, CW, 34, "S");
  doc.setFontSize(8); doc.setFont("helvetica","bold"); doc.setTextColor(80,80,80);
  doc.text("OVERALL SECURITY SCORE", MARGIN + 5, y + 8);
  doc.setFillColor(225,225,225); doc.roundedRect(MARGIN + 5, y + 12, 100, 7, 1, 1, "F");
  doc.setFillColor(...scoreCol); doc.roundedRect(MARGIN + 5, y + 12, scan.score, 7, 1, 1, "F");
  doc.setFontSize(16); doc.setFont("helvetica","bold"); doc.setTextColor(...scoreCol);
  doc.text(`${scan.score} / 100`, MARGIN + 115, y + 18);
  doc.setFontSize(9); doc.setTextColor(...scoreCol);
  doc.text(`Verdict : ${verdict}`, MARGIN + 115, y + 27);
  y += 44;
  y = drawVulnerabilityChart(doc, scan, sevMeta, MARGIN, CW, y);

  // PAGE 2 : EXECUTIVE SUMMARY + TABLE
  y = newPage();
  const verdictMsg = scan.score >= 70
    ? "Critical vulnerabilities were detected. Immediate remediation is strongly recommended before any public exposure of the site."
    : scan.score < 70 && scan.score >= 40
    ? "Moderate risks were identified. It is advised to address these vulnerabilities promptly to reduce your attack surface."
    : "The site shows a satisfactory security posture. Continue to monitor regularly and follow best practices.";
  y = renderPage2Findings(doc, scan, patches, sevMeta, MARGIN, CW, y, verdictMsg);

  // DETAIL PAGES: one page per vulnerability
  patches.forEach((patch, idx) => {
    y = newPage();
    const meta = sevMeta[patch.severity?.toUpperCase()] || sevMeta.INFO;
    doc.setFontSize(13); doc.setFont("helvetica","bold"); doc.setTextColor(20,20,20);
    doc.text(`${idx+1}. ${patch.type || "Vulnerability"}`, MARGIN, y + 4);
    const bW = 26, bX = W - MARGIN - bW;
    doc.setFillColor(...meta.col); doc.roundedRect(bX, y - 4, bW, 10, 2, 2, "F");
    doc.setFontSize(8); doc.setFont("helvetica","bold"); doc.setTextColor(255,255,255);
    doc.text(meta.label.toUpperCase(), bX + bW/2, y + 3, { align: "center" });
    doc.setDrawColor(220,220,220); doc.setLineWidth(0.3);
    doc.line(MARGIN, y + 8, W - MARGIN, y + 8);
    y += 15;

    if (patch.fichier || patch.champ || patch.url) {
      y = sectionTitle(y, "Location");
      if (patch.fichier) y = labelVal(y, "File:", patch.fichier);
      if (patch.champ)   y = labelVal(y, "Field:", patch.champ);
      if (patch.url)     y = labelVal(y, "URL:", patch.url);
      y += 4;
    }
    if (patch.explication) {
      y = checkY(y, 30); y = sectionTitle(y, "Description");
      doc.setFontSize(9); doc.setFont("helvetica","normal"); doc.setTextColor(40,40,40);
      const lines = doc.splitTextToSize(patch.explication, CW);
      doc.text(lines, MARGIN, y); y += lines.length * 5 + 8;
    }
    if (patch.solution) {
      y = checkY(y, 30); y = sectionTitle(y, "Proposed Solution");
      doc.setFontSize(9); doc.setFont("helvetica","normal"); doc.setTextColor(40,40,40);
      const lines = doc.splitTextToSize(patch.solution, CW);
      doc.text(lines, MARGIN, y); y += lines.length * 5 + 8;
    }
    if (patch.code_vulnerable) {
      y = checkY(y, 35); y = sectionTitle(y, "Entry Point");
      y = codeBlock(y, patch.code_vulnerable, [192,0,0]);
    }
    if (patch.code_corrige) {
      y = checkY(y, 35); y = sectionTitle(y, "AI-generated Fix");
      y = codeBlock(y, patch.code_corrige, [0,128,80]);
    }
  });

  const site = (scan.url||"scan").replace(/https?:\/\//,"").replace(/[^a-zA-Z0-9]/g,"_").slice(0,30);
  doc.save(`Scanlyzer_${site}_${new Date().toISOString().slice(0,10)}.pdf`);
}

/**
 * Renders page 2 content: EXECUTIVE SUMMARY (verdict + per-patch descriptions)
 * followed by VULNERABILITY SUMMARY TABLE (Type / Severity / Solution).
 *
 * @param {jsPDF} doc
 * @param {object} scan       - full normalized scan report object
 * @param {array} patches      - array of vulnerability patches from scan.patches
 * @param {object} sevMeta     - severity -> { label, col:[r,g,b] } map
 * @param {number} MARGIN
 * @param {number} PAGE_WIDTH  - usable content width
 * @param {number} y           - starting y position
 * @param {string} verdictMsg  - verdict message to display
 * @returns {number} new y position after everything drawn
 */
function renderPage2Findings(doc, scan, patches, sevMeta, MARGIN, PAGE_WIDTH, y, verdictMsg) {
  // Helper: resolve severity meta safely
  function resolveSevMeta(sev) {
    const key = Object.keys(sevMeta).find(
      k => k.toLowerCase() === String(sev || "").toLowerCase()
    );
    return key ? sevMeta[key] : { label: sev || "Unknown", col: [100, 100, 100] };
  }

  // SECTION 1 — EXECUTIVE SUMMARY
  doc.setFillColor(240,244,255); doc.rect(MARGIN, y, PAGE_WIDTH, 8, "F");
  doc.setFillColor(26,60,140);   doc.rect(MARGIN, y, 3, 8, "F");
  doc.setFontSize(9); doc.setFont("helvetica","bold"); doc.setTextColor(26,60,140);
  doc.text("EXECUTIVE SUMMARY", MARGIN + 7, y + 5.5);
  y += 14;

  doc.setFontSize(9); doc.setFont("helvetica","normal"); doc.setTextColor(40,40,40);
  const summaryText = scan.report_summary || scan.summary || patchesReport?.summary || patchesReport?.report_summary ||
    "This executive summary draws from the same AI-generated findings used by the dashboard: vulnerability type, severity, explanation, and remediation guidance for each issue.";
  const summaryLines = doc.splitTextToSize(summaryText, PAGE_WIDTH);
  doc.text(summaryLines, MARGIN, y);
  y += summaryLines.length * 5 + 10;

  const verdictLines = doc.splitTextToSize(verdictMsg, PAGE_WIDTH);
  doc.text(verdictLines, MARGIN, y);
  y += verdictLines.length * 5 + 12;

  // One summary per patch
  patches.forEach((p, i) => {
    const meta = resolveSevMeta(p.severity);
    doc.setFillColor(...meta.col); doc.circle(MARGIN + 2.5, y - 2.5, 2.2, "F");
    doc.setFontSize(9.5); doc.setFont("helvetica","bold"); doc.setTextColor(20, 20, 20);
    doc.text(`${i + 1}. ${p.type || "Vulnerability"}`, MARGIN + 9, y);
    y += 10;

    doc.setFontSize(8.5); doc.setFont("helvetica","normal"); doc.setTextColor(60, 60, 60);
    const expl = doc.splitTextToSize(p.explication || "—", PAGE_WIDTH - 14);
    doc.text(expl, MARGIN + 9, y);
    y += expl.length * 5 + 8;

    if (p.cve_urls?.length || p.cwe_urls?.length) {
      const linkLines = [
        ...(p.cve_urls || []).slice(0, 2).map((url) => `CVE: ${url}`),
        ...(p.cwe_urls || []).slice(0, 2).map((url) => `CWE: ${url}`),
      ];
      if (linkLines.length > 0) {
        doc.setFontSize(8); doc.setFont("helvetica","italic"); doc.setTextColor(90, 90, 90);
        doc.text(linkLines, MARGIN + 9, y);
        y += linkLines.length * 5 + 8;
      }
    }

    if (y > 760) { doc.addPage(); y = 50; }
  });

  y += 6;

  // SECTION 2 — VULNERABILITY SUMMARY TABLE
  doc.setFillColor(240,244,255); doc.rect(MARGIN, y, PAGE_WIDTH, 8, "F");
  doc.setFillColor(26,60,140);   doc.rect(MARGIN, y, 3, 8, "F");
  doc.setFontSize(9); doc.setFont("helvetica","bold"); doc.setTextColor(26,60,140);
  doc.text("VULNERABILITY SUMMARY TABLE", MARGIN + 7, y + 5.5);
  y += 14;

  const colTypeW = PAGE_WIDTH * 0.30;
  const colSevW = 70;
  const colSolW = PAGE_WIDTH - colTypeW - colSevW;
  const colTypeX = MARGIN;
  const colSevX = MARGIN + colTypeW;
  const colSolX = colSevX + colSevW;

  // Table header
  doc.setFillColor(26, 60, 140); doc.rect(MARGIN, y, PAGE_WIDTH, 9, "F");
  doc.setFontSize(8); doc.setFont("helvetica","bold"); doc.setTextColor(255,255,255);
  doc.text("Type", colTypeX + 3, y + 6);
  doc.text("Severity", colSevX + 3, y + 6);
  doc.text("Solution", colSolX + 3, y + 6);
  y += 10;

  // Table rows
  patches.forEach((p, i) => {
    const meta = resolveSevMeta(p.severity);
    const typeLines = doc.splitTextToSize(p.type || "—", colTypeW - 6);
    const solLines = doc.splitTextToSize(p.solution || "—", colSolW - 6);
    const rowH = Math.max(typeLines.length, solLines.length, 1) * 5 + 6;

    if (y + rowH > 770) {
      doc.addPage();
      y = 50;
      doc.setFillColor(26, 60, 140); doc.rect(MARGIN, y, PAGE_WIDTH, 9, "F");
      doc.setFontSize(8); doc.setFont("helvetica","bold"); doc.setTextColor(255,255,255);
      doc.text("Type", colTypeX + 3, y + 6);
      doc.text("Severity", colSevX + 3, y + 6);
      doc.text("Solution", colSolX + 3, y + 6);
      y += 10;
    }

    if (i % 2 === 0) { doc.setFillColor(248,249,252); doc.rect(MARGIN, y, PAGE_WIDTH, rowH, "F"); }
    doc.setFontSize(8); doc.setFont("helvetica","normal"); doc.setTextColor(40,40,40);
    doc.text(typeLines, colTypeX + 3, y + 2);

    doc.setFillColor(...meta.col); doc.roundedRect(colSevX + 2, y + 1, colSevW - 4, 7, 1, 1, "F");
    doc.setFontSize(7); doc.setFont("helvetica","bold"); doc.setTextColor(255,255,255);
    doc.text(meta.label, colSevX + colSevW / 2, y + 5, { align: "center" });

    doc.setFontSize(8); doc.setFont("helvetica","normal"); doc.setTextColor(40,40,40);
    doc.text(solLines, colSolX + 3, y + 2);

    doc.setDrawColor(220,220,220); doc.setLineWidth(0.2);
    doc.line(MARGIN, y + rowH, MARGIN + PAGE_WIDTH, y + rowH);
    y += rowH;
  });

  return y;
}