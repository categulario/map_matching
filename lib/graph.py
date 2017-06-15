from functools import total_ordering

INF = float('inf')

def frombytes(val):
    return val.decode('utf8') if type(val) == bytes else val

class Node:

    def __init__(self, layer=None, way=None, cost=INF, path=None, parent=None):
        self.cost   = cost
        self.path   = path
        self.parent = parent
        self.layer  = layer
        self.way    = way

    def __hash__(self):
        return Node.hash(self.layer, self.way)

    def __str__(self):
        return '<Node:{} {}>'.format(self.layer, self.cost, self.to_nearestnode)

    @staticmethod
    def hash(layer, way):
        return hash('{}-{}'.format(layer, way))
