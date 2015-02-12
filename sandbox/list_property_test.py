"""
How do I make a read-only class property in python?

Some background:

I can make *local* read-only properties like this:

"""

class LocalTest(object):
    def __init__(self):
        self._local_array = [2, 3, 5]

    @property
    def local_array(self):
        return self._local_array

test = LocalTest()
print test.local_array
test.local_array.append(7)
print test.local_array
test.local_array = [2, 4, 6] # I want this line to throw an error (and it does)

"""
This produces the following output when run:


>>> run test.py
local_test:
[2, 3, 5]
[2, 3, 5, 7]
---------------------------------------------------------------------------
AttributeError                            Traceback (most recent call last)
c:\path\to\my\file\test.py in <module>()
     21 local_test.local_property.append(7)
     22 print local_test.local_property
---> 23 local_test.local_property = [2, 4, 6]
     24
     25

AttributeError: can't set attribute


Note that this is intended behavior: I *do* want to be able to use .append(), I just don't want to accidentally overwrite the variable.
(Is there a more pythonic way to get this behavior? Is it even pythonic at all to want this behavior?)

Now my problem is this: How can I get this behavior on a class variable?

None of the following methods work: (I don't want to get errors from any of these methods but I do)
"""

class ClassTest1(object):
    _static_array = [1, 3, 7, 15]
    @staticmethod
    def get_static_array():
        return _static_array
    static_array = property(get_static_array)

test1 = ClassTest1()

print test1.static_array # --> TypeError: 'staticmethod' object is not callable
test1.static_array.append(7)



class ClassTest2(object):
    _static_array = [1, 3, 7, 15]
    @staticmethod
    @property
    def static_array():
        return _static_array

test2 = ClassTest2()

print test2.static_array
test2.static_array.append(7) # --> AttributeError: 'property' object has no attribute 'append'



class ClassTest3(object):
    _static_array = [1, 3, 7, 15]
    @property
    @staticmethod
    def static_array():
        return _static_array

test3 = ClassTest3()

print test3.static_array # TypeError: 'staticmethod' object is not callable
test3.static_array.append(7)



### I never ended up posting this; I found some similar questions and the easiest answer seems to be "you can't keep the user from doing stupid things". (they DID have solutions, but they got COMPLICATED (e.g. metaclasses))
