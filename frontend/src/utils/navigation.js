/**
 * Section Navigation Helper for MORROW.
 * Loads the target section fresh in React, updates the window hash,
 * and scrolls smoothly to the top of the newly arrived page.
 */

export function scrollToSection(sectionId) {
  if (!sectionId) return;
  if (typeof window !== 'undefined') {
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, '', `#${sectionId}`);
    }
    window.dispatchEvent(new CustomEvent('morrow-navigate', { detail: sectionId }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}


