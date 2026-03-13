/**
 * Study History Navigation
 * Fixed bar below header - completely independent of MkDocs
 */

(function() {
  const STORAGE_KEY = 'study-history';
  const POSITION_KEY = 'study-history-position';
  const MAX_HISTORY = 20;

  function isStudyPage() {
    return window.location.pathname.includes('/studies/') &&
           !window.location.pathname.endsWith('/studies/') &&
           !window.location.pathname.endsWith('/studies/index.html');
  }

  function getCurrentStudy() {
    const path = window.location.pathname;
    const title = document.querySelector('h1')?.textContent ||
                  document.querySelector('.md-content h1')?.textContent ||
                  document.title.split(' - ')[0];

    const match = path.match(/\/studies\/([^\/]+)/);
    const slug = match ? match[1].replace(/\.html?$/, '').replace(/\/$/, '') : null;

    return { path, slug, title: title.trim(), timestamp: Date.now() };
  }

  function getHistory() {
    try {
      return JSON.parse(sessionStorage.getItem(STORAGE_KEY)) || [];
    } catch (e) { return []; }
  }

  function getPosition() {
    try {
      const pos = sessionStorage.getItem(POSITION_KEY);
      return pos !== null ? parseInt(pos) : -1;
    } catch (e) { return -1; }
  }

  function saveHistory(history) {
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(history)); } catch (e) {}
  }

  function savePosition(pos) {
    try { sessionStorage.setItem(POSITION_KEY, pos.toString()); } catch (e) {}
  }

  function addToHistory(study) {
    if (!study.slug) return;

    let history = getHistory();
    let position = getPosition();

    if (position >= 0 && position < history.length && history[position].slug === study.slug) {
      return;
    }

    if (position >= 0 && position < history.length - 1) {
      history = history.slice(0, position + 1);
    }

    if (history.length > 0 && history[history.length - 1].slug === study.slug) {
      return;
    }

    history.push(study);

    if (history.length > MAX_HISTORY) {
      history = history.slice(-MAX_HISTORY);
    }

    saveHistory(history);
    savePosition(history.length - 1);
    updateUI();
  }

  function goBack() {
    const history = getHistory();
    let position = getPosition();
    if (position > 0) {
      position--;
      savePosition(position);
      window.location.href = history[position].path;
    }
  }

  function goForward() {
    const history = getHistory();
    let position = getPosition();
    if (position < history.length - 1) {
      position++;
      savePosition(position);
      window.location.href = history[position].path;
    }
  }

  function goToPosition(pos) {
    const history = getHistory();
    if (pos >= 0 && pos < history.length) {
      savePosition(pos);
      window.location.href = history[pos].path;
    }
  }

  // Create elements once and keep them
  let navBar = null;
  let popup = null;

  function ensureUI() {
    if (!navBar) {
      // Create the fixed nav bar
      navBar = document.createElement('div');
      navBar.id = 'study-nav-bar';

      // Create with inline styles to avoid any CSS conflicts
      navBar.style.cssText = `
        position: fixed;
        top: 48px;
        right: 10px;
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 6px 10px;
        background: #4051b5;
        border-radius: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        z-index: 100;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      `;

      navBar.innerHTML = `
        <button id="study-nav-back" style="
          display: flex; align-items: center; justify-content: center;
          background: transparent; border: none; cursor: pointer;
          padding: 6px; border-radius: 50%; color: white;
        " title="Back" disabled>
          <svg viewBox="0 0 24 24" width="18" height="18" style="display:block;">
            <path fill="white" d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
          </svg>
        </button>
        <button id="study-nav-forward" style="
          display: flex; align-items: center; justify-content: center;
          background: transparent; border: none; cursor: pointer;
          padding: 6px; border-radius: 50%; color: white;
        " title="Forward" disabled>
          <svg viewBox="0 0 24 24" width="18" height="18" style="display:block;">
            <path fill="white" d="M8.59 16.59L10 18l6-6-6-6-1.41 1.41L13.17 12z"/>
          </svg>
        </button>
        <button id="study-nav-history" style="
          display: flex; align-items: center; justify-content: center;
          background: transparent; border: none; cursor: pointer;
          padding: 6px; border-radius: 50%; color: white; position: relative;
        " title="History">
          <svg viewBox="0 0 24 24" width="18" height="18" style="display:block;">
            <path fill="white" d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.25 2.52.77-1.28-3.52-2.09V8z"/>
          </svg>
          <span id="study-nav-count" style="
            position: absolute; top: 0; right: 0;
            background: #7c4dff; color: white;
            font-size: 9px; font-weight: bold;
            min-width: 14px; height: 14px;
            border-radius: 7px; display: none;
            align-items: center; justify-content: center;
          "></span>
        </button>
      `;

      document.body.appendChild(navBar);

      // Event listeners
      document.getElementById('study-nav-back').onclick = goBack;
      document.getElementById('study-nav-forward').onclick = goForward;
      document.getElementById('study-nav-history').onclick = togglePopup;

      // Hover effects
      navBar.querySelectorAll('button').forEach(btn => {
        btn.onmouseenter = () => { if (!btn.disabled) btn.style.background = 'rgba(255,255,255,0.2)'; };
        btn.onmouseleave = () => { btn.style.background = 'transparent'; };
      });
    }

    if (!popup) {
      popup = document.createElement('div');
      popup.id = 'study-history-popup';
      popup.style.cssText = `
        position: fixed;
        display: none;
        top: 90px;
        right: 10px;
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        min-width: 280px;
        max-width: 380px;
        max-height: 50vh;
        overflow: hidden;
        z-index: 101;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      `;

      popup.innerHTML = `
        <div style="display:flex; align-items:center; padding:12px 14px; border-bottom:1px solid #eee; background:#f5f5f5;">
          <span style="font-weight:600; flex:1;">Study History</span>
          <button id="popup-clear" style="
            background:transparent; border:1px solid #999; color:#666;
            padding:4px 10px; border-radius:4px; cursor:pointer; font-size:12px; margin-right:8px;
          ">Clear</button>
          <button id="popup-close" style="
            background:none; border:none; font-size:20px; cursor:pointer; color:#666;
          ">&times;</button>
        </div>
        <div id="popup-list" style="overflow-y:auto; max-height:calc(50vh - 50px);"></div>
      `;

      document.body.appendChild(popup);

      document.getElementById('popup-close').onclick = hidePopup;
      document.getElementById('popup-clear').onclick = () => {
        sessionStorage.removeItem(STORAGE_KEY);
        sessionStorage.removeItem(POSITION_KEY);
        hidePopup();
        updateUI();
      };

      // Close on outside click
      document.addEventListener('click', (e) => {
        if (popup.style.display !== 'none' && !popup.contains(e.target) && !navBar.contains(e.target)) {
          hidePopup();
        }
      });

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') hidePopup();
      });
    }

    // Make sure they're in the DOM
    if (!document.body.contains(navBar)) {
      document.body.appendChild(navBar);
    }
    if (!document.body.contains(popup)) {
      document.body.appendChild(popup);
    }
  }

  function togglePopup() {
    if (popup.style.display === 'none') {
      showPopup();
    } else {
      hidePopup();
    }
  }

  function showPopup() {
    const history = getHistory();
    const position = getPosition();
    const list = document.getElementById('popup-list');

    if (history.length === 0) {
      list.innerHTML = '<div style="padding:20px; text-align:center; color:#666;">No study history yet.</div>';
    } else {
      list.innerHTML = history.slice().reverse().map((study, idx) => {
        const realIdx = history.length - 1 - idx;
        const isCurrent = realIdx === position;
        return `
          <a href="#" data-pos="${realIdx}" style="
            display:flex; align-items:center; gap:10px;
            padding:10px 14px; text-decoration:none; color:#333;
            border-left:3px solid ${isCurrent ? '#7c4dff' : 'transparent'};
            background:${isCurrent ? 'rgba(124,77,255,0.1)' : 'transparent'};
            font-weight:${isCurrent ? '500' : 'normal'};
          ">
            <span style="color:#7c4dff; font-size:10px; width:14px;">${isCurrent ? '▶' : '○'}</span>
            <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${study.title}</span>
          </a>
        `;
      }).join('');

      list.querySelectorAll('a').forEach(a => {
        a.onmouseenter = () => { if (!a.style.background.includes('124,77,255')) a.style.background = 'rgba(124,77,255,0.05)'; };
        a.onmouseleave = () => { if (!a.style.background.includes('0.1')) a.style.background = 'transparent'; };
        a.onclick = (e) => {
          e.preventDefault();
          goToPosition(parseInt(a.dataset.pos));
        };
      });
    }

    popup.style.display = 'block';
  }

  function hidePopup() {
    if (popup) popup.style.display = 'none';
  }

  function updateUI() {
    ensureUI();

    const history = getHistory();
    const position = getPosition();

    const backBtn = document.getElementById('study-nav-back');
    const fwdBtn = document.getElementById('study-nav-forward');
    const countEl = document.getElementById('study-nav-count');

    if (backBtn) {
      backBtn.disabled = position <= 0;
      backBtn.style.opacity = position <= 0 ? '0.4' : '1';
    }
    if (fwdBtn) {
      fwdBtn.disabled = position >= history.length - 1;
      fwdBtn.style.opacity = position >= history.length - 1 ? '0.4' : '1';
    }
    if (countEl) {
      if (history.length > 0) {
        countEl.textContent = history.length;
        countEl.style.display = 'flex';
      } else {
        countEl.style.display = 'none';
      }
    }
  }

  function init() {
    ensureUI();
    if (isStudyPage()) {
      addToHistory(getCurrentStudy());
    }
    updateUI();
  }

  // Handle navigation
  if (typeof document$ !== 'undefined') {
    document$.subscribe(() => {
      setTimeout(() => {
        ensureUI();
        if (isStudyPage()) {
          addToHistory(getCurrentStudy());
        }
        updateUI();
      }, 100);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
