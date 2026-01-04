import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '@/context/AuthContext';
import { Train, Plus, BarChart3, ClipboardList, LogOut, Users, Key, MessageSquare } from 'lucide-react';
import NotificationBell from '@/components/NotificationBell';
import CambiarPasswordModal from '@/components/CambiarPasswordModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LINEAS = [
  { id: 'A', nombre: 'Línea A', color: '#00A7E1' },
  { id: 'B', nombre: 'Línea B', color: '#DC241F' },
  { id: 'C', nombre: 'Línea C', color: '#2C3592' },
  { id: 'D', nombre: 'Línea D', color: '#00B050' },
  { id: 'E', nombre: 'Línea E', color: '#9D5AB7' },
  { id: 'H', nombre: 'Línea H', color: '#FFD700' },
  { id: 'Premetro', nombre: 'Premetro', color: '#85BC22' }
];

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, logout, getAuthHeaders, isAuthenticated } = useAuth();
  const [reclamos, setReclamos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  useEffect(() => {
    initializeDashboard();
  }, []);

  const initializeDashboard = async () => {
    // Si no está autenticado, obtener acceso admin automático
    if (!isAuthenticated && !localStorage.getItem('adminInitialized')) {
      try {
        const response = await axios.get(`${API}/admin/access`);
        const { access_token, user: adminUser } = response.data;
        localStorage.setItem('token', access_token);
        localStorage.setItem('isAdmin', 'true');
        localStorage.setItem('adminInitialized', 'true');
        setIsAdmin(true);
        // Recargar página para actualizar el contexto
        window.location.reload();
      } catch (error) {
        console.error('Error getting admin access:', error);
      }
    } else {
      // Ya está autenticado o ya se inicializó admin
      if (user?.role === 'ADMIN' || localStorage.getItem('isAdmin') === 'true') {
        setIsAdmin(true);
      } else if (user?.role === 'EMISOR_RECLAMO') {
        // Es emisor, verificar si tiene línea asignada
        setIsAdmin(false);
      }
      cargarReclamos();
    }
  };

  const cargarReclamos = async () => {
    try {
      const response = await axios.get(`${API}/reclamos`, {
        headers: getAuthHeaders()
      });
      setReclamos(response.data);
    } catch (error) {
      console.error('Error cargando reclamos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('isAdmin');
    localStorage.removeItem('adminInitialized');
    logout();
    navigate('/emisor-login');
  };

  const contarReclamosPorLinea = (lineaId) => {
    return reclamos.filter(r => r.linea === lineaId).length;
  };

  const contarPendientesPorLinea = (lineaId) => {
    return reclamos.filter(r => r.linea === lineaId && r.estado !== 'Resuelto').length;
  };

  // Filter lineas based on role
  const lineasVisibles = user?.role === 'EMISOR_RECLAMO' && user?.linea_asignada
    ? LINEAS.filter(l => l.id === user.linea_asignada)
    : LINEAS;

  return (
    <div>
      <header className="header-uta">
        <div className="header-content">
          <div className="header-title" data-testid="header-title">
            <Train size={32} />
            <span>Sistema de Reclamos Gremiales UTA</span>
          </div>
          <div className="header-nav">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginRight: '1rem', padding: '0.5rem 1rem', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '8px' }}>
              <span style={{ color: 'white', fontSize: '0.9rem', fontWeight: '500' }}>{user?.username}</span>
              <span style={{ color: '#bfdbfe', fontSize: '0.8rem' }}>({user?.role === 'ADMIN' ? 'Admin' : 'Emisor'})</span>
            </div>
            <button 
              className="nav-button" 
              onClick={() => setShowPasswordModal(true)}
              data-testid="change-password-btn"
              title="Cambiar Contraseña"
            >
              <Key size={16} />
            </button>
            <NotificationBell />
            <button 
              className="nav-button active" 
              onClick={() => navigate('/')}
              data-testid="nav-dashboard-btn"
            >
              Dashboard
            </button>
            <button 
              className="nav-button" 
              onClick={() => navigate('/nuevo-reclamo')}
              data-testid="nav-nuevo-reclamo-btn"
            >
              <Plus size={16} style={{display: 'inline', marginRight: '4px'}} />
              Nuevo Reclamo
            </button>
            <button 
              className="nav-button" 
              onClick={() => navigate('/administracion')}
              data-testid="nav-admin-btn"
            >
              <ClipboardList size={16} style={{display: 'inline', marginRight: '4px'}} />
              Administración
            </button>
            <button 
              className="nav-button" 
              onClick={() => navigate('/estadisticas')}
              data-testid="nav-stats-btn"
            >
              <BarChart3 size={16} style={{display: 'inline', marginRight: '4px'}} />
              Estadísticas
            </button>
            {user?.role === 'ADMIN' && (
              <button 
                className="nav-button" 
                onClick={() => navigate('/usuarios')}
                data-testid="nav-usuarios-btn"
              >
                <Users size={16} style={{display: 'inline', marginRight: '4px'}} />
                Usuarios
              </button>
            )}
            <button 
              className="nav-button" 
              onClick={() => navigate('/comunicados')}
              data-testid="nav-comunicados-btn"
            >
              <MessageSquare size={16} style={{display: 'inline', marginRight: '4px'}} />
              Comunicados
            </button>
            {user?.role === 'ADMIN' ? (
              <button 
                className="nav-button" 
                onClick={() => navigate('/emisor-login')}
                data-testid="emisor-access-btn"
                style={{ background: 'rgba(74, 144, 226, 0.2)', borderColor: '#4a90e2' }}
              >
                <LogOut size={16} style={{display: 'inline', marginRight: '4px', transform: 'scaleX(-1)' }} />
                Acceso Emisores
              </button>
            ) : (
              <button 
                className="nav-button" 
                onClick={handleLogout}
                data-testid="logout-btn"
              >
                <LogOut size={16} style={{display: 'inline', marginRight: '4px'}} />
                Salir
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="page-container">
        <h1 style={{ fontSize: '2.5rem', fontWeight: '700', color: '#1e3a5f', marginBottom: '0.5rem' }} data-testid="dashboard-title">
          Panel Principal
        </h1>
        {user?.role === 'EMISOR_RECLAMO' && !user?.linea_asignada && (
          <div style={{ background: '#fef3c7', border: '2px solid #fbbf24', borderRadius: '12px', padding: '1rem 1.5rem', marginBottom: '2rem' }}>
            <p style={{ color: '#92400e', fontSize: '0.95rem', fontWeight: '500' }}>
              ⚠️ Tu cuenta aún no tiene una línea asignada. Contacta al administrador para que te asigne una línea.
            </p>
          </div>
        )}
        <p style={{ fontSize: '1.1rem', color: '#64748b', marginBottom: '2rem' }}>
          {user?.role === 'ADMIN' ? 'Seleccione una línea para ver los reclamos gremiales' : 'Tus reclamos'}
        </p>

        {/* Tarjeta de credenciales - Ayuda memoria */}
        <div style={{ 
          background: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)', 
          border: '2px solid #3b82f6', 
          borderRadius: '12px', 
          padding: '1.5rem', 
          marginBottom: '2rem',
          boxShadow: '0 4px 12px rgba(59, 130, 246, 0.15)'
        }} data-testid="credentials-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ 
              width: '50px', 
              height: '50px', 
              borderRadius: '12px', 
              background: 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              fontSize: '1.5rem',
              boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
            }}>
              🔐
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: '600', color: '#1e40af', marginBottom: '0.25rem' }}>
                Tus Credenciales de Acceso
              </h3>
              <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Información de tu cuenta</p>
            </div>
          </div>
          
          <div style={{ 
            background: 'white', 
            borderRadius: '10px', 
            padding: '1.25rem',
            border: '1px solid #bfdbfe'
          }}>
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: '500', marginBottom: '0.5rem' }}>
                👤 Nombre de Usuario
              </div>
              <div style={{ 
                fontSize: '1.1rem', 
                color: '#1e293b', 
                fontWeight: '700', 
                fontFamily: 'monospace', 
                background: '#f8fafc', 
                padding: '0.75rem 1rem', 
                borderRadius: '8px',
                border: '2px solid #e2e8f0',
                letterSpacing: '0.5px'
              }} data-testid="user-username">
                {user?.username}
              </div>
            </div>
            
            <div>
              <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: '500', marginBottom: '0.5rem' }}>
                🔑 Contraseña
              </div>
              <div style={{ 
                fontSize: '0.9rem', 
                color: '#475569',
                background: '#fef3c7', 
                padding: '0.75rem 1rem', 
                borderRadius: '8px',
                border: '2px solid #fbbf24',
                fontStyle: 'italic'
              }}>
                La contraseña que te fue asignada por el administrador
              </div>
            </div>
          </div>
          
          <div style={{ 
            marginTop: '1rem', 
            padding: '0.75rem 1rem', 
            background: 'rgba(59, 130, 246, 0.1)', 
            borderRadius: '8px',
            borderLeft: '4px solid #3b82f6'
          }}>
            <p style={{ fontSize: '0.85rem', color: '#1e40af', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>💡</span>
              <span><strong>Importante:</strong> Guarda estas credenciales en un lugar seguro. Necesitarás el usuario y contraseña para acceder al sistema.</span>
            </p>
          </div>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>Cargando...</div>
        ) : (
          <div className="lineas-grid">
            {lineasVisibles.map((linea) => (
              <div
                key={linea.id}
                className="linea-card"
                style={{ '--linea-color': linea.color }}
                onClick={() => navigate(`/administracion?linea=${linea.id}`)}
                data-testid={`linea-card-${linea.id}`}
              >
                <div className="linea-header">
                  <div className="linea-icon" style={{ background: linea.color }}>
                    {linea.id}
                  </div>
                  <div className="linea-info">
                    <h3>{linea.nombre}</h3>
                  </div>
                </div>
                <div className="linea-stats">
                  <div className="stat-item">
                    <div className="stat-value" style={{ color: linea.color }}>
                      {contarReclamosPorLinea(linea.id)}
                    </div>
                    <div className="stat-label">Total</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value" style={{ color: linea.color }}>
                      {contarPendientesPorLinea(linea.id)}
                    </div>
                    <div className="stat-label">Activos</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <CambiarPasswordModal
        isOpen={showPasswordModal}
        onClose={() => setShowPasswordModal(false)}
        getAuthHeaders={getAuthHeaders}
      />
    </div>
  );
};

export default Dashboard;