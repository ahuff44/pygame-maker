# TODO test the speed of pygame.sprite.collide_rect... can I overwrite it? pretty please?
# TODO replace GM terminology object->class. keep "instance" though

from __future__ import division

__version__ = 0.1

from copy import copy
import pygame as pg
import scipy as sp
import itertools as itt

import sys
import os
import logging

from pygame.locals import *

def init_logger(output_dir='.', console_level=logging.INFO):
    """
    Created with help from http://aykutakin.wordpress.com/2013/08/06/logging-to-console-and-file-in-python/
    """

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("LOG:%(name)s:%(levelname)8s:    %(message)s")

    # Create a console handler (Level: INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(console_level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Create an error file handler (Level: ERROR)
    out_file = os.path.join(output_dir, "error.log")
    try:
        os.remove(out_file)
    except OSError:
        pass
    handler = logging.FileHandler(out_file, "w", encoding=None, delay="true") # TODO learn what these flags do
    handler.setLevel(logging.ERROR)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Create a debug file handler (Level: DEBUG)
    out_file = os.path.join(output_dir, "debug.log")
    try:
        os.remove(out_file)
    except OSError:
        pass
    handler = logging.FileHandler(out_file, "w")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
logger = init_logger()

# variables named "dpos" usually refer to these
RIGHT = sp.array((1, 0)) # TODO do something with these
UP    = sp.array((0, -1))
LEFT  = sp.array((-1, 0))
DOWN  = sp.array((0, 1))

FPS = 30
GRID = sp.array((32, 32)) # TODO clean these up, probably merge into GameRoom

# MOUSE_POS = [0, 0] # NOTE: mutable

class Colors:
    #                R    G    B
    WHITE        = (255, 255, 255)
    BLACK        = (  0,   0,   0)
    BRIGHT_RED    = (255,   0,   0)
    RED          = (155,   0,   0)
    BRIGHT_GREEN  = (  0, 255,   0)
    GREEN        = (  0, 155,   0)
    BRIGHT_BLUE   = (  0,   0, 255)
    BLUE         = (  0,   0, 155)
    BRIGHT_YELLOW = (255, 255,   0)
    YELLOW       = (155, 155,   0)
    DARK_GRAY     = ( 40,  40,  40)

    GRAY         = (100, 100, 100)
    NAVY_BLUE     = ( 60,  60, 100)
    WHITE        = (255, 255, 255)
    ORANGE       = (255, 128,   0)
    PURPLE       = (255,   0, 255)
    CYAN         = (  0, 255, 255)

    ALL = (WHITE, BLACK, BRIGHT_RED, RED, BRIGHT_GREEN, GREEN, BRIGHT_BLUE, BLUE, BRIGHT_YELLOW, YELLOW, DARK_GRAY, GRAY, NAVY_BLUE, WHITE, ORANGE, PURPLE, CYAN)

bgColor = Colors.NAVY_BLUE

def pipe(postprocessor): #TODO move to another file and import
    def _decorator(fxn):
        def _fxn(*args, **kwargs):
            return postprocessor(fxn(*args, **kwargs))
        return _fxn
    return _decorator

def main(window_title, first_room):
    # global MOUSE_POS
    global game_room
    # global FPS_CLOCK
    game_room = first_room

    pg.init()
    FPS_CLOCK = pg.time.Clock()
    screen = pg.display.set_mode(first_room.dimensions)
    pg.display.set_caption(window_title)

    try:
        game_room.populate_room()
        while True: # Main game loop
            game_tick(FPS_CLOCK, screen)
    except:
        pg.quit()
        raise # pass the exception to the cmd line, which will print it for us

def game_tick(FPS_CLOCK, screen):
    global game_room

    screen.fill(bgColor) #todo move to right before the draw events?

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
        inst.ev_draw(screen)

    draw_text(screen, str(int(FPS_CLOCK.get_fps()))+" fps", game_room.dimensions - (60, 16))
    pg.display.update() # TODO difference between this and pg.display.flip()?
    FPS_CLOCK.tick(FPS)


