import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json


CRED_PATH_SPOTIFY = "credentials-spotify.json"

with open(CRED_PATH_SPOTIFY, 'r') as handle:
    data = json.load(handle)

spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
    **data
))

print(spotify.me())
