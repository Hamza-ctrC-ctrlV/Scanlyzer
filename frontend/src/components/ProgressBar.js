import React, { useEffect, useState, useRef } from "react";
import { SCAN_STEPS, API_BASE_URL } from "../config/constants";

const STEP_MAP = {
  "waiting": 0,
  "crawling": 1,
  "active_scan": 2,
  "classification": 3,
  "ai_patches": 3,
  "done": 4,
};

/**
 * Real-time progress bar using SSE from backend
 */
export function ProgressBar({ progress, stepIdx, targetUrl, scanning }) {
  const [liveProgress, setLiveProgress] = useState({ pct: 0, msg: "Initialisation...", step: "waiting", elapsed: 0 });
  const [liveStepIdx, setLiveStepIdx] = useState(0);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    if (!scanning || !targetUrl) return;

    // Connect to SSE endpoint
    const url = `${API_BASE_URL}/api/scan-progress?url=${encodeURIComponent(targetUrl)}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLiveProgress(data);
        setLiveStepIdx(STEP_MAP[data.step] ?? 0);
      } catch (e) {
        // ignore parse errors
      }
    };

    es.onerror = () => {
      es.close();
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [scanning, targetUrl]);

  // Use live data if available, otherwise fall back to props
  const displayPct = liveProgress.pct > 0 ? liveProgress.pct : progress;
  const displayStep = liveProgress.pct > 0 ? liveStepIdx : stepIdx;
  const displayMsg = liveProgress.pct > 0 ? liveProgress.msg : "Analyse en cours...";
  const elapsed = liveProgress.elapsed || 0;

  return (
    <div className="prog-wrap fade-in">
      <div className="prog-steps">
        {SCAN_STEPS.map((s, i) => (
          <div key={s} className={`p-step ${i < displayStep ? "done" : i === displayStep ? "active" : ""}`}>
            <div className="ps-dot" /><span>{s}</span>
          </div>
        ))}
      </div>
      <div className="prog-track">
        <div className="prog-fill" style={{ width: `${displayPct}%`, transition: "width 0.6s cubic-bezier(0.16,1,0.3,1)" }}>
          <div className="prog-shine" />
        </div>
      </div>
      <div className="prog-pct">
        <span>{displayPct}% — {displayMsg}</span>
        {elapsed > 0 && <span className="prog-elapsed">{elapsed}s</span>}
      </div>
    </div>
  );
}
