import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Volume2, VolumeX } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '@/context/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Create notification sound using Web Audio API
const createNotificationSound = () => {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  
  const playSound = () => {
    // Create oscillator for a pleasant notification chime
    const oscillator1 = audioContext.createOscillator();
    const oscillator2 = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator1.connect(gainNode);
    oscillator2.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // First tone - higher pitch
    oscillator1.frequency.setValueAtTime(880, audioContext.currentTime); // A5
    oscillator1.type = 'sine';
    
    // Second tone - lower pitch (harmony)
    oscillator2.frequency.setValueAtTime(659.25, audioContext.currentTime); // E5
    oscillator2.type = 'sine';
    
    // Volume envelope - fade in and out
    gainNode.gain.setValueAtTime(0, audioContext.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.05);
    gainNode.gain.linearRampToValueAtTime(0.2, audioContext.currentTime + 0.15);
    gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + 0.4);
    
    oscillator1.start(audioContext.currentTime);
    oscillator2.start(audioContext.currentTime);
    oscillator1.stop(audioContext.currentTime + 0.4);
    oscillator2.stop(audioContext.currentTime + 0.4);
    
    // Second chime after short delay
    setTimeout(() => {
      const osc3 = audioContext.createOscillator();
      const osc4 = audioContext.createOscillator();
      const gain2 = audioContext.createGain();
      
      osc3.connect(gain2);
      osc4.connect(gain2);
      gain2.connect(audioContext.destination);
      
      osc3.frequency.setValueAtTime(1046.5, audioContext.currentTime); // C6
      osc3.type = 'sine';
      osc4.frequency.setValueAtTime(783.99, audioContext.currentTime); // G5
      osc4.type = 'sine';
      
      gain2.gain.setValueAtTime(0, audioContext.currentTime);
      gain2.gain.linearRampToValueAtTime(0.25, audioContext.currentTime + 0.05);
      gain2.gain.linearRampToValueAtTime(0, audioContext.currentTime + 0.5);
      
      osc3.start(audioContext.currentTime);
      osc4.start(audioContext.currentTime);
      osc3.stop(audioContext.currentTime + 0.5);
      osc4.stop(audioContext.currentTime + 0.5);
    }, 150);
  };
  
  return playSound;
};

