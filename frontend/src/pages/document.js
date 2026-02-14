import { useState } from "react";
import ChatUI from "../ChatUI";
import "../App.css";

export default function DocumentChat() {
  const [uploadStatus, setUploadStatus] = useState("");
  const [buildStatus, setBuildStatus] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);
  const [indexReady, setIndexReady] = useState(false);
  const [lastUploadedFileName, setLastUploadedFileName] = useState(null);

  const resetState = () => {
    setUploadStatus("");
    setBuildStatus("");
    setIsUploading(false);
    setIsBuilding(false);
    setIndexReady(false);
    setLastUploadedFileName(null);
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
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
    setIndexReady(false);

    try {
      const res = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        setUploadStatus(`✅ Uploaded: ${file.name}`);
        setLastUploadedFileName(file.name);
      } else {
        setUploadStatus(`❌ Upload failed — ${data.detail || data.message || "server error"}`);
      }
    } catch (err) {
      console.error("Upload error:", err);
      setUploadStatus("❌ Connection error — is backend running?");
    } finally {
      setIsUploading(false);
    }
  };

  const handleBuildIndex = async () => {
    if (!lastUploadedFileName && !indexReady) {
      setBuildStatus("⚠️ Please upload a PDF first.");
      return;
    }

    setIsBuilding(true);
    setBuildStatus("Indexing document... (may take a few seconds)");

    try {
      const res = await fetch("http://127.0.0.1:8000/build", {
        method: "POST",
      });

      const data = await res.json();

      if (res.ok) {
        setBuildStatus(`✅ Success! ${data.message || "Index built."}`);
        setIndexReady(true);
      } else {
        setBuildStatus(`❌ Indexing failed — ${data.detail || data.message || "unknown error"}`);
        setIndexReady(false);
      }
    } catch (err) {
      console.error("Build error:", err);
      setBuildStatus("❌ Cannot connect to backend.");
    } finally {
      setIsBuilding(false);
    }
  };

  return (
    <div
      className="document-container"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        minHeight: "100vh",
        width: "100%",
        padding: "16px 8px",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        color: "#fff",
      }}
    >
      <h1 style={{ margin: "0 0 24px 0", fontSize: "2.1rem", textShadow: "0 2px 8px rgba(0,0,0,0.4)" }}>
        📄 Document Chat
      </h1>

      {/* Control Panel */}
      <div
        style={{
          background: "rgba(255, 255, 255, 0.12)",
          backdropFilter: "blur(10px)",
          borderRadius: "16px",
          padding: "24px",
          width: "100%",
          maxWidth: "500px",
          marginBottom: "32px",
          boxShadow: "0 10px 40px rgba(0,0,0,0.25)",
          border: "1px solid rgba(255,255,255,0.2)",
        }}
      >
        {/* Upload */}
        <div style={{ textAlign: "center", marginBottom: "20px" }}>
          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileUpload}
            id="pdf-upload"
            style={{ display: "none" }}
            disabled={isUploading || isBuilding}
          />
          <label
            htmlFor="pdf-upload"
            style={{
              background: isUploading || isBuilding ? "#555" : "white",
              color: isUploading || isBuilding ? "#aaa" : "#4f46e5",
              padding: "12px 32px",
              borderRadius: "12px",
              fontWeight: "bold",
              cursor: isUploading || isBuilding ? "not-allowed" : "pointer",
              display: "inline-block",
              boxShadow: "0 4px 16px rgba(0,0,0,0.2)",
              transition: "all 0.22s ease",
            }}
          >
            {isUploading ? "⏳ Uploading..." : "📎 Upload PDF"}
          </label>

          {uploadStatus && (
            <p style={{
              marginTop: "12px",
              fontSize: "14px",
              color: uploadStatus.startsWith("✅") ? "#a7f3d0" : "#fecaca",
              lineHeight: 1.4,
            }}>
              {uploadStatus}
            </p>
          )}
        </div>

        {/* Build Button */}
        <div style={{ textAlign: "center" }}>
          <button
            onClick={handleBuildIndex}
            disabled={isBuilding || isUploading || (!lastUploadedFileName && !indexReady)}
            style={{
              background: isBuilding || isUploading || (!lastUploadedFileName && !indexReady)
                ? "#6b7280"
                : "#4f46e5",
              color: "white",
              border: "none",
              padding: "12px 36px",
              borderRadius: "12px",
              fontWeight: "bold",
              fontSize: "1.05rem",
              cursor: isBuilding || isUploading || (!lastUploadedFileName && !indexReady) ? "not-allowed" : "pointer",
              boxShadow: "0 5px 18px rgba(79,70,229,0.35)",
              transition: "all 0.22s ease",
            }}
          >
            {isBuilding ? "⏳ Indexing..." : "⚡ Build Index"}
          </button>

          {buildStatus && (
            <p style={{
              marginTop: "12px",
              fontSize: "14px",
              color: buildStatus.startsWith("✅") ? "#a7f3d0" : "#fecaca",
              lineHeight: 1.4,
            }}>
              {buildStatus}
            </p>
          )}
        </div>

        {/* Ready Indicator */}
        {indexReady && (
          <div style={{
            marginTop: "20px",
            padding: "12px",
            background: "rgba(167,243,208,0.18)",
            borderRadius: "10px",
            textAlign: "center",
            fontWeight: "bold",
            color: "#d1fae5",
          }}>
            ✓ Document indexed — ready to chat!
          </div>
        )}

        {/* Reset button (dev helper) */}
        <div style={{ textAlign: "center", marginTop: "16px" }}>
          <button
            onClick={resetState}
            style={{
              background: "transparent",
              border: "1px solid rgba(255,255,255,0.4)",
              color: "rgba(255,255,255,0.8)",
              padding: "6px 16px",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "13px",
            }}
          >
            Reset
          </button>
        </div>
      </div>

      {/* Chat Component */}
      <div style={{
        width: "100%",
        maxWidth: "760px",
        flex: 1,
        background: "rgba(0,0,0,0.15)",
        borderRadius: "16px",
        overflow: "hidden",
        boxShadow: "0 10px 40px rgba(0,0,0,0.3)",
      }}>
        <ChatUI
          title="Document Assistant"
          endpoint="http://127.0.0.1:8000/ask"
          placeholder={
            indexReady
              ? "Ask anything about your document..."
              : "Upload a PDF and build index first →"
          }
          disabled={!indexReady}
        />
      </div>
    </div>
  );
}