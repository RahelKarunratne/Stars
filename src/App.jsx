import React, { useState } from 'react'

function Spinner({ size = 'md' }) {
  const cls = size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-8 w-8' : 'h-5 w-5'
  return (
    <svg className={`animate-spin ${cls} text-white`} viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  )
}

export default function App() {
  const [phrase, setPhrase] = useState('')
  const [searching, setSearching] = useState(false)
  const [matches, setMatches] = useState([])
  const [message, setMessage] = useState('')
  const [tooMany, setTooMany] = useState(false)
  const [error, setError] = useState(null)
  const [details, setDetails] = useState(null)

  async function onSearch(e) {
    e?.preventDefault()
    setError(null)
    setMatches([])
    setDetails(null)
    if (!phrase.trim()) return setError('Please type a lyric phrase to search.')
    setSearching(true)
    setTooMany(false)
    setMessage('')

    try {
      const form = new FormData()
      form.append('phrase', phrase.trim())
      const res = await fetch('/search', { method: 'POST', body: form })
      const j = await res.json()
      if (j.too_many) {
        setTooMany(true)
        setMessage(j.message || 'Too many matches. Please add more words.')
      } else if (res.ok) {
        setMatches(j.matches || [])
        if (j.corrected) setMessage(`Using corrected phrase: "${j.corrected}"`)
      } else {
        setError(j.error || 'Search failed')
      }
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setSearching(false)
    }
  }

  async function fetchDetails(id) {
    setDetails(null)
    setError(null)
    setSearching(true)
    try {
      const res = await fetch(`/song/${id}`)
      const j = await res.json()
      if (!res.ok) setError(j.error || 'Failed to fetch details')
      else setDetails(j)
    } catch (err) {
      setError('Network error while fetching details')
    } finally {
      setSearching(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#071126] via-[#0b122b] to-[#050616] text-white p-6">
      <div className="w-full max-w-4xl">
        <div className="rounded-3xl p-8 md:p-12 card-bg shadow-soft">
          <header className="text-center mb-6">
            <h1 className="text-3xl sm:text-4xl font-extrabold">Lyrics Finder</h1>
            <p className="mt-2 text-sm text-white/70">Paste a lyric fragment and we’ll suggest matching songs — private & local.</p>
          </header>

          <form onSubmit={onSearch} className="flex flex-col sm:flex-row gap-4 items-center">
            <div className="flex-1">
              <input
                value={phrase}
                onChange={(e) => setPhrase(e.target.value)}
                placeholder='e.g. "we don\'t need no education"'
                className="w-full rounded-full px-6 py-4 text-lg bg-white/4 backdrop-blur-sm border border-white/6 placeholder:text-white/50 focus:outline-none focus:ring-2 focus:ring-accent transition-shadow"
              />
            </div>

            <button type="submit" className="inline-flex items-center gap-3 rounded-full px-6 py-3 bg-gradient-to-r from-[#1db954]/80 to-[#10b981]/70 text-black font-semibold transform transition hover:scale-[1.02] btn-glow">
              {searching ? <Spinner size="sm" /> : (<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-5.2-5.2M9.5 17A7.5 7.5 0 109.5 2a7.5 7.5 0 000 15z" /></svg>)}
              <span className="hidden sm:inline">Search</span>
            </button>
          </form>

          <div className="mt-5 space-y-3">
            {message && !tooMany && (
              <div className="alert bg-white/5 text-white/90 border border-white/6 flex items-center gap-3">
                <div>{message}</div>
              </div>
            )}
            {tooMany && (
              <div className="alert bg-amber-900/70 border border-amber-700 text-amber-200">Too many matches. Please add more words.</div>
            )}
            {error && (
              <div className="alert bg-red-900/70 border border-red-700 text-red-200">{error}</div>
            )}
          </div>

          <main className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            {matches.length > 0 ? (
              matches.map((m, idx) => (
                <article key={`${m.title}-${idx}`} onClick={() => m.spotify_id && fetchDetails(m.spotify_id)} className="cursor-pointer p-4 md:p-5 rounded-xl hover:scale-[1.01] transition transform bg-gradient-to-br from-white/3 to-white/2 border border-white/6">
                  <div className="flex items-start gap-4">
                    <div className="flex-1">
                      <h3 className="text-lg sm:text-xl font-extrabold leading-tight">{m.title}</h3>
                      <p className="mt-1 text-sm text-white/70">{m.artist}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-white/60">{m.release_date ? (new Date(m.release_date).getFullYear()) : '—'}</div>
                      <div className="mt-2 text-xs text-white/50">{m.spotify_id ? 'Open details' : 'No Spotify match'}</div>
                    </div>
                  </div>
                </article>
              ))
            ) : (
              <div className="col-span-full text-center text-white/60 py-8">
                {searching ? <div className="flex justify-center"><Spinner size="lg"/></div> : <div>No results yet — try a different lyric.</div>}
              </div>
            )}
          </main>

          {details && (
            <section className="mt-6 p-4 rounded-xl bg-gradient-to-br from-white/3 to-white/2 border border-white/6">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-xl font-bold">{details.track_name}</h4>
                  <p className="text-sm text-white/70">Artists: {details.artists.join(', ')}</p>
                  <p className="text-sm text-white/70">Album: {details.album || 'N/A'}</p>
                </div>
                <div className="text-sm text-white/60">{details.release_date || 'N/A'}</div>
              </div>
              <div className="mt-3 text-sm text-white/70">Producers: {details.producers || 'N/A'}</div>
              {details.spotify_url && (
                <div className="mt-3">
                  <a className="inline-block px-4 py-2 rounded-full bg-black/40 text-sm hover:bg-black/60 transition" href={details.spotify_url} target="_blank" rel="noreferrer">Open in Spotify</a>
                </div>
              )}
            </section>
          )}

          <footer className="mt-6 text-center text-xs text-white/50">Local-only. Uses search result titles/snippets (no full lyrics pages).</footer>
        </div>
      </div>
    </div>
  )
}
