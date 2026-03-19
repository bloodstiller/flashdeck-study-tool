// Study mode controller — handles all in-session logic

const Study = (() => {
  // ── Session state ─────────────────────────────────────────────────────────────
  let sessionId   = null;
  let queue       = [];    // array of card objects (weighted order)
  let idx         = 0;     // current position in queue
  let history     = [];    // [{cardId, idx}] — visited positions for prev/next
  let historyPos  = -1;    // pointer into history
  let flipped     = false;
  let editing     = false;
  let stats       = { got: 0, hard: 0, skip: 0 };
  let streak      = 0;
  let bestStreak  = 0;
  let sessionHard = {};    // card_id -> hard count this session

  function qs(sel) { return document.querySelector(sel); }

  // ── Start session ─────────────────────────────────────────────────────────────
  async function start(cards, mode = 'all') {
    if (!cards.length) { alert('No cards to study.'); return; }

    try {
      const session = await API.createSession(mode);
      sessionId = session.id;
    } catch (e) { console.error('Could not create session:', e); }

    queue       = [...cards];
    idx         = 0;
    history     = [];
    historyPos  = -1;
    flipped     = false;
    editing     = false;
    streak      = 0;
    bestStreak  = 0;
    sessionHard = {};
    stats       = { got: 0, hard: 0, skip: 0 };

    App.showPage('study');
    qs('.complete-overlay').classList.add('hidden');
    render();
    updateStats();
  }

  // ── Render current card ───────────────────────────────────────────────────────
  function render() {
    if (idx >= queue.length) { showComplete(); return; }
    const card = queue[idx];

    flipped = false;
    editing = false;
    qs('#card-obj').classList.remove('flipped');
    qs('#edit-overlay')?.classList.add('hidden');
    qs('#card-q').textContent    = card.question;
    qs('#card-a').innerHTML      = mdToHtml(card.answer);
    qs('#card-notes').innerHTML  = card.notes ? `<div class="card-notes-block">${mdToHtml(card.notes)}</div>` : '';
    qs('#card-count').textContent = `Card ${idx + 1} of ${queue.length}`;
    qs('#prog').style.width       = `${(idx / queue.length) * 100}%`;
    qs('#card-hint').textContent  = 'Click card to reveal answer';
    qs('#tags-f').innerHTML = renderTags(card.tags || []);
    qs('#tags-b').innerHTML = renderTags(card.tags || []);

    // Due date indicator
    const dueEl = qs('#card-due');
    if (dueEl) {
      if (card.due_date) {
        const due = new Date(card.due_date);
        const now = new Date();
        const diffDays = Math.round((due - now) / 86400000);
        if (diffDays < 0) {
          dueEl.textContent = `Overdue by ${Math.abs(diffDays)}d`;
          dueEl.className = 'card-due overdue';
        } else if (diffDays === 0) {
          dueEl.textContent = 'Due today';
          dueEl.className = 'card-due due-today';
        } else {
          dueEl.textContent = `Due in ${diffDays}d`;
          dueEl.className = 'card-due due-future';
        }
        dueEl.style.display = '';
      } else {
        dueEl.style.display = 'none';
      }
    }

    setActions(false);
    updateNavButtons();
    qs('#res-notify').classList.add('hidden');
    qs('#streak-display').textContent = streak > 1 ? `🔥 ${streak}` : '';
  }

  // ── Flip card ─────────────────────────────────────────────────────────────────
  function flip() {
    if (idx >= queue.length) return;
    if (editing) return;
    const tag = document.activeElement?.tagName;
    if (tag === 'TEXTAREA' || tag === 'INPUT') return;

    flipped = !flipped;
    qs('#card-obj').classList.toggle('flipped', flipped);

    if (flipped) {
      qs('#card-hint').textContent = 'How did you do?';
      setActions(true);
      updatePinButton(queue[idx]);
      loadResources(queue[idx]);
      // Record in history
      history = history.slice(0, historyPos + 1);
      history.push(idx);
      historyPos = history.length - 1;
    } else {
      qs('#card-hint').textContent = 'Click card to reveal answer';
      setActions(false);
    }
    updateNavButtons();
  }

  // ── Redo immediately ──────────────────────────────────────────────────────────
  function redoNow() {
    flipped = false;
    qs('#card-obj').classList.remove('flipped');
    qs('#card-hint').textContent = 'Click card to reveal answer';
    setActions(false);
    qs('#res-notify').classList.add('hidden');
  }

  // ── Redo later (random insert) ────────────────────────────────────────────────
  function redoLater() {
    if (idx >= queue.length) return;
    const card = queue[idx];
    // Insert at a random position somewhere in the remaining queue
    const remaining = queue.length - idx - 1;
    if (remaining <= 0) {
      queue.push(card);
    } else {
      const insertAt = idx + 1 + Math.floor(Math.random() * remaining);
      queue.splice(insertAt, 0, card);
    }
    // Don't mark result — just advance
    idx++;
    flipped = false;
    render();
    updateStats();
  }

  // ── Navigation ────────────────────────────────────────────────────────────────
  function prev() {
    if (historyPos <= 0) return;
    historyPos--;
    idx = history[historyPos];
    flipped = false;
    render();
  }

  function next() {
    if (historyPos < history.length - 1) {
      // Move forward in existing history
      historyPos++;
      idx = history[historyPos];
      flipped = false;
      render();
    } else if (flipped) {
      // Already flipped — advance to next unseen card
      mark('skip');
    }
  }

  function updateNavButtons() {
    const prevBtn = qs('#btn-prev');
    const nextBtn = qs('#btn-next');
    if (prevBtn) prevBtn.disabled = historyPos <= 0;
    if (nextBtn) nextBtn.disabled = !flipped && historyPos >= history.length - 1;
  }

  // ── Mark result ───────────────────────────────────────────────────────────────
  async function mark(result) {
    if (idx >= queue.length) return;
    const card = queue[idx];

    if (result === 'got') {
      stats.got++;
      streak++;
      bestStreak = Math.max(bestStreak, streak);
    } else if (result === 'hard') {
      stats.hard++;
      streak = 0;
      sessionHard[card.id] = (sessionHard[card.id] || 0) + 1;
    } else {
      stats.skip++;
      streak = 0;
    }

    // Fire-and-forget to server (SM-2 runs server-side)
    if (sessionId) {
      API.recordResult(sessionId, card.id, result).catch(console.error);
    }

    updateStats();
    idx++;
    render();
  }

  // ── Pin toggle ────────────────────────────────────────────────────────────────
  async function togglePin() {
    if (idx >= queue.length) return;
    const card = queue[idx];
    try {
      const updated = await API.pinCard(card.id);
      card.pinned = updated.pinned;
      updatePinButton(card);
    } catch (e) { console.error('Pin failed:', e); }
  }

  function updatePinButton(card) {
    const btn = qs('#btn-pin');
    if (!btn) return;
    btn.classList.toggle('pinned', !!card.pinned);
    btn.innerHTML = card.pinned
      ? '📌 Pinned <span class="key">P</span>'
      : '📌 Pin <span class="key">P</span>';
  }

  // ── Inline edit ───────────────────────────────────────────────────────────────
  function openEdit() {
    if (idx >= queue.length) return;
    const card = queue[idx];
    editing = true;

    const overlay = qs('#edit-overlay');
    qs('#edit-question').value = card.question;
    qs('#edit-answer').value   = card.answer;
    qs('#edit-notes').value    = card.notes || '';
    overlay.classList.remove('hidden');
  }

  function closeEdit() {
    editing = false;
    qs('#edit-overlay')?.classList.add('hidden');
  }

  async function saveEdit() {
    if (idx >= queue.length) return;
    const card = queue[idx];
    const q = qs('#edit-question').value.trim();
    const a = qs('#edit-answer').value.trim();
    const n = qs('#edit-notes').value.trim();
    if (!q || !a) { alert('Question and answer cannot be empty.'); return; }

    try {
      const updated = await API.patch(`/api/cards/${card.id}`, { question: q, answer: a, notes: n || null });
      // Update card in queue
      queue[idx].question = updated.question;
      queue[idx].answer   = updated.answer;
      queue[idx].notes    = updated.notes;
      closeEdit();
      render();
      if (flipped) flip(); // re-flip to show updated answer
    } catch (e) { alert(`Save failed: ${e.message}`); }
  }

  // ── Resources notify ──────────────────────────────────────────────────────────
  async function loadResources(card) {
    try {
      const res = await API.resourcesForCard(card.id);
      if (res.length) {
        const n = qs('#res-notify');
        qs('#res-notify-txt').textContent = `${res.length} resource${res.length > 1 ? 's' : ''} available`;
        n.classList.remove('hidden');
        n._resources = res;
      }
    } catch (_) {}
  }

  // ── Session complete ──────────────────────────────────────────────────────────
  async function showComplete() {
    qs('#prog').style.width   = '100%';
    qs('#d-got').textContent  = stats.got;
    qs('#d-hard').textContent = stats.hard;
    qs('#d-skip').textContent = stats.skip;
    qs('#d-streak').textContent = bestStreak;

    // Fetch weak spots
    const weakEl = qs('#weak-spots-list');
    if (weakEl && sessionId) {
      try {
        const spots = await API.weakSpots(sessionId);
        if (spots.length) {
          weakEl.innerHTML = `
            <div class="weak-spots-title">⚠ Struggled with these ${spots.length} card${spots.length > 1 ? 's' : ''}</div>
            ${spots.map(s => `
              <div class="weak-spot-item">
                <div class="weak-spot-q">${esc(s.card.question)}</div>
                <div class="weak-spot-a">${esc(s.card.answer)}</div>
                <div class="weak-spot-count">Marked hard ${s.hard_count}× this session</div>
              </div>
            `).join('')}`;
        } else {
          weakEl.innerHTML = '<div class="weak-spots-none">No cards were marked hard more than once — great session!</div>';
        }
      } catch (_) { weakEl.innerHTML = ''; }
    }

    const hc = Object.keys(sessionHard).length;
    qs('#done-sub').textContent = hc
      ? `${hc} card${hc > 1 ? 's' : ''} marked hard — study them again?`
      : 'All cards reviewed — great session!';

    qs('.complete-overlay').classList.remove('hidden');
    if (sessionId) API.endSession(sessionId).catch(console.error);
    App.refreshStats();
  }

  async function restartHard() {
    qs('.complete-overlay').classList.add('hidden');
    const hard = await API.hardQueue();
    if (!hard.length) { alert('No hard cards recorded.'); return; }
    await start(hard, 'hard');
  }

  // ── Helpers ───────────────────────────────────────────────────────────────────
  function setActions(on) {
    qs('#btn-got').disabled  = !on;
    qs('#btn-hard').disabled = !on;
    qs('#btn-pin').disabled  = !on;
  }

  function updateStats() {
    qs('#s-got').textContent   = stats.got;
    qs('#s-hard').textContent  = stats.hard;
    qs('#s-skip').textContent  = stats.skip;
    qs('#streak-display').textContent = streak > 1 ? `🔥 ${streak}` : '';
  }

  function renderTags(tags) {
    return tags.map(t => `<span class="tag">${t.name || t}</span>`).join('');
  }

  function mdToHtml(s) {
    if (!s) return '';
    return s
      .replace(/```([\s\S]*?)```/g, (_, c) => `<pre>${esc(c.trim())}</pre>`)
      .replace(/`([^`]+)`/g, (_, c) => `<code>${esc(c)}</code>`)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g,
      c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }

  return {
    start, flip, mark, prev, next,
    redoNow, redoLater,
    togglePin, openEdit, closeEdit, saveEdit,
    restartHard,
  };
})();

window.Study = Study;
