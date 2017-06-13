from functools import total_ordering

def frombytes(val):
    return val.decode('utf8') if type(val) == bytes else val

@total_ordering
class Edge:

    def __init__(self, weigth=0, to_layer=0, to_nearestnode='', path=None, parent=None):
        self.weigth         = weigth
        self.to_layer       = to_layer
        self.to_nearestnode = frombytes(to_nearestnode)
        self.path           = path
        self.parent         = parent

    def __eq__(self, other):
        pass

    def __lt__(self, other):
        pass

    def __hash__(self):
        return hash(self.from_street + '-' + self.to_street)

    def __str__(self):
        return '<Edge:{} {} {}>'.format(self.to_layer, self.weigth, self.to_nearestnode)
