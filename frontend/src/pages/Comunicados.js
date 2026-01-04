import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '@/context/AuthContext';
import { ArrowLeft, Send, Users, MapPin, User, Image, MessageSquare, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LINEAS = ['A', 'B', 'C', 'D', 'E', 'H', 'Premetro'];

const Comunicados = () => {
  const navigate = useNavigate();
  const { getAuthHeaders, user, isAuthenticated, loading: authLoading } = useAuth();
  const [comunicados, setComunicados] = useState([]);
  const [usuarios, setUsuarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [expandedComunicado, setExpandedComunicado] = useState(null);
  
  const [formData, setFormData] = useState({
    titulo: '',
    mensaje: '',
    tipo_destinatario: 'todos',
    lineas_destino: [],
    usuarios_destino: [],
    imagen: null
  });

  useEffect(() => {
    // Wait for auth to finish loading
    if (authLoading) return;
    
    // If user is authenticated, load data
    if (isAuthenticated && user) {
      cargarDatos();
    } else if (!isAuthenticated) {
      // Not authenticated - try admin access or redirect
      const token = localStorage.getItem('token');
      if (token) {
        // Has token, try to load
        cargarDatos();
      } else if (localStorage.getItem('adminInitialized')) {
        // Admin was initialized but no token - reload
        window.location.reload();
      } else {
        // No auth at all - try admin access
        initializeAdminAccess();
      }
    }
  }, [authLoading, isAuthenticated, user]);

  const initializeAdminAccess = async () => {
    try {
      const response = await axios.get(`${API}/admin/access`);
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('adminInitialized', 'true');
      window.location.reload();
    } catch (error) {
      console.error('Error getting admin access:', error);
      navigate('/emisor-login');
    }
  };

  const cargarDatos = async () => {
    setLoading(true);
    try {
      const headers = getAuthHeaders();
      
      // Load comunicados
      const comResponse = await axios.get(`${API}/comunicados`, { headers });
      setComunicados(comResponse.data);
      
      // Only load users list if admin (for recipient selection)
      if (user?.role === 'ADMIN') {
        try {
          const usersResponse = await axios.get(`${API}/users`, { headers });
          setUsuarios(usersResponse.data.filter(u => u.role === 'EMISOR_RECLAMO'));
        } catch (err) {
          console.error('Error loading users:', err);
        }
      }
    } catch (error) {
      console.error('Error cargando datos:', error);
      if (error.response?.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('token');
        navigate('/emisor-login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleEnviar = async (e) => {
    e.preventDefault();
    
    if (!formData.titulo.trim() || !formData.mensaje.trim()) {
      toast.error('Complete el título y mensaje');
      return;
    }

    if (formData.tipo_destinatario === 'lineas' && formData.lineas_destino.length === 0) {
      toast.error('Seleccione al menos una línea');
      return;
    }

    if (formData.tipo_destinatario === 'usuarios' && formData.usuarios_destino.length === 0) {
      toast.error('Seleccione al menos un usuario');
      return;
    }

    setEnviando(true);
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('titulo', formData.titulo);
      formDataToSend.append('mensaje', formData.mensaje);
      formDataToSend.append('tipo_destinatario', formData.tipo_destinatario);
      formDataToSend.append('lineas_destino', formData.lineas_destino.join(','));
      formDataToSend.append('usuarios_destino', formData.usuarios_destino.join(','));
      
      if (formData.imagen) {
        formDataToSend.append('imagen', formData.imagen);
      }

      const response = await axios.post(
        `${API}/comunicados?titulo=${encodeURIComponent(formData.titulo)}&mensaje=${encodeURIComponent(formData.mensaje)}&tipo_destinatario=${formData.tipo_destinatario}&lineas_destino=${formData.lineas_destino.join(',')}&usuarios_destino=${formData.usuarios_destino.join(',')}`,
        formData.imagen ? formDataToSend : null,
        {
          headers: {
            ...getAuthHeaders(),
            ...(formData.imagen ? { 'Content-Type': 'multipart/form-data' } : {})
          }
        }
      );

      toast.success(`Comunicado enviado a ${response.data.destinatarios} destinatarios`);
      setFormData({
        titulo: '',
        mensaje: '',
        tipo_destinatario: 'todos',
        lineas_destino: [],
        usuarios_destino: [],
        imagen: null
      });
      setShowForm(false);
      cargarDatos();
    } catch (error) {
      console.error('Error enviando comunicado:', error);
      toast.error(error.response?.data?.detail || 'Error al enviar comunicado');
    } finally {
      setEnviando(false);
    }
  };

  const handleEliminar = async (comunicadoId) => {
    if (!window.confirm('¿Está seguro de eliminar este comunicado?')) return;

    try {
      await axios.delete(`${API}/comunicados/${comunicadoId}`, {
        headers: getAuthHeaders()
      });
      toast.success('Comunicado eliminado');
      cargarDatos();
    } catch (error) {
      console.error('Error eliminando comunicado:', error);
      toast.error('Error al eliminar comunicado');
    }
  };

  const toggleLinea = (linea) => {
    setFormData(prev => ({
      ...prev,
      lineas_destino: prev.lineas_destino.includes(linea)
        ? prev.lineas_destino.filter(l => l !== linea)
        : [...prev.lineas_destino, linea]
    }));
  };

  const toggleUsuario = (userId) => {
    setFormData(prev => ({
      ...prev,
      usuarios_destino: prev.usuarios_destino.includes(userId)
        ? prev.usuarios_destino.filter(u => u !== userId)
        : [...prev.usuarios_destino, userId]
    }));
  };

  const formatearFecha = (fecha) => {
    try {
      return format(new Date(fecha), "dd/MM/yyyy HH:mm", { locale: es });
    } catch {
      return fecha;
    }
  };

  const getDestinatariosTexto = (comunicado) => {
    if (comunicado.tipo_destinatario === 'todos') return 'Todos los emisores';
    if (comunicado.tipo_destinatario === 'lineas') return `Líneas: ${comunicado.lineas_destino.join(', ')}`;
    if (comunicado.tipo_destinatario === 'usuarios') {
      const nombres = comunicado.usuarios_destino.map(uid => {
        const user = usuarios.find(u => u.id === uid);
        return user ? user.username : uid;
      });
      return `Usuarios: ${nombres.join(', ')}`;
    }
    return '';
  };

  return (
    <div>
      <header className="header-uta">
        <div className="header-content">
          <div className="header-title">
            <MessageSquare size={28} />
            <span>Comunicados</span>
          </div>
          <button className="nav-button" onClick={() => navigate('/')}>
            <ArrowLeft size={16} style={{display: 'inline', marginRight: '4px'}} />
            Volver al Dashboard
          </button>
        </div>
      </header>

      <div className="page-container">
        {user?.role === 'ADMIN' && (
          <div style={{ marginBottom: '2rem' }}>
            {!showForm ? (
              <button className="btn-primary" onClick={() => setShowForm(true)}>
                <Send size={18} style={{display: 'inline', marginRight: '6px'}} />
                Nuevo Comunicado
              </button>
            ) : (
              <div style={{ background: 'white', borderRadius: '16px', padding: '2rem', boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)' }}>
                <h3 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1e3a5f', marginBottom: '1.5rem' }}>
                  Enviar Nuevo Comunicado
                </h3>
                
                <form onSubmit={handleEnviar}>
                  <div className="form-group">
                    <label className="form-label">Título *</label>
                    <input
                      type="text"
                      className="form-input"
                      value={formData.titulo}
                      onChange={(e) => setFormData({...formData, titulo: e.target.value})}
                      placeholder="Ej: Mejoras salariales 2025"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Mensaje *</label>
                    <textarea
                      className="form-textarea"
                      value={formData.mensaje}
                      onChange={(e) => setFormData({...formData, mensaje: e.target.value})}
                      placeholder="Escriba el contenido del comunicado..."
                      rows={4}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">
                      <Image size={16} style={{display: 'inline', marginRight: '4px'}} />
                      Imagen (opcional)
                    </label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setFormData({...formData, imagen: e.target.files[0]})}
                      style={{ padding: '0.5rem' }}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Enviar a:</label>
                    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                        <input
                          type="radio"
                          name="tipo_destinatario"
                          value="todos"
                          checked={formData.tipo_destinatario === 'todos'}
                          onChange={(e) => setFormData({...formData, tipo_destinatario: e.target.value})}
                        />
                        <Users size={16} />
                        <span>Todos</span>
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                        <input
                          type="radio"
                          name="tipo_destinatario"
                          value="lineas"
                          checked={formData.tipo_destinatario === 'lineas'}
                          onChange={(e) => setFormData({...formData, tipo_destinatario: e.target.value})}
                        />
                        <MapPin size={16} />
                        <span>Por Línea</span>
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                        <input
                          type="radio"
                          name="tipo_destinatario"
                          value="usuarios"
                          checked={formData.tipo_destinatario === 'usuarios'}
                          onChange={(e) => setFormData({...formData, tipo_destinatario: e.target.value})}
                        />
                        <User size={16} />
                        <span>Usuarios específicos</span>
                      </label>
                    </div>

                    {formData.tipo_destinatario === 'lineas' && (
                      <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', marginTop: '1rem' }}>
                        <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '0.75rem' }}>Seleccione las líneas:</p>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                          {LINEAS.map(linea => (
                            <button
                              key={linea}
                              type="button"
                              onClick={() => toggleLinea(linea)}
                              style={{
                                padding: '0.5rem 1rem',
                                borderRadius: '8px',
                                border: formData.lineas_destino.includes(linea) ? '2px solid #2563eb' : '2px solid #e2e8f0',
                                background: formData.lineas_destino.includes(linea) ? '#dbeafe' : 'white',
                                color: formData.lineas_destino.includes(linea) ? '#1e40af' : '#64748b',
                                cursor: 'pointer',
                                fontWeight: '500',
                                transition: 'all 0.2s'
                              }}
                            >
                              Línea {linea}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {formData.tipo_destinatario === 'usuarios' && (
                      <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', marginTop: '1rem', maxHeight: '200px', overflowY: 'auto' }}>
                        <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '0.75rem' }}>Seleccione los usuarios:</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                          {usuarios.map(usuario => (
                            <label
                              key={usuario.id}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.75rem',
                                padding: '0.5rem',
                                background: formData.usuarios_destino.includes(usuario.id) ? '#dbeafe' : 'white',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                border: formData.usuarios_destino.includes(usuario.id) ? '1px solid #2563eb' : '1px solid #e2e8f0'
                              }}
                            >
                              <input
                                type="checkbox"
                                checked={formData.usuarios_destino.includes(usuario.id)}
                                onChange={() => toggleUsuario(usuario.id)}
                              />
                              <span style={{ fontWeight: '500' }}>{usuario.username}</span>
                              <span style={{ color: '#64748b', fontSize: '0.85rem' }}>
                                ({usuario.linea_asignada ? `Línea ${usuario.linea_asignada}` : 'Sin línea'})
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                    <button type="submit" className="btn-primary" disabled={enviando}>
                      <Send size={18} style={{display: 'inline', marginRight: '6px'}} />
                      {enviando ? 'Enviando...' : 'Enviar Comunicado'}
                    </button>
                    <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>
                      Cancelar
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        )}

        {/* Lista de comunicados */}
        <div style={{ background: 'white', borderRadius: '16px', padding: '2rem', boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1e3a5f', marginBottom: '1.5rem' }}>
            {user?.role === 'ADMIN' ? 'Historial de Comunicados' : 'Comunicados'}
          </h2>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>Cargando...</div>
          ) : comunicados.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
              No hay comunicados
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {comunicados.map(comunicado => (
                <div
                  key={comunicado.id}
                  style={{
                    border: '1px solid #e2e8f0',
                    borderRadius: '12px',
                    overflow: 'hidden'
                  }}
                >
                  <div
                    style={{
                      padding: '1.25rem',
                      background: '#f8fafc',
                      cursor: 'pointer'
                    }}
                    onClick={() => setExpandedComunicado(expandedComunicado === comunicado.id ? null : comunicado.id)}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                      <div style={{ flex: 1 }}>
                        <h3 style={{ fontSize: '1.1rem', fontWeight: '600', color: '#1e3a5f', marginBottom: '0.5rem' }}>
                          {comunicado.titulo}
                        </h3>
                        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', fontSize: '0.85rem', color: '#64748b' }}>
                          <span>📅 {formatearFecha(comunicado.created_at)}</span>
                          <span>👤 {comunicado.autor_nombre}</span>
                          <span>📩 {getDestinatariosTexto(comunicado)}</span>
                          {comunicado.respuestas?.length > 0 && (
                            <span style={{ color: '#2563eb', fontWeight: '500' }}>
                              💬 {comunicado.respuestas.length} respuesta(s)
                            </span>
                          )}
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {user?.role === 'ADMIN' && (
                          <button
                            onClick={(e) => { e.stopPropagation(); handleEliminar(comunicado.id); }}
                            style={{
                              background: '#fee2e2',
                              color: '#991b1b',
                              border: 'none',
                              padding: '0.4rem',
                              borderRadius: '6px',
                              cursor: 'pointer'
                            }}
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                        {expandedComunicado === comunicado.id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                      </div>
                    </div>
                  </div>

                  {expandedComunicado === comunicado.id && (
                    <div style={{ padding: '1.25rem', borderTop: '1px solid #e2e8f0' }}>
                      <p style={{ lineHeight: '1.6', color: '#334155', marginBottom: '1rem', whiteSpace: 'pre-wrap' }}>
                        {comunicado.mensaje}
                      </p>
                      
                      {comunicado.imagen && (
                        <div style={{ marginBottom: '1rem' }}>
                          <img
                            src={`${BACKEND_URL}${comunicado.imagen}`}
                            alt="Imagen adjunta"
                            style={{ maxWidth: '100%', maxHeight: '400px', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                          />
                        </div>
                      )}

                      {/* Respuestas */}
                      {comunicado.respuestas?.length > 0 && (
                        <div style={{ marginTop: '1.5rem' }}>
                          <h4 style={{ fontSize: '1rem', fontWeight: '600', color: '#1e3a5f', marginBottom: '1rem' }}>
                            Respuestas ({comunicado.respuestas.length})
                          </h4>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {comunicado.respuestas.map(resp => (
                              <div
                                key={resp.id}
                                style={{
                                  background: '#f1f5f9',
                                  padding: '1rem',
                                  borderRadius: '8px',
                                  borderLeft: '3px solid #2563eb'
                                }}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                  <span style={{ fontWeight: '600', color: '#1e3a5f' }}>{resp.username}</span>
                                  <span style={{ fontSize: '0.8rem', color: '#64748b' }}>{formatearFecha(resp.created_at)}</span>
                                </div>
                                <p style={{ color: '#334155' }}>{resp.texto}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Form para responder (solo emisores) */}
                      {user?.role === 'EMISOR_RECLAMO' && (
                        <ResponderForm comunicadoId={comunicado.id} onSuccess={cargarDatos} getAuthHeaders={getAuthHeaders} />
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Componente para responder
const ResponderForm = ({ comunicadoId, onSuccess, getAuthHeaders }) => {
  const [texto, setTexto] = useState('');
  const [enviando, setEnviando] = useState(false);

  const handleResponder = async (e) => {
    e.preventDefault();
    if (!texto.trim()) {
      toast.error('Escriba una respuesta');
      return;
    }

    setEnviando(true);
    try {
      await axios.post(
        `${API}/comunicados/${comunicadoId}/respuestas`,
        { texto },
        { headers: getAuthHeaders() }
      );
      toast.success('Respuesta enviada');
      setTexto('');
      onSuccess();
    } catch (error) {
      console.error('Error enviando respuesta:', error);
      toast.error('Error al enviar respuesta');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <form onSubmit={handleResponder} style={{ marginTop: '1.5rem', borderTop: '1px solid #e2e8f0', paddingTop: '1rem' }}>
      <div className="form-group">
        <label className="form-label">Tu respuesta</label>
        <textarea
          className="form-textarea"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Escriba su respuesta..."
          rows={3}
        />
      </div>
      <button type="submit" className="btn-primary" disabled={enviando}>
        <Send size={16} style={{display: 'inline', marginRight: '4px'}} />
        {enviando ? 'Enviando...' : 'Enviar Respuesta'}
      </button>
    </form>
  );
};

export default Comunicados;
