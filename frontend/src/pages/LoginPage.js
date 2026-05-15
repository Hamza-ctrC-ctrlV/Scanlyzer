import React, { useState } from "react";

export function LoginPage({ onLogin, onSwitchToSignup, loading = false, error = "" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    onLogin(email, password);
  };

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="auth-badge">Supabase Auth</div>
        <h1 className="auth-title">Connexion</h1>
        <p className="auth-subtitle">Accédez au scanner avec votre compte sécurisé.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="vous@exemple.com"
              autoComplete="email"
            />
          </label>

          <label className="auth-field">
            <span>Mot de passe</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </label>

          {error && <div className="auth-error">{error}</div>}

          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? "Connexion..." : "Se connecter"}
          </button>
        </form>

        <button className="auth-link" type="button" onClick={onSwitchToSignup}>
          Créer un compte
        </button>
      </section>
    </main>
  );
}
