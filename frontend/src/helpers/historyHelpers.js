/**
 * History management — Supabase integration
 *
 * All scan persistence is handled server-side via Supabase.
 * This module provides the fetch/clear helpers used by HistoryPage.
 */

import { SCANS_URL } from "../config/constants";

/**
 * Fetch history from Supabase API with token verification (secure)
 * Returns array of scan entries from Supabase
 */
export async function fetchHistoryFromSupabase(token) {
  try {
    if (!token) {
      return { success: false, data: [], error: "No authentication token" };
    }

    const response = await fetch(SCANS_URL, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return { success: false, data: [], error: errorData.error || "Failed to fetch scans" };
    }

    const data = await response.json();
    return { success: true, data: data.scans || [] };
  } catch (error) {
    return { success: false, data: [], error: error.message };
  }
}

/**
 * Smart history loader — fetches from Supabase directly
 */
export async function loadHistorySmart(token) {
  const result = await fetchHistoryFromSupabase(token);
  if (result.success) {
    return { success: true, data: result.data, fromCache: false };
  }
  return { success: false, data: [], error: result.error || "No scans found" };
}

/**
 * Clear local history cache
 */
export function clearHistory() {
  localStorage.removeItem("vulnscan_history");
  localStorage.removeItem("vulnscan_history_timestamp");
}
