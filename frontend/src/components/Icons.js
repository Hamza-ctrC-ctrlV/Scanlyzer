/**
 * Reusable SVG Icons
 */

export const IconShield = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
    <path d="M12 2L4 6v6c0 5.5 3.8 10.7 8 12 4.2-1.3 8-6.5 8-12V6l-8-4z" fill="url(#sg)"/>
    <path d="M9 12l2 2 4-4" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    <defs><linearGradient id="sg" x1="4" y1="2" x2="20" y2="22" gradientUnits="userSpaceOnUse">
      <stop stopColor="#3b82f6"/><stop offset="1" stopColor="#0ea5e9"/>
    </linearGradient></defs>
  </svg>
);

export const IconBug = ({ size=16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M9 3h6M9 3a3 3 0 0 0-3 3v1M9 3a3 3 0 0 1 3 3m3-3a3 3 0 0 1 3 3v1M12 6a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V9a3 3 0 0 0-3-3z" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/>
    <path d="M6 10H3M21 10h-3M6 14H3M21 14h-3" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/>
  </svg>
);

export const IconCode = ({ size=16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <polyline points="16,18 22,12 16,6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <polyline points="8,6 2,12 8,18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconHistory = ({ size=16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8"/>
    <polyline points="12,7 12,12 15,15" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
  </svg>
);

export const IconChevron = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
    <polyline points="6,9 12,15 18,9" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconTrash = ({ size=14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <polyline points="3,6 5,6 21,6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    <path d="M19 6l-1 14H6L5 6M10 11v6M14 11v6M9 6V4h6v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconCopy = ({ size=14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
  </svg>
);
