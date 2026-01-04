import '@/App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import Dashboard from '@/pages/Dashboard';
import NuevoReclamo from '@/pages/NuevoReclamo';
import Administracion from '@/pages/Administracion';
import DetalleReclamo from '@/pages/DetalleReclamo';
import Estadisticas from '@/pages/Estadisticas';
import Login from '@/pages/Login';
import GestionUsuarios from '@/pages/GestionUsuarios';
import AceptarInvitacion from '@/pages/AceptarInvitacion';
import Comunicados from '@/pages/Comunicados';
import { Toaster } from '@/components/ui/sonner';

const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div style={{ fontSize: '1.2rem', color: '#64748b' }}>Cargando...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && user?.role !== 'ADMIN') {
    return <Navigate to="/" replace />;
  }

  return children;
};

const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div style={{ fontSize: '1.2rem', color: '#64748b' }}>Cargando...</div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/emisor-login" element={<PublicRoute><Login /></PublicRoute>} />
            <Route path="/invitacion/:token" element={<AceptarInvitacion />} />
            <Route path="/" element={<Dashboard />} />
            <Route path="/nuevo-reclamo" element={<ProtectedRoute><NuevoReclamo /></ProtectedRoute>} />
            <Route path="/administracion" element={<Administracion />} />
            <Route path="/reclamo/:id" element={<ProtectedRoute><DetalleReclamo /></ProtectedRoute>} />
            <Route path="/estadisticas" element={<Estadisticas />} />
            <Route path="/usuarios" element={<GestionUsuarios />} />
            <Route path="/comunicados" element={<Comunicados />} />
          </Routes>
          <Toaster position="top-right" richColors />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;