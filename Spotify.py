import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from Youtube import playlist
import os

# Eliminar import de 'credenciales'
sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),  # Variables de entorno
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    )
)

def get_spotify_info(url: str):
    if "track" in url:
        track = sp.track(url)
        title = track["name"]
        artists = ", ".join(artist["name"] for artist in track["artists"])
        return [f"{title} - {artists}"]
    
    elif "playlist" in url:
        playlist_data = sp.playlist(url)
        songs = []
        for item in playlist_data["tracks"]["items"]:
            track = item["track"]
            title = track["name"]
            artists = ", ".join(artist["name"] for artist in track["artists"])
            songs.append(f"{title} - {artists}")
        return songs
    
    elif "album" in url:
        album = sp.album(url)
        songs = [
            f"{track['name']} - {', '.join(artist['name'] for artist in track['artists'])}"
            for track in album["tracks"]["items"]
        ]
        return songs
    
    else:
        return None