def _do_boundary_collisions(instances):
    for inst in instances:
        if inst.rect:
            side = get_boundary_touching(inst.rect)
            if side != None:
                inst.ev_boundary_collision(side)

def get_boundary_touching(rect): #TODO rename; and think seriously about the fact that "if get_boundary_touching():" will fail in horrible ways since RIGHT == 0
    width, height = game_room.dimensions
    if rect.right >= width:
        return RIGHT
    if rect.left <= 0:
        return LEFT #todo engine this whole global constants thing is making me squeamish
    if rect.bottom >= height:
        return DOWN
    if rect.top <= 0:
        return UP

def _do_outside_room_events(instances):
    for inst in instances:
        if inst.rect:
            if is_outside_room(inst.rect):
                inst.ev_outside_room()

def is_outside_room(rect):
    return not check_rect_overlap(rect, game_room.rect)

def check_rect_overlap(rect1, rect2):
    return rect1.colliderect(rect2)
    # return (
    #         check_interval_overlap((rect1.left, rect1.right), (rect2.left, rect2.right))
    #         and check_interval_overlap((rect1.top, rect1.bottom), (rect2.top, rect2.bottom))
    # )

# def check_interval_overlap(t1, t2):
#     ''' Returns whether $(a, b)$ interected with $(c, d)$ is not the empty set,
#             where t1 and t2 are tuples (a, b) and (c, d);
#         '''
#     (a, b) = t1
#     (c, d) = t2
#     assert a <= b, 'Malformed interval'
#     assert c <= d, 'Malformed interval'
#     return b > c and d > a
#     # return not(a <= b <= c <= d or c <= d <= a <= b)

def _do_collisions(instances):
    for inst_a, inst_b in _do_find_collisions(instances):
        logger.debug("Collision detected: %s + %s"%(inst_a.__class__.__name__, inst_b.__class__.__name__))
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
        if inst.rect != None and inst.rect.collidepoint(pos):
            yield inst

def is_free(pos, allowed_instances):
    """ Returns whether the given position is free of instances. Instances in allowed_instances are ignored
    """
    # If there are any instances at the next position, they must all be on the allowed instances list:
    return all(
        inst in allowed_instances
        for inst in get_instances_at_position(pos)
    )

def clamp(x, a, b):
    ''' Clamps the value of x to be between a and b:
            Returns x if $x \in [a, b]$
            Returns a if $x < a$
            Returns b if $x > b$
        '''
    return min(max(a, x), b)

def grid_view(g_top, g_left, g_width, g_height):
    """
    TODO document this. Basically this returns a view of the instances on the game grid within the given rectangle (given in grid coordinates, not world coordinates)
    """
    assert g_width > 0
    assert g_height > 0
    return sp.array([[get_instances_at_position((g_left+dg_x, g_top+dg_y)*GRID) for dg_x in range(g_width)] for dg_y in range(g_height)])

