# Lyrics Finder (local-only)

A simple local web app that helps you identify songs from a partial lyrics phrase.

Features
- You type a phrase from a song lyric (minor spelling mistakes tolerated).
- App corrects obvious misspellings using fuzzy matching of tokens found in search results.
- Searches DuckDuckGo HTML results (only titles/snippets) for "<phrase> lyrics".
- Parses titles/snippets to extract song title and artist (heuristic-based).
- Removes duplicates. If more than 15 matches, asks you to add more words.
- If 15 or fewer matches, uses Spotify API to get release dates and sorts oldest→newest.
- Click a song to fetch metadata from Spotify (album, artists, release date). Producers may be unavailable.

IMPORTANT: This app does NOT scrape full lyrics pages (it only reads search result titles and snippets).

---

Requirements
- Python 3.10+
- Windows (instructions below assume PowerShell)

Install Python deps

1. (Recommended) Create a virtual environment and activate it:
   python -m venv venv
   .\venv\Scripts\Activate.ps1

2. Install required packages:
   pip install -r requirements.txt

Spotify API setup (free)
1. Create an app at https://developer.spotify.com/dashboard/ (log in with Spotify account).
2. Create a new app and note the Client ID and Client Secret.
3. You can set them in your shell for the session (PowerShell example):
   $env:SPOTIFY_CLIENT_ID = "your_client_id"
   $env:SPOTIFY_CLIENT_SECRET = "your_client_secret"

(Optional) Use a .env file in the project root for convenience (create a file named `.env`):

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

The app will pick up these values automatically if you put them in `.env`.

Running the app
1. Start the Flask app (from project root):
   python app.py
2. Open http://127.0.0.1:5000 in your browser.

Tips & Troubleshooting
- If you see the message about Spotify credentials not being set, make sure you set the environment variables as shown above or created a `.env` file and restarted the app.
- If you get many matches (>15), the phrase is too short or ambiguous—add a few more words from the lyric to narrow results.
- If a match has no Spotify link, it means Spotify search didn't find a confident match for that title/artist pair; you can still search again with a slightly different phrase.

Privacy & usage
- This app runs locally and only sends requests to DuckDuckGo and Spotify; it is intended for personal, non-commercial use.
- The app purposely only reads titles and snippets returned by search results and does not fetch full lyric pages.

How it works (high-level, for beginners)
- The app sends your phrase to DuckDuckGo's HTML search endpoint and reads the *titles* and *snippets* from the search results.
- A fuzzy-correction step compares your words to the most common words in those titles/snippets and fixes obvious typos.
- The app heuristically parses titles/snippets like "Song Title - Artist" or "\"Title\" by Artist" to propose matches.
- If there are too many possible matches (>15), it will ask you to add more words because the phrase is too ambiguous.
- If matches are 15 or fewer, the app asks Spotify for official track metadata (release date), sorts matches by release date, and shows clickable results.
- Clicking a result fetches more metadata from Spotify.

Notes and limitations
- Parsing is heuristic — very messy or rare title formats may not parse correctly.
- Producers are not reliably available from Spotify and will show as N/A when not provided.
- The app is intentionally simple for learning and local personal use.

If you want help customizing or improving any heuristics, tell me what you'd like to change.

---

Frontend (React + Vite + Tailwind)

I added a `frontend/` folder with a Vite + React app and Tailwind CSS. The frontend is configured to proxy `/search` and `/song` to the Flask backend running at `http://127.0.0.1:5000` so no backend changes are needed.

Quick start (from project root):
1. Start the Flask backend:
   python app.py
2. Open a new terminal and start the frontend:
   cd frontend
   npm install
   npm run dev

Open the URL shown by Vite (usually http://localhost:5173) and try the app.

If you want, I can add an npm script to start both backend and frontend together (using concurrently) or create a Docker Compose setup.

