import { useNavigate } from "react-router-dom";
import "../App.css";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="home">
      <h1>AI Tutor Platform</h1>
      <p className="subtitle">
        Choose a tutor to start learning
      </p>

      <div className="card-container">
        <div className="card">
          <h3>🩺 Medical Tutor</h3>
          <p>
            Ask about diseases, symptoms, first aid and basic healthcare.
          </p>
          <button onClick={() => navigate("/medical")}>
            Start Medical Chat
          </button>
        </div>

        <div className="card">
          <h3>⚛️ Physics Tutor</h3>
          <p>
            Learn physics concepts with formulas, steps and examples.
          </p>
          <button onClick={() => navigate("/physics")}>
            Start Physics Chat
          </button>
        </div>
      </div>
    </div>
  );
}
