import React, { useState, useEffect } from "react";
import "./App.css";
import { Header } from "../components/Header";
import { DashboardPage } from "../pages/DashboardPage";
import { HistoryPage } from "../pages/HistoryPage";
import { LoginPage } from "../pages/LoginPage";
import { SignupPage } from "../pages/SignupPage";
import { HEALTH_URL } from "../config/constants";

/**
 * Main App Component
 * Handles page routing and backend health check
 */
export default function App() {
  const [page, setPage] = useState("login");
  const [selectedReport, setSelectedReport] = useState(null);
  const [authUser, setAuthUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState("");
  const [theme, setTheme] = useState("dark");

  useEffect(() => {
    const savedTheme = localStorage.getItem("vulnscan_theme") || "dark";
    setTheme(savedTheme);
  }, []);

  useEffect(() => {
    if (theme === "light") {
      document.body.setAttribute("data-theme", "light");
    } else {
      document.body.removeAttribute("data-theme");
    }
  }, [theme]);

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    localStorage.setItem("vulnscan_theme", newTheme);
  };

  useEffect(() => {
    const checkBackend = async () => {
      try {
        await fetch(HEALTH_URL);
      } catch {
        // Ignore error
      }
    };

    checkBackend();
  }, []);

  useEffect(() => {
    let cancelled = false;

    const verifySession = async () => {
      const storedToken = localStorage.getItem("vulnscan_token");
      const storedEmail = localStorage.getItem("vulnscan_email");

      if (!storedToken) {
        if (!cancelled) {
          setAuthLoading(false);
          setPage("login");
        }
        return;
      }

      try {
        const response = await fetch("/auth/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token: storedToken }),
        });
        const data = await response.json();

        if (!cancelled && response.ok && data.success) {
          localStorage.setItem("vulnscan_user_id", data.user_id || "");
          setAuthUser({
            user_id: data.user_id,
            email: data.email || storedEmail || "",
            token: storedToken,
          });
          setPage("dashboard");
        } else if (!cancelled) {
          localStorage.removeItem("vulnscan_token");
          localStorage.removeItem("vulnscan_email");
          localStorage.removeItem("vulnscan_user_id");
          setPage("login");
        }
      } catch {
        if (!cancelled) {
          setPage("login");
        }
      } finally {
        if (!cancelled) {
          setAuthLoading(false);
        }
      }
    };

    verifySession();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleAuthSuccess = (result) => {
    localStorage.setItem("vulnscan_token", result.token);
    localStorage.setItem("vulnscan_email", result.email || "");
    localStorage.setItem("vulnscan_user_id", result.user_id || "");
    setAuthUser(result);
    setAuthError("");
    setPage("dashboard");
  };

  const handleLogin = async (email, password) => {
    setAuthBusy(true);
    setAuthError("");

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Impossible de se connecter.");
      }

      handleAuthSuccess({
        user_id: data.user_id,
        email: data.email,
        token: data.session?.access_token,
      });
    } catch (error) {
      setAuthError(error.message || "Impossible de se connecter.");
    } finally {
      setAuthBusy(false);
    }
  };

  const handleSignup = async (email, password, confirmPassword) => {
    if (password !== confirmPassword) {
      setAuthError("Les mots de passe ne correspondent pas.");
      return;
    }

    setAuthBusy(true);
    setAuthError("");

    try {
      const response = await fetch("/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Impossible de créer le compte.");
      }

      handleAuthSuccess({
        user_id: data.user_id,
        email: data.email,
        token: data.session?.access_token || data.user_id,
      });
    } catch (error) {
      setAuthError(error.message || "Impossible de créer le compte.");
    } finally {
      setAuthBusy(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("vulnscan_token");
    localStorage.removeItem("vulnscan_email");
    localStorage.removeItem("vulnscan_user_id");
    setAuthUser(null);
    setSelectedReport(null);
    setPage("login");
  };

  const handleLoadReport = (reportData) => {
    // Callback from DashboardPage when report is loaded
    // Can be used for future analytics or state management
    setSelectedReport(reportData);
  };

  if (authLoading) {
    return (
      <div className="app">
        <div className="aurora" />
        <div className="mesh-grid" />
        <main className="auth-shell">
          <section className="auth-card">
            <div className="auth-badge">Supabase Auth</div>
            <h1 className="auth-title">Chargement...</h1>
            <p className="auth-subtitle">Vérification de votre session sécurisée.</p>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="aurora" />
      <div className="mesh-grid" />

      {page === "login" && (
        <LoginPage
          onLogin={handleLogin}
          onSwitchToSignup={() => setPage("signup")}
          loading={authBusy}
          error={authError}
        />
      )}

      {page === "signup" && (
        <SignupPage
          onSignup={handleSignup}
          onSwitchToLogin={() => setPage("login")}
          loading={authBusy}
          error={authError}
        />
      )}

      {(page === "dashboard" || page === "history") && authUser && (
        <>
          {page === "dashboard" && <div className="scanline" />}
          <Header page={page} setPage={setPage} onLogout={handleLogout} userEmail={authUser.email} theme={theme} toggleTheme={toggleTheme} />

          {page === "dashboard" && (
            <DashboardPage authUser={authUser} onReportLoad={handleLoadReport} initialReport={selectedReport} />
          )}

          {page === "history" && (
            <HistoryPage
              authUser={authUser}
              onBack={() => setPage("dashboard")}
            />
          )}
        </>
      )}
    </div>
  );
}