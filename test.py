class MyMeta(type):
    def __init__(cls, name, bases, dct):
        obj = map(str, (cls, name, map(str, bases), dct))
        print "%s, %s, %s, %s"%tuple(obj)

class MyKlass(object):
    __metaclass__ = MyMeta

    attr = 4

    def __init__(self, *args):
        print "Initialized"

print
print "Done defining"
print

k = MyKlass(3, 5)
