import React from "react";
import { SEV } from "../config/constants";
import { ScoreRing } from "./Charts";

/**
 * Report metrics — score and severity tiles
 */
function ReportMetrics({ report, scoreColor, scoreVerdict }) {
  return (
    <div className="metrics-row">
      <div className="score-panel">
        <div className="sp-label">SECURITY SCORE</div>
        <div className="score-ring-wrap">
          <ScoreRing score={report.score} color={scoreColor}/>
          <div className="score-center">
            <div className="sp-num" style={{color:scoreColor}}>{report.score}</div>
            <div className="sp-verdict" style={{color:scoreColor}}>{scoreVerdict}</div>
          </div>
        </div>
        <div className="sp-bar-track">
          <div className="sp-bar-fill" style={{width:`${report.score}%`,background:scoreColor}}/>
        </div>
      </div>

      <div className="sev-tiles">
        {Object.entries(report.stats).map(([k,v])=>(
          <div className="sev-tile" key={k} style={{"--tc":SEV[k]?.color,"--tg":SEV[k]?.glow}}>
            <div className="st-glow"/>
            <div className="sev-count">{v}</div>
            <div className="sev-name">{k}</div>
            <div className="st-bar" style={{background:SEV[k]?.color}}/>
          </div>
        ))}
      </div>
    </div>
  );
}

export default React.memo(ReportMetrics);
