
from src.muzik import Muzik
from prototyping.data import load_from_api
from prototyping.playlist import create_playlist

if __name__ == "__main__":
    muzik = Muzik()

    ach = load_from_api()
    ach.set_index(['genre', 'sub_genre', 'artist', 'album', 'song'],
                  inplace=True)

    muzik.update(ach)
