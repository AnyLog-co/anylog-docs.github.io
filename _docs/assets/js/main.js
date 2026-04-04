// Sidebar toggle (mobile)
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

// Simple client-side search filter on sidebar links
const searchInput = document.getElementById('doc-search');
if (searchInput) {
  searchInput.addEventListener('input', () => {
    const q = searchInput.value.toLowerCase().trim();
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
