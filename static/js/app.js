/**
 * Dubai Real Estate Intelligence Agent — Main Frontend JS
 * Shared utilities available on every page.
 */

// ── Number formatting ──────────────────────────────────────────────────────
function fmtNum(n) {
  if (n === null || n === undefined || isNaN(n)) return '0';
  const num = Math.abs(Number(n));
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(num >= 10_000_000 ? 1 : 2) + 'M';
  if (num >= 1_000)     return (num / 1_000).toFixed(num >= 10_000 ? 0 : 1) + 'K';
  return Number(n).toLocaleString('en-AE', {maximumFractionDigits: 2});
}

function fmtCurrency(n, cur = 'AED') {
  return cur + ' ' + fmtNum(n);
}

// ── Toast notifications ────────────────────────────────────────────────────
let toastTimer = null;

function showToast(msg, type = 'info') {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className   = `toast ${type} show`;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.classList.remove('show'); }, 3500);
}

// ── Sidebar toggle (mobile) ────────────────────────────────────────────────
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', e => {
  const sidebar = document.getElementById('sidebar');
  const toggle  = document.querySelector('.sidebar-toggle');
  if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains('open')
      && !sidebar.contains(e.target) && e.target !== toggle) {
    sidebar.classList.remove('open');
  }
});

// ── Chart.js global defaults ────────────────────────────────────────────────
if (typeof Chart !== 'undefined') {
  Chart.defaults.color          = '#8892a2';
  Chart.defaults.borderColor    = 'rgba(255,255,255,.06)';
  Chart.defaults.font.family    = "'Inter', sans-serif";
  Chart.defaults.font.size      = 12;
  Chart.defaults.plugins.tooltip.backgroundColor = '#1a2942';
  Chart.defaults.plugins.tooltip.borderColor     = 'rgba(212,168,67,.3)';
  Chart.defaults.plugins.tooltip.borderWidth      = 1;
  Chart.defaults.plugins.tooltip.titleColor       = '#d4a843';
  Chart.defaults.plugins.tooltip.bodyColor        = '#e2e8f0';
  Chart.defaults.plugins.tooltip.padding          = 10;
  Chart.defaults.plugins.legend.labels.color      = '#e2e8f0';
}

// ── Utility: format date string ─────────────────────────────────────────────
function fmtDate(dt) {
  if (!dt) return '—';
  try {
    return new Date(dt).toLocaleDateString('en-AE', {
      year: 'numeric', month: 'short', day: 'numeric'
    });
  } catch { return dt; }
}

// ── Utility: escape HTML (prevents XSS) ─────────────────────────────────────
function escHtml(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// ── Utility: debounce ────────────────────────────────────────────────────────
function debounce(fn, delay = 300) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}

// ── AED currency formatter shorthand ────────────────────────────────────────
function aed(n) { return 'AED ' + fmtNum(n); }

// ── Animate number counting up ───────────────────────────────────────────────
function animateCount(el, target, duration = 800) {
  const start = 0;
  const step  = (target - start) / (duration / 16);
  let   curr  = start;
  const interval = setInterval(() => {
    curr += step;
    if (curr >= target) { curr = target; clearInterval(interval); }
    el.textContent = Math.floor(curr).toLocaleString();
  }, 16);
}

// ── On DOM ready ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Animate KPI numbers if present
  document.querySelectorAll('.kpi-val[data-count]').forEach(el => {
    animateCount(el, parseInt(el.dataset.count, 10));
  });
});
