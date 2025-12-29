async function api(method, url, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  const text = await res.text();
  let data;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) {
    const msg = (data && data.detail) ? data.detail : (data && data.error && data.error.message) ? data.error.message : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

function debounce(fn, ms) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

function enableSortableList(ul, onChange) {
  // Minimal HTML5 DnD reordering.
  let dragEl = null;

  ul.querySelectorAll('li').forEach(li => {
    li.draggable = true;
    li.addEventListener('dragstart', e => {
      dragEl = li;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', '');
    });

    li.addEventListener('dragover', e => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      const target = e.currentTarget;
      if (!dragEl || target === dragEl) return;
      const rect = target.getBoundingClientRect();
      const before = (e.clientY - rect.top) < (rect.height / 2);
      ul.insertBefore(dragEl, before ? target : target.nextSibling);
    });

    li.addEventListener('drop', e => {
      e.preventDefault();
      dragEl = null;
      if (onChange) onChange();
    });
  });
}

// LOGIN
async function loginInit() {
  const form = document.querySelector('[data-login]');
  if (!form) return;

  const status = document.querySelector('[data-status]');
  const usernameEl = document.querySelector('[data-username]');
  const otpEl = document.querySelector('[data-otp]');
  const otpArea = document.querySelector('[data-otp-area]');
  const blockArea = document.querySelector('[data-block-area]');
  const blockBtn = document.querySelector('[data-block-btn]');

  function setStatus(msg, isError=false) {
    status.textContent = msg || '';
    status.className = isError ? 'error' : 'small';
  }

  document.querySelector('[data-send-otp]').addEventListener('click', async () => {
    setStatus('Sending OTP...');
    try {
      const r = await api('POST', '/api/v1/auth/otp/request', { username: usernameEl.value.trim() });
      otpArea.style.display = 'block';
      blockArea.style.display = 'none';
      setStatus(`OTP sent. Expires in ${r.expires_in_seconds}s.`);
      otpEl.focus();
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.querySelector('[data-verify-otp]').addEventListener('click', async () => {
    setStatus('Verifying...');
    try {
      const r = await api('POST', '/api/v1/auth/otp/verify', { username: usernameEl.value.trim(), otp: otpEl.value.trim() });
      if (r.status === 'ok') {
        window.location.href = '/';
        return;
      }
      if (r.status === 'unrequested') {
        blockArea.style.display = 'block';
        blockBtn.dataset.hours = r.default_block_hours;
        setStatus('Unrequested OTP verification. Did you request this OTP?', true);
        return;
      }
      if (r.status === 'invalid') {
        setStatus(`Invalid OTP. Attempts remaining: ${r.attempts_remaining}`, true);
        return;
      }
      if (r.status === 'locked') {
        setStatus(`Locked. Retry after ${r.retry_after_seconds}s.`, true);
        return;
      }
      setStatus('Unexpected response', true);
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  blockBtn.addEventListener('click', async () => {
    const hours = Number(blockBtn.dataset.hours || '72');
    setStatus('Blocking IP...');
    try {
      const r = await api('POST', '/api/v1/auth/ipblock', { action: 'block', hours });
      setStatus(`IP blocked until ${r.blocked_until}.`, true);
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

// INDEX (catalog + working playlist)
async function indexInit() {
  const root = document.querySelector('[data-index]');
  if (!root) return;

  const qEl = document.querySelector('[data-q]');
  const catEl = document.querySelector('[data-categories]');
  const resultsEl = document.querySelector('[data-results]');
  const workEl = document.querySelector('[data-working]');
  const saveBtn = document.querySelector('[data-save]');
  const status = document.querySelector('[data-status]');

  let working = [];

  function setStatus(msg, isError=false) {
    status.textContent = msg || '';
    status.className = isError ? 'error' : 'small';
  }

  function renderWorking() {
    workEl.innerHTML = '';
    working.forEach((it, idx) => {
      const li = document.createElement('li');
      li.dataset.videoId = it.video_id;
      li.innerHTML = `<span class="handle">⠿</span><span class="grow">${it.title}</span><button data-rm="${idx}">Remove</button>`;
      workEl.appendChild(li);
    });

    workEl.querySelectorAll('button[data-rm]').forEach(btn => {
      btn.addEventListener('click', () => {
        const i = Number(btn.dataset.rm);
        working.splice(i, 1);
        renderWorking();
      });
    });

    enableSortableList(workEl, () => {
      const ids = Array.from(workEl.querySelectorAll('li')).map(li => li.dataset.videoId);
      working = ids.map(id => working.find(w => w.video_id === id));
    });
  }

  async function loadCategories() {
    const r = await api('GET', '/api/v1/catalog/categories');
    catEl.innerHTML = '';
    r.categories.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c;
      opt.textContent = c;
      catEl.appendChild(opt);
    });
  }

  function selectedCategories() {
    return Array.from(catEl.selectedOptions).map(o => o.value);
  }

  async function runSearch() {
    const q = qEl.value.trim();
    const cats = selectedCategories();
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    cats.forEach(c => params.append('category', c));
    params.set('limit', '50');
    params.set('offset', '0');

    const r = await api('GET', `/api/v1/catalog/search?${params.toString()}`);
    resultsEl.innerHTML = '';
    r.items.forEach(it => {
      const li = document.createElement('li');
      li.innerHTML = `<span class="grow">${it.title}</span><button data-add="${it.video_id}">Add</button>`;
      li.dataset.videoId = it.video_id;
      li.dataset.title = it.title;
      resultsEl.appendChild(li);
    });

    resultsEl.querySelectorAll('button[data-add]').forEach(btn => {
      btn.addEventListener('click', () => {
        const li = btn.closest('li');
        working.push({ video_id: li.dataset.videoId, title: li.dataset.title });
        renderWorking();
      });
    });
  }

  saveBtn.addEventListener('click', async () => {
    const name = prompt('Playlist name?');
    if (!name) return;
    try {
      const payload = { name, items: working.map(w => ({ video_id: w.video_id })) };
      const r = await api('POST', '/api/v1/playlists', payload);
      window.location.href = `/playlists/${r.playlist_id}`;
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  const debouncedSearch = debounce(() => runSearch().catch(e => setStatus(e.message, true)), 200);
  qEl.addEventListener('input', debouncedSearch);
  catEl.addEventListener('change', debouncedSearch);

  await loadCategories();
  await runSearch();
  renderWorking();
}

async function playlistsInit() {
  const root = document.querySelector('[data-playlists]');
  if (!root) return;
  const listEl = document.querySelector('[data-playlist-list]');
  const status = document.querySelector('[data-status]');

  function setStatus(msg, isError=false) {
    status.textContent = msg || '';
    status.className = isError ? 'error' : 'small';
  }

  try {
    const r = await api('GET', '/api/v1/playlists');
    listEl.innerHTML = '';
    r.playlists.forEach(p => {
      const li = document.createElement('li');
      li.innerHTML = `<a class="grow" href="/playlists/${p.playlist_id}">${p.name}</a><span class="small">${p.updated_at}</span><button data-del="${p.playlist_id}" class="danger" style="margin-left:8px;">Delete</button>`;
      listEl.appendChild(li);
    });

    listEl.querySelectorAll('button[data-del]').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (!confirm('Delete this playlist?')) return;
        const pid = btn.dataset.del;
        try {
          await api('DELETE', `/api/v1/playlists/${pid}`);
          btn.closest('li').remove();
        } catch (e) {
          setStatus(e.message, true);
        }
      });
    });
  } catch (e) {
    setStatus(e.message, true);
  }
}

async function applyInit() {
  const root = document.querySelector('[data-apply]');
  if (!root) return;
  const select = document.querySelector('[data-playlist]');
  const mode = document.querySelector('[data-mode]');
  const btn = document.querySelector('[data-apply-btn]');
  const status = document.querySelector('[data-status]');

  function setStatus(msg, isError=false) {
    status.textContent = msg || '';
    status.className = isError ? 'error' : 'small';
  }

  const idx = await api('GET', '/api/v1/playlists');
  select.innerHTML = '';
  idx.playlists.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.playlist_id;
    opt.textContent = p.name;
    select.appendChild(opt);
  });

  btn.addEventListener('click', async () => {
    const selectedName = select.options[select.selectedIndex]?.text || '';
    const modeLabel = mode.options[mode.selectedIndex]?.text || mode.value;
    if (!confirm(`Apply "${selectedName}" using mode ${modeLabel}?`)) return;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Applying...';
    try {
      const r = await api('POST', '/api/v1/queue/apply', { playlist_id: select.value, mode: mode.value });
      if (r.status === 'ok') setStatus(`Applied. Enqueued: ${r.enqueued_count}`);
      else setStatus(r.error || 'Error', true);
    } catch (e) {
      setStatus(e.message, true);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Apply';
    }
  });
}

async function statsInit() {
  const root = document.querySelector('[data-stats]');
  if (!root) return;
  const status = document.querySelector('[data-status]');
  const likeBtn = document.querySelector('[data-like]');

  function setStatus(msg, isError=false) {
    status.textContent = msg || '';
    status.className = isError ? 'error' : 'small';
  }

  likeBtn.addEventListener('click', async () => {
    try {
      await api('POST', '/api/v1/likes/current', {});
      setStatus('Liked.');
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

window.addEventListener('DOMContentLoaded', () => {
  loginInit();
  indexInit();
  playlistsInit();
  editorInit();
  marathonInit();
  applyInit();
  statsInit();
});

async function marathonInit() {
  const root = document.querySelector('[data-marathon]');
  if (!root) return;

  const sourcesEl = document.querySelector('[data-sources]');
  const addSourceBtn = document.querySelector('[data-add-source]');
  const methodEl = document.querySelector('[data-method]');
  const shuffleOpts = document.querySelector('[data-shuffle-opts]');
  const interleaveOpts = document.querySelector('[data-interleave-opts]');
  const seedEl = document.querySelector('[data-seed]');
  const patternEl = document.querySelector('[data-pattern]');
  const episodeOrderEl = document.querySelector('[data-episode-order]');
  const generateBtn = document.querySelector('[data-generate]');
  const status = document.querySelector('[data-status]');
  const resultEl = document.querySelector('[data-result]');
  const countEl = document.querySelector('[data-count]');
  const itemsEl = document.querySelector('[data-items]');
  const warningsEl = document.querySelector('[data-warnings]');
  const warningsText = document.querySelector('[data-warnings-text]');
  const saveNameEl = document.querySelector('[data-save-name]');
  const saveBtn = document.querySelector('[data-save]');

  let playlists = [];
  let sources = [];
  let generatedItems = [];
  const labels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

  function setStatus(msg, isError = false) {
    status.textContent = msg || '';
    status.className = isError ? 'error' : 'small';
  }

  function nextLabel() {
    const used = new Set(sources.map(s => s.label));
    for (const c of labels) {
      if (!used.has(c)) return c;
    }
    return null;
  }

  function renderSources() {
    sourcesEl.innerHTML = '';
    sources.forEach((src, idx) => {
      const div = document.createElement('div');
      div.className = 'source-row';
      div.innerHTML = `
        <span class="label">${src.label}</span>
        <select data-src-playlist="${idx}">
          ${playlists.map(p => `<option value="${p.playlist_id}" ${p.playlist_id === src.playlist_id ? 'selected' : ''}>${p.name}</option>`).join('')}
        </select>
        <button data-rm-src="${idx}" class="danger">×</button>
      `;
      sourcesEl.appendChild(div);
    });

    sourcesEl.querySelectorAll('select[data-src-playlist]').forEach(sel => {
      sel.addEventListener('change', () => {
        const idx = Number(sel.dataset.srcPlaylist);
        sources[idx].playlist_id = sel.value;
      });
    });

    sourcesEl.querySelectorAll('button[data-rm-src]').forEach(btn => {
      btn.addEventListener('click', () => {
        sources.splice(Number(btn.dataset.rmSrc), 1);
        renderSources();
      });
    });
  }

  addSourceBtn.addEventListener('click', () => {
    const label = nextLabel();
    if (!label) {
      setStatus('Maximum 26 sources', true);
      return;
    }
    sources.push({ label, playlist_id: playlists[0]?.playlist_id || '' });
    renderSources();
  });

  methodEl.addEventListener('change', () => {
    const v = methodEl.value;
    shuffleOpts.style.display = v === 'shuffle' ? 'block' : 'none';
    interleaveOpts.style.display = v === 'interleave' ? 'block' : 'none';
  });

  generateBtn.addEventListener('click', async () => {
    if (sources.length === 0) {
      setStatus('Add at least one source', true);
      return;
    }

    generateBtn.disabled = true;
    generateBtn.innerHTML = '<span class="spinner"></span> Generating...';
    setStatus('');

    try {
      const payload = {
        sources: sources.map(s => ({ label: s.label, playlist_id: s.playlist_id })),
        method: methodEl.value,
        shuffle_seed: seedEl.value.trim() || null,
        interleave_pattern: patternEl.value.trim() || null,
        preserve_episode_order: episodeOrderEl.checked,
      };

      const r = await api('POST', '/api/v1/marathon/generate', payload);
      generatedItems = r.items;

      itemsEl.innerHTML = '';
      r.items.forEach((it, idx) => {
        const li = document.createElement('li');
        li.innerHTML = `<span class="small">${idx + 1}.</span> ${it.title}`;
        itemsEl.appendChild(li);
      });

      countEl.textContent = `(${r.items.length} items)`;

      if (r.warnings && r.warnings.length) {
        warningsText.textContent = r.warnings.join(', ');
        warningsEl.style.display = 'block';
      } else {
        warningsEl.style.display = 'none';
      }

      resultEl.style.display = 'block';
      setStatus(`Generated ${r.items.length} items`);
    } catch (e) {
      setStatus(e.message, true);
    } finally {
      generateBtn.disabled = false;
      generateBtn.textContent = 'Generate Marathon';
    }
  });

  saveBtn.addEventListener('click', async () => {
    const name = saveNameEl.value.trim();
    if (!name) {
      setStatus('Enter a name for the playlist', true);
      return;
    }
    if (generatedItems.length === 0) {
      setStatus('No items to save', true);
      return;
    }

    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner"></span> Saving...';

    try {
      const r = await api('POST', '/api/v1/marathon/save', { name, items: generatedItems });
      window.location.href = `/playlists/${r.playlist_id}`;
    } catch (e) {
      setStatus(e.message, true);
      saveBtn.disabled = false;
      saveBtn.textContent = 'Save Playlist';
    }
  });

  // Load playlists
  try {
    const r = await api('GET', '/api/v1/playlists');
    playlists = r.playlists;
    if (playlists.length > 0) {
      sources.push({ label: 'A', playlist_id: playlists[0].playlist_id });
      renderSources();
    }
  } catch (e) {
    setStatus(e.message, true);
  }
}

async function editorInit() {
  const root = document.querySelector('[data-editor]');
  if (!root) return;

  const playlistId = root.dataset.playlistId;
  const nameEl = document.querySelector('[data-name]');
  const itemsEl = document.querySelector('[data-items]');
  const searchEl = document.querySelector('[data-search-results]');
  const qEl = document.querySelector('[data-q]');
  const saveBtn = document.querySelector('[data-save]');
  const deleteBtn = document.querySelector('[data-delete]');
  const status = document.querySelector('[data-status]');

  let items = [];

  function setStatus(msg, isError=false) {
    status.textContent = msg || '';
    status.className = isError ? 'error' : 'small';
  }

  function renderItems() {
    itemsEl.innerHTML = '';
    items.forEach((it, idx) => {
      const li = document.createElement('li');
      li.dataset.videoId = it.video_id;
      li.innerHTML = `<span class="handle">⠿</span><span class="grow">${it.title || it.video_id}</span><button data-rm="${idx}">Remove</button>`;
      itemsEl.appendChild(li);
    });

    itemsEl.querySelectorAll('button[data-rm]').forEach(btn => {
      btn.addEventListener('click', () => {
        items.splice(Number(btn.dataset.rm), 1);
        renderItems();
      });
    });

    enableSortableList(itemsEl, () => {
      const ids = Array.from(itemsEl.querySelectorAll('li')).map(li => li.dataset.videoId);
      items = ids.map(id => items.find(it => it.video_id === id));
    });
  }

  async function loadPlaylist() {
    const pl = await api('GET', `/api/v1/playlists/${playlistId}`);
    nameEl.value = pl.name || '';
    items = (pl.items || []).map(it => ({ video_id: it.video_id, title: it.title || it.video_id }));
    renderItems();
  }

  async function runSearch() {
    const q = (qEl.value || '').trim();
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    params.set('limit', '30');
    params.set('offset', '0');
    const r = await api('GET', `/api/v1/catalog/search?${params}`);
    searchEl.innerHTML = '';
    r.items.forEach(it => {
      const li = document.createElement('li');
      li.innerHTML = `<span class="grow">${it.title}</span><button data-add>Add</button>`;
      li.querySelector('[data-add]').addEventListener('click', () => {
        items.push({ video_id: it.video_id, title: it.title });
        renderItems();
      });
      searchEl.appendChild(li);
    });
  }

  const debouncedSearch = debounce(() => runSearch().catch(e => setStatus(e.message, true)), 200);
  qEl.addEventListener('input', debouncedSearch);

  saveBtn.addEventListener('click', async () => {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner"></span> Saving...';
    try {
      await api('PUT', `/api/v1/playlists/${playlistId}`, {
        name: nameEl.value.trim(),
        items: items.map(it => ({ video_id: it.video_id })),
      });
      setStatus('Saved.');
    } catch (e) {
      setStatus(e.message, true);
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = 'Save';
    }
  });

  deleteBtn.addEventListener('click', async () => {
    if (!confirm('Delete this playlist?')) return;
    deleteBtn.disabled = true;
    try {
      await api('DELETE', `/api/v1/playlists/${playlistId}`);
      window.location.href = '/playlists';
    } catch (e) {
      setStatus(e.message, true);
      deleteBtn.disabled = false;
    }
  });

  await loadPlaylist();
  await runSearch();
}
