import React from "react";
import { SCAN_STEPS } from "../config/constants";

/**
 * Real-time progress bar — pure presentational component.
 *
 * All progress data is passed as props from DashboardPage,
 * which owns the single SSE connection.
 *
 * Props:
 *   progress  — percentage (0-100)
 *   stepIdx   — current step index in SCAN_STEPS
 *   statusMsg — human-readable status message from backend
 *   elapsed   — seconds elapsed since scan start
 */
export function ProgressBar({ progress, stepIdx, statusMsg, elapsed }) {
  return (
    <div className="prog-wrap fade-in">
      <div className="prog-steps">
        {SCAN_STEPS.map((s, i) => (
          <div key={s} className={`p-step ${i < stepIdx ? "done" : i === stepIdx ? "active" : ""}`}>
            <div className="ps-dot" /><span>{s}</span>
          </div>
        ))}
      </div>
      <div className="prog-track">
        <div className="prog-fill" style={{ width: `${progress}%`, transition: "width 0.6s cubic-bezier(0.16,1,0.3,1)" }}>
          <div className="prog-shine" />
        </div>
      </div>
      <div className="prog-pct">
        <span>{progress}% — {statusMsg || "Analyse en cours..."}</span>
        {elapsed > 0 && <span className="prog-elapsed">{elapsed}s</span>}
      </div>
    </div>
  );
}
