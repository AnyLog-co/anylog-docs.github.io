// ── Sidebar toggle (mobile) ───────────────────────────────────────────────────
const toggle = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('sidebar-overlay');

function openSidebar() {
  sidebar.classList.add('open');
  overlay.classList.add('open');
  toggle.setAttribute('aria-expanded', 'true');
}
function closeSidebar() {
  sidebar.classList.remove('open');
  overlay.classList.remove('open');
  toggle.setAttribute('aria-expanded', 'false');
}

if (toggle) toggle.addEventListener('click', () =>
  sidebar.classList.contains('open') ? closeSidebar() : openSidebar()
);
if (overlay) overlay.addEventListener('click', closeSidebar);

// ── Sidebar nav filter ────────────────────────────────────────────────────────
const sidebarSearch = document.getElementById('doc-search');
if (sidebarSearch) {
  sidebarSearch.addEventListener('input', () => {
    const q = sidebarSearch.value.toLowerCase().trim();
    document.querySelectorAll('.nav-section ul li').forEach(li => {
      const text = li.textContent.toLowerCase();
      li.style.display = (!q || text.includes(q)) ? '' : 'none';
    });
    document.querySelectorAll('.nav-section').forEach(section => {
      const visible = [...section.querySelectorAll('li')].some(li => li.style.display !== 'none');
      section.style.display = visible ? '' : 'none';
    });
  });
}

// ── Dark / light mode ─────────────────────────────────────────────────────────
const themeToggle = document.getElementById('theme-toggle');
const root = document.documentElement;

// apply saved preference immediately (overrides the default "light" in HTML attr)
const savedTheme = localStorage.getItem('theme') || 'light';
root.setAttribute('data-theme', savedTheme);

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  });
}

// ── Full-text search (Lunr.js) ────────────────────────────────────────────────
let lunrIndex = null;
let searchDocs = [];

const headerSearchInput   = document.getElementById('header-search-input');
const headerSearchResults = document.getElementById('header-search-results');

// only load the index if the search input exists on this page
if (headerSearchInput) {
  fetch('/search-index.json')
    .then(r => r.json())
    .then(data => {
      searchDocs = data;
      lunrIndex = lunr(function () {
        this.ref('url');
        this.field('title', { boost: 10 });
        this.field('content');
        data.forEach(doc => this.add(doc));
      });
    })
    .catch(() => {
      // search-index.json not yet built — fail silently
    });

  headerSearchInput.addEventListener('input', () => {
    const q = headerSearchInput.value.trim();

    if (!q || !lunrIndex) {
      headerSearchResults.hidden = true;
      return;
    }

    let hits = [];
    try {
      hits = lunrIndex.search(q + '*').slice(0, 8);
    } catch (_) {
      // lunr throws on some partial queries — ignore
    }

    if (!hits.length) {
      headerSearchResults.hidden = true;
      return;
    }

    headerSearchResults.innerHTML = hits.map(({ ref }) => {
      const doc = searchDocs.find(d => d.url === ref);
      if (!doc) return '';
      return `<a href="${doc.url}"><span class="result-title">${doc.title}</span></a>`;
    }).join('');

    headerSearchResults.hidden = false;
  });

  // close results when clicking outside the search widget
  document.addEventListener('click', e => {
    if (!e.target.closest('.header-search')) {
      headerSearchResults.hidden = true;
    }
  });

  // close on Escape
  headerSearchInput.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      headerSearchResults.hidden = true;
      headerSearchInput.blur();
    }
  });
}
// ── Search ────────────────────────────────────────────────
(function () {
  const input = document.getElementById('search-input');
  const results = document.getElementById('search-results');
  if (!input || !results) return;

  let idx, docs;

  // Fetch and build the lunr index once
  fetch('/search-index.json')
    .then(r => r.json())
    .then(data => {
      docs = data;
      idx = lunr(function () {
        this.ref('url');
        this.field('title', { boost: 10 });
        this.field('content');
        data.forEach(d => this.add(d));
      });
    });

  input.addEventListener('input', function () {
    const q = this.value.trim();
    results.innerHTML = '';
    if (!q || !idx) { results.classList.remove('active'); return; }

    const hits = idx.search(q + '*');   // trailing wildcard for partial match
    if (!hits.length) {
      results.innerHTML = '<li style="padding:.6rem 1rem;color:var(--text-muted,#64748b)">No results</li>';
    } else {
      hits.slice(0, 8).forEach(hit => {
        const doc = docs.find(d => d.url === hit.ref);
        if (!doc) return;
        const li = document.createElement('li');
        li.innerHTML = `<a href="${doc.url}"><strong>${doc.title}</strong><span>${doc.content.slice(0, 80)}…</span></a>`;
        results.appendChild(li);
      });
    }
    results.classList.add('active');
  });

  // Close results when clicking outside
  document.addEventListener('click', e => {
    if (!input.contains(e.target) && !results.contains(e.target)) {
      results.classList.remove('active');
    }
  });
})();