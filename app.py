"""
Flask web app that allows searching a phrase of lyrics and matching songs.
- Uses DuckDuckGo HTML search for results (titles + snippets only)
- Fuzzy-corrects obvious spelling using tokens from search results
- Uses Spotify API (client credentials) to fetch release dates and metadata

Run: set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your environment, then:
    python app.py
"""
from flask import Flask, render_template, request, jsonify
from lyrics_finder import ddg_search, utils, spotify
import os
# Optional: load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    # Load environment variables from a local .env file, if present (optional)
    load_dotenv()
except Exception:
    # dotenv not available; proceed without loading .env
    load_dotenv = None

app = Flask(__name__)

MAX_MATCHES = 15


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    phrase = request.form.get("phrase", "").strip()
    if not phrase:
        return jsonify({"error": "Please enter a phrase."}), 400

    # 1) initial DDG search
    query = f"{phrase} lyrics"
    results = ddg_search.ddg_search(query, max_results=40)

    # 2) try to correct spelling by using tokens found in the results
    tokens = ddg_search.result_tokens(results)
    corrected, changed = utils.fuzzy_correct_phrase(phrase, tokens)

    if changed:
        # re-run with corrected phrase to get better results
        phrase = corrected
        results = ddg_search.ddg_search(f"{phrase} lyrics", max_results=60)

    # 3) extract (title, artist) pairs
    candidates = ddg_search.extract_candidates(results)

    # 4) deduplicate
    seen = set()
    unique = []
    for t, a in candidates:
        key = utils.normalize_pair(t, a)
        if key in seen:
            continue
        seen.add(key)
        unique.append({"title": t, "artist": a})

    if len(unique) > MAX_MATCHES:
        return jsonify({"too_many": True, "message": "Too many matches. Please add more words."})

    # 5) enrich with Spotify metadata to get release dates and IDs for sorting
    token = spotify.get_spotify_token()
    if not token:
        # Can't sort; warn user but still return list so they can click
        for u in unique:
            u.update({"spotify_id": None, "release_date": None})
        return jsonify({"corrected": changed and corrected or None, "matches": unique, "note": "SPOTIFY_CLIENT_ID/SECRET not set; install them to enable sorting and metadata."})

    enriched = []
    for u in unique:
        s = spotify.search_track(token, u["title"], u["artist"])
        if s:
            release = s.get("album", {}).get("release_date")
            u.update({"spotify_id": s.get("id"), "release_date": release})
        else:
            u.update({"spotify_id": None, "release_date": None})
        enriched.append(u)

    # sort by release_date: oldest first. release_date may be None; place them last
    def sort_key(item):
        rd = item.get("release_date")
        return (rd is None, rd or "")

    enriched = sorted(enriched, key=sort_key)

    return jsonify({"corrected": changed and corrected or None, "matches": enriched})


@app.route("/song/<track_id>")
def song_info(track_id):
    token = spotify.get_spotify_token()
    if not token:
        return jsonify({"error": "Spotify credentials not set on server."}), 400
    meta = spotify.get_track_metadata(token, track_id)
    if not meta:
        return jsonify({"error": "Not found"}), 404
    return jsonify(meta)


if __name__ == "__main__":
    # Flask debug server for local use only
    app.run(debug=True, host="127.0.0.1", port=5000)
