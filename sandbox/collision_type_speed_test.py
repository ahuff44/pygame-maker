"""
I'm wondering what the fastest way to test the collision type of objects is
Possibilities:
    1) objects that have instance variables
    2) objects that have class variables
    3) objects that are of certain classes (isinstance() testing)
    4) objects automatically added to a set that keeps track of all e.g. passive colliding objects
    5) using pygame.Sprite and its Groups. (but I've seen the source and it's basically #4)
"""

from matplotlib import pyplot as plt
import numpy as np
from timeit import timeit

size = 1000
num_tests = 1000

class ClassVar_Solid(object):
    class_solid = True
    def __init__(self, solid):
        self.instance_solid = solid

class ClassVar_NotSolid(object):
    class_solid = False
    def __init__(self, solid):
        self.instance_solid = solid

solids = {ClassVar_Solid(True) for x in xrange(size)}
not_solids = {ClassVar_NotSolid(False) for x in xrange(size)}

all_objs = list(solids) + list(not_solids)

def do_filter(tester, objs):
    solid_results = set()
    not_solid_results = set()
    np.random.shuffle(objs)
    for obj in objs:
        if tester(obj):
            solid_results.add(obj)
        else:
            not_solid_results.add(obj)
    return solid_results, not_solid_results

methods = [
    ("instance variables", lambda obj: obj.instance_solid),
    ("class variables", lambda obj: obj.class_solid),
    ("isinstance", lambda obj: isinstance(obj, ClassVar_Solid)),
    ("set membership", lambda obj: obj in solids),
]

print "Results: (size=%d, num_tests=%d)"%(size, num_tests)
for doc, fxn in methods:
    time = timeit(lambda: do_filter(fxn, all_objs), number=num_tests)
    print "\t%s: %f"%(doc, time)

"""
Results: (size=1000, num_tests=1000)
        instance variables: 1.857847
        class variables: 1.636275
        isinstance: 1.933527
        set membership: 1.088798
"""
"""
The results still vary pretty wildly... (why???) ...but it's generally 4 (best) < 2 < 1 < 3 (worst)
"""

def do_filter():
    solid_results = set()
    not_solid_results = set()
    for obj in solids:
        solid_results.add(obj)
    return solid_results, not_solid_results # won't actually return any not_solids
doc = "direct set membership (looping over member set)"
time = timeit(do_filter, number=num_tests)
print "\t%s: %f"%(doc, time)    # ooh yeah this is hella better (~4x faster)
