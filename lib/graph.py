from functools import total_ordering

@total_ordering
class StreetNode:

    def __init__(self, weight, layer, name, parent=None):
        self.weight = weight
        self.name = name
        self.parent = parent
        self.layer = layer

    def __eq__(self, other):
        pass

    def __lt__(self, other):
        pass

    def __hash__(self):
        return hash(self.name)
