class Shape(object):
  def __init__(self, name):
    super(Shape, self).__init__()
    self.name = name

class Rectangle(Shape):
  def __init__(self, name, width, height):
    super(Rectangle, self).__init__(name)
    self.width = width
    self.height = height

class Square(Rectangle):
  def __init__(self, name, width):
    super(Square, self).__init__(name, width, width)

class Creature(object):
  def __init__(self, name, age):
    super(Creature, self).__init__()
    self.name = name
    self.age = age

class Sponge(Creature):
  def __init__(self, name, age, color):
    super(Sponge, self).__init__(name, age)
    self.color = color

# class SquareSponge(Square, Sponge):
#   def __init__(self, name, width, age, color):
#     super(SquareSpong, self).__init__()


# bob = SpongeSquare("Bob", 10, 18, "yellow")
sq = Square("Larry", 10)
print "Larry:"
print sq.name, sq.width, sq.height
print "MROs:"
print Square.__mro__
# print SquareSponge.__mro__
assert isinstance(sq, Square)
assert isinstance(sq, Rectangle)
assert isinstance(sq, Shape)
