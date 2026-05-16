import React from "react";

/**
 * Skeleton shimmer block for loading states
 */
export function Skeleton({ width = "100%", height = "16px", borderRadius = "8px", style = {} }) {
  return (
    <div
      className="skeleton"
      style={{
        width,
        height,
        borderRadius,
        ...style,
      }}
    />
  );
}

/**
 * Skeleton for the report metrics section
 */
export function MetricsSkeleton() {
  return (
    <div className="skeleton-metrics fade-in">
      <div className="skeleton-score-panel">
        <Skeleton width="120px" height="80px" borderRadius="16px" />
        <div style={{ flex: 1 }}>
          <Skeleton width="60%" height="14px" style={{ marginBottom: "10px" }} />
          <Skeleton width="100%" height="8px" borderRadius="4px" style={{ marginBottom: "8px" }} />
          <Skeleton width="40%" height="12px" />
        </div>
      </div>
      <div className="skeleton-tiles">
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} className="skeleton-tile">
            <Skeleton width="36px" height="36px" borderRadius="50%" style={{ margin: "0 auto 8px" }} />
            <Skeleton width="50%" height="10px" style={{ margin: "0 auto" }} />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Skeleton for vulnerability cards
 */
export function VulnCardSkeleton({ count = 3 }) {
  return (
    <div className="skeleton-vulns">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton-vuln-card" style={{ animationDelay: `${i * 0.1}s` }}>
          <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
            <Skeleton width="10px" height="10px" borderRadius="50%" />
            <div style={{ flex: 1 }}>
              <Skeleton width="45%" height="14px" style={{ marginBottom: "8px" }} />
              <Skeleton width="70%" height="10px" />
            </div>
            <Skeleton width="60px" height="22px" borderRadius="6px" />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Skeleton for history cards
 */
export function HistoryCardSkeleton({ count = 3 }) {
  return (
    <div className="skeleton-history">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton-hist-card" style={{ animationDelay: `${i * 0.08}s` }}>
          <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
            <Skeleton width="70px" height="48px" borderRadius="10px" />
            <div style={{ flex: 1 }}>
              <Skeleton width="55%" height="14px" style={{ marginBottom: "8px" }} />
              <Skeleton width="80%" height="10px" style={{ marginBottom: "6px" }} />
              <div style={{ display: "flex", gap: "8px" }}>
                <Skeleton width="50px" height="18px" borderRadius="6px" />
                <Skeleton width="50px" height="18px" borderRadius="6px" />
              </div>
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <Skeleton width="32px" height="32px" borderRadius="8px" />
              <Skeleton width="32px" height="32px" borderRadius="8px" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
