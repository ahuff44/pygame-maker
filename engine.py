# TODO test the speed of pygame.sprite.collide_rect... can I overwrite it? pretty please?
# TODO replace GM terminology object->class. keep "instance" though

from __future__ import division

from copy import copy
import pygame as pg
import scipy as sp
# from numpy.linalg import norm

import itertools as itt
import sys

from pygame.locals import *


RIGHT = 0 # TODO do something with these
UP    = 1
LEFT  = 2
DOWN  = 3

FPS = 30 # TODO do something with these
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
GRID_X = 32
GRID_Y = 32

MOUSE_POS = [0, 0] # NOTE: mutable

class Colors:
    #                R    G    B
    WHITE        = (255, 255, 255)
    BLACK        = (  0,   0,   0)
    BRIGHTRED    = (255,   0,   0)
    RED          = (155,   0,   0)
    BRIGHTGREEN  = (  0, 255,   0)
    GREEN        = (  0, 155,   0)
    BRIGHTBLUE   = (  0,   0, 255)
    BLUE         = (  0,   0, 155)
    BRIGHTYELLOW = (255, 255,   0)
    YELLOW       = (155, 155,   0)
    DARKGRAY     = ( 40,  40,  40)

    GRAY         = (100, 100, 100)
    NAVYBLUE     = ( 60,  60, 100)
    WHITE        = (255, 255, 255)
    ORANGE       = (255, 128,   0)
    PURPLE       = (255,   0, 255)
    CYAN         = (  0, 255, 255)

    ALL = (GRAY, NAVYBLUE, WHITE, RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, CYAN)

bgColor = Colors.NAVYBLUE

def pipe(postprocessor): #TODO move to another file and import
    def _decorator(fxn):
        def _fxn(*args, **kwargs):
            return postprocessor(fxn(*args, **kwargs))
        return _fxn
    return _decorator

def main(window_title, first_room):
    global MOUSE_POS
    global game_room
    game_room = first_room

    pg.init()
    FPS_CLOCK = pg.time.Clock()
    DISPLAY_SURF = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pg.display.set_caption(window_title)

    try:
        game_room.populate_room()
        while True: # Main game loop
            game_tick(FPS_CLOCK, DISPLAY_SURF)
    except:
        pg.quit()
        raise # pass the exception to the cmd line, which will print it for us

def game_tick(FPS_CLOCK, DISPLAY_SURF):
    global game_room

    DISPLAY_SURF.fill(bgColor) #todo move to right before the draw events?

    for inst in copy(game_room.all_instances):
        inst.ev_step_begin()

    for alarm in Alarm.all_alarms:
        alarm.ev_step()

    events = pg.event.get() # TODO do I also need to call pygame.event.poll()?
    #todo enginde idea: have it hold a table of keys and whether or not they're pressed, down, or released
    for ev in events:
        for inst in copy(game_room.all_instances):
            inst.process_event(ev)

    for inst in copy(game_room.all_instances):
        inst.ev_step()

    _do_collisions(copy(game_room.all_instances)) # NOTE: This copy() is very important because of filtering I do later
    _do_boundary_collisions(copy(game_room.all_instances))
    _do_outside_room_events(copy(game_room.all_instances))

    for inst in copy(game_room.all_instances):
        inst.ev_step_end()
        # TODO order?

    for inst in copy(game_room.all_instances):
        inst.ev_draw(DISPLAY_SURF)

    pg.display.update() # TODO difference between this and pg.display.flip()?
    FPS_CLOCK.tick(FPS)


def _do_boundary_collisions(instances):
    for inst in instances:
        if inst.rect:
            side = get_boundary_touching(inst.rect)
            if side != None:
                inst.ev_boundary_collision(side)

def get_boundary_touching(rect): #TODO rename; and think seriously about the fact that "if get_boundary_touching():" will fail in horrible ways since RIGHT == 0
    if rect.right >= WINDOW_WIDTH:
        return RIGHT
    if rect.left <= 0:
        return LEFT #todo engine this whole global constants thing is making me squeamish
    if rect.bottom >= WINDOW_HEIGHT:
        return DOWN
    if rect.top <= 0:
        return UP

def _do_outside_room_events(instances):
    for inst in instances:
        if inst.rect:
            if is_outside_room(inst.rect):
                inst.ev_outside_room()

