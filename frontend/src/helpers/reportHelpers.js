/**
 * Report helpers — Scoring, stats, normalization
 */

/**
 * Calculate security score using weighted severity.
 * The score is the weighted severity total divided by the maximum possible
 * severity total for the same number of vulnerabilities, then converted to a
 * percentage out of 100.
 */
const SEVERITY_WEIGHTS = {
  CRITICAL: 30,
  HIGH: 25,
  MEDIUM: 15,
  LOW: 10,
  INFO: 5,
};

export function computeScore(patches) {
  if (!patches || patches.length === 0) return 0;

  const maxWeight = Math.max(...Object.values(SEVERITY_WEIGHTS));
  const totalWeight = patches.reduce((sum, p) => {
    const severity = (p.severity || "").toUpperCase();
    return sum + (SEVERITY_WEIGHTS[severity] || 0);
  }, 0);

  const maxTotalWeight = patches.length * maxWeight;
  const score = maxTotalWeight === 0 ? 0 : (totalWeight / maxTotalWeight) * 100;

  return Math.round(Math.min(100, Math.max(0, score)));
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
 * Score = weighted severity percentage from 0 to 100
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
  if (score > 60) return "CRITICAL";
  if (score > 30) return "MODERATE";
  return "GOOD";
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
