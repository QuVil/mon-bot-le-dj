from src.muzik import Muzik
from prototyping.playlist import create_playlist, shuffle_playlist
from src.ach import Ach

if __name__ == "__main__":
    # create Spotify connector
    muzik = Muzik()

    # fetches latest update from the datasheet
    ach = Ach()
    sheet = ach.get_sheets()

    # OPTIONAL but better to do
    # updated the cached list with the latest version
    # of the datasheet
    #
    # updates the cached version

    ids = muzik.update(sheet)

    # OPTIONAL but better to do
    # update the missing id list from the sheet
    ach.update_missing(ids, muzik.name)

    # generate playlist with only the songs that "exists"
    playlist = create_playlist(sheet.loc[ids.index], ["Qu", "Vi", "Ro"], count_factor=.8, inhib_factor=2,
                               min_score=7.75, size=150, default_grade=5, eliminating_grade=4.6)

    playlist = shuffle_playlist(playlist, default_transition="4,0", chain_factor=.7, desperation_factor=1,
                                default_threshold=8.5)

    # push the playlist
    muzik.create_playlist(playlist)
