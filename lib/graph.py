from functools import total_ordering

def frombytes(val):
    return val.decode('utf8') if type(val) == bytes else val

@total_ordering
class Edge:

    def __init__(self, weigth=0, to_layer=0, from_street='', to_street='', from_nearestnode='', to_nearestnode='', parent=None):
        self.weigth           = weigth
        self.to_layer         = to_layer
        self.from_street      = frombytes(from_street)
        self.to_street        = frombytes(to_street)
        self.from_nearestnode = frombytes(from_nearestnode)
        self.to_nearestnode   = frombytes(to_nearestnode)
        self.from_nearestnode = frombytes(from_nearestnode)
        self.to_nearestnode   = frombytes(to_nearestnode)
        self.parent           = parent

    def __eq__(self, other):
        pass

    def __lt__(self, other):
        pass

    def __hash__(self):
        return hash(self.from_street + '-' + self.to_street)

    def __str__(self):
        return '<Edge:{0} {2}-{3} {1}>'.format(self.to_layer, self.weigth, self.from_nearestnode, self.to_nearestnode)
