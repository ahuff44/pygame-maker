class PropTest(object):
    def getx(self):
        print 'Retrieving'
        return self._x
    def setx(self, val):
        print 'Updating'
        self._x = val
    x = property(getx, setx)

    def __init__(self, name):
        print 'Initializing'
        self.name = name
        self.x = 10

m = PropTest("Bobby")
print m.x
m.x = 20
print m.x
