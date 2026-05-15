import React from "react";

/**
 * Reusable Severity Badge component
 * Shows severity level with consistent styling and glowing effect
 */
export function SeverityBadge({ severity, sev, className = "" }) {
  return (
    <span 
      className={`sev-badge ${className}`} 
      style={{
        color: sev?.color,
        borderColor: sev?.color + "40",
        background: sev?.bg,
      }}
    >
      <span className="sev-pip" style={{ background: sev?.color }} />
      {sev?.label}
    </span>
  );
}
