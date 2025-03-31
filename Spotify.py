import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

# Configurar Spotipy con variables de entorno
sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    )
)

def get_spotify_tracks(url: str):
    """Obtiene las canciones de un enlace de Spotify (track/playlist/album)."""
    try:
        if "track" in url:
            track = sp.track(url)
            title = track["name"]
            artist = ", ".join(a["name"] for a in track["artists"])
            return [f"{title} - {artist}"]
        
        elif "playlist" in url:
            playlist = sp.playlist(url)
            tracks = []
            for item in playlist["tracks"]["items"]:
                track = item["track"]
                title = track["name"]
                artist = ", ".join(a["name"] for a in track["artists"])
                tracks.append(f"{title} - {artist}")
            return tracks
        
        elif "album" in url:
            album = sp.album(url)
            tracks = []
            for track in album["tracks"]["items"]:
                title = track["name"]
                artist = ", ".join(a["name"] for a in track["artists"])
                tracks.append(f"{title} - {artist}")
            return tracks
        
        else:
            return None

    except Exception as e:
        print(f"🔴 Spotify Error: {e}")
        return None
