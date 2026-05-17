import React, { useState, useEffect, useRef, useCallback } from "react";
import { CHAT_URL } from "../config/constants";

/**
 * Renders a single chat message bubble.
 * role: "user" | "assistant" | "typing"
 */
const ChatCodeBlock = ({ lang, code }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="chat-code-block">
      <div className="chat-code-header">
        <div className="chat-code-lang">{lang || "code"}</div>
        <button className="chat-code-copy" onClick={handleCopy} title="Copy code">
          {copied ? "✓ Copied" : "📋 Copy"}
        </button>
      </div>
      <pre><code>{code}</code></pre>
    </div>
  );
};

function ChatBubble({ role, content }) {
  const isUser = role === "user";

  if (role === "typing") {
    return (
      <div className="chat-bubble chat-bubble--ai">
        <div className="chat-typing">
          <span /><span /><span />
        </div>
      </div>
    );
  }

  // Minimal markdown: **bold**, `code`, ```code blocks```
  const renderContent = (text) => {
    const lines = text.split("\n");
    const elements = [];
    let inCodeBlock = false;
    let codeLines = [];
    let lang = "";

    lines.forEach((line, i) => {
      if (line.startsWith("```")) {
        if (!inCodeBlock) {
          inCodeBlock = true;
          lang = line.slice(3).trim();
          codeLines = [];
        } else {
          inCodeBlock = false;
          elements.push(
            <ChatCodeBlock key={`cb-${i}`} lang={lang} code={codeLines.join("\n")} />
          );
          codeLines = [];
          lang = "";
        }
        return;
      }
      if (inCodeBlock) { codeLines.push(line); return; }

      // Inline: **bold** and `code`
      const parts = line
        .split(/(\*\*[^*]+\*\*|`[^`]+`)/g)
        .map((part, j) => {
          if (part.startsWith("**") && part.endsWith("**"))
            return <strong key={j}>{part.slice(2, -2)}</strong>;
          if (part.startsWith("`") && part.endsWith("`"))
            return <code key={j} className="chat-inline-code">{part.slice(1, -1)}</code>;
          return part;
        });

      elements.push(<p key={`p-${i}`} className="chat-para">{parts}</p>);
    });

    return elements;
  };

  return (
    <div className={`chat-bubble ${isUser ? "chat-bubble--user" : "chat-bubble--ai"}`}>
      {!isUser && (
        <div className="chat-ai-label">
          <span className="chat-ai-icon">🛡️</span>
          <span>Scanlyzer AI</span>
        </div>
      )}
      <div className="chat-bubble-body">{renderContent(content)}</div>
    </div>
  );
}

/**
 * AIChat — interactive chat panel embedded inside a vulnerability card.
 *
 * Props:
 *   context  — { type, severity, explication, solution, code_vulnerable, url }
 *   token    — JWT bearer token for authenticated requests
 *   onClose  — callback to close the panel
 */
export function AIChat({ context, token, onClose }) {
  const [messages, setMessages] = useState([]);  // [{role, content}]
  const [input, setInput]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const scrollRef               = useRef(null);
  const inputRef                = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  // Focus input on open
  useEffect(() => {
    inputRef.current?.focus();
  }, []);



  const sendMessage = useCallback(
    async (userMsg, history) => {
      const updatedHistory = [...history, userMsg];
      setMessages((prev) => [...prev, userMsg]);
      setLoading(true);
      setError(null);

      try {
        const res = await fetch(CHAT_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            messages: updatedHistory,
            context,
          }),
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
          throw new Error(data.message || data.error || "AI error");
        }

        const aiMsg = { role: "assistant", content: data.reply };
        setMessages((prev) => [...prev, aiMsg]);
      } catch (err) {
        setError(err.message || "Network error — please try again.");
      } finally {
        setLoading(false);
      }
    },
    [context, token]
  );

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    setInput("");
    const userMsg = { role: "user", content: trimmed };
    sendMessage(userMsg, messages);
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="ai-chat-panel">
      {/* Header */}
      <div className="ai-chat-header">
        <div className="ai-chat-title">
          <span className="ai-chat-icon">💬</span>
          <span>Discuter avec l'IA</span>
          <span className="ai-chat-ctx-badge">{context.type}</span>
        </div>
        <button
          className="ai-chat-close"
          onClick={onClose}
          aria-label="Fermer le chat"
        >
          ✕
        </button>
      </div>

      {/* Messages */}
      <div className="ai-chat-messages" ref={scrollRef}>
        {messages.map((msg, i) => (
          <ChatBubble key={i} role={msg.role} content={msg.content} />
        ))}
        {loading && <ChatBubble role="typing" />}
        {error && (
          <div className="ai-chat-error">⚠️ {error}</div>
        )}
      </div>

      {/* Input */}
      <div className="ai-chat-input-row">
        <textarea
          ref={inputRef}
          className="ai-chat-input"
          rows={2}
          placeholder="Posez une question sur cette vulnérabilité…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          disabled={loading}
        />
        <button
          className={`ai-chat-send ${loading ? "ai-chat-send--loading" : ""}`}
          onClick={handleSend}
          disabled={loading || !input.trim()}
          aria-label="Envoyer"
        >
          {loading ? <span className="spinner" /> : "↑"}
        </button>
      </div>
    </div>
  );
}

export default React.memo(AIChat);
