// Main application controller

const App = (() => {
  function qs(sel)  { return document.querySelector(sel); }
  function qsa(sel) { return [...document.querySelectorAll(sel)]; }

  // ── Page routing ─────────────────────────────────────────────────────────────
  function showPage(name) {
    qsa('.page').forEach(p => p.classList.remove('active'));
    qsa('.nav-item[data-page]').forEach(n => n.classList.remove('active'));
    const page = document.getElementById(`page-${name}`);
    const nav  = document.querySelector(`.nav-item[data-page="${name}"]`);
    if (page) page.classList.add('active');
    if (nav)  nav.classList.add('active');
    if (name === 'cards')     loadCardsPage();
    if (name === 'hard')      loadHardPage();
    if (name === 'pinned')    loadPinnedPage();
    if (name === 'topics')    loadTopicsPage();
    if (name === 'due')       loadDuePage();
    if (name === 'sessions')  loadSessionsPage();
    if (name === 'resources') loadResourcesPage();
    if (name === 'import')    { resetImportLog(); loadResourceStatus(); }
  }

  // ── Sidebar stats ─────────────────────────────────────────────────────────────
  async function refreshStats() {
    try {
      const s = await API.deckStats();
      qs('#stat-total').textContent    = s.total_cards;
      qs('#stat-hard').textContent     = s.hard_cards;
      qs('#stat-pinned').textContent   = s.pinned_cards;
      qs('#stat-unseen').textContent   = s.unseen_cards;
      qs('#stat-sessions').textContent = s.total_sessions;
      const hardBadge   = qs('#hard-badge');
      const pinnedBadge = qs('#pinned-badge');
      if (hardBadge)   { hardBadge.textContent   = s.hard_cards   || ''; hardBadge.style.display   = s.hard_cards   ? '' : 'none'; }
      if (pinnedBadge) { pinnedBadge.textContent = s.pinned_cards || ''; pinnedBadge.style.display = s.pinned_cards ? '' : 'none'; }
    } catch (_) {}
  }

  // ── Summary bar helper ────────────────────────────────────────────────────────
  function renderSummary(stats) {
    const pct = stats.seen > 0 ? Math.round(stats.correct / stats.seen * 100) : 0;
    return `
      <div class="section-summary">
        <div class="summary-stat">
          <div class="summary-val amber">${stats.total}</div>
          <div class="summary-lbl">Cards</div>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-stat">
          <div class="summary-val coral">${stats.hard}</div>
          <div class="summary-lbl">Hard</div>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-stat">
          <div class="summary-val teal">${stats.seen > 0 ? pct + '%' : '—'}</div>
          <div class="summary-lbl">Confident</div>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-stat">
          <div class="summary-val" style="color:var(--muted)">${stats.total - stats.seen}</div>
          <div class="summary-lbl">Unseen</div>
        </div>
      </div>`;
  }

  // ── Cards page ────────────────────────────────────────────────────────────────
  async function loadCardsPage(filter = {}) {
    const grid = qs('#cards-grid');
    grid.innerHTML = '<div class="empty-state"><span class="spinner"></span></div>';
    try {
      const cards = await API.cards(filter);
      renderCardsGrid(cards, filter);
    } catch (e) {
      grid.innerHTML = `<div class="empty-state log-err">Failed to load cards: ${e.message}</div>`;
    }
  }

  function renderCardsGrid(cards, filter = {}) {
    const grid = qs('#cards-grid');
    if (!cards.length) {
      grid.innerHTML = '<div class="empty-state">No cards match this filter.</div>';
      return;
    }
    const showConfident = !!filter.hard;
    const showUnpin     = !!filter.pinned;
    grid.innerHTML = cards.map(c => `
      <div class="card-item" data-id="${c.id}">
        <div class="card-item-q">${esc(c.question)}</div>
        <div class="card-item-a">${esc(c.answer)}</div>
        <div class="card-item-meta">
          ${c.tags.map(t => `<span class="tag">${t.name}</span>`).join('')}
          ${c.pinned        ? `<span class="diff-badge" style="background:var(--amber-bg);color:var(--amber);border:1px solid var(--amber-bd)">📌 pinned</span>` : ''}
          ${c.times_hard > 0 ? `<span class="diff-badge diff-hard">hard ×${c.times_hard}</span>` : ''}
          ${c.times_seen > 0 && c.times_hard === 0 ? `<span class="diff-badge diff-ok">✓ ${c.times_correct}/${c.times_seen}</span>` : ''}
        </div>
        <div class="card-item-actions">
          <button class="card-action-btn ${c.pinned ? 'unpin-btn' : ''}" onclick="App.handlePin(${c.id}, this)">
            ${c.pinned ? '📌 Unpin' : '📌 Pin'}
          </button>
          ${c.times_hard > 0 ? `<button class="card-action-btn confident-btn" onclick="App.handleResetHard(${c.id}, this)">✓ Mark Confident</button>` : ''}
        </div>
      </div>
    `).join('');
  }

  async function handlePin(cardId, btn) {
    try {
      const updated = await API.pinCard(cardId);
      const item = btn.closest('.card-item');
      // re-render just the actions and meta for this card
      const meta    = item.querySelector('.card-item-meta');
      const actions = item.querySelector('.card-item-actions');
      // toggle pin badge
      const pinBadge = meta.querySelector('[style*="pinned"]');
      if (updated.pinned) {
        if (!pinBadge) meta.insertAdjacentHTML('afterbegin', `<span class="diff-badge" style="background:var(--amber-bg);color:var(--amber);border:1px solid var(--amber-bd)">📌 pinned</span>`);
        btn.textContent = '📌 Unpin';
        btn.classList.add('unpin-btn');
      } else {
        if (pinBadge) pinBadge.remove();
        btn.textContent = '📌 Pin';
        btn.classList.remove('unpin-btn');
      }
      refreshStats();
    } catch (e) { console.error(e); }
  }

  async function handleResetHard(cardId, btn) {
    try {
      await API.resetHard(cardId);
      const item = btn.closest('.card-item');
      item.querySelector('.diff-badge.diff-hard')?.remove();
      btn.remove();
      refreshStats();
    } catch (e) { console.error(e); }
  }

  // ── Hard page ─────────────────────────────────────────────────────────────────
  async function loadHardPage() {
    const container = qs('#hard-container');
    container.innerHTML = '<div class="empty-state"><span class="spinner"></span></div>';
    try {
      const cards = await API.hardQueue();
      const seen    = cards.reduce((a, c) => a + (c.times_seen > 0 ? 1 : 0), 0);
      const correct = cards.reduce((a, c) => a + c.times_correct, 0);
      const stats   = { total: cards.length, hard: cards.length, seen, correct };
      let html = renderSummary(stats);
      if (!cards.length) {
        html += '<div class="empty-state">No hard cards — great work!</div>';
      } else {
        html += `<div class="cards-grid">${cards.map(c => `
          <div class="card-item" data-id="${c.id}">
            <div class="card-item-q">${esc(c.question)}</div>
            <div class="card-item-a">${esc(c.answer)}</div>
            <div class="card-item-meta">
              <span class="diff-badge diff-hard">hard ×${c.times_hard}</span>
              ${c.times_seen > 0 ? `<span class="diff-badge" style="background:var(--surface2);color:var(--muted);border:1px solid var(--border)">${c.times_correct}/${c.times_seen} correct</span>` : ''}
            </div>
            <div class="card-item-actions">
              <button class="card-action-btn confident-btn" onclick="App.handleResetHardRefresh(${c.id}, this, 'hard')">✓ Mark Confident</button>
              <button class="card-action-btn ${c.pinned ? 'unpin-btn' : ''}" onclick="App.handlePin(${c.id}, this)">
                ${c.pinned ? '📌 Unpin' : '📌 Pin'}
              </button>
            </div>
          </div>`).join('')}</div>`;
      }
      container.innerHTML = html;
    } catch (e) {
      container.innerHTML = `<div class="empty-state log-err">${e.message}</div>`;
    }
  }

  async function handleResetHardRefresh(cardId, btn, page) {
    try {
      await API.resetHard(cardId);
      refreshStats();
      if (page === 'hard')   loadHardPage();
      if (page === 'pinned') loadPinnedPage();
    } catch (e) { console.error(e); }
  }

  // ── Pinned page ───────────────────────────────────────────────────────────────
  async function loadPinnedPage() {
    const container = qs('#pinned-container');
    container.innerHTML = '<div class="empty-state"><span class="spinner"></span></div>';
    try {
      const cards = await API.pinnedQueue();
      const seen    = cards.reduce((a, c) => a + (c.times_seen > 0 ? 1 : 0), 0);
      const correct = cards.reduce((a, c) => a + c.times_correct, 0);
      const hard    = cards.reduce((a, c) => a + (c.times_hard > 0 ? 1 : 0), 0);
      const stats   = { total: cards.length, hard, seen, correct };
      let html = renderSummary(stats);
      if (!cards.length) {
        html += '<div class="empty-state">No pinned cards yet.<br>During study, press <strong>P</strong> to pin a card.</div>';
      } else {
        html += `<div class="cards-grid">${cards.map(c => `
          <div class="card-item" data-id="${c.id}">
            <div class="card-item-q">${esc(c.question)}</div>
            <div class="card-item-a">${esc(c.answer)}</div>
            <div class="card-item-meta">
              <span class="diff-badge" style="background:var(--amber-bg);color:var(--amber);border:1px solid var(--amber-bd)">📌 pinned</span>
              ${c.times_hard > 0 ? `<span class="diff-badge diff-hard">hard ×${c.times_hard}</span>` : ''}
              ${c.times_seen > 0 ? `<span class="diff-badge diff-ok">${c.times_correct}/${c.times_seen} correct</span>` : ''}
            </div>
            <div class="card-item-actions">
              <button class="card-action-btn unpin-btn" onclick="App.handleUnpinRefresh(${c.id}, this)">📌 Unpin</button>
              ${c.times_hard > 0 ? `<button class="card-action-btn confident-btn" onclick="App.handleResetHardRefresh(${c.id}, this, 'pinned')">✓ Mark Confident</button>` : ''}
            </div>
          </div>`).join('')}</div>`;
      }
      container.innerHTML = html;
    } catch (e) {
      container.innerHTML = `<div class="empty-state log-err">${e.message}</div>`;
    }
  }

  async function handleUnpinRefresh(cardId, btn) {
    try {
      await API.pinCard(cardId);
      refreshStats();
      loadPinnedPage();
    } catch (e) { console.error(e); }
  }

  // ── Topics page ───────────────────────────────────────────────────────────────
  async function loadTopicsPage() {
    const grid = qs('#topics-grid');
    grid.innerHTML = '<div class="empty-state"><span class="spinner"></span></div>';

    try {
      const [folders, mastery, forecast] = await Promise.all([
        API.folders(),
        API.masteryStats(),
        API.forecast(),
      ]);

      if (!folders.length) {
        grid.innerHTML = '<div class="empty-state">No folders found — import cards first.</div>';
        return;
      }

      // Build forecast banner
      const forecastHtml = `
        <div class="forecast-bar">
          <div class="forecast-item">
            <span class="forecast-val ${forecast.due_today > 0 ? 'amber' : 'teal'}">${forecast.due_today}</span>
            <span class="forecast-lbl">due today</span>
          </div>
          <div class="forecast-item">
            <span class="forecast-val coral">${forecast.overdue}</span>
            <span class="forecast-lbl">overdue</span>
          </div>
          <div class="forecast-item">
            <span class="forecast-val">${forecast.avg_daily_cards}</span>
            <span class="forecast-lbl">cards/day avg</span>
          </div>
          <div class="forecast-item">
            <span class="forecast-val teal">${forecast.days_to_clear !== null ? forecast.days_to_clear === 0 ? '✓' : forecast.days_to_clear + 'd' : '—'}</span>
            <span class="forecast-lbl">to clear queue</span>
          </div>
          ${forecast.due_today > 0
            ? `<button class="btn btn-primary btn-sm" onclick="document.getElementById('btn-study-due').click()" style="margin-left:auto">▶ Study Due (${forecast.due_today})</button>`
            : '<span style="margin-left:auto;font-size:.72rem;color:var(--teal)">✓ Queue clear</span>'}
        </div>`;

      // Merge mastery data into folders
      const masteryMap = {};
      mastery.forEach(m => { masteryMap[m.folder] = m; });

      grid.innerHTML = forecastHtml + '<div class="topics-grid-inner">' + folders.map(f => {
        const m      = masteryMap[f.folder] || {};
        const pct    = m.mastery ?? f.pct_confident;
        const barPct = Math.min(pct, 100);
        const trend  = m.trend;
        const trendIcon = trend === 'up' ? '<span style="color:var(--teal)">↑</span>'
                        : trend === 'down' ? '<span style="color:var(--coral)">↓</span>'
                        : '';
        const dueCount = m.due_count ?? 0;
        return `
        <div class="topic-card">
          <div class="topic-card-header">
            <div class="topic-card-name">${esc(f.folder)}</div>
            <div class="topic-card-total">${f.total} cards</div>
          </div>
          <div class="topic-progress-bar">
            <div class="topic-progress-fill" style="width:${barPct}%"></div>
          </div>
          <div class="topic-stats">
            <div class="topic-stat"><span class="dot dot-g"></span><strong>${pct > 0 ? pct.toFixed(1) + '%' : '—'}</strong>&nbsp;mastery ${trendIcon}</div>
            <div class="topic-stat"><span class="dot dot-h"></span><strong>${f.hard}</strong>&nbsp;hard</div>
            <div class="topic-stat"><span class="dot dot-s"></span><strong>${f.total - f.seen}</strong>&nbsp;unseen</div>
            ${dueCount > 0 ? `<div class="topic-stat" style="color:var(--amber)">⏰&nbsp;<strong>${dueCount}</strong>&nbsp;due</div>` : ''}
          </div>
          <div class="topic-card-actions">
            <button class="btn btn-primary btn-sm" onclick="App.studyFolder('${esc(f.folder)}')">Study All</button>
            ${dueCount > 0 ? `<button class="btn btn-sm" style="background:var(--amber-bg);color:var(--amber);border:1px solid var(--amber-bd)" onclick="App.studyFolderDue('${esc(f.folder)}')">Due (${dueCount})</button>` : ''}
            ${f.hard > 0 ? `<button class="btn btn-danger btn-sm" onclick="App.studyFolderHard('${esc(f.folder)}')">Hard (${f.hard})</button>` : ''}
          </div>
        </div>`;
      }).join('') + '</div>';

    } catch (e) {
      grid.innerHTML = `<div class="empty-state log-err">Failed: ${e.message}</div>`;
    }
  }

  async function studyFolderDue(folder) {
    try {
      const all = await API.folderQueue(folder);
      const now = new Date();
      const due = all.filter(c => !c.due_date || new Date(c.due_date) <= now);
      if (!due.length) { alert(`No due cards in ${folder}`); return; }
      Study.start(due, `due:${folder}`);
    } catch (e) { alert(`Failed: ${e.message}`); }
  }

  async function studyFolder(folder) {
    try {
      const cards = await API.folderQueue(folder);
      if (!cards.length) { alert(`No cards found in folder: ${folder}`); return; }
      Study.start(cards, `folder:${folder}`);
    } catch (e) { alert(`Failed to load folder: ${e.message}`); }
  }

  async function studyFolderHard(folder) {
    try {
      const all  = await API.folderQueue(folder);
      const hard = all.filter(c => c.times_hard > 0);
      if (!hard.length) { alert(`No hard cards in ${folder}`); return; }
      Study.start(hard, `hard:${folder}`);
    } catch (e) { alert(`Failed to load folder: ${e.message}`); }
  }

  // ── Study starters ────────────────────────────────────────────────────────────
  async function studyAll() {
    const cards = await API.weightedQueue();
    if (!cards.length) { alert('No cards yet — import some first.'); return; }
    Study.start(cards, 'all');
  }

  async function studyDue() {
    const cards = await API.dueQueue();
    if (!cards.length) { alert('Nothing due for review today — great work!'); return; }
    Study.start(cards, 'due');
  }
  async function studyHard() {
    const cards = await API.hardQueue();
    if (!cards.length) { alert('No hard cards yet — study a full deck first.'); return; }
    Study.start(cards, 'hard');
  }
  async function studyPinned() {
    const cards = await API.pinnedQueue();
    if (!cards.length) { alert('No pinned cards yet — pin some during study with P.'); return; }
    Study.start(cards, 'pinned');
  }
  async function studyUnseen() {
    const cards = await API.cards({ unseen: true });
    if (!cards.length) { alert('No unseen cards — you have reviewed everything!'); return; }
    Study.start(cards, 'unseen');
  }

  // ── Due today page ───────────────────────────────────────────────────────────
  async function loadDuePage() {
    // Due today redirects to study
    studyDue();
  }

  // ── Topics page (with mastery) ────────────────────────────────────────────────
  // ── Resources page ────────────────────────────────────────────────────────────
  let allResources = [];

  async function loadResourcesPage() {
    const container = qs('#resources-list');
    container.innerHTML = '<div class="empty-state"><span class="spinner"></span></div>';
    try {
      allResources = await API.resources();
      await populateTopicFilter();
      renderResourcesPage(allResources);
    } catch (e) {
      container.innerHTML = `<div class="res-empty">Failed to load resources: ${e.message}</div>`;
    }
  }

  async function populateTopicFilter() {
    const sel = qs('#res-topic-filter');
    if (!sel) return;
    try {
      const topics = await API.get('/api/resources/topics');
      sel.innerHTML = '<option value="">All topics</option>' +
        topics.map(t => `<option value="${t}">${t.replace(/_/g, ' ')}</option>`).join('');
    } catch (_) {}
  }

  function renderResourcesPage(resources) {
    const container = qs('#resources-list');
    if (!resources.length) {
      container.innerHTML = '<div class="res-empty">No resources yet.<br>Go to Import to load the bundled seed or generate with DuckDuckGo.</div>';
      return;
    }
    const grouped = {};
    for (const r of resources) {
      if (!grouped[r.topic]) grouped[r.topic] = [];
      grouped[r.topic].push(r);
    }
    container.innerHTML = Object.entries(grouped)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([topic, items]) => `
        <div class="topic-group">
          <div class="topic-heading">
            ${topic.replace(/_/g, ' ')}
            <span class="topic-count">${items.length}</span>
          </div>
          ${items.map(r => `
            <div class="res-card" onclick="window.open('${esc(r.url)}','_blank','noopener')">
              <div class="res-card-body">
                <div class="res-card-title">${esc(r.title)}</div>
                ${r.description ? `<div class="res-card-desc">${esc(r.description)}</div>` : ''}
                <div class="res-card-url">${esc(r.url)}</div>
              </div>
              <div class="res-card-arrow">→</div>
            </div>
          `).join('')}
        </div>
      `).join('');
  }

  function filterResources() {
    const query  = (qs('#res-search')?.value  || '').toLowerCase();
    const topic  = (qs('#res-topic-filter')?.value || '');
    const filtered = allResources.filter(r => {
      const matchTopic = !topic || r.topic === topic;
      const matchQuery = !query ||
        r.title.toLowerCase().includes(query) ||
        (r.description || '').toLowerCase().includes(query) ||
        r.url.toLowerCase().includes(query) ||
        r.topic.includes(query);
      return matchTopic && matchQuery;
    });
    renderResourcesPage(filtered);
  }

  // ── Import page ───────────────────────────────────────────────────────────────
  function resetImportLog() {
    qs('#import-log').innerHTML = '<span class="log-dim">Waiting for files…</span>';
    qsa('.zone.loaded').forEach(z => z.classList.remove('loaded'));
  }

  function log(msg, cls = '') {
    const el   = qs('#import-log');
    const line = document.createElement('div');
    line.className   = cls;
    line.textContent = msg;
    if (el.querySelector('.log-dim')) el.innerHTML = '';
    el.appendChild(line);
    el.scrollTop = el.scrollHeight;
  }

  async function handleFileImport(input) {
    const files = [...input.files].filter(f => /\.(md|txt)$/i.test(f.name));
    if (!files.length) { log('No .md files found in selection.', 'log-err'); return; }
    log(`Uploading ${files.length} file${files.length > 1 ? 's' : ''}…`, 'log-dim');
    try {
      const result = await API.importFiles(files);
      log(`✓ Imported ${result.imported} cards, skipped ${result.skipped} duplicates`, 'log-ok');
      result.errors.forEach(e => log(`⚠ ${e}`, 'log-err'));
      input.closest('.zone')?.classList.add('loaded');
      const hint = input.closest('.zone')?.querySelector('.zone-hint');
      if (hint) hint.textContent = `✓ ${result.imported} cards imported`;
      refreshStats();
    } catch (e) { log(`✗ Import failed: ${e.message}`, 'log-err'); }
  }

  async function handleFolderImport(input) {
    const files = [...input.files].filter(f => /\.(md|txt)$/i.test(f.name));
    if (!files.length) { log('No .md files found.', 'log-err'); return; }
    log(`Uploading ${files.length} files from folder…`, 'log-dim');
    try {
      const result = await API.importFiles(files);
      log(`✓ Imported ${result.imported} cards from ${files.length} files, skipped ${result.skipped} duplicates`, 'log-ok');
      result.errors.forEach(e => log(`⚠ ${e}`, 'log-err'));
      input.closest('.zone')?.classList.add('loaded');
      const hint = input.closest('.zone')?.querySelector('.zone-hint');
      if (hint) hint.textContent = `✓ ${result.imported} cards from ${files.length} files`;
      refreshStats();
    } catch (e) { log(`✗ Import failed: ${e.message}`, 'log-err'); }
  }

  async function scanFolder() {
    log('Scanning mounted /cards directory…', 'log-dim');
    const btn = qs('#btn-scan');
    btn.disabled = true;
    try {
      const result = await API.scanFolder();
      log(`✓ Found ${result.files_found} files — imported ${result.imported}, skipped ${result.skipped} duplicates`, 'log-ok');
      result.errors.forEach(e => log(`⚠ ${e}`, 'log-err'));
      refreshStats();
    } catch (e) { log(`✗ Scan failed: ${e.message}`, 'log-err'); }
    btn.disabled = false;
  }

  // ── Resource status + generation ──────────────────────────────────────────────
  async function loadResourceStatus() {
    const container = qs('#res-methods');
    if (!container) return;
    container.innerHTML = '<span class="log-dim" style="font-size:.75rem">Checking availability…</span>';
    try {
      const status = await API.resourceStatus();
      container.innerHTML = renderResourceMethods(status);
      container.querySelector('#btn-res-seed')?.addEventListener('click',   () => runGeneration('seed'));
      container.querySelector('#btn-res-ddg')?.addEventListener('click',    () => runGeneration('ddg'));
      container.querySelector('#btn-res-ollama')?.addEventListener('click', () => runGeneration('ollama'));
      container.querySelector('#btn-res-claude')?.addEventListener('click', () => runGeneration('claude'));
      container.querySelector('#btn-res-auto')?.addEventListener('click',   () => runGeneration('auto'));
    } catch (e) {
      container.innerHTML = `<span class="log-err" style="font-size:.75rem">Could not load status: ${e.message}</span>`;
    }
  }

  function renderResourceMethods(status) {
    const badge = (ok, msg) => ok
      ? `<span class="res-badge res-badge-ok">✓ ${msg}</span>`
      : `<span class="res-badge res-badge-off">✗ ${msg}</span>`;
    return `
      <div class="res-method-grid">
        <div class="res-method-card res-method-primary">
          <div class="res-method-header"><span class="res-method-icon">📦</span><span class="res-method-name">Bundled Resources</span>${badge(true, 'Always available')}</div>
          <div class="res-method-desc">Pre-curated security links shipped with FlashDeck. No internet required.</div>
          <button class="btn btn-ghost btn-sm" id="btn-res-seed">Load Seed Resources</button>
        </div>
        <div class="res-method-card">
          <div class="res-method-header"><span class="res-method-icon">🔍</span><span class="res-method-name">DuckDuckGo Search</span>${badge(true, 'No key required')}</div>
          <div class="res-method-desc">Searches DDG for resources based on your card topics. Prioritises PortSwigger, HackTricks, OWASP.</div>
          <button class="btn btn-ghost btn-sm" id="btn-res-ddg">Search DuckDuckGo</button>
        </div>
        <div class="res-method-card ${!status.ollama.available ? 'res-method-dim' : ''}">
          <div class="res-method-header"><span class="res-method-icon">🦙</span><span class="res-method-name">Ollama (Local LLM)</span>${badge(status.ollama.available, status.ollama.message)}</div>
          <div class="res-method-desc">Uses a local model — fully offline, no API key.${!status.ollama.available ? ` <code style="font-family:var(--mono);font-size:.68em">docker compose --profile ollama up</code>` : ''}</div>
          <button class="btn btn-ghost btn-sm" id="btn-res-ollama" ${!status.ollama.available ? 'disabled' : ''}>Generate with Ollama</button>
        </div>
        <div class="res-method-card ${!status.claude.available ? 'res-method-dim' : ''}">
          <div class="res-method-header"><span class="res-method-icon">✦</span><span class="res-method-name">Claude API</span>${badge(status.claude.available, status.claude.available ? 'API key set' : 'No key set')}</div>
          <div class="res-method-desc">${!status.claude.available ? 'Set <code style="font-family:var(--mono);font-size:.68em">ANTHROPIC_API_KEY</code> in docker-compose.yml to enable.' : 'Analyses your cards and generates tailored resources.'}</div>
          <button class="btn btn-ghost btn-sm" id="btn-res-claude" ${!status.claude.available ? 'disabled' : ''}>Generate with Claude</button>
        </div>
      </div>
      <div style="margin-top:1rem;display:flex;align-items:center;gap:.75rem;">
        <button class="btn btn-primary btn-sm" id="btn-res-auto">⚡ Auto — Use Best Available</button>
        <span style="font-size:.7rem;color:var(--dim)">Tries Claude → Ollama → DDG, always loads seed as baseline</span>
      </div>`;
  }

  async function runGeneration(method) {
    qsa('#res-methods button').forEach(b => b.disabled = true);
    const label = { seed: 'seed resources', ddg: 'DuckDuckGo', ollama: 'Ollama', claude: 'Claude', auto: 'auto' }[method];
    log(`Running resource generation via ${label}…`, 'log-dim');
    try {
      let result;
      if (method === 'seed')   result = await API.post('/api/resources/seed', {});
      if (method === 'ddg')    result = await API.post('/api/resources/generate/ddg', {});
      if (method === 'ollama') result = await API.post('/api/resources/generate/ollama', {});
      if (method === 'claude') result = await API.post('/api/resources/generate/claude', {});
      if (method === 'auto')   result = await API.post('/api/resources/generate', {});
      if (method === 'auto') {
        log(`✓ ${result.message} (method: ${result.method}, total: ${result.total})`, 'log-ok');
      } else if (method === 'seed') {
        log(`✓ Loaded ${result.added} resources across ${result.topics?.length || '?'} topics`, 'log-ok');
      } else {
        const count = Array.isArray(result) ? result.length : result.generated;
        log(`✓ Generated ${count} resources via ${label}`, 'log-ok');
      }
    } catch (e) {
      let msg = e.message;
      try { msg = JSON.parse(e.message).detail || msg; } catch (_) {}
      log(`✗ ${label} failed: ${msg}`, 'log-err');
    }
    await loadResourceStatus();
  }

  // ── Resource panel (during study) ─────────────────────────────────────────────
  function openResPanel(resources) {
    const grouped = {};
    for (const r of resources) {
      if (!grouped[r.topic]) grouped[r.topic] = [];
      grouped[r.topic].push(r);
    }
    let html = '';
    if (!Object.keys(grouped).length) {
      html = '<p class="empty-state">No resources matched this card yet.<br>Visit Import → load seed or search DuckDuckGo.</p>';
    } else {
      for (const [topic, items] of Object.entries(grouped)) {
        html += `<div class="res-group"><div class="res-group-label">${topic.replace(/_/g, ' ')}</div>`;
        for (const r of items) {
          html += `<div class="res-item" onclick="window.open('${r.url}','_blank','noopener')">
            <div class="res-item-title">${r.title}</div>
            ${r.description ? `<div class="res-item-desc">${r.description}</div>` : ''}
            <div class="res-item-url">${r.url}</div>
          </div>`;
        }
        html += '</div>';
      }
    }
    qs('#res-list').innerHTML = html;
    qs('#res-panel').classList.add('open');
    qs('#backdrop').classList.add('open');
  }

  function closeResPanel() {
    qs('#res-panel').classList.remove('open');
    qs('#backdrop').classList.remove('open');
  }

  // ── Sessions page ─────────────────────────────────────────────────────────────
  async function loadSessionsPage() {
    const list = qs('#sessions-list');
    list.innerHTML = '<div class="empty-state"><span class="spinner"></span></div>';
    try {
      const sessions = await API.sessions();
      if (!sessions.length) { list.innerHTML = '<div class="empty-state">No study sessions yet.</div>'; return; }
      list.innerHTML = sessions.map(s => `
        <div class="session-row">
          <div class="session-date">${new Date(s.started_at).toLocaleString()}</div>
          <span class="session-mode">${s.mode}</span>
          <div class="session-nums">
            <span class="session-num"><span class="dot dot-s"></span>${s.total} cards</span>
            <span class="session-num"><span class="dot dot-g"></span>${s.got}</span>
            <span class="session-num"><span class="dot dot-h"></span>${s.hard}</span>
          </div>
        </div>
      `).join('');
    } catch (e) { list.innerHTML = `<div class="empty-state log-err">${e.message}</div>`; }
  }

  // ── Helpers ───────────────────────────────────────────────────────────────────
  function esc(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  // ── Create card ──────────────────────────────────────────────────────────────
  async function createCard() {
    const q = qs('#new-question').value.trim();
    const a = qs('#new-answer').value.trim();
    const n = qs('#new-notes').value.trim();
    if (!q || !a) { alert('Question and answer are required.'); return; }
    try {
      await API.createCard({ question: q, answer: a, notes: n || null });
      qs('#new-question').value = '';
      qs('#new-answer').value   = '';
      qs('#new-notes').value    = '';
      document.getElementById('create-modal').classList.remove('open');
      refreshStats();
      loadCardsPage();
    } catch (e) { alert(`Failed to create card: ${e.message}`); }
  }

  // ── Init ──────────────────────────────────────────────────────────────────────
  function init() {
    qsa('.nav-item[data-page]').forEach(item =>
      item.addEventListener('click', () => showPage(item.dataset.page)));

    qs('#btn-study-all')?.addEventListener('click',    studyAll);
    qs('#btn-study-hard')?.addEventListener('click',   studyHard);
    qs('#btn-study-pinned')?.addEventListener('click', studyPinned);
    qs('#btn-study-due')?.addEventListener('click', studyDue);
    qs('#btn-study-unseen')?.addEventListener('click', studyUnseen);

    qs('#card-scene')?.addEventListener('click', () => Study.flip());
    qs('#btn-got')?.addEventListener('click',   () => Study.mark('got'));
    qs('#btn-hard')?.addEventListener('click',  () => Study.mark('hard'));
    qs('#btn-skip')?.addEventListener('click',  () => Study.mark('skip'));
    qs('#btn-pin')?.addEventListener('click',   () => Study.togglePin());

    qs('#res-notify')?.addEventListener('click', () => openResPanel(qs('#res-notify')._resources || []));
    qs('#backdrop')?.addEventListener('click',  closeResPanel);
    qs('#res-close')?.addEventListener('click', closeResPanel);

    qs('#file-cards')?.addEventListener('change',  e => handleFileImport(e.target));
    qs('#file-folder')?.addEventListener('change', e => handleFolderImport(e.target));
    qs('#btn-scan')?.addEventListener('click', scanFolder);

    qs('#btn-restart-hard')?.addEventListener('click', Study.restartHard);
    qs('#btn-new-deck')?.addEventListener('click', () => {
      qs('.complete-overlay').classList.add('hidden');
      showPage('cards');
    });

    qs('#cards-search')?.addEventListener('input', e => {
      const q = e.target.value.trim();
      loadCardsPage(q ? { q } : {});
    });
    qs('#btn-filter-hard')?.addEventListener('click',   () => loadCardsPage({ hard: true }));
    qs('#btn-filter-pinned')?.addEventListener('click', () => loadCardsPage({ pinned: true }));
    qs('#btn-filter-all')?.addEventListener('click',    () => loadCardsPage());

    qs('#res-search')?.addEventListener('input', filterResources);
    qs('#res-topic-filter')?.addEventListener('change', filterResources);

    document.addEventListener('keydown', e => {
      // Never trigger shortcuts when typing in any input or textarea
      const tag = e.target.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || e.target.isContentEditable) return;

      if (e.key === '?') { document.getElementById('keys-modal')?.classList.add('open'); return; }

      const page = document.querySelector('.page.active')?.id;
      if (page !== 'page-study') return;

      if (e.code === 'Space' || e.code === 'Enter') { e.preventDefault(); Study.flip(); }
      if (e.key === 'g' || e.key === 'G') Study.mark('got');
      if (e.key === 'h' || e.key === 'H') Study.mark('hard');
      if (e.key === 's' || e.key === 'S') Study.mark('skip');
      if (e.key === 'p' || e.key === 'P') Study.togglePin();
      if (e.key === 'e' || e.key === 'E') Study.openEdit();
      if (e.key === 'n' || e.key === 'N') Study.redoNow();
      if (e.key === 'l' || e.key === 'L') Study.redoLater();
      if (e.key === 'ArrowLeft')  { e.preventDefault(); Study.prev(); }
      if (e.key === 'ArrowRight') { e.preventDefault(); Study.next(); }
      if (e.key === 'r' || e.key === 'R') {
        const n = qs('#res-notify');
        if (!n.classList.contains('hidden')) openResPanel(n._resources || []);
      }
    });

    showPage('cards');
    refreshStats();
  }

  return {
    init, showPage, refreshStats, createCard,
    handlePin, handleResetHard, handleResetHardRefresh, handleUnpinRefresh,
    studyFolder, studyFolderHard, studyFolderDue,
  };
})();

document.addEventListener('DOMContentLoaded', App.init);
window.App = App;
