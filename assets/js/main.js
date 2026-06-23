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

// ── Full-text search ──────────────────────────────────────────────────────────
(function () {
  const searchTargets = [
    {
      input: document.getElementById('doc-search'),
      results: document.getElementById('doc-search-results'),
      itemTag: 'a',
      limit: 10,
      onQueryChange(query) {
        const nav = document.querySelector('.sidebar-nav');
        if (nav) nav.hidden = Boolean(query);
      },
    },
    {
      input: document.getElementById('header-search-input'),
      results: document.getElementById('header-search-results'),
      itemTag: 'a',
      limit: 8,
    },
    {
      input: document.getElementById('search-input'),
      results: document.getElementById('search-results'),
      itemTag: 'li',
      limit: 8,
      activeClass: 'active',
    },
  ].filter(target => target.input && target.results);

  if (!searchTargets.length || typeof lunr === 'undefined') return;

  let docs = [];
  let docsByUrl = new Map();
  let idx = null;
  let loadError = false;
  const indexReady = fetch('/search-index.json')
    .then(response => response.json())
    .then(data => {
      docs = data.map(doc => ({
        ...doc,
        content: doc.content || '',
      }));
      docsByUrl = new Map(docs.map(doc => [doc.url, doc]));
      idx = lunr(function () {
        this.ref('url');
        this.field('title', { boost: 12 });
        this.field('url', { boost: 3 });
        this.field('content');
        docs.forEach(doc => this.add(doc));
      });
    })
    .catch(() => {
      loadError = true;
    });

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, char => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    }[char]));
  }

  function queryTerms(query) {
    return query
      .toLowerCase()
      .replace(/[^a-z0-9_]+/g, ' ')
      .split(/\s+/)
      .filter(Boolean);
  }

  function searchQuery(terms) {
    return terms.map(term => `${term}*`).join(' ');
  }

  function manualMatches(terms) {
    if (!terms.length) return [];

    return docs
      .map(doc => {
        const haystack = `${doc.title} ${doc.url} ${doc.content}`.toLowerCase();
        const matched = terms.filter(term => haystack.includes(term));
        if (!matched.length) return null;

        const title = doc.title.toLowerCase();
        const score = matched.length * 2 + matched.filter(term => title.includes(term)).length * 3;
        return { ref: doc.url, score };
      })
      .filter(Boolean)
      .sort((a, b) => b.score - a.score);
  }

  function searchDocs(query) {
    const terms = queryTerms(query);
    if (!terms.length || !idx) return [];

    try {
      const hits = idx.search(searchQuery(terms));
      if (hits.length) return hits;
    } catch (_) {
      // Lunr can throw while the user is typing partial syntax-like input.
    }

    return manualMatches(terms);
  }

  function snippetFor(doc, terms) {
    const content = doc.content || '';
    const lowerContent = content.toLowerCase();
    const index = terms.reduce((best, term) => {
      const found = lowerContent.indexOf(term);
      return found === -1 || (best !== -1 && found >= best) ? best : found;
    }, -1);

    if (index === -1) {
      return content.slice(0, 140).trim();
    }

    const start = Math.max(0, index - 55);
    const end = Math.min(content.length, index + 120);
    const prefix = start > 0 ? '...' : '';
    const suffix = end < content.length ? '...' : '';
    return `${prefix}${content.slice(start, end).trim()}${suffix}`;
  }

  function resultHtml(doc, query) {
    const terms = queryTerms(query);
    const title = escapeHtml(doc.title || doc.url);
    const url = escapeHtml(doc.url);
    const snippet = escapeHtml(snippetFor(doc, terms));

    return `
      <a href="${url}">
        <span class="result-title">${title}</span>
        <span class="result-path">${url}</span>
        <span class="result-snippet">${snippet}</span>
      </a>
    `;
  }

  function setResultsVisible(target, visible) {
    if (target.activeClass) {
      target.results.classList.toggle(target.activeClass, visible);
    } else {
      target.results.hidden = !visible;
    }
  }

  function renderResults(target, hits, query) {
    if (!hits.length) {
      target.results.innerHTML = '<div class="search-empty">No results</div>';
      setResultsVisible(target, true);
      return;
    }

    target.results.innerHTML = hits.slice(0, target.limit).map(hit => {
      const doc = docsByUrl.get(hit.ref);
      if (!doc) return '';
      const html = resultHtml(doc, query);
      return target.itemTag === 'li' ? `<li>${html}</li>` : html;
    }).join('');
    setResultsVisible(target, true);
  }

  searchTargets.forEach(target => {
    target.input.addEventListener('input', () => {
      const query = target.input.value.trim();
      if (target.onQueryChange) target.onQueryChange(query);

      if (!query) {
        target.results.innerHTML = '';
        setResultsVisible(target, false);
        return;
      }

      if (loadError) {
        target.results.innerHTML = '<div class="search-empty">Search index unavailable</div>';
        setResultsVisible(target, true);
        return;
      }

      if (!idx) {
        target.results.innerHTML = '<div class="search-empty">Loading search...</div>';
        setResultsVisible(target, true);
        indexReady.then(() => renderResults(target, searchDocs(query), query));
        return;
      }

      renderResults(target, searchDocs(query), query);
    });

    target.input.addEventListener('keydown', event => {
      if (event.key === 'Escape') {
        target.input.value = '';
        target.input.dispatchEvent(new Event('input'));
        target.input.blur();
      }
    });
  });

  document.addEventListener('click', event => {
    searchTargets.forEach(target => {
      if (!target.input.contains(event.target) && !target.results.contains(event.target)) {
        setResultsVisible(target, false);
      }
    });
  });
})();
