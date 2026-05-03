(function() {
  var ICONS = {
    light: 'fa-sun',
    dark: 'fa-moon',
    system: 'fa-circle-half-stroke'
  };
  var LABELS = {
    light: 'Light theme (click for dark)',
    dark: 'Dark theme (click for system)',
    system: 'System theme (click for light)'
  };
  var ORDER = ['light', 'dark', 'system'];

  function getTheme() {
    try {
      var t = localStorage.getItem('theme');
      if (t === 'light' || t === 'dark') return t;
    } catch (e) {}
    return 'system';
  }

  function setTheme(t) {
    try {
      if (t === 'system') {
        localStorage.removeItem('theme');
        document.documentElement.removeAttribute('data-theme');
      } else {
        localStorage.setItem('theme', t);
        document.documentElement.setAttribute('data-theme', t);
      }
    } catch (e) {}
    updateButton();
  }

  function updateButton() {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;
    var t = getTheme();
    var icon = btn.querySelector('i');
    if (icon) {
      icon.className = 'fas ' + ICONS[t];
    }
    btn.setAttribute('aria-label', LABELS[t]);
    btn.setAttribute('title', LABELS[t]);
  }

  function init() {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      var current = getTheme();
      var next = ORDER[(ORDER.indexOf(current) + 1) % ORDER.length];
      setTheme(next);
    });
    updateButton();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
