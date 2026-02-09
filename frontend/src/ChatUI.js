import React, { useState, useRef, useEffect } from "react";
import "./App.css";

export default function ChatUI({ title, endpoint, placeholder }) {
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState([]);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendPrompt = async () => {
    if (!prompt.trim()) return;

    setMessages(prev => [...prev, { type: "user", text: prompt }]);
    setPrompt("");

    setMessages(prev => [...prev, { type: "bot", text: "🤖 Thinking..." }]);

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });

    const data = await res.json();

    setMessages(prev => {
      const updated = [...prev];
      updated[updated.length - 1] = {
        type: "bot",
        text: data.response
      };
      return updated;
    });
  };

  return (
    <div className="container">
      <div className="header">{title}</div>

      <div className="chat-box">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.type}`}>
            {m.type === "bot" && <div className="avatar">🤖</div>}
            <div className="bubble">{m.text}</div>
            {m.type === "user" && <div className="avatar">🧑</div>}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <div className="input-area">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={placeholder}
        />
        <button onClick={sendPrompt}>Send</button>
      </div>
    </div>
  );
}
