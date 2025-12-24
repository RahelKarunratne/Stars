"""
Spotify API helpers (Client Credentials flow).
"""
import os
import base64
import time
import requests
from typing import Optional, Dict, Any

TOKEN_URL = "https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search"
TRACK_URL = "https://api.spotify.com/v1/tracks/{}"

_token_cache = {"token": None, "expires_at": 0}


def _load_dotenv_simple(path: str = ".env") -> None:
    """Simple .env loader: reads KEY=VALUE lines and sets os.environ if missing."""
    import os
    try:
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                # don't overwrite existing env vars
                if k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


def get_spotify_token() -> Optional[str]:
    """Return a bearer token using Client Credentials. Expects env vars SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.

    If environment variables are not set, the function will try to read a local `.env` file as a convenience for local development.
    """
    now = time.time()
    if _token_cache.get("token") and _token_cache.get("expires_at", 0) > now + 30:
        return _token_cache["token"]

    # convenience: try reading .env if variables missing
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        _load_dotenv_simple()
        client_id = os.environ.get("SPOTIFY_CLIENT_ID")
        client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        return None

    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}"}
    data = {"grant_type": "client_credentials"}

    r = requests.post(TOKEN_URL, headers=headers, data=data, timeout=10)
    if r.status_code != 200:
        return None
    j = r.json()
    token = j.get("access_token")
    expires = j.get("expires_in", 3600)
    _token_cache["token"] = token
    _token_cache["expires_at"] = time.time() + expires
    return token


def search_track(token: str, title: str, artist: str) -> Optional[Dict[str, Any]]:
    """Search for track on Spotify; returns first track object or None."""
    if not token:
        return None
    q = f"track:{title} artist:{artist}"
    params = {"q": q, "type": "track", "limit": 1}
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10)
    if r.status_code != 200:
        return None
    j = r.json()
    tracks = j.get("tracks", {}).get("items", [])
    if not tracks:
        # try a looser search
        params = {"q": f"{title} {artist}", "type": "track", "limit": 1}
        r = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            return None
        j = r.json()
        tracks = j.get("tracks", {}).get("items", [])
        if not tracks:
            return None
    return tracks[0]


def get_track_metadata(token: str, track_id: str) -> Optional[Dict[str, Any]]:
    """Fetch track metadata: album, artists, release date. Producers may not be available from Spotify."""
    if not token:
        return None
    r = requests.get(TRACK_URL.format(track_id), headers={"Authorization": f"Bearer {token}"}, timeout=10)
    if r.status_code != 200:
        return None
    j = r.json()
    album = j.get("album", {})
    artists = [a.get("name") for a in j.get("artists", [])]
    release_date = album.get("release_date")
    album_name = album.get("name")
    # Spotify doesn't expose producer credits in the track endpoint; return None if unavailable
    producers = None
    return {
        "track_name": j.get("name"),
        "album": album_name,
        "artists": artists,
        "release_date": release_date,
        "producers": producers,
        "spotify_url": j.get("external_urls", {}).get("spotify")
    }
