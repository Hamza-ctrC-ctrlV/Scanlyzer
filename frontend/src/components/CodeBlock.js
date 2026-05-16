import React from "react";

import { IconCopy } from "./Icons";

/**
 * Copy button for code blocks
 */
function CopyBtn({ text }) {
  const [copied, setCopied] = React.useState(false);
  return (
    <button className={`copy-btn ${copied?"copied":""}`} onClick={() => {
      navigator.clipboard.writeText(text||"");
      setCopied(true); setTimeout(()=>setCopied(false), 2000);
    }}>
      <IconCopy/> {copied ? "Copié !" : "Copier"}
    </button>
  );
}

/**
 * Reusable Code Block component
 * Renders code in a styled window with title bar and optional copy button
 *
 * @param {string} code - The code content to display
 * @param {string} filename - Optional filename to show in title bar
 * @param {string} type - "vulnerable" or "fixed" determines styling
 * @param {boolean} showCopyBtn - Whether to show copy button (default: false)
 */
function CodeBlock({ code, filename, type = "fixed", showCopyBtn = true }) {
  const codeClassName = type === "vulnerable" ? "fix-code danger-code" : "fix-code success-code";

  return (
    <div className="code-window">
      <div className="code-titlebar">
        <span className="dot r" />
        <span className="dot y" />
        <span className="dot g" />
        <span className="code-filename">{filename || (type === "vulnerable" ? "code_vulnerable" : "code_corrige")}</span>
      </div>
      <pre className={codeClassName}>{code}</pre>
      {showCopyBtn && code && <CopyBtn text={code} />}
    </div>
  );
}

const MemoizedCodeBlock = React.memo(CodeBlock);
export { MemoizedCodeBlock as CodeBlock };