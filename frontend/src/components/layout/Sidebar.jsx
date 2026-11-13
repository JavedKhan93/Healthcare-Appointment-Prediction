import React from 'react';
import {
  LayoutDashboard,
  ClipboardList,
  Activity,
  BarChart3,
  Database,
  ShieldCheck,
} from 'lucide-react';

export default function Sidebar({ isOpen, onClose, activeSection, onNavigate, healthStatus }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'appointments', label: 'Appointments', icon: ClipboardList },
    { id: 'predict', label: 'Prediction Desk', icon: Activity },
    { id: 'model-results', label: 'Model Results', icon: BarChart3 },
    { id: 'data-quality', label: 'Data Quality', icon: Database },
    { id: 'responsible-use', label: 'Responsible Use', icon: ShieldCheck },
  ];

  const handleNavClick = (e, id) => {
    e.preventDefault();
    if (onNavigate) {
      onNavigate(id);
    }
    if (onClose) {
      onClose();
    }
  };

  const isApiOnline = healthStatus?.status === 'operational';
  const isModelReady = Boolean(healthStatus?.model_artifact?.loaded);
  const isDbConnected = Boolean(healthStatus?.mongodb?.connected);

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`} aria-label="Main Navigation">
      <div className="sidebar-brand">
        <div className="sidebar-brand-title">MORROW</div>
        <div className="sidebar-brand-subtitle">Appointment Insights</div>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Main Menu</div>
        {navItems.map((item) => {
          const IconComponent = item.icon;
          const isActive = activeSection === item.id;
          return (
            <a
              key={item.id}
              href={`#${item.id}`}
              className={`nav-link ${isActive ? 'active' : ''}`}
              onClick={(e) => handleNavClick(e, item.id)}
            >
              <IconComponent size={18} strokeWidth={1.75} />
              <span>{item.label}</span>
            </a>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status-title">System Status</div>

        <div className="sidebar-status-item">
          <span className={`status-dot ${isApiOnline ? 'online' : 'offline'}`} />
          <span>{isApiOnline ? 'API Online' : 'API Offline'}</span>
        </div>

        <div className="sidebar-status-item">
          <span className={`status-dot ${isModelReady ? 'online' : 'offline'}`} />
          <span>{isModelReady ? 'Model Ready' : 'Model Unavailable'}</span>
        </div>

        <div className="sidebar-status-item">
          <span className={`status-dot ${isDbConnected ? 'online' : 'offline'}`} />
          <span>{isDbConnected ? 'Database Connected' : 'Database Offline'}</span>
        </div>

        <div className="sidebar-status-note">Synthetic data prototype</div>
      </div>
    </aside>
  );
}

