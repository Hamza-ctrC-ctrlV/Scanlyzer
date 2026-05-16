import React from "react";

/**
 * Header with clickable logo, navigation, and backend status
 */
export function Header({ page, setPage, onLogout, userEmail, theme, toggleTheme }) {
  return (
    <header className="header">
      <div className="logo" onClick={() => setPage("dashboard")} style={{cursor: "pointer"}} title="Retour au dashboard">
        <div className="logo-text">SECURE<span>SCAN</span></div>
      </div>
      <nav className="nav">
        <button className={`nav-link ${page==="dashboard"?"active":""}`} onClick={()=>setPage("dashboard")}>
          Dashboard
        </button>
        <button className={`nav-link ${page==="history"?"active":""}`} onClick={()=>setPage("history")}>
          Historique
        </button>
      </nav>
      <div style={{display:"flex", alignItems:"center", gap:"12px"}}>
        <button className="theme-toggle" onClick={toggleTheme}>
          {theme === "light" ? "🌙 Sombre" : "☀️ Clair"}
        </button>
        {userEmail && <div className="user-chip">{userEmail}</div>}
        <button className="nav-link" onClick={onLogout}>Déconnexion</button>
      </div>
    </header>
  );
}
