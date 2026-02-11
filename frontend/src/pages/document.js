import { useState } from "react";
import ChatUI from "../ChatUI";
import "../App.css"; // Ensure styles are applied

export default function DocumentChat() {
  const [uploadStatus, setUploadStatus] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (file.type !== "application/pdf") {
      setUploadStatus("❌ Please upload a PDF file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setIsUploading(true);
    setUploadStatus("Uploading and indexing...");

    try {
      const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        setUploadStatus("✅ Success! Your document is ready to chat.");
      } else {
        setUploadStatus("❌ Upload failed. Check backend connection.");
      }
    } catch (error) {
      setUploadStatus("❌ Error: Could not connect to the server.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="document-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100vh', width: '100%' }}>
      
      {/* --- NEW UPLOAD SECTION --- */}
      <div className="upload-section" style={{ 
        background: "rgba(255, 255, 255, 0.1)", 
        padding: "15px", 
        borderRadius: "12px", 
        margin: "10px 0", 
        width: "95%", 
        maxWidth: "420px",
        textAlign: "center",
        border: "1px dashed white"
      }}>
        <input 
          type="file" 
          accept=".pdf" 
          onChange={handleFileUpload} 
          id="pdf-upload" 
          style={{ display: 'none' }} 
        />
        <label htmlFor="pdf-upload" style={{
          backgroundColor: isUploading ? "#ccc" : "#fff",
          color: "#667eea",
          padding: "8px 16px",
          borderRadius: "8px",
          cursor: isUploading ? "not-allowed" : "pointer",
          fontWeight: "bold",
          display: "inline-block"
        }}>
          {isUploading ? "⏳ Processing..." : "📁 Upload PDF"}
        </label>
        <p style={{ color: "white", fontSize: "12px", marginTop: "8px", marginBottom: "0" }}>
          {uploadStatus || "Upload a PDF to start the RAG process."}
        </p>
      </div>

      {/* --- EXISTING CHAT UI --- */}
      <ChatUI
        title="📄 Document Assistant"
        endpoint="http://127.0.0.1:8000/ask"
        placeholder="Ask something about your PDF..."
      />
    </div>
  );
}