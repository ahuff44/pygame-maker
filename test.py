class X:
    def __init__(self, a):
        self.a = a
        self.__b = a

    def m(self):
        print self.a
        print self.__b

def a2(self):
    print (2*self.a)
    print (2*self.__b)

x = X(2)
x.m()
x.m = lambda: a2(x)
x.m()
