/**
 * Report helpers — Scoring, stats, normalization
 */

const SEVERITY_POINTS = {
  CRITICAL: 25,
  HIGH: 15,
  MEDIUM: 8,
  LOW: 3,
  INFO: 1,
};

/**
 * Calculate security score based on vulnerabilities
 * Score = 100 - sum of severity points (capped at 0)
 */
export function computeScore(patches) {
  const total = patches.reduce((acc, p) => {
    const severity = p.severity?.toUpperCase();
    return acc + (SEVERITY_POINTS[severity] || 0);
  }, 0);
  return Math.max(0, 100 - total);
}

/**
 * Calculate statistics (counts) by severity level
 */
export function computeStats(patches) {
  const stats = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 };
  patches.forEach(p => {
    const k = p.severity?.toUpperCase();
    if (k in stats) stats[k]++;
  });
  return stats;
}

/**
 * Get color based on score
 */
export function getScoreColor(score) {
  if (score < 40) return "#ff4d6d";  // red
  if (score < 70) return "#ff8c42";  // orange
  return "#06d6a0";                   // green
}

/**
 * Get verdict text based on score
 */
export function getScoreVerdict(score) {
  if (score < 40) return "CRITIQUE";
  if (score < 70) return "MODÉRÉ";
  return "BON";
}

/**
 * Normalize report structure from API response
 * Handles various field name variations from backend
 */
export function normalizeReport(apiData, url) {
  const vulnerabilitiesReport = apiData.vulnerabilities_report || {};
  const patchesReport = apiData.patches_report || {};
  const patches = patchesReport.patches || apiData.patches || [];
  
  const scanId = vulnerabilitiesReport.scan_id || patchesReport.scan_id || apiData.scan_id || `scan-${Date.now()}`;
  const generatedAt = patchesReport.generated_at || vulnerabilitiesReport.scan_date || apiData.generated_at || new Date().toISOString();
  const score = computeScore(patches);
  const stats = computeStats(patches);
  
  return {
    scan_id: scanId,
    url: url.trim(),
    generated_at: generatedAt,
    score,
    stats,
    total_patches: patchesReport.total_patches ?? apiData.total_patches ?? patches.length,
    pages_crawled: vulnerabilitiesReport.pages_crawled || apiData.pages_crawled || null,
    scan_duration_seconds: vulnerabilitiesReport.scan_duration_seconds || apiData.scan_duration_seconds || null,
    scan_duration_total: apiData.scan_duration_total || patchesReport.scan_duration_total || vulnerabilitiesReport.scan_duration_total || null,
    patches,
    vulnerabilities_report: vulnerabilitiesReport,
    patches_report: patchesReport,
  };
}
