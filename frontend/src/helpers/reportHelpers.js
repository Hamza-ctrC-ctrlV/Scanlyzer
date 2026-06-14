/**
 * Report helpers — Scoring, stats, normalization
 */

/**
 * Calculate security score based on CONFIRMED vulnerabilities
 * Score = (confirmed_vulns / total_vulns) * 100
 * 100 = all confirmed (bad) | 0 = none confirmed (good)
 */
export function computeScore(patches) {
  if (!patches || patches.length === 0) return 0; // No vulns = good score
  
  const confirmedCount = patches.filter(p => p.confirmed === true).length;
  const score = (confirmedCount / patches.length) * 100;
  
  return Math.round(score);
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
 * Get color based on score (INVERTED: 100 = bad/red, 0 = good/green)
 * Score = % of vulnerabilities that are confirmed
 */
export function getScoreColor(score) {
  if (score > 60) return "#ff4d6d";   // red - most confirmed (bad)
  if (score > 30) return "#ff8c42";   // orange - some confirmed
  return "#06d6a0";                   // green - few/none confirmed (good)
}

/**
 * Get verdict text based on score (INVERTED: 100 = bad, 0 = good)
 */
export function getScoreVerdict(score) {
  if (score > 60) return "CRITIQUE";
  if (score > 30) return "MODÉRÉ";
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
  const vulnerabilities = vulnerabilitiesReport.vulnerabilities || apiData.vulnerabilities || [];
  
  const scanId = vulnerabilitiesReport.scan_id || patchesReport.scan_id || apiData.scan_id || `scan-${Date.now()}`;
  const generatedAt = patchesReport.generated_at || vulnerabilitiesReport.scan_date || apiData.generated_at || new Date().toISOString();
  
  // Prefer score from API response; fall back to calculation if not provided
  let score = apiData.score;
  let stats = apiData.stats;
  
  if (score === undefined || stats === undefined) {
    // Use vulnerabilities for scoring (contains confirmed field)
    // Fall back to patches only if no vulnerabilities
    const itemsForStats = vulnerabilities.length > 0 ? vulnerabilities : patches;
    score = computeScore(itemsForStats);
    stats = computeStats(itemsForStats);
  }
  
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
    vulnerabilities,
    vulnerabilities_report: vulnerabilitiesReport,
    patches_report: patchesReport,
  };
}
