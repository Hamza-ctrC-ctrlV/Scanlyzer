import React, { useState, useEffect } from "react";
import { IconHistory, IconTrash } from "../components/Icons";
import { loadHistorySmart, deleteFromHistory, clearHistory } from "../helpers/historyHelpers";
import { SEV } from "../config/constants";

/**
 * History page — view and manage past scans
 * Uses smart caching: localStorage first, then validates against Supabase
 */
export function HistoryPage({ authUser, onSelect, onBack }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [fromCache, setFromCache] = useState(false);
  const [stale, setStale] = useState(false);
  const scoreColor = s => s < 40 ? "#ff4d6d" : s < 70 ? "#ff8c42" : "#06d6a0";

  useEffect(() => {
    const loadScanHistory = async () => {
      setLoading(true);
      setError("");
      setFromCache(false);
      setStale(false);
      
      try {
        // Get the authentication token
        const token = localStorage.getItem("vulnscan_token");
        
        if (!token) {
          setError("Session expirée. Veuillez vous reconnecter.");
          setLoading(false);
          return;
        }

        // Use smart loading: localStorage first (fast), then validate
        const result = await loadHistorySmart(token);
        
        if (result.success && result.data.length > 0) {
          setHistory(result.data);
          setFromCache(result.fromCache);
          setStale(result.stale || false);
          if (result.stale) {
            setError("(Données en cache - connexion lente)");
          }
        } else if (result.data.length === 0) {
          setHistory([]);
          if (result.error) {
            setError("");  // Silent fail for empty history
          }
        } else {
          setError(result.error || "Impossible de charger l'historique");
          setHistory([]);
        }
      } catch (err) {
        setError("Erreur lors du chargement de l'historique");
        setHistory([]);
      } finally {
        setLoading(false);
      }
    };

    loadScanHistory();
  }, [authUser]);

  const handleClearAll = () => {
    clearHistory();
    setHistory([]);
  };

  const handleDeleteOne = id => {
    const updated = deleteFromHistory(id);
    setHistory(updated);
  };

  return (
    <main className="main">
      <div className="history-page fade-in">
        <div className="history-header">
          <div>
            <h2 className="history-title">Historique des scans</h2>
            <p className="history-sub">
              {history.length} scan(s) sauvegardé(s)
              {fromCache && " (cache local)"}
              {stale && " • données en cache"}
            </p>
          </div>
          <div style={{display:"flex", gap:10}}>
            <button className="btn-outline" onClick={onBack}>← Retour</button>
            {history.length > 0 && <button className="btn-danger" onClick={handleClearAll}>Tout effacer</button>}
          </div>
        </div>

        {loading && history.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon"><IconHistory size={32}/></div>
            <div className="empty-title">CHARGEMENT</div>
            <p className="empty-sub">Récupération de votre historique...</p>
          </div>
        )}

        {error && error !== "" && (
          <div style={{padding: "10px 15px", margin: "10px 0", backgroundColor: "rgba(255,77,109,0.1)", borderRadius: "6px", fontSize: "12px", color: "#ff4d6d"}}>
            ⚠️ {error}
          </div>
        )}

        {!loading && history.length === 0 && !error && (
          <div className="empty-state">
            <div className="empty-icon"><IconHistory size={32}/></div>
            <div className="empty-title">AUCUN HISTORIQUE</div>
            <p className="empty-sub">Vos scans apparaîtront ici après chaque analyse.</p>
          </div>
        )}

        {history.length > 0 && (
          <div className="history-list">
            {history.map(entry => (
              <div key={entry.scan_id} className="history-card">
                <div className="hc-left" onClick={()=>onSelect(entry)}>
                  <div className="hc-score" style={{color:scoreColor(entry.score)}}>
                    {entry.score}<span>/100</span>
                  </div>
                  <div>
                    <div className="hc-url">{entry.url}</div>
                    <div className="hc-meta">
                      {entry.generated_at && <span>📅 {new Date(entry.generated_at).toLocaleString("fr-FR")}</span>}
                      <span>🐛 {entry.total_patches} vulnérabilité(s)</span>
                      <span className="hc-id">{entry.scan_id}</span>
                    </div>
                    <div className="hc-badges">
                      {Object.entries(entry.stats||{}).map(([k,v]) => v > 0 ? (
                        <span key={k} className="hc-badge" style={{color:SEV[k]?.color, borderColor:SEV[k]?.color+"40", background:SEV[k]?.bg}}>
                          {v} {k}
                        </span>
                      ) : null)}
                    </div>
                  </div>
                </div>
                <button className="btn-icon" onClick={()=>handleDeleteOne(entry.scan_id)}><IconTrash/></button>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
