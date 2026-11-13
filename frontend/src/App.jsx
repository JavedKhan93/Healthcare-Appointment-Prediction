import React, { useState, useEffect, useCallback } from 'react';
import { Menu, X } from 'lucide-react';
import Sidebar from './components/layout/Sidebar';
import Dashboard from './pages/Dashboard';
import AppointmentRegister from './pages/AppointmentRegister';
import PredictionDesk from './pages/PredictionDesk';
import ModelEvidence from './pages/ModelEvidence';
import DataQuality from './pages/DataQuality';
import ResponsibleUse from './pages/ResponsibleUse';
import { fetchHealth } from './api/api';

const SECTION_CONFIG = {
  overview: {
    id: 'overview',
    label: 'Overview',
    component: Dashboard,
    prev: null,
    next: 'appointments',
  },
  appointments: {
    id: 'appointments',
    label: 'Appointments',
    component: AppointmentRegister,
    prev: 'overview',
    next: 'predict',
  },
  predict: {
    id: 'predict',
    label: 'Prediction Desk',
    component: PredictionDesk,
    prev: 'appointments',
    next: 'model-results',
  },
  'model-results': {
    id: 'model-results',
    label: 'Model Results',
    component: ModelEvidence,
    prev: 'predict',
    next: 'data-quality',
  },
  'data-quality': {
    id: 'data-quality',
    label: 'Data Quality',
    component: DataQuality,
    prev: 'model-results',
    next: 'responsible-use',
  },
  'responsible-use': {
    id: 'responsible-use',
    label: 'Responsible Use',
    component: ResponsibleUse,
    prev: 'data-quality',
    next: null,
  },
};

const SECTION_IDS = Object.keys(SECTION_CONFIG);

const PATH_TO_SECTION = {
  '/': 'overview',
  '/appointments': 'appointments',
  '/predict': 'predict',
  '/model-evidence': 'model-results',
  '/model-results': 'model-results',
  '/data-quality': 'data-quality',
  '/responsible-use': 'responsible-use',
};

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [health, setHealth] = useState(null);
  const [activeSection, setActiveSection] = useState('overview');

  useEffect(() => {
    fetchHealth()
      .then((data) => setHealth(data))
      .catch(() => setHealth({ status: 'offline' }));
  }, []);

  const handleNavigate = useCallback((sectionId) => {
    if (!sectionId || !SECTION_CONFIG[sectionId]) return;
    setActiveSection(sectionId);
    setSidebarOpen(false);
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, '', `#${sectionId}`);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  // Listen to morrow-navigate custom events (e.g. from in-page buttons like Make a Prediction)
  useEffect(() => {
    const handleCustomNav = (e) => {
      if (e.detail && SECTION_CONFIG[e.detail]) {
        handleNavigate(e.detail);
      }
    };
    window.addEventListener('morrow-navigate', handleCustomNav);
    return () => window.removeEventListener('morrow-navigate', handleCustomNav);
  }, [handleNavigate]);

  // Sync section from URL hash or path on initial load and popstate
  useEffect(() => {
    const syncFromUrl = () => {
      const hash = window.location.hash.replace('#', '');
      const pathTarget = PATH_TO_SECTION[window.location.pathname];
      const target = SECTION_IDS.includes(hash)
        ? hash
        : pathTarget && pathTarget !== 'overview'
        ? pathTarget
        : null;

      if (target && SECTION_CONFIG[target]) {
        setActiveSection(target);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    };

    syncFromUrl();
    window.addEventListener('hashchange', syncFromUrl);
    window.addEventListener('popstate', syncFromUrl);
    return () => {
      window.removeEventListener('hashchange', syncFromUrl);
      window.removeEventListener('popstate', syncFromUrl);
    };
  }, []);

  const currentSection = SECTION_CONFIG[activeSection] || SECTION_CONFIG.overview;
  const CurrentComponent = currentSection.component;

  return (
    <div className="app-shell">
      {/* Mobile Topbar */}
      <div className="mobile-topbar">
        <span style={{ fontWeight: 700, letterSpacing: '0.08em', fontSize: '1.15rem' }}>
          MORROW
        </span>
        <button
          type="button"
          onClick={() => setSidebarOpen((o) => !o)}
          style={{
            background: 'none',
            border: '1px solid rgba(243,240,230,0.45)',
            color: '#F3F0E6',
            padding: '0.35rem 0.5rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            borderRadius: '3px',
          }}
          aria-label="Toggle Menu"
          aria-expanded={sidebarOpen}
        >
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Stable Left Navigation Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activeSection={activeSection}
        onNavigate={handleNavigate}
        healthStatus={health}
      />

      {/* Freshly Loaded Modern Hover-Page Main Content */}
      <main className="main-content">
        <article
          key={activeSection}
          id={activeSection}
          className="modern-hover-page"
          aria-label={currentSection.label}
        >
          <CurrentComponent onNavigate={handleNavigate} />

          {/* Modern Section Footer Pager */}
          <footer className="modern-section-pager">
            {currentSection.prev ? (
              <button
                type="button"
                className="btn btn-secondary pager-btn"
                onClick={() => handleNavigate(currentSection.prev)}
              >
                ← Previous: {SECTION_CONFIG[currentSection.prev].label}
              </button>
            ) : (
              <div />
            )}

            {currentSection.next ? (
              <button
                type="button"
                className="btn btn-primary pager-btn"
                onClick={() => handleNavigate(currentSection.next)}
              >
                Next: {SECTION_CONFIG[currentSection.next].label} →
              </button>
            ) : (
              <div />
            )}
          </footer>
        </article>
      </main>
    </div>
  );
}


