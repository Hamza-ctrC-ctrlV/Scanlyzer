import React from "react";
import { SCAN_STEPS } from "../config/constants";

/**
 * Progress bar showing scan stages and completion percentage
 */
export function ProgressBar({ progress, stepIdx }) {
  return (
    <div className="prog-wrap fade-in">
      <div className="prog-steps">
        {SCAN_STEPS.map((s,i)=>(
          <div key={s} className={`p-step ${i<stepIdx?"done":i===stepIdx?"active":""}`}>
            <div className="ps-dot"/><span>{s}</span>
          </div>
        ))}
      </div>
      <div className="prog-track">
        <div className="prog-fill" style={{width:`${progress}%`}}>
          <div className="prog-shine"/>
        </div>
      </div>
      <div className="prog-pct">{progress}% — Analyse en cours...</div>
    </div>
  );
}
