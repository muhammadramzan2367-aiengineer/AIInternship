import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import PhysicsChat from "./pages/PhysicsChat";
import MedicalChat from "./pages/MedicalChat";
import DocumentChat from "./pages/document"; // Import the new file

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/physics" element={<PhysicsChat />} />
        <Route path="/medical" element={<MedicalChat />} />
        <Route path="/document" element={<DocumentChat />} /> {/* Add this line */}
      </Routes>
    </BrowserRouter>
  );
}

export default App