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
        <div className="auth-badge">Scanlyzer Portal</div>
        <h1 className="auth-title">Login</h1>
        <p className="auth-subtitle">Access the scanner with your secure account.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
            />
          </label>

          <label className="auth-field">
            <span>Password</span>
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
            {loading ? "Logging in..." : "Log in"}
          </button>
        </form>

        <button className="auth-link" type="button" onClick={onSwitchToSignup}>
          Create an account
        </button>
      </section>
    </main>
  );
}
