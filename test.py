def g(start, val=None):
    x = 4
    if start:
        g.x = val
    else:
        print g.x, x

g(True, 30)
g(False)
g(False)

class X:
    def f(self, start, val=None):
        if start:
            self.f.x = val
        else:
            print self.f.x
x=X()
y=X()

x.f(True, 50)
x.f(False)
x.f(False)

y.f(True, 100)
y.f(False)
y.f(False)