def is_outside_room(rect):
    return not check_rect_overlap(rect, pg.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

def check_rect_overlap(rect1, rect2): # TODO move into your own rect class?
    return (
            check_interval_overlap((rect1.left, rect1.right), (rect2.left, rect2.right))
            and check_interval_overlap((rect1.top, rect1.bottom), (rect2.top, rect2.bottom))
    )

def check_interval_overlap(t1, t2):
    ''' Returns whether $(a, b)$ interected with $(c, d)$ is not the empty set,
            where t1 and t2 are tuples (a, b) and (c, d);
        '''
    (a, b) = t1
    (c, d) = t2
    assert a <= b, 'Malformed interval'
    assert c <= d, 'Malformed interval'
    return b > c and d > a
    # return not(a <= b <= c <= d or c <= d <= a <= b)

def _do_collisions(instances):
    for inst_a, inst_b in _do_find_collisions(instances):
        print "Collision detected: %s + %s"%(inst_a.__class__.__name__, inst_b.__class__.__name__) # DEBUG
        inst_a.ev_collision(inst_b)

@pipe(list)
def _do_find_collisions(instances):
    ''' Finds collisions among the instances.
        It completely ignores any instance with collisions == GameObject.CollisionType.NONE
        It only generates collision events for instances with collisions == GameObject.CollisionType.ACTIVE,
            but these events can involve the ACTIVE instance colliding with a PASSIVE instacnce
        '''
    colliding_instances = filter(lambda inst: inst.collisions, instances) # NOTE: This list has been copy()ed before
    for i, inst_a in enumerate(colliding_instances):
        if inst_a.collisions == GameObject.CollisionType.ACTIVE:
            for inst_b in colliding_instances[i+1:]:
                if inst_a == inst_b:
                    raise Exception("Programmer Logic error; you shouldn't be seeing this message (this is a bug in the game engine; there's probably an instance that is on the instance list twice)") # TODO make sure this actually throws this error if there are duplicates
                if (
                        inst_a.rect != None and inst_b.rect != None
                        and check_rect_overlap(inst_a.rect, inst_b.rect)
                ):
                    yield (inst_a, inst_b)

# Convinience functions:

def terminate(): # TODO make a mixin to be added to Controllers that automatically does this
    pg.quit() # redundant because of the try-catch
    sys.exit()

@pipe(list)
def get_instances_at_position(pos):
    """ Returns a list off all instances that are at the given position
        Calculated by seeing what instances would collide with a point
        """
    for inst in copy(game_room.all_instances):
        if inst.rect != None and check_rect_overlap(inst.rect, pg.Rect(pos[0], pos[1], 0, 0)):
            yield inst

def clamp(x, a, b):
    ''' Clamps the value of x to be between a and b:
            Returns x if $x \in [a, b]$
            Returns a if $x < a$
            Returns b if $x > b$
        '''
    return min(max(a, x), b)

random_int = sp.random.randint

# TODO there's lots of stuff that will break when you add multiple rooms. The main game loop will break, for one
class Room(object):
    @property
    def all_instances(self):
        return self._all_instances

    def __init__(self):
        self._instances_to_create = []
        self._all_instances = []

    def precreate(self, class_, *args, **kwargs): # TODO rename. maybe combine with create() by checking whether or not self == engine.get_current_room() or something
        """ Use this to load an instance at the start of a room
        """
        self._instances_to_create.append((class_, args, kwargs))

    def create(self, class_, *args, **kwargs):
        """ Use this to create all GameObjects
        """
        # TODO add a check to make sure the inst is callable? or I suppose it'll error automatically
        # The order of the following two lines is arbitrary but very important:
        inst = class_(*args, **kwargs)
        self.all_instances.append(inst)
        return inst

    def destroy(self, inst):
        """ Use this to create all GameObjects
        """
        # The order of the following two lines is arbitrary but very important:
        inst.ev_destroy()
        self.all_instances.remove(inst)

    def populate_room(self):
        # TODO should the instances have create events? it seems like they probably should... Or I could delay the actual creation by using a fxn like create(Snake, args, kwargs) but idk which is better
        for class_, args, kwargs in self._instances_to_create:
            self.create(class_, *args, **kwargs)

# TODO make alarms deorators. you can start them with my_alarm_func.activate
class Alarm(object):
    all_alarms = []

    def __init__(self, fxn, activation_time, repeat=False):
        if not activation_time > 0:
            raise ArgumentError
        self.activation_time = activation_time
        self.time_left = activation_time
        self.fxn = fxn #TODO look up using __func__ or __call__ to do this. see ft.partial maybe?
        self.repeat = repeat

    def ev_step(self):
        self.time_left -= 1
        assert self.time_left >= 0
        if self.time_left <= 0: # TODO should this really be <= ?
            self.fxn()
            if self.repeat:
                self.time_left = self.activation_time
            else:
                Alarm.all_alarms.remove(self)

class Sprite(object):
    @property
    def rect(self):
        return pg.Rect(
                (GRID_X-self.image_width)/2,
                (GRID_Y-self.image_height)/2,
                self.image_width,
                self.image_height
        )

    def __init__(self, image_width, image_height, color):
        self.image_width = image_width
        self.image_height = image_height
        self.color = color

    def ev_draw(self, DISPLAY_SURF, pos): # todo idk how i feel about passing in pos here
        pg.draw.rect(DISPLAY_SURF, self.color, self.rect.move(*pos))
Sprite.DEFAULT = Sprite(GRID_X, GRID_Y, Colors.WHITE)

class GameObject(object):
    class CollisionType(object):
        """ See _do_find_collisions() for an explanation of these codes
        """
        NONE = 0 # NOTE: It's important with the current logic that bool(NONE) is False
        PASSIVE = 1
        ACTIVE = 2
    collisions = CollisionType.PASSIVE

    sprite = Sprite.DEFAULT

    @property
    def rect(self):
        # print "GameObject rect.getter"
        return self.__class__.sprite.rect.move(*self.pos)

    @property
    def pos(self):
        # print "GameObject pos.getter"
        return (self.x, self.y)
    @pos.setter
    def pos(self, value):
        # print "GameObject pos.setter"
        self.x, self.y = value

    def __init__(self, pos):
        print "GameObject __init__:", self.__class__.__name__
        self.pos = pos

    def ev_step_begin(self):
        pass
    def process_event(self, ev):
        pass
    def ev_step(self):
        pass
    def ev_collision(self, other):
        pass
    def ev_boundary_collision(self, side):
        pass
    def ev_outside_room(self):
        game_room.destroy(self)
    def ev_step_end(self):
        pass
    def ev_draw(self, DISPLAY_SURF):
        self.sprite.ev_draw(DISPLAY_SURF, self.pos)
    def ev_destroy(self):
        print "%s destroyed"%self.__class__.__name__

class GhostObject(GameObject):
    """ Represents a GameObject that has no position, rectangle, sprite, or collisions
    """

    collisions = GameObject.CollisionType.NONE
    sprite = None

    @property
    def rect(self):
        return None

    def __init__(self):
        pass

    def ev_draw(self, DISPLAY_SURF):
        pass