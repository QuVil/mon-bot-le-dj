
from .color import Color
import pandas as pd
import numpy as np
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import spotipy
from spotipy import SpotifyException
import math
import json
import hashlib
import os
import base64
CACHE_DIR = "cache/"
ACH_IDS = "ids.pkl"
MISSING_IDS = "missing.csv"
CRED_PATH_SPOTIFY = "credentials-spotify.json"
UNAUTHORIZED_ST_CODE = 401
MAX_TRACK_PER_REQUESTS = 100
MARKETS = ["FR", "US"]
PLAYLIST_NAME = "Mon Bot le DJ"
PLAYLIST_COVER = "data/playlist_cover.jpg"
PLAYLIST_DESC = "Auto generated playlist for the"\
                " project mon-bot-le-dj, visit"\
                " https://github.com/QuVil/mon-bot-le-dj"\
                " for more information"


class Muzik:

    def __init__(self, public_api=False):
        self.__create_cache_dir()
        self.ids = self.__read_cached_ids()
        if public_api:
            self.__sp = self.__connect_spotify()
        self.__sp_user = self.__connect_spotify_user()
        self.__user_id = self.__sp_user.me()["id"]

    def __create_cache_dir(self):
        """
        Create cache dir at `CACHE_DIR` if doesn't already exists
        """
        if not os.path.isdir(CACHE_DIR):
            os.mkdir(CACHE_DIR)

    def __read_cached_ids(self) -> pd.Series:
        """
        Read the cached already fetched ids from the cache folder
        either returns the cached pd.Series, or empty series if
        no file there
        """
        path = CACHE_DIR + ACH_IDS
        if os.path.exists(path):
            print(f"Reading data from cache file {path}")
            df = pd.read_pickle(path)
        else:
            df = pd.Series()
        print(f"Local library contains {len(df)} songs")
        return df

    def __read_credentials(self):
        """
        Opens and return the content of `CRED_PATH_SPOTIFY` as
        a python dict
        """
        with open(CRED_PATH_SPOTIFY, 'r') as handle:
            data = json.load(handle)
        return data

    def __connect_spotify_user(self):
        """
        Connect to the API using the spotify user credentials
        needs more informations than the other method, but can
        access to personnal informations (including playlists :o)
        of the user
        """
        data = self.__read_credentials()
        # generate a unique random number to prevent csrf
        state = hashlib.sha256(os.urandom(1024)).hexdigest()
        self.__user_credentials = SpotifyOAuth(
            **data,
            state=state,
        )
        return self.__get_spotify_user(
            self.__user_credentials.get_access_token(as_dict=(False))
        )

    def __get_spotify_user(self, token):
        """
        Returns a Spotify client authentified with the provided
        token
        """
        return spotipy.Spotify(
            auth=token
        )

    def __connect_spotify(self):
        """
        Connect to the public API of Spotify, useful to fetch songs ids
        since the API limite rate is higher here, however not really
        useful to create playlists and stuff
        """
        data = self.__read_credentials()
        auth = {}
        auth["client_id"] = data["client_id"]
        auth["client_secret"] = data["client_secret"]
        return spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            **auth
        ))

    def __refresh_token(self):
        """
        Refreshes the tokenn if it has expired or not
        and updates the sp_user Spotify Interface with
        the new token
        """
        cached = self.__user_credentials.get_cached_token()
        refreshed = self.__user_credentials.refresh_access_token(
            cached["refresh_token"]
        )
        self.__sp_user = self.__get_spotify_user(
            refreshed["access_token"]
        )

    def __update_token(self):
        """
        Updates the token if it has expired
        !! may not work flawlessely (probably not in fact),
        hard to test since the token lasts for 1 hour haha
        """
        # built-in function, does not work always good
        cached = self.__user_credentials.get_cached_token()
        if self.__user_credentials.is_token_expired(cached):
            print("Token expired, refreshing now")
            self.__refresh_token()
        # handmade function just in case the one above fails
        try:
            _ = self.__sp_user.me()
        except SpotifyException as e:
            if e.http_status == UNAUTHORIZED_ST_CODE:
                print("Token expired, refreshing now")
                self.__refresh_token()

    def __search_strings(self, row):
        """
        Creates the search string for the Spotify API based on
        the information of the row
        Returns a list of multiple strings, to take into account
        if there is special characters (like "'")
        or multiple markets
        input:
            - row : pd.Series with genre, artists, songs,...
        output:
            - searches : list of tuples (search string, market)
        """
        search = ""
        # artists
        artists = list(map(str.strip, row.artist.split(",")))
        if len(artists) > 1:
            sep = '" AND "'
            search += f"artist:\"{sep.join(artists)}\""
        else:
            search += f"artist:\"{artists[0]}\""
        # album
        if row.album != "N/A":
            search += f" album:\"{row.album}\""
        # track name
        search += f" track:\"{row.song}\""
        # dealing with "'""
        # sometimes it will work with the "'" and sometimes not
        if "'" in search:
            searches_s = [search, search.replace("'", "")]
        else:
            searches_s = [search]
        searches = []
        for market in MARKETS:
            for search in searches_s:
                searches.append((search, market))
        return searches

    def __fetch_id(self, df):
        """
        Fetches the Spotify songs id for each provided songs
        If it cannot find ids for a song, it will be set to None
        input:
            - df : a pd.DataFrame with a random index and the
                   song specific columns (genre, artist, ...)
        """
        # small hack to access the data from the index & the columns
        indexs = pd.MultiIndex.from_frame(df)
        songs = pd.DataFrame(data=df.values, index=indexs,
                             columns=df.columns)
        ids = pd.Series(index=indexs,
                        dtype=str, name="ids")
        bad_formats = []
        # chosing the endpoint
        # by default try to take the public one, if doesn't exists
        # (public_api = False), use the private one
        try:
            endpoint = self.__sp
        except AttributeError:
            endpoint = self.__sp_user
        # format string padding used for the debug output
        str_format = int(math.log(len(songs), 10)) + 1
        for idx, (_, content) in enumerate(songs.iterrows()):
            searches = self.__search_strings(content)
            bad_format = []
            for search, market in searches:
                try:
                    res = endpoint.search(search, market=market)
                    track = res['tracks']['items'][0]
                except IndexError:
                    bad_format.append((search, market))
                else:
                    # succeed to fetch an id
                    break
            else:
                # did not managed to find an id with all the search strings
                # provided, set the id of the song to None
                bad_formats.append(bad_format)
                ids.iloc[idx] = None
                print(f"{Color.FAIL}"
                      f"{idx + 1:<{str_format}}/{len(df)}"
                      f"{Color.ENDC}"
                      f" : {search} not in Spotify")
                continue
            album = track['album']['name']
            name = track['name']
            artist = track['artists'][0]['name']
            id = track['id']
            ids.iloc[idx] = id
            print(f"{Color.OKGREEN}"
                  f"{idx + 1:<{str_format}}/{len(df)}"
                  f"{Color.ENDC}"
                  f" : {id} {name} {artist} {album}")
        return ids

    def __update_missing_list(self):
        """
        Create a csv file containing every tracks that were not
        available on spotify
        """
        missing = self.ids[self.ids.isnull()]
        missing.index.to_frame(index=False).to_csv(CACHE_DIR + MISSING_IDS)

    def __create_user_playlist(self):
        """
        Creates a new playlist using PLAYLIST_NAME, PLAYLIST_DESC
        also pushes playlist cover PLAYLIST_COVER
        return:
            - playlist_id : string containing the id of the playlist
        """
        # create the playlist with name, description, visibility
        print(f"Creating {PLAYLIST_NAME}...")
        ret = self.__sp_user.user_playlist_create(user=self.__user_id,
                                                  name=PLAYLIST_NAME,
                                                  public=True,
                                                  description=PLAYLIST_DESC)
        playlist_id = ret["id"]
        # most important, upload the playlist image
        print(f"Uploading playlist cover from {PLAYLIST_COVER}")
        with open(PLAYLIST_COVER, "rb") as image_file:
            cover = base64.b64encode(image_file.read())
        ret = self.__sp_user.playlist_upload_cover_image(playlist_id, cover)
        return playlist_id

    def __get_playlist_id(self):
        """
        Returns the playlist id of PLAYLIST_NAME
        if the playlist doesn't exists yet, it will create it
        and return the id of the newly created playlist
        """
        # check if the playlist already exists
        user_playlists = self.__sp_user.user_playlists(self.__user_id)
        playlist_id = None
        if len(user_playlists["items"]) > 0:
            for user_pl in user_playlists["items"]:
                if user_pl["name"] == PLAYLIST_NAME:
                    playlist_id = user_pl["id"]
                    break
        # at this point, if the playlist exists, the id is stored in
        # playlist_id, otherwise we have still a None value
        if playlist_id is None:
            print(f"Playlist {PLAYLIST_NAME} doesn't exists yet")
            playlist_id = self.__create_user_playlist()
        print(f"Using playlist {PLAYLIST_NAME} : {playlist_id}")
        return playlist_id

    def update(self, ach):
        """
        updates the known list of ids with the newer version of the
        ach musik sheet
        input:
            - ach : raw sheet from google with multiindex
        """
        self.__update_token()
        # turn the index to DataFrame objects
        new_songs = ach.index.to_frame().reset_index(drop=True)
        if self.ids.empty:
            # in case the cached list was empty, simply fetch the whole
            # list
            self.ids = self.__fetch_id(new_songs)
        else:
            old_songs = self.ids.index.to_frame().reset_index(drop=True)
            # get the list of the common values
            common_songs = new_songs.merge(old_songs, how='inner')
            # remove the songs that are not anymore in the cached df
            depr = pd.concat([common_songs, old_songs]
                             ).drop_duplicates(keep=False)
            to_remove = pd.MultiIndex.from_frame(depr)
            if len(to_remove) > 0:
                self.ids = self.ids.drop(to_remove)
            # adds the new songs from the ach sheet
            news = pd.concat([common_songs, new_songs]
                             ).drop_duplicates(keep=False)
            if len(news) > 0:
                new_ids = self.__fetch_id(news)
                self.ids = pd.concat([self.ids, new_ids])
            else:
                print("Local list already updated")
        # save updated list in cache
        self.ids.to_pickle(CACHE_DIR + ACH_IDS)
        # also updates missing ID list
        self.__update_missing_list()

    def create_playlist(self, playlist):
        """
        Create (or replace) a playlist containing all the songs provided
        in the playlists DataFrame
        input:
            - playlist : pd.DataFrame indexed by a MultiIndex with
                         genre, artist, song, ...
        """
        self.__update_token()
        # get the playlist id of PLAYLIST_NAME
        playlist_id = self.__get_playlist_id()
        # get the tracks
        print(self.ids[self.ids.index.duplicated()])
        tracks_all = self.ids[playlist.index]
        tracks_results = tracks_all.isnull().value_counts()
        print(f"Adding {tracks_results[False]} tracks,"
              f" Missing {tracks_results[True]} tracks")
        tracks_id = tracks_all.dropna().values
        print(f"Inserting {len(tracks_id)} songs in the playlist...")
        # spotify api "only" handles 100 tracks by requests
        # so here we split the data
        batch_size = int(len(tracks_id)/MAX_TRACK_PER_REQUESTS) + 1
        batches = np.array_split(tracks_id, batch_size)
        str_format = int(math.log(len(batches), 10)) + 1
        print(f"{0:<{str_format}}/{len(batches)} batch inserting...")
        # the first call `replace_tracks` clear the playlist AND
        # adds the supplied tracks
        self.__sp_user.user_playlist_replace_tracks(
            self.__user_id,
            playlist_id=playlist_id,
            tracks=batches[0]
        )
        if len(batches) > 1:
            for idx, batch in enumerate(batches[1:]):
                print(f"{idx+2:<{str_format}}/{len(batches)}"
                      " batch inserting...")
                # add the rest of the tracks
                self.__sp_user.user_playlist_add_tracks(
                    self.__user_id,
                    playlist_id=playlist_id,
                    tracks=batch
                )

        print("Playlist done")

    def get_playlists(self):
        self.__update_token()
        return self.__sp_user.user_playlists(self.__user_id)
