import ChatUI from "../ChatUI";

export default function MedicalChat() {
  return (
    <ChatUI
      title="🩺 Medical ChatBot"
      endpoint="http://127.0.0.1:8000/medical"
      placeholder="Ask a medical question..."
    />
  );
}
