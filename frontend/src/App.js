import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import PhysicsChat from "./pages/PhysicsChat";
import MedicalChat from "./pages/MedicalChat";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/physics" element={<PhysicsChat />} />
        <Route path="/medical" element={<MedicalChat />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
