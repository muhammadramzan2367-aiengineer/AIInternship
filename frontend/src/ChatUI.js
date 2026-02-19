// ChatUI.jsx
import React, { useState, useRef, useEffect } from "react";
import "./App.css";  // or wherever your styles live

export default function ChatUI({
  title = "Chat",
  placeholder = "Type your message...",
  disabled = false,
  onSend,                        // ← this must be used
  statusMessage = "",
  showSources = true,
}) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || sending || disabled) return;

    // Show user message immediately
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    setSending(true);

    // Temporary loading message
    const tempId = Date.now();
    setMessages((prev) => [
      ...prev,
      { id: tempId, role: "assistant", content: "Thinking...", loading: true },
    ]);

    try {
      // Call the prop function passed from DocumentChat
      const response = await onSend(trimmed);

      // Replace loading message
      setMessages((prev) =>
        prev.map((m) =>
          m.id === tempId
            ? {
                ...m,
                content: response.content || "No response received",
                sources: response.sources || [],
                loading: false,
              }
            : m
        )
      );
    } catch (err) {
      console.error("Send failed:", err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === tempId
            ? {
                ...m,
                content: `Error: ${err.message || "Request failed"}`,
                error: true,
                loading: false,
              }
            : m
        )
      );
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div className="chat-header">{title}</div>

      <div className="messages" style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
        {messages.length === 0 && (
          <div style={{ textAlign: "center", color: "#aaa", marginTop: "40px" }}>
            {disabled ? "Index documents first" : "Ask a question..."}
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id || `${msg.role}-${msg.content.slice(0,20)}`}
            className={`message ${msg.role}`}
            style={{
              display: "flex",
              marginBottom: "16px",
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
            }}
          >
            <div
              className="bubble"
              style={{
                maxWidth: "75%",
                padding: "10px 14px",
                borderRadius: "18px",
                background: msg.role === "user" ? "#667eea" : "#e2e8f0",
                color: msg.role === "user" ? "white" : "#1f2937",
                position: "relative",
              }}
            >
              {msg.loading ? (
                <span>Thinking...</span>
              ) : (
                <div>{msg.content}</div>
              )}

              {showSources && msg.role === "assistant" && msg.sources?.length > 0 && !msg.loading && (
                <div style={{ marginTop: "10px", fontSize: "0.82rem", opacity: 0.8 }}>
                  <strong>Sources:</strong>
                  <ul style={{ margin: "4px 0 0 16px", paddingLeft: 0 }}>
                    {msg.sources.map((src, i) => (
                      <li key={i}>{src}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      <div className="input-area" style={{ padding: "12px", borderTop: "1px solid #ddd" }}>
        {statusMessage && (
          <div style={{ color: "#10b981", fontSize: "0.9rem", textAlign: "center", marginBottom: "8px" }}>
            {statusMessage}
          </div>
        )}

        <div style={{ display: "flex", gap: "8px" }}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || sending}
            style={{
              flex: 1,
              minHeight: "48px",
              maxHeight: "120px",
              resize: "vertical",
              padding: "12px",
              borderRadius: "12px",
              border: "1px solid #ccc",
              fontFamily: "inherit",
            }}
          />
          <button
            onClick={handleSend}
            disabled={disabled || sending || !input.trim()}
            style={{
              padding: "0 24px",
              background: sending ? "#9ca3af" : "#667eea",
              color: "white",
              border: "none",
              borderRadius: "12px",
              cursor: sending || disabled ? "not-allowed" : "pointer",
            }}
          >
            {sending ? "..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}