def snap_to_grid(pos):
    # TODO test that this works properly
    return (pos // GRID).astype(int) * GRID # yes, using 'astype' is necessary, even though I'm also using '//' for division

def draw_text(screen, text, pos, text_color=Colors.WHITE, smooth=True): # TODO clean up/generalize this
    myfont = pg.font.SysFont("Courier", 16)
    surf = myfont.render(text, smooth, text_color)
    screen.blit(surf, pos)

random_int = sp.random.randint

# TODO there's lots of stuff that will break when you add multiple rooms. The main game loop will break, for one
class GameRoom(object):

    @property
    def all_instances(self):
        return self._all_instances

    @property
    def rect(self):
        return pg.Rect((0, 0), self.dimensions)

    @staticmethod
    def make_room(populate_room, *args, **kwargs):
        """ Use this instead of __init__
        """
        room = GameRoom(*args, **kwargs)
        room.populate_room = lambda: populate_room(room) # TODO see if there's a better way to make this work; I want to be able to say room.populate_room = populate_room but then self isn't auto-passed in for some reason
        return room

    def __init__(self, dimensions=(640, 480)):
        """ Do not use this to create rooms; use GameRoom.make_room() instead
        """
        self._instances_to_create = []
        self._all_instances = []
        self.dimensions = sp.array(dimensions)

    def create(self, class_, *args, **kwargs):
        """ Use this to create all GameObjects
        """
        # TODO add a check to make sure the inst is callable? or I suppose it'll error automatically
        # The order of the following two lines is arbitrary but very important:
        inst = class_(*args, **kwargs)
        self.all_instances.append(inst)
        return inst

    def destroy(self, inst):
        """ Use this to destroy all GameObjects
        """
        # The order of the following two lines is arbitrary but very important:
        inst.ev_destroy()
        self.all_instances.remove(inst)

    def populate_room(self):
        raise NotImplementedError("This should have be overridden")

# TODO make alarms deorators. you can start them with my_alarm_func.activate
class Alarm(object):
    all_alarms = []

    @staticmethod
    def new_alarm(*args, **kwargs):
        """ Use this instead of __init__
        """
        alarm = Alarm(*args, **kwargs)
        Alarm.all_alarms.append(alarm)
        return alarm

    def __init__(self, fxn, activation_time, repeat=False):
        """ Do not use this; use Alarm.new_alarm() instead
        """
        if not activation_time > 0:
            raise ArgumentError
        self.activation_time = activation_time
        self.time_left = activation_time
        self.fxn = fxn #TODO look up using __func__ or __call__ to do this. see ft.partial maybe?
        self.repeat = repeat

    def ev_step(self):
        self.time_left -= 1
        if self.time_left == 0:
            self.fxn() # Perform the delayed action
            if self.repeat:
                self.reset()

    def time_since_last_activation(self):
        # TODO test
        if self.time_left > 0:
            return self.activation_time - self.time_left
        else:
            return -self.time_left

    def reset(self):
        self.time_left = self.activation_time

class Sprite(object):
    @property
    def rect(self):
        return pg.Rect(self.center, self.dimensions)

    def __init__(self, dimensions, color, center=(0, 0)):
        self.dimensions = copy(dimensions)
        self.color = color
        self.center = center

    def ev_draw(self, screen, pos):
        pg.draw.rect(screen, self.color, self.rect.move(*pos))
Sprite.DEFAULT = Sprite(GRID, Colors.WHITE)

class GameObject(object):
    class CollisionType(object):
        """ See _do_find_collisions() for an explanation of these codes
        """
        NONE = 0; assert not NONE
        PASSIVE = 1
        ACTIVE = 2
    collisions = CollisionType.PASSIVE

    sprite = Sprite.DEFAULT

    @property
    def rect(self):
        return self.sprite.rect.move(*self.pos)

    @property
    def x(self):
        return self.pos[0]
    @x.setter
    def x(self, value):
        self.pos[0] = value

    @property
    def y(self):
        return self.pos[1]
    @y.setter
    def y(self, value):
        self.pos[1] = value

    def __init__(self, pos):
        logger.debug("%s: default __init__()"%self.__class__.__name__)
        self.pos = sp.array(pos)

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
        logger.debug("%s: default ev_outside_room()"%self.__class__.__name__)
        game_room.destroy(self)
    def ev_step_end(self):
        pass
    def ev_draw(self, screen):
        self.sprite.ev_draw(screen, self.pos)
    def ev_destroy(self):
        logger.debug("%s: default ev_destroy()"%self.__class__.__name__)

class GhostObject(GameObject): #TODO does this have pos? i think it does- kill it
    """ Represents a GameObject that has no position, rectangle, sprite, or collisions
    """

    collisions = GameObject.CollisionType.NONE
    sprite = None

    @property
    def rect(self):
        return None

    def __init__(self):
        pass

    def ev_draw(self, screen):
        pass

class GameController(GhostObject):
    def process_event(self, ev):
        if self.is_quit_event(ev):
            terminate()

    @staticmethod
    def is_quit_event(ev):
        return (
            ev.type == QUIT
            or (ev.type == KEYUP and ev.key == K_ESCAPE)
        )
