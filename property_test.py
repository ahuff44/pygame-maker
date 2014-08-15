import scipy as sp


class PropTest(object):

    @property
    def x(self):
        return self.pos[0]
    @x.setter
    def x(self, value):
        self.pos[0] = value

    @property
    def y(self):
        return self.pos[1]
    @y.setter
    def y(self, value):
        self.pos[1] = value

    def __init__(self, pos):
        print 'Initializing'
        self.pos = sp.array(pos)

m = PropTest((11, 32))
print m.x, m.y, m.pos
m.x = 20
print m.x, m.y, m.pos
m.y += 100
print m.x, m.y, m.pos
