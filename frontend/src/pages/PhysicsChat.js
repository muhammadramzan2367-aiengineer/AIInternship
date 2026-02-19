import ChatUI from "../ChatUI";

export default function PhysicsChat() {
  return (
    <ChatUI
      title="⚛️ Physics ChatBot"
      endpoint="http://127.0.0.1:8000/chat"
      placeholder="Ask a physics question..."
    />
  );
}
