NONE = 0
PASSIVE = 1
ACTIVE = 2

class CollisionEnforcer(type):
    def __init__(cls, name, bases, dct):
        """ Checks to make sure the game programmer hasn't messed up by giving a ev_collision method to an object that doesn't do collisions"""
        if name != CollisionEnforcer.BASE_OBJ_NAME:
            assert issubclass(cls, GameObject), name
            print cls, name
            derived_fxn = cls.ev_collision.__func__
            base_fxn = GameObject.ev_collision.__func__
            if not cls.collisions and derived_fxn is not base_fxn:
                raise RuntimeError("Class %s has collisions = NONE yet it has an ev_collision event"%(name))
            else:
                print "Class %s passed ev_collision inspection"%(name)
        return super(CollisionEnforcer, cls).__init__(name, bases, dct)

    def test(self):
        pass

CollisionEnforcer.BASE_OBJ_NAME = "GameObject"
class GameObject(object):
    __metaclass__ = CollisionEnforcer
    collisions = NONE
    def ev_collision(self, other):
        pass


class Shot(GameObject):
    collisions = ACTIVE
    def ev_collision(self, other):
        # super(SubKlassA, self).ev_collision()
        print "Shot coll"

class Wall(GameObject):
    collisions = NONE

class MegaShot(Shot):
    def ev_collision(self, other):
        print "MegaShot coll"


for klass in [Shot, Wall, MegaShot]:
    obj = klass()
    obj.ev_collision(obj)
