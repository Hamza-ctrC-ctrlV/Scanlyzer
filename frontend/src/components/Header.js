import React from "react";

/**
 * Header with logo, navigation, and backend status
 */
export function Header({ page, setPage, onLogout, userEmail }) {
  return (
    <header className="header">
      <div className="logo">
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
        {userEmail && <div className="user-chip">{userEmail}</div>}
        <button className="nav-link" onClick={onLogout}>Déconnexion</button>
      </div>
    </header>
  );
}
