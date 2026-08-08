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

// ── Keep the current page visible in the sidebar ────────────────────────────
(function () {
  if (!sidebar) return;

  const activeLink = sidebar.querySelector('.nav-page-link.active[aria-current="page"]');
  if (!activeLink) return;

  window.requestAnimationFrame(() => {
    const sidebarRect = sidebar.getBoundingClientRect();
    const activeRect = activeLink.getBoundingClientRect();
    const isAbove = activeRect.top < sidebarRect.top + 72;
    const isBelow = activeRect.bottom > sidebarRect.bottom - 24;

    if (isAbove || isBelow) {
      activeLink.scrollIntoView({
        block: 'center',
        inline: 'nearest',
      });
    }
  });
})();

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

// ── Documentation images ─────────────────────────────────────────────────────
(function () {
  const content = document.querySelector('.doc-content');
  if (!content) return;

  function replaceBrokenImage(img) {
    if (!img || img.dataset.fallbackApplied === 'true') return;
    img.dataset.fallbackApplied = 'true';

    const fallback = document.createElement('div');
    fallback.className = 'doc-image-fallback';

    const label = document.createElement('strong');
    label.textContent = img.alt || 'Image unavailable';
    fallback.appendChild(label);

    const src = img.getAttribute('src');
    if (src) {
      const path = document.createElement('div');
      path.textContent = src;
      fallback.appendChild(path);
    }

    img.replaceWith(fallback);
  }

  content.querySelectorAll('img').forEach(img => {
    img.loading = img.loading || 'lazy';
    img.decoding = 'async';
    img.addEventListener('error', () => replaceBrokenImage(img), { once: true });

    if (img.complete && img.naturalWidth === 0) {
      replaceBrokenImage(img);
    }
  });
})();

// ── Copy buttons for code blocks ────────────────────────────────────────────
(function () {
  const content = document.querySelector('.doc-content');
  if (!content) return;
  const baseUrl = (window.siteBaseUrl || '').replace(/\/$/, '');

  function iconUrl(path) {
    return `${baseUrl}${path}`;
  }

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }

    const helper = document.createElement('textarea');
    helper.value = text;
    helper.setAttribute('readonly', '');
    helper.style.position = 'absolute';
    helper.style.left = '-9999px';
    document.body.appendChild(helper);
    helper.select();
    document.execCommand('copy');
    helper.remove();
  }

  function codeTextFor(pre) {
    const code = pre.querySelector('code');
    return (code ? code.textContent : pre.textContent || '').replace(/\s+$/, '');
  }

  function blockContainerFor(pre) {
    const highlighted = pre.closest('.highlighter-rouge, .highlight');
    return highlighted || pre;
  }

  content.querySelectorAll('pre').forEach(pre => {
    if (pre.id === 'env-content') return;

    const container = blockContainerFor(pre);
    if (!container || container.querySelector('.doc-code-toolbar')) return;

    container.classList.add('doc-code-block');

    const toolbar = document.createElement('div');
    toolbar.className = 'doc-code-toolbar';

    const copyButton = document.createElement('button');
    copyButton.type = 'button';
    copyButton.className = 'doc-code-button copy-code-button';
    copyButton.setAttribute('aria-label', 'Copy code');
    copyButton.setAttribute('title', 'Copy code');
    copyButton.innerHTML = `
      <img src="${iconUrl('/assets/img/icons/copy-light.png')}" alt="" class="copy-icon theme-icon-light" />
      <img src="${iconUrl('/assets/img/icons/copy-dark.png')}" alt="" class="copy-icon theme-icon-dark" />
    `;

    copyButton.addEventListener('click', async () => {
      const text = codeTextFor(pre);
      if (!text) return;

      copyButton.classList.remove('failed');
      copyButton.classList.remove('copied');
      try {
        await copyText(text);
        copyButton.classList.add('copied');
      } catch (_) {
        copyButton.classList.add('failed');
      }

      window.setTimeout(() => {
        copyButton.classList.remove('copied');
        copyButton.classList.remove('failed');
      }, 1800);
    });

    toolbar.appendChild(copyButton);
    container.appendChild(toolbar);
  });
})();

// ── Full-text search ──────────────────────────────────────────────────────────
(function () {
  const searchTargets = [
    {
      input: document.getElementById('doc-search'),
      results: document.getElementById('doc-search-results'),
      itemTag: 'a',
      limit: 10,
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
  const baseUrl = (window.siteBaseUrl || '').replace(/\/$/, '');
  const indexReady = fetch(`${baseUrl}/search-index.json`)
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
