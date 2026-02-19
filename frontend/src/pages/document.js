import { useState, useRef } from "react";
import ChatUI from "../ChatUI";           // adjust path
import "../App.css";

export default function DocumentChat() {
  const [uploadStatus, setUploadStatus] = useState("");
  const [buildStatus, setBuildStatus] = useState("");
  const [chatStatus, setChatStatus] = useState("");
  
  const [isUploading, setIsUploading] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  
  const [indexBuilt, setIndexBuilt] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  
  const fileInputRef = useRef(null);

  const resetState = () => {
    setUploadStatus("");
    setBuildStatus("");
    setChatStatus("");
    setIsUploading(false);
    setIsBuilding(false);
    setIsAsking(false);
    setIndexBuilt(false);
    setUploadedFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== "application/pdf") {
      setUploadStatus("❌ Only PDF files are allowed.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setIsUploading(true);
    setUploadStatus(`Uploading ${file.name}...`);
    setBuildStatus("");
    setChatStatus("");

    try {
      const res = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || data.message || "Upload failed");
      }

      setUploadStatus(`✅ Uploaded: ${file.name}`);
      setUploadedFiles((prev) => [...new Set([...prev, file.name])]);
      setIndexBuilt(false); // force re-index
    } catch (err) {
      console.error("Upload failed:", err);
      setUploadStatus(`❌ ${err.message || "Connection error — is backend running?"}`);
    } finally {
      setIsUploading(false);
      e.target.value = "";
    }
  };

  const handleBuildIndex = async () => {
    if (uploadedFiles.length === 0) {
      setBuildStatus("⚠️ Please upload at least one PDF first.");
      return;
    }

    setIsBuilding(true);
    setBuildStatus("Building vector index... (may take 10–60 seconds)");
    setChatStatus("");

    try {
      const res = await fetch("http://127.0.0.1:8000/build-index", {
        method: "POST",
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Indexing failed");
      }

      const data = await res.json();

      setBuildStatus(`✅ Index updated — ${data.added_chunks || "?"} new chunks added`);
      setIndexBuilt(true);
    } catch (err) {
      console.error("Build index error:", err);
      setBuildStatus(`❌ ${err.message || "Cannot connect to backend"}`);
      setIndexBuilt(false);
    } finally {
      setIsBuilding(false);
    }
  };

  const handleAskQuestion = async (userMessage) => {
    if (!userMessage?.trim()) return null;

    setIsAsking(true);
    setChatStatus("Searching documents and generating answer...");

    try {
      const res = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMessage.trim() }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to get answer");
      }

      const data = await res.json();

      setChatStatus("");

      return {
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
        contexts: data.contexts || [],
      };
    } catch (err) {
      console.error("Ask failed:", err);
      setChatStatus(`❌ ${err.message}`);
      return {
        role: "assistant",
        content: `Sorry, something went wrong: ${err.message}`,
      };
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="document-container" style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      color: "#fff",
      padding: "20px",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
    }}>
      <h1 style={{ marginBottom: "32px", fontSize: "2.4rem", textShadow: "0 2px 10px rgba(0,0,0,0.5)" }}>
        📚 Document Chat
      </h1>

      <div style={{
        background: "rgba(255,255,255,0.13)",
        backdropFilter: "blur(12px)",
        borderRadius: "16px",
        padding: "28px",
        width: "100%",
        maxWidth: "540px",
        marginBottom: "40px",
        boxShadow: "0 12px 48px rgba(0,0,0,0.3)",
        border: "1px solid rgba(255,255,255,0.18)",
      }}>
        {/* Upload Section */}
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <input
            id="pdf-upload"                     // ← FIXED: added id
            type="file"
            accept="application/pdf"
            onChange={handleFileUpload}
            ref={fileInputRef}
            style={{ display: "none" }}
            disabled={isUploading || isBuilding}
          />
          <label
            htmlFor="pdf-upload"                // ← FIXED: matches input id
            style={{
              background: isUploading || isBuilding ? "#555" : "#ffffff",
              color: isUploading || isBuilding ? "#aaa" : "#4f46e5",
              padding: "14px 40px",
              borderRadius: "12px",
              fontWeight: "bold",
              cursor: isUploading || isBuilding ? "not-allowed" : "pointer",
              display: "inline-block",
              boxShadow: "0 4px 20px rgba(0,0,0,0.25)",
              transition: "all 0.25s ease",
            }}
          >
            {isUploading ? "Uploading..." : "📤 Upload PDF"}
          </label>

          {uploadStatus && (
            <p style={{
              marginTop: "14px",
              color: uploadStatus.startsWith("✅") ? "#a7f3d0" : "#fecaca",
              fontSize: "0.95rem",
            }}>
              {uploadStatus}
            </p>
          )}

          {uploadedFiles.length > 0 && (
            <div style={{ marginTop: "16px", fontSize: "0.9rem", opacity: 0.9 }}>
              Uploaded: {uploadedFiles.join(", ")}
            </div>
          )}
        </div>

        {/* Build Index */}
        <div style={{ textAlign: "center" }}>
          <button
            onClick={handleBuildIndex}
            disabled={isBuilding || isUploading || uploadedFiles.length === 0}
            style={{
              background: isBuilding || isUploading || uploadedFiles.length === 0
                ? "#6b7280"
                : "#4f46e5",
              color: "white",
              border: "none",
              padding: "14px 48px",
              borderRadius: "12px",
              fontWeight: "bold",
              fontSize: "1.1rem",
              cursor: (isBuilding || isUploading || uploadedFiles.length === 0) ? "not-allowed" : "pointer",
              boxShadow: "0 6px 20px rgba(79,70,229,0.4)",
              transition: "all 0.25s ease",
            }}
          >
            {isBuilding ? "Building Index..." : "⚡ Build / Update Index"}
          </button>

          {buildStatus && (
            <p style={{
              marginTop: "14px",
              color: buildStatus.startsWith("✅") ? "#a7f3d0" : "#fecaca",
              fontSize: "0.95rem",
            }}>
              {buildStatus}
            </p>
          )}
        </div>

        {indexBuilt && (
          <div style={{
            marginTop: "24px",
            padding: "14px",
            background: "rgba(167,243,208,0.22)",
            borderRadius: "12px",
            textAlign: "center",
            fontWeight: 600,
            color: "#d1fae5",
            border: "1px solid rgba(167,243,208,0.4)",
          }}>
            ✓ Index is ready — you can now ask questions
          </div>
        )}

        <div style={{ textAlign: "center", marginTop: "20px" }}>
          <button
            onClick={resetState}
            style={{
              background: "transparent",
              border: "1px solid rgba(255,255,255,0.5)",
              color: "rgba(255,255,255,0.85)",
              padding: "8px 20px",
              borderRadius: "10px",
              cursor: "pointer",
              fontSize: "0.9rem",
            }}
          >
            Reset Everything
          </button>
        </div>
      </div>

      <div style={{
        width: "100%",
        maxWidth: "820px",
        flex: 1,
        background: "rgba(0,0,0,0.2)",
        borderRadius: "16px",
        overflow: "hidden",
        boxShadow: "0 12px 50px rgba(0,0,0,0.35)",
      }}>
        <ChatUI
          title="Document Assistant"
          placeholder={
            indexBuilt
              ? "Ask anything about the uploaded documents..."
              : "Upload PDFs and build index first"
          }
          disabled={!indexBuilt || isAsking}
          onSend={handleAskQuestion}
          statusMessage={chatStatus}
          showSources={true}
        />
      </div>
    </div>
  );
}