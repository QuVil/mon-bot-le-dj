import math
import random
import re

import pandas as pd
from prototyping.data import load_from_api


def create_playlist(data, people=None, count_factor=.1, inhib_factor=2, min_score=5.5, size=300, default_grade=5,
                    eliminating_grade=4.6, default_genres=True, playlist_type="default"):
    """
    Create a personalized playlist with ACHMUSIK data loaded directly from the sheet
    :param playlist_type: default or reco
    :param default_genres: Whether or not to apply default genre grades to total table
    :param data:
    :param people: The people presently present at the gathering to include in the scoring
    :param count_factor: multiplicative factor to help properly graded songs rise to the top
    :param inhib_factor: the added factor to scoring is count_factor * (COUNT - len(people) / inhib_factor)
    :param min_score: minimum score for songs to be kept in the roulette wheel
    :param size: size of the playlist
    :param default_grade: grade applied to songs not graded by any member of people yet
    :param eliminating_grade: minimum required grade for every person (unless not graded yet)
    :return: a shuffled playlist (DataFrame)
    """
    if people is None:
        people = ["Qu", "Gr", "Vi", "Ro"]
    count_inhib = len(people) // inhib_factor

    # Keeping only present people at the hypothetical party!
    data = data.filter(people)

    # Keeping only non numerical results (recommendations) for reco type PL
    # TODO allow for more than 1 person to create a recommended playlist! Couldn't figure out the snippet to do it right
    if playlist_type == "reco":
        data = data[data[people[0]].apply(lambda x: "." not in x and not x.isnumeric() and x != "")]
    else:
        for i in range(data.columns.size):
            data[data.columns[i]] = pd.to_numeric(data[data.columns[i]], errors='coerce')

    # Applying default genre grades if necessary
    if default_genres and playlist_type != "reco":
        print("Applying default genre grades...")
        defaults = load_from_api("genre_default", fallback="data/csv/genre_default.csv")

        for i in range(1, defaults.columns.size):
            defaults[defaults.columns[i]] = pd.to_numeric(defaults[defaults.columns[i]], errors='coerce')
        defaults = defaults.set_index(["genre"])

        # index holds genre, sub_genre, artist, album and song, row the rest
        for index, row in data.iterrows():
            for person, grade in row[5:-2].items():
                if math.isnan(grade) and defaults.at[index[0], person]:
                    data.loc[index, person] = defaults.at[index[0], person]

    # Hard to do this shit inplace -- if no grades at all, give it a chance to play with default grade
    data = data.dropna(how="all").append(data[data.isnull().all(axis=1)].fillna(default_grade))

    # No need for score for recommendation PLs
    if playlist_type != "reco":
        # Mean of all notes for each track
        data["mean"] = data[data.columns].mean(axis=1)
        # Amount of notes for each track
        data["count"] = data.count(axis=1) - 1
        # Helping songs graded by more people in the group
        data["score"] = data["mean"] + (count_factor * (data["count"] - count_inhib))
        # Truncating to keep only the acceptable songs
        data = data[data["score"] > min_score]
    else:
        data["score"] = 10

    # Using ranking of scores as weight for the playlist bootstrap
    print("Creating playlist...")
    data = data.sort_values("score", ascending=False)
    data["rank"] = data["score"].rank(method="min")

    # Eliminating tracks with a grade under the required minimum
    if playlist_type != "reco":
        data = data[data[data.columns[:-4]].min(axis=1) > eliminating_grade]

    # Creating bootstrap sample of adequate size
    playlist = data.sample(n=size if size < len(data) else len(data), weights="rank")

    return playlist


def shuffle_playlist(playlist, default_transition="4,0", chain_factor=.6, desperation_factor=1, default_threshold=8,
                     verbose=False):
    """
    shuffles a playlist according to genre distance scores
    :param verbose: self-explanatory
    :param playlist: DataFrame created by create_playlist()
    :param default_transition: default value for transition scores between different genres
    :param chain_factor: 0 < < 1 -- how much chaining the same genre again and again lowers the threshold
    :param desperation_factor: if no track is found after looping over the playlist, how much to lower threshold
    :param default_threshold: default threshold for the score needed to accept track as next in shuffle
    :return: a shuffled playlist (DataFrame)
    """
    transitions = load_from_api("Transitions", fallback="data/csv/transitions.csv").fillna(default_transition)
    transitions.index = transitions[""]
    transitions.drop("", axis=1, inplace=True)

    # Getting the decimals right again -- commas to points and no more Nones
    for i in range(transitions.columns.size):
        transitions[transitions.columns[i]] = transitions[transitions.columns[i]].str.replace(",", ".")
        transitions[transitions.columns[i]] = pd.to_numeric(transitions[transitions.columns[i]], errors='coerce')

    playlist.reset_index(inplace=True)

    # This is so horribly un-optimized... May the Python Lords forgive me.
    shuffled_playlist = playlist.iloc[0:1].drop(playlist.columns[5:], axis=1)
    playlist.drop(0, inplace=True)
    current_genre = shuffled_playlist.iloc[0]["genre"]
    current_artist = shuffled_playlist.iloc[0]["artist"]

    chain = 0
    threshold = default_threshold
    remove_indices = []

    while playlist.size > 0:
        for row in playlist.iterrows():
            if current_genre != row[1]["genre"]:
                chain_score = (chain * chain_factor)
            else:
                chain_score = -(chain * chain_factor) / 2

            if verbose:
                print("Trying with ", row[1]["song"], " from ", row[1]["artist"], "-- of genre ", row[1]["genre"],
                      " transition score from ", current_genre, " is ", transitions[current_genre][row[1]["genre"]],
                      " plus ", chain, " adding ", chain_score)
                print("threshold is currently ", threshold)

            if (transitions[current_genre][row[1]["genre"]] + chain_score > threshold
                and (row[1]["artist"] != current_artist or threshold != default_threshold)) or threshold < 0:
                if verbose:
                    print("ACCEPTED")
                # Song accepted -- increment or reset chain + reset threshold if lowered
                if current_genre == row[1]["genre"]:
                    chain += 1
                else:
                    chain = 0
                    current_genre = row[1]["genre"]
                    threshold = default_threshold

                # Add song to shuffled playlist and its index to a list for further removal
                shuffled_playlist = shuffled_playlist.append(playlist.loc[row[0]].drop(playlist.columns[5:]))
                remove_indices.append(row[0])
                # Reset threshold if it has gone too low
                if (default_threshold - threshold) > 2:
                    threshold = default_threshold

        # Removing songs that were added during the for loop
        if remove_indices:
            playlist.drop(remove_indices, inplace=True)
            remove_indices = []
            threshold = default_threshold
        else:
            threshold -= desperation_factor

    return shuffled_playlist.reset_index(drop=True).set_index(["genre", "sub_genre", "artist", "album", "song"])


if __name__ == "__main__":
    sheet = pd.read_csv("../data/csv/achmusik.csv")
    print(create_playlist(sheet))
