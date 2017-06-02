from functools import total_ordering

@total_ordering
class Edge:

    def __init__(self, weigth=0, layer=0, from_street='', to_street='', from_nearestnode=None, to_nearestnode=None, parent=None):
        self.weigth           = weigth
        self.layer            = layer
        self.from_street      = from_street
        self.to_street        = to_street
        self.from_nearestnode = from_nearestnode
        self.to_nearestnode   = to_nearestnode
        self.parent           = parent

    def __eq__(self, other):
        pass

    def __lt__(self, other):
        pass

    def __hash__(self):
        return hash(self.from_street + '-' + self.to_street)
