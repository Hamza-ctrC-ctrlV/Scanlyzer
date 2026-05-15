import React, { useMemo } from "react";
import { SEV } from "../config/constants";
import { Donut } from "./Charts";

/**
 * Report charts — horizontal bar and donut visualization
 */
function ReportCharts({ report }) {
  const { total, maxStat } = useMemo(() => ({
    total: Object.values(report.stats).reduce((a,b)=>a+b,0),
    maxStat: Math.max(...Object.values(report.stats),1)
  }), [report.stats]);

  return (
    <div className="charts-row">
      <div className="chart-panel">
        <div className="panel-title">Répartition par sévérité</div>
        <div className="hbar-list">
          {Object.entries(report.stats).map(([k,v])=>(
            <div className="hbar-item" key={k}>
              <div className="hbar-lbl">{k}</div>
              <div className="hbar-track">
                <div className="hbar-fill" style={{
                  width:`${(v/maxStat)*100}%`,
                  background:SEV[k]?.color||"#4cc9f0",
                  boxShadow:`0 0 8px ${SEV[k]?.glow}`
                }}/>
              </div>
              <div className="hbar-val" style={{color:SEV[k]?.color}}>{v}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="donut-panel">
        <div className="panel-title">Distribution</div>
        <div className="donut-wrap">
          <Donut stats={report.stats}/>
          <div className="donut-inner">
            <div className="donut-total">{total}</div>
            <div className="donut-sub">vulnérabilités</div>
          </div>
        </div>
        <div className="donut-legend">
          {Object.entries(report.stats).map(([k,v])=>(
            <div className="dl-item" key={k}>
              <div className="dl-left">
                <div className="dl-dot" style={{background:SEV[k]?.color}}/>
                <span className="dl-name">{k}</span>
              </div>
              <span className="dl-cnt" style={{color:SEV[k]?.color}}>{v}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default React.memo(ReportCharts);
