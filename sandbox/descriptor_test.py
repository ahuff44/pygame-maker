class RevealAccess(object):
    """A data descriptor that sets and returns values
       normally and prints a message logging their access.
    """
    def __init__(self, initval=None, name='var'):
        print "Initializing", name, "to", initval
        self.val = initval
        self.name = name
    def __get__(self, obj, objtype):
        print 'Retrieving', self.name, "from", obj.name, "(type %s)"%str(objtype)
        return self.val
    def __set__(self, obj, val):
        print 'Updating', self.name, "in", obj.name, "to", val
        self.val = val

class DescTest(object):
    def __init__(self, name):
        self.name = name
    x = RevealAccess(10, 'var "x"')
    y = 5

m = DescTest("Bobby")
m.x
m.x = 20
m.x
m.y





