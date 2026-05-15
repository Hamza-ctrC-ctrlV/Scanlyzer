import React, { useState } from "react";

export function SignupPage({ onSignup, onSwitchToLogin, loading = false, error = "" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    onSignup(email, password, confirmPassword);
  };

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="auth-badge">Supabase Auth</div>
        <h1 className="auth-title">Inscription</h1>
        <p className="auth-subtitle">Créez un compte pour sauvegarder vos scans et historiques.</p>

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
              autoComplete="new-password"
            />
          </label>

          <label className="auth-field">
            <span>Confirmer le mot de passe</span>
            <input
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="••••••••"
              autoComplete="new-password"
            />
          </label>

          {error && <div className="auth-error">{error}</div>}

          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? "Création..." : "Créer le compte"}
          </button>
        </form>

        <button className="auth-link" type="button" onClick={onSwitchToLogin}>
          J’ai déjà un compte
        </button>
      </section>
    </main>
  );
}
