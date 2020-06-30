
from src.muzik import Muzik
from prototyping.data import load_from_api
from prototyping.playlist import create_playlist

if __name__ == "__main__":
    # create Spotify connector
    muzik = Muzik()

    # OPTIONAL but better to do
    # updated the cached list with the latest version
    # of the datasheet
    #
    # fetches latest update from the datasheet
    ach = load_from_api()
    # index preprocessing, should be done beforehand
    # (load_from_api)
    ach.set_index(['genre', 'sub_genre', 'artist', 'album', 'song'], inplace=True)
    # updates the cached version
    muzik.update(ach)
    
    # generate playlist
    playlist = create_playlist()
    # push the playlist
    muzik.create_playlist(playlist)
