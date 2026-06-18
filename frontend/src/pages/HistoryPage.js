import React, { useState, useEffect } from "react";
import { IconHistory, IconTrash } from "../components/Icons";
import { loadHistorySmart, deleteFromHistory, clearHistory } from "../helpers/historyHelpers";
import { generatePDF } from "../helpers/pdfHelper";
import { SEV, API_BASE_URL, REPORT_URL } from "../config/constants";
import { normalizeReport, getScoreColor } from "../helpers/reportHelpers";
import { HistoryCardSkeleton } from "../components/Skeleton";
import ReportViewer from "../components/ReportViewer";

/**
 * History page — view and manage past scans
 * Each card is expandable with full report details inline
 */
export function HistoryPage({ authUser, onBack }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [fromCache, setFromCache] = useState(false);
  const [stale, setStale] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [expandedData, setExpandedData] = useState({});
  const [loadingReport, setLoadingReport] = useState(null);

  useEffect(() => {
    const loadScanHistory = async () => {
      setLoading(true);
      setError("");
      setFromCache(false);
      setStale(false);
      
      try {
        const token = localStorage.getItem("vulnscan_token");
        
        if (!token) {
          setError("Session expired. Please log in again.");
          setLoading(false);
          return;
        }

        const result = await loadHistorySmart(token);
        
        if (result.success && result.data.length > 0) {
          setHistory(result.data);
          setFromCache(result.fromCache);
          setStale(result.stale || false);
          if (result.stale) {
            setError("(Cached data - slow connection)");
          }
        } else if (result.data.length === 0) {
          setHistory([]);
          if (result.error) {
            setError("");
          }
        } else {
          setError(result.error || "Unable to load history");
          setHistory([]);
        }
      } catch (err) {
        setError("Error loading history");
        setHistory([]);
      } finally {
        setLoading(false);
      }
    };

    loadScanHistory();
  }, [authUser]);

  const handleClearAll = () => {
    if (!window.confirm("Are you sure you want to clear EVERYTHING? This action is irreversible.")) return;

    const currentHistory = [...history];
    clearHistory();
    setHistory([]);
    setExpandedId(null);
    setExpandedData({});

    try {
      const token = authUser?.token || localStorage.getItem("vulnscan_token");
      const userId = authUser?.user_id || localStorage.getItem("vulnscan_user_id");
      if (!token || !userId) return;

      const deleteUrl = `${API_BASE_URL}/api/delete-scan`;
      currentHistory.forEach(entry => {
        fetch(deleteUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
          body: JSON.stringify({ user_id: userId, scan_id: entry.scan_id })
        }).catch(err => console.error("Backend deletion error:", err));
      });
    } catch (err) {
      console.error("General deletion error:", err);
    }
  };

  const handleDeleteOne = async (id) => {
    if (!window.confirm("Do you really want to delete this scan?")) return;

    setHistory(prev => prev.filter(h => h.scan_id !== id));
    if (expandedId === id) { setExpandedId(null); }

    try {
      const token = authUser?.token || localStorage.getItem("vulnscan_token");
      const userId = authUser?.user_id || localStorage.getItem("vulnscan_user_id");
      if (!token || !userId) return;

      await fetch(`${API_BASE_URL}/api/delete-scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ user_id: userId, scan_id: id })
      });
    } catch (err) {
      console.error("Backend deletion error:", err);
    }
  };

  const fetchFullReport = async (entry) => {
    const id = entry.scan_id;
    if (expandedData[id]) return expandedData[id];

    setLoadingReport(id);
    try {
      const token = authUser?.token || localStorage.getItem("vulnscan_token");
      const url = `${REPORT_URL}?scan_id=${encodeURIComponent(id)}`;
      const res = await fetch(url, {
        headers: { Authorization: token ? `Bearer ${token}` : "" },
      });
      const data = await res.json();
      if (res.ok && data) {
        const reportData = normalizeReport(data, entry.url || "");
        setExpandedData(prev => ({ ...prev, [id]: reportData }));
        return reportData;
      }
    } catch (e) {
      console.error("Error loading report:", e);
    } finally {
      setLoadingReport(null);
    }
    return null;
  };

  const toggleExpand = async (entry) => {
    const id = entry.scan_id;

    if (expandedId === id) {
      setExpandedId(null);
      return;
    }

    setExpandedId(id);
    if (!expandedData[id]) {
      await fetchFullReport(entry);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "—";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  };

  return (
    <main className="main">
      <div className="history-page fade-in">
        <div className="history-header">
          <div>
            <h2 className="history-title">Scan History</h2>
            <p className="history-sub">
              {history.length} saved scan(s)
              {fromCache && " (local cache)"}
              {stale && " • cached data"}
            </p>
          </div>
          <div style={{display:"flex", gap:10}}>
            <button className="btn-outline" onClick={onBack}>← Back</button>
            {history.length > 0 && <button className="btn-danger" onClick={handleClearAll}>Clear All</button>}
          </div>
        </div>

        {loading && history.length === 0 && (
          <HistoryCardSkeleton count={4} />
        )}

        {error && error !== "" && (
          <div style={{padding: "10px 15px", margin: "10px 0", backgroundColor: "rgba(255,77,109,0.1)", borderRadius: "6px", fontSize: "12px", color: "#ff4d6d"}}>
            ⚠️ {error}
          </div>
        )}

        {!loading && history.length === 0 && !error && (
          <div className="empty-state">
            <div className="empty-icon"><IconHistory size={32}/></div>
            <div className="empty-title">NO HISTORY</div>
            <p className="empty-sub">Your scans will appear here after each analysis.</p>
          </div>
        )}

        {history.length > 0 && (
          <div className="history-list">
            {history.map(entry => {
              const isOpen = expandedId === entry.scan_id;
              const report = expandedData[entry.scan_id];
              const isLoadingThis = loadingReport === entry.scan_id;

              return (
                <div key={entry.scan_id} className={`hist-card ${isOpen ? "hist-card--open" : ""}`}>
                  {/* Card header — click to expand */}
                  <div className="hist-card-header" onClick={() => toggleExpand(entry)}>
                    <div className="hist-card-score" style={{ color: getScoreColor(entry.score) }}>
                      <span className="hist-score-num">{entry.score}</span>
                      <span className="hist-score-max">/100</span>
                    </div>

                    <div className="hist-card-info">
                      <div className="hist-card-url">{entry.url || "—"}</div>
                      <div className="hist-card-meta">
                        <span> {formatDate(entry.generated_at)}</span>
                        <span> {entry.total_patches} vulnerability(s)</span>
                        {entry.scan_duration_total && <span>⏱ {entry.scan_duration_total}s</span>}
                      </div>
                      <div className="hc-badges">
                        {Object.entries(entry.stats || {}).map(([k, v]) => v > 0 ? (
                          <span key={k} className="hc-badge" style={{ color: SEV[k]?.color, borderColor: SEV[k]?.color + "40", background: SEV[k]?.bg }}>
                            {v} {k}
                          </span>
                        ) : null)}
                      </div>
                    </div>

                    <div className="hist-card-actions">
                      <button className="btn-icon" title="Export to PDF" onClick={(e) => { e.stopPropagation(); generatePDF(entry); }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                      </button>
                      <button className="btn-icon" title="Delete" onClick={(e) => { e.stopPropagation(); handleDeleteOne(entry.scan_id); }}>
                        <IconTrash />
                      </button>
                      <span className={`hist-chevron ${isOpen ? "hist-chevron--open" : ""}`}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                      </span>
                    </div>
                  </div>

                  {/* Expandable body */}
                  {isOpen && (
                    <div className="hist-card-body">
                      {isLoadingThis && (
                        <div className="hist-loading">
                          <div className="hist-loading-spinner" />
                          <span>Loading report...</span>
                        </div>
                      )}

                      {!isLoadingThis && !report && (
                        <div className="hist-loading">
                          <span style={{ color: "var(--muted)" }}>No detailed report available.</span>
                        </div>
                      )}

                      {!isLoadingThis && report && (
                        <div style={{ padding: "0 16px 16px" }}>
                          <ReportViewer report={report} hideTopbar={true} />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}

