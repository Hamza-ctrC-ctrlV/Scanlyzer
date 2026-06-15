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
      const res = await fetch("/api/verify/list", {
        headers: getAuthHeader(),
      });
      if (!res.ok && res.status === 404) {
        const altRes = await fetch("/verify/list", { headers: getAuthHeader() });
        const altData = await altRes.json();
        if (altRes.ok && altData.verifications) setVerifiedSites(altData.verifications);
        return;
      }
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

  // Wait, I should just use /verify/list since the proxy handles it.
  // Actually, wait, the endpoints are under /verify in verify_routes.py but it is registered without url_prefix="/api" in app.py!
  // app.register_blueprint(verify_bp) -> so it's /verify/list.
  
  useEffect(() => {
    if (viewMode === "list") {
      fetchVerifiedSites();
    }
  }, [viewMode]);

  const deleteVerification = async (domain) => {
    if (!window.confirm(`Are you sure you want to delete the verification for ${domain}?`)) return;
    
    try {
      const res = await fetch("/verify/delete", {
        method: "DELETE",
        headers: { "Content-Type": "application/json", ...getAuthHeader() },
        body: JSON.stringify({ domain })
      });
      if (res.ok) {
        setVerifiedSites(prev => prev.filter(s => s.domain !== domain));
      } else {
        alert("Failed to delete verification.");
      }
    } catch (e) {
      console.error("Failed to delete verification", e);
    }
  };

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
        // Refresh the list after a short delay
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
              <div className="hero-eyebrow">Verified Sites</div>
              <h2 className="hero-title verify-title" style={{ fontSize: '1.5rem', marginBottom: 0 }}>Your Domains</h2>
            </div>
            <button className="scan-btn" onClick={() => setViewMode("new")} style={{ padding: '8px 16px', height: 'auto', borderRadius: 'var(--r)' }}>
              + New Verification
            </button>
          </div>

          <div style={{ marginTop: '20px' }}>
            {fetchingList ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {[1, 2].map(i => (
                  <div key={i} className="skeleton skeleton-hist-card" style={{ height: '70px', padding: 0, borderRadius: '12px' }}></div>
                ))}
              </div>
            ) : verifiedSites.length === 0 ? (
              <div className="empty-state" style={{ marginTop: '20px', padding: '40px 20px' }}>
                <p>No verified sites yet.</p>
              </div>
            ) : (
              <ul className="verified-sites-list">
                {verifiedSites.map((site, idx) => (
                  <li key={idx} className="verified-site-item">
                    <div>
                      <strong>{site.domain}</strong>
                      <div className="verified-date">
                        Verified on {new Date(site.verified_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div className="verified-badge">✓ Verified</div>
                      <button 
                        className="btn-icon" 
                        title="Delete verification"
                        onClick={() => deleteVerification(site.domain)}
                        style={{ border: 'none', background: 'rgba(255,77,109,0.1)', color: '#ff4d6d' }}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="3 6 5 6 21 6"></polyline>
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                      </button>
                    </div>
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
            <div className="hero-eyebrow">Verification</div>
            <h2 className="hero-title verify-title">Verify Site Ownership</h2>
            <p className="hero-sub">
              Enter your domain and create a special HTML file or meta tag to prove you control this site.
            </p>
          </div>
          <button className="btn-outline" style={{ borderRadius: 'var(--r)' }} onClick={() => {
              setViewMode("list");
              setUrl("");
              setRecord(null);
              setMessage("");
          }}>
            Back
          </button>
        </div>

        <div className={`url-wrapper${message && message.toLowerCase().includes('error') ? ' has-error' : ''}`}>
          <input
            className="url-input"
            type="text"
            placeholder="https://example.com"
            value={url}
            onChange={e => setUrl(e.target.value)}
          />
          <button className="scan-btn" onClick={startVerification} disabled={loading || !url}>
            {loading ? 'Loading...' : 'Start'}
          </button>
        </div>
        <p className="verify-note">
            Enter the URL of the website you want to analyze and click <strong>Start</strong>. The generated tag will appear below.
        </p>

        {record && (
          <div className="verify-result">
            <div className="verify-help">
              <p>The verification tag is generated below.</p>
              <p>You can use either of the following two options:</p>
              <ul>
                <li>Create a `scanner-verify.html` file at the root of your site</li>
                <li>Add the meta-tag into the <code>&lt;head&gt;</code> of your homepage</li>
              </ul>
            </div>
            <div className="verify-field">
              <div className="verify-label">File URL</div>
              <div className="verify-value">{record.file_url}</div>
            </div>
            <div className="verify-field">
              <div className="verify-label">File Content</div>
              <div className="verify-value">{record.file_contents}</div>
            </div>
            <div className="verify-field">
              <div className="verify-label">Meta Tag</div>
              <div className="verify-value">{record.meta_tag}</div>
            </div>
            <div className="verify-actions">
              <button className="copy-btn" style={{ borderRadius: 'var(--r)' }} onClick={() => navigator.clipboard?.writeText(record.file_url)}>
                Copy URL
              </button>
              <button className="copy-btn" style={{ borderRadius: 'var(--r)' }} onClick={() => navigator.clipboard?.writeText(record.file_contents)}>
                Copy Content
              </button>
              <button className="copy-btn" style={{ borderRadius: 'var(--r)' }} onClick={() => navigator.clipboard?.writeText(record.meta_tag)}>
                Copy Meta Tag
              </button>
              <button className="scan-btn" style={{ borderRadius: 'var(--r)' }} onClick={checkVerification} disabled={loading}>
                Check Now
              </button>
            </div>
            <p className="verify-note">
              Add either the `scanner-verify.html` file to the root of your site, or the meta tag above into the <code>&lt;head&gt;</code> of your homepage.
            </p>
          </div>
        )}

        {message && <div className="verify-message">{message}</div>}
      </section>
    </main>
  );
}

export default VerifyPage;
