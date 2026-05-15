import React from "react";
import { SEV } from "../config/constants";

/**
 * Donut chart showing vulnerability distribution by severity
 */
export function Donut({ stats }) {
  const total = Object.values(stats).reduce((a,b)=>a+b,0);
  const r=54, cx=70, cy=70, circ=2*Math.PI*r;
  let offset=0;
  const slices = Object.entries(stats).filter(([,v])=>v>0).map(([k,v])=>{
    const dash=(v/total)*circ-3;
    const sl={key:k, dash:Math.max(0,dash), offset, color:SEV[k]?.color||"#4cc9f0"};
    offset+=(v/total)*circ;
    return sl;
  });
  
  return (
    <svg width="140" height="140" viewBox="0 0 140 140">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="14"/>
      {slices.map(s=>(
        <circle key={s.key} cx={cx} cy={cy} r={r} fill="none"
          stroke={s.color} strokeWidth="14"
          strokeDasharray={`${s.dash} ${circ-s.dash}`}
          strokeDashoffset={circ/4-s.offset}
          style={{transition:"stroke-dasharray 1.2s ease", filter:`drop-shadow(0 0 6px ${s.color}80)`}}
        />
      ))}
    </svg>
  );
}

/**
 * Score ring showing security score as circular progress
 */
export function ScoreRing({ score, color }) {
  const r=52, circ=2*Math.PI*r;
  return (
    <svg width="140" height="140" viewBox="0 0 140 140">
      <circle cx="70" cy="70" r={r} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="10"/>
      <circle cx="70" cy="70" r={r} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
        strokeDasharray={`${(score/100)*circ} ${circ}`} strokeDashoffset={circ/4}
        style={{transition:"stroke-dasharray 1.4s ease", filter:`drop-shadow(0 0 10px ${color})`}}
      />
    </svg>
  );
}
