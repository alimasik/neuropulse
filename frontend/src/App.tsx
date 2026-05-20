import { Routes, Route, useLocation } from 'react-router-dom';
import NavBar from './components/NavBar';
import HomeScreen from './routes/HomeScreen';
import InterventionScreen from './routes/InterventionScreen';
import SensoryMap from './routes/SensoryMap';
import AACScreen from './routes/AACScreen';
import DoctorDashboard from './routes/DoctorDashboard';

export default function App() {
  const location = useLocation();

  return (
    <div className="flex flex-col min-h-screen" style={{ backgroundColor: 'var(--color-bg)' }}>
      <main className="flex-1 pb-20">
        <Routes>
          <Route path="/"             element={<HomeScreen />} />
          <Route path="/intervention" element={<InterventionScreen />} />
          <Route path="/map"          element={<SensoryMap />} />
          <Route path="/aac"          element={<AACScreen />} />
          <Route path="/doctor"       element={<DoctorDashboard />} />
        </Routes>
      </main>

      <NavBar currentPath={location.pathname} />
    </div>
  );
}
