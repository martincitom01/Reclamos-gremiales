import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '@/context/AuthContext';
import { ArrowLeft, Upload, X } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LINEAS = ['A', 'B', 'C', 'D', 'E', 'H', 'Premetro'];
const CATEGORIAS = [
  'Condiciones de trabajo',
  'Faltante de materiales o elementos de seguridad',
  'Higiene y salubridad',
  'Seguridad y prevención',
  'Personal y recursos humanos',
  'Conflictos o situaciones laborales',
  'Otros reclamos gremiales'
];

const NuevoReclamo = () => {
  const navigate = useNavigate();
  const { user, getAuthHeaders } = useAuth();
  const [formData, setFormData] = useState({
    linea: '',
    categoria: '',
    sector_estacion: '',
    descripcion: ''
  });
  const [archivos, setArchivos] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Auto-set line for emisores when user data loads
  useEffect(() => {
    if (user?.role === 'EMISOR_RECLAMO' && user?.linea_asignada) {
      setFormData(prev => ({
        ...prev,
        linea: user.linea_asignada
      }));
    }
  }, [user]);

  // Check if emisor has line assigned
  if (user?.role === 'EMISOR_RECLAMO' && !user?.linea_asignada) {
    return (
      <div>
        <header className="header-uta">
          <div className="header-content">
            <div className="header-title">Nuevo Reclamo Gremial</div>
            <button className="nav-button" onClick={() => navigate('/')}>
              <ArrowLeft size={16} style={{display: 'inline', marginRight: '4px'}} />
              Volver
            </button>
          </div>
        </header>
        <div className="page-container">
          <div className="form-container">
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <h2 style={{ color: '#1e3a5f', marginBottom: '1rem' }}>No puedes crear reclamos</h2>
              <p style={{ color: '#64748b' }}>Tu cuenta no tiene una línea asignada. Contacta al administrador.</p>
              <button className="btn-primary" onClick={() => navigate('/')} style={{ marginTop: '1.5rem' }}>
                Volver al Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setArchivos([...archivos, ...files]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    setArchivos([...archivos, ...files]);
  };

  const removeFile = (index) => {
    setArchivos(archivos.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.linea || !formData.categoria || !formData.sector_estacion || !formData.descripcion) {
      toast.error('Por favor complete todos los campos obligatorios');
      return;
    }

    setSubmitting(true);

    try {
      // Crear reclamo
      const response = await axios.post(`${API}/reclamos`, formData, {
        headers: getAuthHeaders()
      });
      const reclamoId = response.data.id;

      // Subir archivos
      for (const archivo of archivos) {
        const formDataFile = new FormData();
        formDataFile.append('file', archivo);
        await axios.post(`${API}/reclamos/${reclamoId}/archivos`, formDataFile, {
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'multipart/form-data'
          }
        });
      }

      toast.success(`Reclamo creado: ${response.data.numero_reclamo}`);
      setTimeout(() => {
        navigate(`/reclamo/${reclamoId}`);
      }, 1500);
    } catch (error) {
      console.error('Error creando reclamo:', error);
      toast.error(error.response?.data?.detail || 'Error al crear el reclamo');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <header className="header-uta">
        <div className="header-content">
          <div className="header-title" data-testid="nuevo-reclamo-title">
            Nuevo Reclamo Gremial
          </div>
          <button 
            className="nav-button" 
            onClick={() => navigate('/')}
            data-testid="back-to-dashboard-btn"
          >
            <ArrowLeft size={16} style={{display: 'inline', marginRight: '4px'}} />
            Volver
          </button>
        </div>
      </header>

      <div className="page-container">
        <form onSubmit={handleSubmit} className="form-container" data-testid="nuevo-reclamo-form">
          <h2 className="form-title">Registrar Nuevo Reclamo</h2>

          <div className="form-group">
            <label className="form-label" htmlFor="linea">Línea de Subte *</label>
            <select
              id="linea"
              name="linea"
              className="form-select"
              value={formData.linea}
              onChange={handleChange}
              required
              disabled={user?.role === 'EMISOR_RECLAMO'}
              data-testid="select-linea"
            >
              <option value="">Seleccione una línea</option>
              {LINEAS.map(linea => (
                <option key={linea} value={linea}>{linea === 'Premetro' ? 'Premetro' : `Línea ${linea}`}</option>
              ))}
            </select>
            {user?.role === 'EMISOR_RECLAMO' && (
              <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.5rem' }}>
                Tu línea asignada: <strong>Línea {user?.linea_asignada}</strong>
              </p>
            )}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="categoria">Categoría del Reclamo *</label>
            <select
              id="categoria"
              name="categoria"
              className="form-select"
              value={formData.categoria}
              onChange={handleChange}
              required
              data-testid="select-categoria"
            >
              <option value="">Seleccione una categoría</option>
              {CATEGORIAS.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="sector_estacion">Sector o Estación *</label>
            <input
              type="text"
              id="sector_estacion"
              name="sector_estacion"
              className="form-input"
              value={formData.sector_estacion}
              onChange={handleChange}
              placeholder="Ej: Estación Agüero"
              required
              data-testid="input-sector-estacion"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="descripcion">Descripción del Reclamo *</label>
            <textarea
              id="descripcion"
              name="descripcion"
              className="form-textarea"
              value={formData.descripcion}
              onChange={handleChange}
              placeholder="Detalle del hecho, fecha, personas involucradas, etc."
              required
              data-testid="textarea-descripcion"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Archivos Adjuntos (Fotos, Documentos)</label>
            <div
              className={`file-upload-area ${dragOver ? 'drag-over' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-input').click()}
              data-testid="file-upload-area"
            >
              <Upload size={32} style={{ color: '#4a90e2', margin: '0 auto 0.5rem' }} />
              <p style={{ color: '#64748b', marginBottom: '0.5rem' }}>Haga clic o arrastre archivos aquí</p>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Soporta imágenes, PDF y documentos</p>
              <input
                id="file-input"
                type="file"
                multiple
                style={{ display: 'none' }}
                onChange={handleFileSelect}
                accept="image/*,.pdf,.doc,.docx"
              />
            </div>
            {archivos.length > 0 && (
              <div className="file-list" data-testid="file-list">
                {archivos.map((file, index) => (
                  <div key={index} className="file-item">
                    {file.name}
                    <span className="file-item-remove" onClick={() => removeFile(index)}>×</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '2rem' }}>
            <button 
              type="button" 
              className="btn-secondary" 
              onClick={() => navigate('/')}
              data-testid="cancel-btn"
            >
              Cancelar
            </button>
            <button 
              type="submit" 
              className="btn-primary" 
              disabled={submitting}
              data-testid="submit-reclamo-btn"
            >
              {submitting ? 'Creando...' : 'Crear Reclamo'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NuevoReclamo;