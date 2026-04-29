import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";

const SUGGESTIONS = [
  "How many passengers survived?",
  "Show survival by gender",
  "Top 5 passengers by age",
  "Average fare by class",
];

const ROLE_LABELS = {
  user:      "You",
  assistant: "QueryMind",
  system:    "System",
};

function SqlBlock({ sql }) {
  const [open, setOpen] = useState(false);
  const copyRef = useRef();
  const copy = () => {
    navigator.clipboard.writeText(sql);
    copyRef.current.textContent = "Copied!";
    setTimeout(() => { if (copyRef.current) copyRef.current.textContent = "Copy"; }, 1500);
  };
  return (
    <>
      <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
        <button className="sql-toggle-btn" onClick={() => setOpen((o) => !o)}>
          {open ? "▲ Hide SQL" : "▼ Show SQL"}
        </button>
        {open && (
          <button className="sql-toggle-btn" onClick={copy}>
            <span ref={copyRef}>Copy</span>
          </button>
        )}
      </div>
      {open && <pre className="sql-block">{sql}</pre>}
    </>
  );
}

const mdComponents = {
  p: ({ children }) => <span>{children}</span>,
  strong: ({ children }) => <strong style={{ color: "#e2e8f0" }}>{children}</strong>,
  em: ({ children }) => <em style={{ color: "#94a3b8" }}>{children}</em>,
  code: ({ children }) => (
    <code style={{ background: "#020617", padding: "1px 5px", borderRadius: 3, fontFamily: "JetBrains Mono, monospace", fontSize: 12 }}>
      {children}
    </code>
  ),
  ul: ({ children }) => <ul style={{ paddingLeft: 18, margin: "6px 0" }}>{children}</ul>,
  ol: ({ children }) => <ol style={{ paddingLeft: 18, margin: "6px 0" }}>{children}</ol>,
  li: ({ children }) => <li style={{ marginBottom: 2 }}>{children}</li>,
};

function Message({ msg }) {
  const isUser = msg.role === "user";
  const isSystem = msg.role === "system";
  const roleClass = isUser ? "user" : isSystem ? "system" : "assistant";

  return (
    <div className={`msg ${roleClass}`}>
      <div className={`msg-role ${roleClass}`}>
        {msg.intent && (
          <span className="intent-badge">{msg.intent.replace("_", " ").toUpperCase()}</span>
        )}
        {ROLE_LABELS[roleClass] ?? msg.role}
      </div>
      <div className="msg-bubble">
        {isUser || isSystem ? (
          msg.text
        ) : (
          <ReactMarkdown components={mdComponents}>{msg.text}</ReactMarkdown>
        )}
      </div>
      {msg.sql && <SqlBlock sql={msg.sql} />}
    </div>
  );
}

// Source picker dropdown
function SourcePicker({ sources, sourceId, onChange }) {
  if (!sources.length) {
    return (
      <div className="source-bar">
        <div className="source-label">Data Source</div>
        <div style={{ fontSize: 12, color: "var(--text-muted)", paddingTop: 4 }}>
          No sources connected — add one via API first.
        </div>
      </div>
    );
  }

  return (
    <div className="source-bar">
      <div className="source-label">Data Source</div>
      <select
        className="source-select"
        value={sourceId}
        onChange={(e) => onChange(e.target.value)}
      >
        {sources.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name} ({s.source_type})
          </option>
        ))}
      </select>
    </div>
  );
}

export default function ChatPanel({ messages, loading, onAsk, sources, sourceId, onSourceChange }) {
  const [question, setQuestion] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const submit = () => {
    if (!question.trim() || !sourceId) return;
    onAsk({ question: question.trim() });
    setQuestion("");
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
  };

  return (
    <section className="chat-panel">
      <div className="panel-header">
        <div className="panel-title">Conversation</div>
      </div>

      <SourcePicker sources={sources} sourceId={sourceId} onChange={onSourceChange} />

      <div className="messages-area">
        {messages.length === 0 && (
          <div className="empty-chat-hint">
            Select a data source and ask a question to get started.
          </div>
        )}
        {messages.map((m, i) => <Message key={i} msg={m} />)}

        {loading && (
          <div className="typing-indicator">
            <div className="typing-dots"><span /><span /><span /></div>
            <span className="typing-text">Agents are working…</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="input-area">
        <div className="input-row">
          <textarea
            className="question-input"
            placeholder="Ask a question… (Enter to send)"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKey}
            rows={1}
          />
          <button
            className="ask-btn"
            onClick={submit}
            disabled={loading || !question.trim() || !sourceId}
          >
            {loading ? "Running…" : "Ask"}
          </button>
        </div>
        <div className="suggestions">
          {SUGGESTIONS.map((s) => (
            <button key={s} className="suggestion-chip" onClick={() => setQuestion(s)}>
              {s}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