const NotificationBell = () => {
  const navigate = useNavigate();
  const { getAuthHeaders, user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(() => {
    const saved = localStorage.getItem('notificationSound');
    return saved !== 'false'; // Default to true
  });
  const previousUnreadCount = useRef(0);
  const playSound = useRef(null);
  const isInitialLoad = useRef(true);

  // Initialize audio on first user interaction
  useEffect(() => {
    const initAudio = () => {
      if (!playSound.current) {
        playSound.current = createNotificationSound();
      }
      document.removeEventListener('click', initAudio);
    };
    document.addEventListener('click', initAudio);
    return () => document.removeEventListener('click', initAudio);
  }, []);

  const loadNotifications = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/notifications`, {
        headers: getAuthHeaders()
      });
      setNotifications(response.data.slice(0, 5)); // Only show last 5
    } catch (error) {
      console.error('Error loading notifications:', error);
    }
  }, [getAuthHeaders]);

  const loadUnreadCount = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/notifications/unread/count`, {
        headers: getAuthHeaders()
      });
      const newCount = response.data.count;
      
      // Play sound if there are NEW unread notifications (not on initial load)
      if (!isInitialLoad.current && newCount > previousUnreadCount.current && soundEnabled && playSound.current) {
        playSound.current();
        
        // Also show browser notification if permitted
        if (Notification.permission === 'granted') {
          new Notification('Nueva notificación', {
            body: 'Tienes una nueva notificación en el sistema de reclamos',
            icon: '/favicon.ico'
          });
        }
      }
      
      previousUnreadCount.current = newCount;
      setUnreadCount(newCount);
      isInitialLoad.current = false;
    } catch (error) {
      console.error('Error loading unread count:', error);
    }
  }, [getAuthHeaders, soundEnabled]);

  useEffect(() => {
    // Request notification permission
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }
    
    loadNotifications();
    loadUnreadCount();
    
    // Check for new notifications every 10 seconds (faster for real-time feel)
    const interval = setInterval(() => {
      loadUnreadCount();
      loadNotifications();
    }, 10000);

    return () => clearInterval(interval);
  }, [loadNotifications, loadUnreadCount]);

  const toggleSound = () => {
    const newValue = !soundEnabled;
    setSoundEnabled(newValue);
    localStorage.setItem('notificationSound', newValue.toString());
    
    // Play test sound when enabling
    if (newValue && playSound.current) {
      playSound.current();
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await axios.patch(`${API}/notifications/${notificationId}/read`, {}, {
        headers: getAuthHeaders()
      });
      loadNotifications();
      loadUnreadCount();
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const handleNotificationClick = (notification) => {
    markAsRead(notification.id);
    navigate(`/reclamo/${notification.reclamo_id}`);
    setShowDropdown(false);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Ahora';
    if (diffMins < 60) return `Hace ${diffMins} min`;
    if (diffMins < 1440) return `Hace ${Math.floor(diffMins / 60)} h`;
    return `Hace ${Math.floor(diffMins / 1440)} d`;
  };

  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      {/* Sound toggle button */}
      <button
        onClick={toggleSound}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '0.5rem',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: soundEnabled ? '#059669' : '#94a3b8',
          transition: 'all 0.2s'
        }}
        title={soundEnabled ? 'Sonido activado' : 'Sonido desactivado'}
        data-testid="sound-toggle-btn"
      >
        {soundEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
      </button>

      <button
        className="nav-button"
        onClick={() => setShowDropdown(!showDropdown)}
        style={{ position: 'relative' }}
        data-testid="notification-bell-btn"
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span
            style={{
              position: 'absolute',
              top: '-4px',
              right: '-4px',
              background: '#dc2626',
              color: 'white',
              borderRadius: '50%',
              width: '20px',
              height: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.7rem',
              fontWeight: '700',
              animation: unreadCount > 0 ? 'pulse 2s infinite' : 'none'
            }}
            data-testid="notification-count"
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {showDropdown && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 10px)',
            right: 0,
            width: '380px',
            background: 'white',
            borderRadius: '12px',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.15)',
            zIndex: 1000,
            maxHeight: '400px',
            overflow: 'auto'
          }}
          data-testid="notification-dropdown"
        >
          <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '600', color: '#1e3a5f' }}>Notificaciones</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: soundEnabled ? '#059669' : '#94a3b8' }}>
              {soundEnabled ? <Volume2 size={14} /> : <VolumeX size={14} />}
              <span>{soundEnabled ? 'Sonido ON' : 'Sonido OFF'}</span>
            </div>
          </div>

          {notifications.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
              No hay notificaciones
            </div>
          ) : (
            <div>
              {notifications.map((notif) => (
                <div
                  key={notif.id}
                  onClick={() => handleNotificationClick(notif)}
                  style={{
                    padding: '1rem 1.25rem',
                    borderBottom: '1px solid #f1f5f9',
                    cursor: 'pointer',
                    background: notif.is_read ? 'white' : '#eff6ff',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                  onMouseLeave={(e) => e.currentTarget.style.background = notif.is_read ? 'white' : '#eff6ff'}
                  data-testid={`notification-${notif.id}`}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontSize: '0.9rem', color: '#1e293b', marginBottom: '0.25rem', fontWeight: notif.is_read ? '400' : '600' }}>
                        {notif.message}
                      </p>
                      <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
                        {notif.reclamo_numero}
                      </p>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8', whiteSpace: 'nowrap', marginLeft: '0.5rem' }}>
                      {formatDate(notif.created_at)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }
      `}</style>
    </div>
  );
};

export default NotificationBell;
