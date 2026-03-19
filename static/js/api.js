// Thin wrapper around the FlashDeck REST API

const API = {
  async get(path) {
    const r = await fetch(path);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },

  async post(path, body) {
    const r = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },

  async patch(path, body) {
    const r = await fetch(path, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },

  async delete(path) {
    const r = await fetch(path, { method: 'DELETE' });
    if (!r.ok && r.status !== 204) throw new Error(await r.text());
  },

  async upload(path, files) {
    const fd = new FormData();
    for (const f of files) fd.append('files', f);
    const r = await fetch(path, { method: 'POST', body: fd });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },

  // Cards
  cards:      (params = {}) => API.get('/api/cards?' + new URLSearchParams(params)),
  createCard: (body)        => API.post('/api/cards', body),
  folders:    ()            => API.get('/api/cards/folders'),
  exportCards: ()           => window.open('/api/cards/export', '_blank'),
  dueToday:   ()            => API.get('/api/cards/due-today'),
  pinCard:    (id)          => API.post(`/api/cards/${id}/pin`, {}),
  resetHard:  (id)          => API.post(`/api/cards/${id}/reset-hard`, {}),
  card:      (id)          => API.get(`/api/cards/${id}`),
  importFiles:(files)      => API.upload('/api/cards/import', files),
  scanFolder: ()           => API.post('/api/cards/scan', {}),
  deleteCard: (id)         => API.delete(`/api/cards/${id}`),
  updateCard: (id, body)   => API.patch(`/api/cards/${id}`, body),

  // Sessions
  createSession: (mode)       => API.post('/api/sessions', { mode }),
  endSession:    (id)         => API.post(`/api/sessions/${id}/end`, {}),
  recordResult:  (id, card_id, result) => API.post(`/api/sessions/${id}/results`, { card_id, result }),
  sessions:      ()           => API.get('/api/sessions'),
  deckStats:     ()           => API.get('/api/sessions/stats/deck'),
  hardQueue:     ()                    => API.get('/api/sessions/queue/hard'),
  pinnedQueue:   ()                    => API.get('/api/sessions/queue/pinned'),
  dueQueue:      ()                    => API.get('/api/sessions/queue/due'),
  weightedQueue: ()                    => API.get('/api/sessions/queue/weighted'),
  folderQueue:   (folder)              => API.get(`/api/sessions/queue/folder/${encodeURIComponent(folder)}`),
  folderStats:   ()                    => API.get('/api/sessions/stats/folders'),
  masteryStats:  ()                    => API.get('/api/sessions/stats/mastery'),
  forecast:      ()                    => API.get('/api/sessions/stats/forecast'),
  weakSpots:     (sessionId)           => API.get(`/api/sessions/${sessionId}/weak-spots`),

  // Resources
  resources:         (topic)  => API.get('/api/resources' + (topic ? `?topic=${topic}` : '')),
  resourceTopics:    ()       => API.get('/api/resources/topics'),
  resourcesForCard:  (id)     => API.get(`/api/resources/for-card/${id}`),
  resourceStatus:    ()       => API.get('/api/resources/status'),
  generateResources: ()       => API.post('/api/resources/generate', {}),
};

window.API = API;
