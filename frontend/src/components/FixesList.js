import React from "react";
import { SEV } from "../config/constants";
import { SeverityBadge } from "./SeverityBadge";
import { CodeBlock } from "./CodeBlock";

/**
 * List of AI-generated fixes
 */
function FixesList({ patches }) {
  return (
    <div className="fixes-list">
      {patches.map((p,i)=>{
        const sev=SEV[p.severity?.toUpperCase()]||SEV.INFO;
        return (
          <div key={p.vuln_id||i} className="fix-block fade-in" style={{animationDelay:`${i*0.06}s`}}>
            <div className="fix-block-head" style={{borderLeft:`3px solid ${sev.color}`}}>
              <div>
                <div className="fb-title">{p.type}</div>
                <div className="fb-ep">{p.fichier}{p.champ?` — ${p.champ}`:""}</div>
              </div>
              <SeverityBadge severity={p.severity} sev={sev} />
            </div>
            {p.code_corrige
              ? <CodeBlock code={p.code_corrige} filename={p.fichier} type="fixed" />
              : <div style={{padding:"16px 20px",color:"var(--muted)",fontSize:"0.82rem"}}>
                  {p.solution||"Voir la description de la vulnérabilité."}
                </div>
            }
          </div>
        );
      })}
    </div>
  );
}

export default React.memo(FixesList);
