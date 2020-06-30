
class track:
    def __init__(self, genre, subgenre, artist, album, title):
        self.genre = genre if genre else None
        self.subgenre = subgenre if subgenre else None
        self.artist = artist if artist else None
        self.album = album if album else None
        self.title = title if title else None

    def __str__(self) -> str:
        return "{}, {}, {}, {}, {}".format(self.genre, self.subgenre, self.artist, self.album, self.title)
        
    def __repr__(self) -> str:
        return "{}".format(self.title)
        
if __name__ == "__main__":
    import data

    print("Those are the listed track on Ach! Musik: ")
    for row in data.data():
        print(track(row[0], row[1], row[2], row[3], row[4]))