import collections

class contributor:
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.ratings = collections.defaultdict(list)
        
    def __str__(self) -> str:
        return self.name
        
    def __repr__(self) -> str:
        return self.name
        
    def __sort_ratings(self):
        self.ratings = { r: self.ratings[r] for r in sorted(self.ratings, reverse=True) }

    def personal_ranking(self) -> list:
        self.__sort_ratings()
        return self.ratings.values()

# Hardcoded contributors and column indexes.
CONTRIBUTORS = [ 
    contributor('Quentin', 'ntQ'), contributor('Gary', 'ntG'), contributor('Vincent', 'ntV'),
    contributor('Romain', 'ntR'), contributor('Samuel', 'ntS'), contributor('Galtier', 'ntGl'), 
    contributor('Roxane', 'ntRx'), contributor('Clémence', 'ntC'), contributor('Lucas', 'ntL')
]

if __name__ == "__main__":
    print("Ach! Musik contributors are: {}".format(CONTRIBUTORS))