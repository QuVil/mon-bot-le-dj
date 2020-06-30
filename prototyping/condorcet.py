import contributor
from data import data
from track import track
import utils

def initialize() -> tuple:
    tracks, ratings = [], {}
    for label, content in data.data.iterrows():
        current_track = track.track(content.genre, content.sub_genre, content.artist, content.album, content.song)
        tracks.append(current_track)
        ratings[current_track] = { c: utils.as_real_or_none(content[c.index]) for c in contributor.CONTRIBUTORS }
    return (tracks, ratings)


def condorcet_method(candidate):
    pass

def schulze_method():
    pass

tracks, ratings = initialize()
for t in ratings:
    for c in ratings[t]:
        if ratings[t][c]:
            c.ratings[ratings[t][c]].append(t) 

for c in contributor.CONTRIBUTORS:
    print("{}: {}".format(c, c.personal_ranking()))