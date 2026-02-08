import React, { useState } from "react";
import "./App.css";

function App() {
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState("");

  const sendPrompt = async () => {
    if (!prompt.trim()) {
      setResponse("Please type something...");
      return;
    }

    setResponse("🤔 Thinking...");

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      const data = await res.json();
      setResponse(data.response || "No response from server.");
    } catch (error) {
      setResponse("⚠️ Backend not responding. Check server.");
    }
  };

  return (
    <div className="container">
      <h1>⚛️ Physics ChatBot</h1>
      <p className="subtitle">Ask me anything about physics!</p>

      <textarea
        placeholder="Type your question..."
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      ></textarea>

      <button onClick={sendPrompt}>Send</button>

      <div className="response-box">
        <h3>Response</h3>
        <p>{response}</p>
      </div>
    </div>
  );
}

export default App;
