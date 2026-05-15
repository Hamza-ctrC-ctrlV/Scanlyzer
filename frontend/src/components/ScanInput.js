import React from "react";

/**
 * URL input form with validation feedback
 */
export function ScanInput({ url, onUrlChange, onScan, urlError, apiError, scanning }) {
  return (
    <section className="hero">
      <div className="hero-eyebrow">Outil d'audit de sécurité web · Powered by AI</div>
      <h1 className="hero-title">
        ANALYSE DE<span className="hl"> VULNÉRABILITÉS</span><br/>AUTOMATISÉE
      </h1>
      <p className="hero-sub">
        Entrez l'URL de votre site cible. Le scanner détecte les vulnérabilités
        et l'IA génère les correctifs en temps réel.
      </p>

      {/* URL INPUT */}
      <div className={`url-wrapper ${urlError?"has-error":""}`}>
        <div className="url-prefix">TARGET URL</div>
        <input
          className="url-input"
          type="text"
          placeholder="https://example.com"
          value={url}
          onChange={e=>{ onUrlChange(e.target.value); }}
          onKeyDown={e=>e.key==="Enter" && onScan()}
          disabled={scanning}
        />
        <button className={`scan-btn ${scanning?"scanning":""}`} onClick={onScan} disabled={scanning}>
          {scanning ? <><span className="spinner"/>ANALYSE...</> : <>LANCER LE SCAN</>}
        </button>
      </div>

      {/* Error messages */}
      {urlError && <div className="error-msg">⚠️ {urlError}</div>}
      {apiError && !scanning && <div className="error-msg error-api">🔴 {apiError}</div>}
    </section>
  );
}
