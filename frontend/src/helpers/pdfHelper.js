import { jsPDF } from "jspdf";

/* ════════════════════════════════════════════════════════════
   GÉNÉRATION PDF (jsPDF)
   → Rapport professionnel fond blanc
   → Page 1 : couverture + infos + score
   → Page 2 : résumé exécutif + tableau récapitulatif
   → Pages suivantes : une page par vulnérabilité avec
     point d'entrée (rouge) et correctif proposé (vert)
════════════════════════════════════════════════════════════ */
export function generatePDF(scan) {
  const doc     = new jsPDF();
  const patches = scan.patches || [];
  const W       = doc.internal.pageSize.getWidth();
  const MARGIN  = 18;
  const CW      = W - MARGIN * 2;

  const scoreCol = scan.score < 40 ? [192,0,0] : scan.score < 70 ? [180,95,0] : [0,128,80];
  const verdict  = scan.score < 40 ? "CRITIQUE" : scan.score < 70 ? "MODÉRÉ" : "BON";

  const sevMeta = {
    CRITICAL: { label: "Critique", col: [192,0,0]   },
    HIGH:     { label: "Élevé",    col: [180,95,0]  },
    MEDIUM:   { label: "Moyen",    col: [160,130,0] },
    LOW:      { label: "Faible",   col: [0,128,80]  },
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
    doc.text("SecureScan AI — Rapport confidentiel d'analyse de sécurité", MARGIN, 290);
    doc.text(new Date().toLocaleDateString("fr-FR"), W - MARGIN, 290, { align: "right" });
    return 20;
  };

  const checkY = (y, needed = 20) => {
    if (y + needed > 278) {
      y = newPage();
      doc.setFontSize(8); doc.setTextColor(150,150,150);
      doc.text("(suite)", MARGIN, y); y += 8;
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

  // PAGE 1 : COUVERTURE
  let y = newPage();
  doc.setFontSize(22); doc.setFont("helvetica","bold"); doc.setTextColor(20,20,20);
  doc.text("Rapport d'Analyse de Sécurité Web", MARGIN, y + 12);
  doc.setFontSize(11); doc.setFont("helvetica","normal"); doc.setTextColor(100,100,100);
  doc.text("Généré automatiquement par SecureScan AI", MARGIN, y + 20);
  doc.setDrawColor(26,60,140); doc.setLineWidth(1);
  doc.line(MARGIN, y + 26, W - MARGIN, y + 26);
  y += 34;

  const infoRows = [
    ["URL analysée",   scan.url || "—"],
    ["Date du scan",   scan.generated_at ? new Date(scan.generated_at).toLocaleString("fr-FR") : new Date().toLocaleString("fr-FR")],
    ["Identifiant",    scan.scan_id || "—"],
    ["Vulnérabilités", `${patches.length} détectée(s)`],
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
  doc.text("SCORE DE SÉCURITÉ GLOBAL", MARGIN + 5, y + 8);
  doc.setFillColor(225,225,225); doc.roundedRect(MARGIN + 5, y + 12, 100, 7, 1, 1, "F");
  doc.setFillColor(...scoreCol); doc.roundedRect(MARGIN + 5, y + 12, scan.score, 7, 1, 1, "F");
  doc.setFontSize(16); doc.setFont("helvetica","bold"); doc.setTextColor(...scoreCol);
  doc.text(`${scan.score} / 100`, MARGIN + 115, y + 18);
  doc.setFontSize(9); doc.setTextColor(...scoreCol);
  doc.text(`Niveau : ${verdict}`, MARGIN + 115, y + 27);
  y += 44;

  doc.setFontSize(9); doc.setFont("helvetica","bold"); doc.setTextColor(20,20,20);
  doc.text("Répartition des vulnérabilités :", MARGIN, y); y += 8;
  Object.entries(sevMeta).forEach(([k, meta]) => {
    doc.setFillColor(...meta.col); doc.circle(MARGIN + 3, y + 2, 2.5, "F");
    doc.setFontSize(9); doc.setFont("helvetica","normal"); doc.setTextColor(40,40,40);
    doc.text(`${meta.label} :`, MARGIN + 9, y + 5);
    doc.setFont("helvetica","bold"); doc.setTextColor(...meta.col);
    doc.text(`${scan.stats?.[k] || 0}`, MARGIN + 48, y + 5);
    y += 9;
  });

  // PAGE 2 : RÉSUMÉ + TABLEAU
  y = newPage();
  y = sectionTitle(y, "Résumé exécutif");
  const reco = scan.score < 40
    ? "Des vulnérabilités critiques ont été détectées. Une correction immédiate est fortement recommandée avant toute exposition publique du site."
    : scan.score < 70
    ? "Des risques modérés ont été identifiés. Il est conseillé de traiter ces vulnérabilités rapidement afin de réduire la surface d'attaque."
    : "Le site présente un niveau de sécurité satisfaisant. Continuez à surveiller régulièrement et appliquez les bonnes pratiques.";
  doc.setFontSize(9); doc.setFont("helvetica","normal"); doc.setTextColor(40,40,40);
  const recoLines = doc.splitTextToSize(reco, CW);
  doc.text(recoLines, MARGIN, y); y += recoLines.length * 5 + 12;

  y = sectionTitle(y, "Tableau récapitulatif des vulnérabilités");
  doc.setFillColor(26,60,140); doc.rect(MARGIN, y, CW, 9, "F");
  doc.setFontSize(8); doc.setFont("helvetica","bold"); doc.setTextColor(255,255,255);
  doc.text("N°", MARGIN+2, y+6); doc.text("Type", MARGIN+14, y+6);
  doc.text("Fichier", MARGIN+68, y+6); doc.text("Champ", MARGIN+108, y+6);
  doc.text("Sévérité", MARGIN+146, y+6);
  y += 9;
  patches.forEach((p, i) => {
    y = checkY(y, 10);
    if (i % 2 === 0) { doc.setFillColor(248,249,252); doc.rect(MARGIN, y, CW, 9, "F"); }
    const meta = sevMeta[p.severity?.toUpperCase()] || sevMeta.INFO;
    doc.setFontSize(8); doc.setFont("helvetica","normal"); doc.setTextColor(40,40,40);
    doc.text(`${i+1}`, MARGIN+2, y+6);
    doc.text(doc.splitTextToSize(p.type||"—",52)[0], MARGIN+14, y+6);
    doc.text(doc.splitTextToSize(p.fichier||"—",36)[0], MARGIN+68, y+6);
    doc.text(doc.splitTextToSize(p.champ||"—",34)[0], MARGIN+108, y+6);
    doc.setFont("helvetica","bold"); doc.setTextColor(...meta.col);
    doc.text(meta.label, MARGIN+146, y+6);
    y += 9;
  });

  // PAGES DÉTAIL : une page par vulnérabilité
  patches.forEach((patch, idx) => {
    y = newPage();
    const meta = sevMeta[patch.severity?.toUpperCase()] || sevMeta.INFO;
    doc.setFontSize(13); doc.setFont("helvetica","bold"); doc.setTextColor(20,20,20);
    doc.text(`${idx+1}. ${patch.type || "Vulnérabilité"}`, MARGIN, y + 4);
    const bW = 26, bX = W - MARGIN - bW;
    doc.setFillColor(...meta.col); doc.roundedRect(bX, y - 4, bW, 10, 2, 2, "F");
    doc.setFontSize(8); doc.setFont("helvetica","bold"); doc.setTextColor(255,255,255);
    doc.text(meta.label.toUpperCase(), bX + bW/2, y + 3, { align: "center" });
    doc.setDrawColor(220,220,220); doc.setLineWidth(0.3);
    doc.line(MARGIN, y + 8, W - MARGIN, y + 8);
    y += 15;

    if (patch.fichier || patch.champ || patch.url) {
      y = sectionTitle(y, "Localisation");
      if (patch.fichier) y = labelVal(y, "Fichier :", patch.fichier);
      if (patch.champ)   y = labelVal(y, "Champ :",   patch.champ);
      if (patch.url)     y = labelVal(y, "URL :",     patch.url);
      y += 4;
    }
    if (patch.explication) {
      y = checkY(y, 30); y = sectionTitle(y, "Description");
      doc.setFontSize(9); doc.setFont("helvetica","normal"); doc.setTextColor(40,40,40);
      const lines = doc.splitTextToSize(patch.explication, CW);
      doc.text(lines, MARGIN, y); y += lines.length * 5 + 8;
    }
    if (patch.solution) {
      y = checkY(y, 30); y = sectionTitle(y, "Solution proposée");
      doc.setFontSize(9); doc.setFont("helvetica","normal"); doc.setTextColor(40,40,40);
      const lines = doc.splitTextToSize(patch.solution, CW);
      doc.text(lines, MARGIN, y); y += lines.length * 5 + 8;
    }
    if (patch.code_vulnerable) {
      y = checkY(y, 35); y = sectionTitle(y, "Point d'entrée");
      y = codeBlock(y, patch.code_vulnerable, [192,0,0]);
    }
    if (patch.code_corrige) {
      y = checkY(y, 35); y = sectionTitle(y, "Correctif proposé — généré par IA");
      y = codeBlock(y, patch.code_corrige, [0,128,80]);
    }
  });

  const site = (scan.url||"scan").replace(/https?:\/\//,"").replace(/[^a-zA-Z0-9]/g,"_").slice(0,30);
  doc.save(`SecureScan_${site}_${new Date().toISOString().slice(0,10)}.pdf`);
}
