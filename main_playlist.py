
from src.muzik import Muzik
from src.ach import Ach
from prototyping.playlist import create_playlist

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
    playlist = create_playlist(sheet.loc[ids.index])
    # push the playlist
    muzik.create_playlist(playlist)
