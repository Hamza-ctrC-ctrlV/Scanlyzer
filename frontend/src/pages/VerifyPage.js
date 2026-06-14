import React, { useState, useEffect } from "react";

export function VerifyPage({ authUser }) {
  const [viewMode, setViewMode] = useState("list"); // "list" or "new"
  const [verifiedSites, setVerifiedSites] = useState([]);
  const [fetchingList, setFetchingList] = useState(false);

  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [record, setRecord] = useState(null);
  const [message, setMessage] = useState("");

  const getAuthHeader = () => {
    const token = localStorage.getItem("vulnscan_token") || authUser?.token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchVerifiedSites = async () => {
    setFetchingList(true);
    try {
      const res = await fetch("/verify/list", {
        headers: getAuthHeader(),
      });
      const data = await res.json();
      if (res.ok && data.verifications) {
        setVerifiedSites(data.verifications);
      }
    } catch (e) {
      console.error("Failed to fetch verified sites", e);
    } finally {
      setFetchingList(false);
    }
  };

  useEffect(() => {
    if (viewMode === "list") {
      fetchVerifiedSites();
    }
  }, [viewMode]);

  const startVerification = async () => {
    setLoading(true);
    setMessage("");
    setRecord(null);

    try {
      const res = await fetch("/verify/start", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeader() },
        body: JSON.stringify({ url }),
      });
      let data;
      try {
        data = await res.json();
      } catch (jsonError) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
      }
      if (!res.ok) throw new Error(data.error || JSON.stringify(data));
      setRecord(data);
      setMessage(
        "Verification data generated — add the file at the URL shown or insert the meta tag into your homepage <head>, then click Check Now."
      );
    } catch (e) {
      console.error("Verify start error", e);
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const checkVerification = async () => {
    if (!record?.domain) return setMessage("No domain to check.");
    setLoading(true);
    setMessage("");

    try {
      const res = await fetch("/verify/check", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeader() },
        body: JSON.stringify({ domain: record.domain }),
      });
      let data;
      try {
        data = await res.json();
      } catch (jsonError) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
      }
      if (!res.ok) throw new Error(data.error || JSON.stringify(data));
      if (data.verified) {
        setMessage(data.message || "Domain verified!");
        // Refresh the list after a short delay or user action
        setTimeout(() => {
           setViewMode("list");
           setUrl("");
           setRecord(null);
           setMessage("");
        }, 2000);
      } else {
        setMessage(
          data.message ||
            "Not verified yet. Your generated verification file and meta tag are still shown above. Add one of them and try again."
        );
      }
    } catch (e) {
      console.error("Verify check error", e);
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (viewMode === "list") {
    return (
      <main className="main verify-page">
        <section className="verify-card">
          <div className="verify-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div className="hero-eyebrow">Sites Vérifiés</div>
              <h2 className="hero-title verify-title" style={{ fontSize: '1.5rem', marginBottom: 0 }}>Vos domaines</h2>
            </div>
            <button className="scan-btn" onClick={() => setViewMode("new")} style={{ padding: '8px 16px', height: 'auto' }}>
              + Nouvelle vérification
            </button>
          </div>

          <div style={{ marginTop: '20px' }}>
            {fetchingList ? (
              <p>Chargement des sites vérifiés...</p>
            ) : verifiedSites.length === 0 ? (
              <div className="empty-state" style={{ marginTop: '20px', padding: '40px 20px' }}>
                <p>Aucun site vérifié pour le moment.</p>
              </div>
            ) : (
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {verifiedSites.map((site, idx) => (
                  <li key={idx} style={{ 
                    padding: '16px', 
                    background: 'var(--bg-glass)', 
                    border: '1px solid var(--border)', 
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <strong>{site.domain}</strong>
                      <div style={{ fontSize: '0.85em', color: 'var(--text-muted)', marginTop: '4px' }}>
                        Vérifié le {new Date(site.verified_at).toLocaleDateString('fr-FR')}
                      </div>
                    </div>
                    <div style={{ color: 'var(--accent-glow)', fontWeight: 'bold' }}>✓ Vérifié</div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="main verify-page">
      <section className="verify-card">
        <div className="verify-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div className="hero-eyebrow">Vérification</div>
            <h2 className="hero-title verify-title">Vérifier la propriété du site</h2>
            <p className="hero-sub">
              Saisissez votre domaine et créez un fichier HTML spécial pour prouver que vous contrôlez ce site.
            </p>
          </div>
          <button className="theme-toggle" onClick={() => {
              setViewMode("list");
              setUrl("");
              setRecord(null);
              setMessage("");
          }}>
            Retour
          </button>
        </div>

        <div className={`url-wrapper${message && message.toLowerCase().includes('error') ? ' has-error' : ''}`}>
          <input
            className="url-input"
            type="text"
            placeholder="https://example.com, http://localhost:8000, or example.com"
            value={url}
            onChange={e => setUrl(e.target.value)}
          />
          <button className="scan-btn" onClick={startVerification} disabled={loading || !url}>
            {loading ? 'Chargement...' : 'Démarrer'}
          </button>
        </div>
        <p className="verify-note">
          Tip: pour tester localement, utilisez une URL entière comme <strong>http://localhost:8000</strong>.
          Après avoir cliqué sur Démarrer, le tag généré apparaît ci-dessous.
        </p>

        {record && (
          <div className="verify-result">
            <div className="verify-help">
              <p>Le tag à insérer est généré après avoir cliqué sur Démarrer.</p>
              <p>Vous pouvez utiliser l'une des deux options ci-dessous :</p>
              <ul>
                <li>Créer un fichier `scanner-verify.html` à la racine du site</li>
                <li>Ajouter le meta-tag dans le <code>&lt;head&gt;</code> de la page d'accueil</li>
              </ul>
            </div>
            <div className="verify-field">
              <div className="verify-label">URL du fichier</div>
              <div className="verify-value">{record.file_url}</div>
            </div>
            <div className="verify-field">
              <div className="verify-label">Contenu du fichier</div>
              <div className="verify-value">{record.file_contents}</div>
            </div>
            <div className="verify-field">
              <div className="verify-label">Meta tag</div>
              <div className="verify-value">{record.meta_tag}</div>
            </div>
            <div className="verify-actions">
              <button className="copy-btn" onClick={() => navigator.clipboard?.writeText(record.file_url)}>
                Copier l'URL
              </button>
              <button className="copy-btn" onClick={() => navigator.clipboard?.writeText(record.file_contents)}>
                Copier le contenu
              </button>
              <button className="copy-btn" onClick={() => navigator.clipboard?.writeText(record.meta_tag)}>
                Copier la balise meta
              </button>
              <button className="scan-btn" onClick={checkVerification} disabled={loading}>
                Vérifier maintenant
              </button>
            </div>
            <p className="verify-note">
              Ajoutez soit le fichier `scanner-verify.html` à la racine du site, soit la balise meta ci-dessus dans le <code>&lt;head&gt;</code> de la page d'accueil.
            </p>
          </div>
        )}

        {message && <div className="verify-message">{message}</div>}
      </section>
    </main>
  );
}

export default VerifyPage;
