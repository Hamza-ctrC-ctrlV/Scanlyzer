/**
 * History management — localStorage helpers and Supabase integration with smart caching
 */

import { SCANS_URL } from "../config/constants";

const LS_KEY = "vulnscan_history";
const LS_CACHE_TIMESTAMP = "vulnscan_history_timestamp";
const CACHE_DURATION_MS = 60 * 1000; // 1 minute cache

/**
 * Load history from localStorage
 * Returns array of scan entries or empty array if invalid
 */
export function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(LS_KEY)) || [];
  } catch {
    return [];
  }
}

/**
 * Check if local cache is still valid (less than CACHE_DURATION_MS old)
 */
export function isCacheValid() {
  try {
    const timestamp = localStorage.getItem(LS_CACHE_TIMESTAMP);
    if (!timestamp) return false;
    const age = Date.now() - parseInt(timestamp);
    return age < CACHE_DURATION_MS;
  } catch {
    return false;
  }
}

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

export async function loadHistorySmart(token) {
  const result = await fetchHistoryFromSupabase(token);
  if (result.success) {
    return { success: true, data: result.data, fromCache: false };
  }
  return { success: false, data: [], error: result.error || "No scans found" };
}

/**
 * Save history array to localStorage with timestamp
 */
export function saveHistory(list) {
  localStorage.setItem(LS_KEY, JSON.stringify(list));
  localStorage.setItem(LS_CACHE_TIMESTAMP, Date.now().toString());
}

export function addToHistory(entry) {
  // Now handled by Supabase entirely
}

export function deleteFromHistory(scanId) {
  // Handled by API
  return [];
}

/**
 * Clear all history and cache timestamp
 */
export function clearHistory() {
  localStorage.removeItem(LS_KEY);
  localStorage.removeItem(LS_CACHE_TIMESTAMP);
}

