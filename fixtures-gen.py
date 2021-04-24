import json
import os

from src.ach import Ach


def element_id(elt, keys, elts, elt_name, **kwargs):
    _id = None
    if elt not in keys:
        fields = {
            "name": elt,
            **kwargs
        }
        _id = len(elts) + 1
        elts.append(fixt(_id, elt_name, fields))
        keys[elt] = _id
        print(f"added {elt_name} :  {elt} with id {_id}")
    else:
        _id = keys[elt]
    return _id


def fixt(pk, model, fields):
    fixt_ = {
        "model": f"api.{model}",
        "fields": fields
    }
    if pk is not None:
        fixt_["pk"] = pk
    return fixt_


def export_json(name, array):
    os.makedirs("fixtures", exist_ok=True)
    with open(f"fixtures/{name}.json", 'w') as handler:
        json.dump(array, handler, indent=2)


if __name__ == "__main__":
    print("Getting the sheets...")
    ach = Ach()
    sheets = ach.get_sheets()

    users = []
    user_keys = {}
    for user in sheets.columns[:-1]:
        u_fields = {
            "name": user,
            "spotify_id": None,
            "blacklist": [],
            "friends": []
        }
        _id = len(users) + 1
        user_keys[user] = _id
        users.append(fixt(_id, 'user', u_fields))

    artists = []
    artist_keys = {}
    albums = []
    album_keys = {}
    genres = []
    genre_keys = {}
    songs = []
    grades = []

    for line in sheets.iterrows():
        genre, sub_genres_list, artists_list, album, song = line[0]
        genre_id = element_id(genre, genre_keys, genres, 'genre')
        artists_id = [
            element_id(artist.strip(), artist_keys, artists,
                       'artist', spotify_id=None, albums=[])
            for artist in artists_list.split(',')]
        album_id = element_id(album, album_keys, albums,
                              'album', spotify_id=None, date=None)
        song_id = len(songs) + 1
        song_fields = {
            "name": song,
            "spotify_id": None,
            "album": album_id,
            "genres": [genre_id],
            "artists": artists_id
        }
        songs.append(fixt(song_id, 'song', song_fields))
        for user, user_id in user_keys.items():
            grade_str = line[1][user]
            grade_nb = 0
            if not grade_str:
                break
            try:
                grade_nb = float(grade_str)
            except ValueError:
                break
            grades_fields = {
                "grade": float(grade_str),
                "user": user_id,
                "song": song_id
            }
            grades.append(fixt(None, 'grade', grades_fields))

    export_json("songs", songs)
    export_json("artists", artists)
    export_json("grades", grades)
    export_json("albums", albums)
    export_json("users", users)
    export_json("genres", genres)
