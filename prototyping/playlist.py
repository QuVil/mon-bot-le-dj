import random

import pandas as pd


def create_playlist(data, people=None, count_factor=.1, inhib_factor=2, min_score=5.5, size=300, default_grade=5,
                    eliminating_grade=4.6):
    """
    Create a personalized playlist with ACHMUSIK data loaded directly from the sheet
    :param eliminating_grade: minimum required grade for every person (unless not graded yet)
    :param people: The people presently present at the gathering to include in the scoring
    :param count_factor: multiplicative factor to help properly graded songs rise to the top
    :param inhib_factor: the added factor to scoring is count_factor * (COUNT - len(people) / inhib_factor)
    :param min_score: minimum score for songs to be kept in the roulette wheel
    :param size: size of the playlist
    :param default_grade: grade applied to songs not graded by any member of people yet
    :return:
    """
    if people is None:
        people = ["Qu", "Gr", "Vi", "Ro"]
    count_inhib = len(people) // inhib_factor

    for i in range(data.columns.size):
        data[data.columns[i]] = data[data.columns[i]].str.replace(",", ".")
        data[data.columns[i]] = pd.to_numeric(data[data.columns[i]], errors='coerce')

    # Keeping only present people at the hypothetical party!
    data = data.filter(people)

    # Hard to do this shit inplace -- if no grades at all, give it a chance to play with default grade
    data = data.dropna(how="all").append(data[data.isnull().all(axis=1)].fillna(default_grade))

    # Mean of all notes for each track
    data["mean"] = data[data.columns].mean(axis=1)
    # Amount of notes for each track
    data["count"] = data.count(axis=1) - 1
    # Helping songs graded by more people in the group
    data["score"] = data["mean"] + (count_factor * (data["count"] - count_inhib))
    # Truncating to keep only the acceptable songs
    data = data[data["score"] > min_score]

    # Using ranking of scores as weight for the playlist bootstrap
    print("Creating playlist...")
    data = data.sort_values("score", ascending=False)
    data["rank"] = data["score"].rank(method="min")

    # Eliminating tracks with a grade under the required minimum
    data = data[data[data.columns[:-4]].min(axis=1) > eliminating_grade]

    playlist = data.sample(n=size, weights="rank")

    # Rearranging playlist to avoid sudden genre changes
    genres = [playlist for _, playlist in playlist.groupby("genre")]
    random.shuffle(genres)

    return pd.concat(genres)


if __name__ == "__main__":
    print(create_playlist())
