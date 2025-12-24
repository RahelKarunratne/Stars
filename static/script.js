(function(){
  const form = document.getElementById('search-form');
  const phraseInput = document.getElementById('phrase');
  const messageEl = document.getElementById('message');
  const resultsEl = document.getElementById('results');
  const detailEl = document.getElementById('detail');

  function setMessage(html, type = 'info'){
    if(!html){ messageEl.innerHTML = ''; return; }
    let base = 'rounded-md px-4 py-3 text-sm';
    if(type === 'error') base += ' bg-red-900/70 border border-red-700 text-red-200';
    else if(type === 'warn') base += ' bg-amber-900/70 border border-amber-700 text-amber-200';
    else base += ' bg-white/5 text-white/90 border border-white/6';
    messageEl.innerHTML = `<div class="${base}">${html}</div>`;
  }

  function spinnerHtml(size = 6){
    return `<svg class="animate-spin h-${size} w-${size} text-white" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg>`;
  }

  function clearResults(){ resultsEl.innerHTML = ''; detailEl.innerHTML = ''; }

  form.addEventListener('submit', async function(e){
    e.preventDefault();
    const phrase = phraseInput.value.trim();
    if(!phrase){ setMessage('Please type a lyric phrase.', 'error'); return; }
    setMessage(spinnerHtml(5) + ' Searching...');
    clearResults();

    const fd = new FormData(); fd.append('phrase', phrase);
    try{
      const res = await fetch('/search', { method: 'POST', body: fd });
      const j = await res.json();
      if(res.status !== 200){ setMessage(j.error || 'Search failed', 'error'); return; }
      if(j.too_many){ setMessage(j.message || 'Too many matches. Please add more words.', 'warn'); return; }
      setMessage(j.corrected ? `Using corrected phrase: "${j.corrected}"` : '');
      const matches = j.matches || [];
      if(matches.length === 0){ resultsEl.innerHTML = `<div class="col-span-full text-center text-white/60 py-8">No matches found.</div>`; return; }

      // Render matches as cards
      matches.forEach(m => {
        const card = document.createElement('div');
        card.className = 'cursor-pointer p-4 md:p-5 rounded-xl hover:scale-[1.01] transition transform bg-gradient-to-br from-white/3 to-white/2 border border-white/6';
        card.innerHTML = `
          <div class="flex items-start gap-4">
            <div class="flex-1">
              <h3 class="text-lg sm:text-xl font-extrabold leading-tight">${escapeHtml(m.title)}</h3>
              <p class="mt-1 text-sm text-white/70">${escapeHtml(m.artist)}</p>
            </div>
            <div class="text-right">
              <div class="text-sm text-white/60">${m.release_date ? (new Date(m.release_date).getFullYear()) : '—'}</div>
              <div class="mt-2 text-xs text-white/50">${m.spotify_id ? 'Open details' : 'No Spotify match'}</div>
            </div>
          </div>
        `;
        card.addEventListener('click', ()=>{
          if(!m.spotify_id){ detailEl.innerHTML = `<div class="rounded-md px-4 py-3 text-sm bg-white/5">No Spotify match available for this item.</div>`; return; }
          fetchDetails(m.spotify_id);
        });
        resultsEl.appendChild(card);
      });

    }catch(err){ console.error(err); setMessage('Network error or server error.', 'error'); }
  });

  async function fetchDetails(id){
    detailEl.innerHTML = `<div class="p-4 rounded-xl bg-white/4">${spinnerHtml(6)} Loading details...</div>`;
    try{
      const r = await fetch(`/song/${id}`);
      const j = await r.json();
      if(!r.ok){ detailEl.innerHTML = `<div class="rounded-md px-4 py-3 text-sm bg-red-900/70">${j.error||'Not found'}</div>`; return; }
      const html = `
        <div class="p-4 rounded-xl bg-gradient-to-br from-white/3 to-white/2 border border-white/6">
          <div class="flex items-start justify-between">
            <div>
              <h4 class="text-xl font-bold">${escapeHtml(j.track_name)}</h4>
              <p class="text-sm text-white/70">Artists: ${escapeHtml((j.artists||[]).join(', '))}</p>
              <p class="text-sm text-white/70">Album: ${escapeHtml(j.album||'N/A')}</p>
            </div>
            <div class="text-sm text-white/60">${escapeHtml(j.release_date||'N/A')}</div>
          </div>
          <div class="mt-3 text-sm text-white/70">Producers: ${escapeHtml(j.producers||'N/A')}</div>
          ${j.spotify_url ? `<div class="mt-3"><a class="inline-block px-4 py-2 rounded-full bg-black/40 text-sm hover:bg-black/60 transition" href="${escapeAttr(j.spotify_url)}" target="_blank" rel="noreferrer">Open in Spotify</a></div>` : ''}
        </div>
      `;
      detailEl.innerHTML = html;
    }catch(err){ console.error(err); detailEl.innerHTML = `<div class="rounded-md px-4 py-3 text-sm bg-red-900/70">Network error while fetching details.</div>`; }
  }

  // Small helpers to avoid XSS
  function escapeHtml(s){ if(!s) return ''; return String(s).replace(/[&<>\"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
  function escapeAttr(s){ if(!s) return ''; return String(s).replace(/"/g,'&quot;'); }
})();