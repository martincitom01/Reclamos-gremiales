import { useState, useEffect } from 'react';
import { X, User, Mail, Key, MapPin, Save } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LINEAS = ['A', 'B', 'C', 'D', 'E', 'H', 'Premetro'];

const EditarUsuarioModal = ({ isOpen, onClose, onSuccess, usuario, getAuthHeaders }) => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    linea_asignada: ''
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (usuario) {
      setFormData({
        username: usuario.username || '',
        email: usuario.email || '',
        password: '',
        linea_asignada: usuario.linea_asignada || ''
      });
    }
  }, [usuario]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.username.trim()) {
      toast.error('El nombre de usuario es requerido');
      return;
    }
    
    if (!formData.email.trim()) {
      toast.error('El email es requerido');
      return;
    }

    if (formData.password && formData.password.length < 6) {
      toast.error('La contraseña debe tener al menos 6 caracteres');
      return;
    }

    setSaving(true);
    try {
      const dataToSend = {
        username: formData.username,
        email: formData.email,
        linea_asignada: formData.linea_asignada || null
      };

      // Only include password if it was changed
      if (formData.password.trim()) {
        dataToSend.password = formData.password;
      }

      await axios.put(`${API}/users/${usuario.id}`, dataToSend, {
        headers: getAuthHeaders()
      });

      toast.success('Usuario actualizado exitosamente');
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Error actualizando usuario:', error);
      toast.error(error.response?.data?.detail || 'Error al actualizar usuario');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem'
      }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
      data-testid="edit-user-modal"
    >
      <div 
        style={{
          background: 'white',
          borderRadius: '16px',
          padding: '2rem',
          maxWidth: '500px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1e3a5f', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <User size={24} />
            Editar Usuario
          </h2>
          <button 
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '0.5rem',
              borderRadius: '8px',
              transition: 'background 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = '#f1f5f9'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
            data-testid="close-edit-modal"
          >
            <X size={24} color="#64748b" />
          </button>
        </div>

        <div style={{ 
          background: '#f8fafc', 
          padding: '1rem', 
          borderRadius: '8px', 
          marginBottom: '1.5rem',
          border: '1px solid #e2e8f0'
        }}>
          <p style={{ fontSize: '0.9rem', color: '#64748b', margin: 0 }}>
            Editando usuario: <strong style={{ color: '#1e3a5f' }}>{usuario?.username}</strong>
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label className="form-label" htmlFor="edit-username" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <User size={16} />
              Nombre de Usuario *
            </label>
            <input
              id="edit-username"
              type="text"
              className="form-input"
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              required
              data-testid="edit-username-input"
            />
          </div>

          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label className="form-label" htmlFor="edit-email" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Mail size={16} />
              Email *
            </label>
            <input
              id="edit-email"
              type="email"
              className="form-input"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              required
              data-testid="edit-email-input"
            />
          </div>

          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label className="form-label" htmlFor="edit-password" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Key size={16} />
              Nueva Contraseña
            </label>
            <input
              id="edit-password"
              type="text"
              className="form-input"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              placeholder="Dejar vacío para no cambiar"
              minLength={6}
              data-testid="edit-password-input"
            />
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.25rem' }}>
              Dejar vacío si no desea cambiar la contraseña. Mínimo 6 caracteres.
            </p>
          </div>

          {usuario?.role === 'EMISOR_RECLAMO' && (
            <div className="form-group" style={{ marginBottom: '1.5rem' }}>
              <label className="form-label" htmlFor="edit-linea" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <MapPin size={16} />
                Línea Asignada
              </label>
              <select
                id="edit-linea"
                className="form-select"
                value={formData.linea_asignada}
                onChange={(e) => setFormData({...formData, linea_asignada: e.target.value})}
                data-testid="edit-linea-select"
              >
                <option value="">Sin asignar</option>
                {LINEAS.map(linea => (
                  <option key={linea} value={linea}>Línea {linea}</option>
                ))}
              </select>
            </div>
          )}

          <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
            <button 
              type="submit" 
              className="btn-primary"
              disabled={saving}
              style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
              data-testid="save-user-btn"
            >
              <Save size={18} />
              {saving ? 'Guardando...' : 'Guardar Cambios'}
            </button>
            <button 
              type="button"
              className="btn-secondary"
              onClick={onClose}
              style={{ flex: 1 }}
              data-testid="cancel-edit-btn"
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditarUsuarioModal;
