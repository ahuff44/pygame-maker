# TODO make GameObject inherit from pygame.Sprite. Learn how that junk code works. See C:\Program Files\Anaconda\Lib\site-packages\pygame\examples\aliens.py
# TODO unify terminology

from __future__ import division

__version__ = 0.1

from copy import copy
import pygame as pg
import scipy as sp
import itertools as itt

from collections import defaultdict

import sys
import os
import logging

from pygame.locals import *

from decorators import *


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

TARGET_FPS = 30
GRID = sp.array((32, 32)) # TODO clean these up, probably merge into GameRoom

class MyColor: # TODO some of these names suck
    #                R    G    B
    BLACK         = (  0,   0,   0)
    DARK_GRAY     = ( 63,  63,  63)
    GRAY          = (127, 127, 127)
    WHITE         = (255, 255, 255)

    BRIGHT_RED    = (255,   0,   0)
    RED           = (127,   0,   0)
    BRIGHT_YELLOW = (255, 255,   0)
    YELLOW        = (127, 127,   0)
    BRIGHT_ORANGE = (255, 127,   0)
    ORANGE        = (127,  63,   0)
    BRIGHT_GREEN  = (  0, 255,   0)
    GREEN         = (  0, 127,   0)
    BRIGHT_BLUE   = (  0,   0, 255)
    BLUE          = (  0,   0, 127)
    BRIGHT_PURPLE = (255,   0, 255)
    PURPLE        = (127,   0, 127)


    CYAN          = (  0, 255, 255)
    NAVY_BLUE     = ( 63,  63, 127)

    ALL = (BLACK, DARK_GRAY, GRAY, WHITE, BRIGHT_RED, RED, BRIGHT_GREEN, GREEN, BRIGHT_BLUE, BLUE, YELLOW, PURPLE, CYAN, NAVY_BLUE, ORANGE)

def main(window_title, first_room):
    global game_room
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

    screen.fill(game_room.bgcolor) #todo move to right before the draw events?

    for inst in copy(game_room.all_instances):
        inst.ev_step_begin()

    for alarm in Alarm.all_alarms:
        alarm.ev_step()

    events = pg.event.get()
    for ev in input_manager.filter_events(events):
        for inst in copy(game_room.all_instances):
            inst.process_event(ev)

    for inst in copy(game_room.all_instances):
        inst.ev_step()

    _do_collisions()
    _do_boundary_collisions()
    _do_outside_room_events()

    for inst in copy(game_room.all_instances):
        inst.ev_step_end()
        # TODO order?

    for inst in copy(game_room.all_instances):
        inst.ev_draw(screen)

    color = (FPS_CLOCK.get_fps() > (2*TARGET_FPS)//3) and MyColor.WHITE or MyColor.BRIGHT_RED
    draw_text(screen, str(int(FPS_CLOCK.get_fps()))+" fps", game_room.dimensions - (60, 16), color=color)
    pg.display.update() # TODO difference between this and pg.display.flip()?
    FPS_CLOCK.tick(TARGET_FPS)


def _do_boundary_collisions():
    for inst in copy(game_room.solid_instances):
        if inst.rect is not None:
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

def _do_outside_room_events():
    for inst in copy(game_room.solid_instances):
        if inst.rect is not None:
            if is_outside_room(inst.rect):
                inst.ev_outside_room()

def is_outside_room(rect):
    return not check_rect_overlap(rect, game_room.rect)

def check_rect_overlap(rect1, rect2):
    return rect1.colliderect(rect2)

def _do_collisions():
    for inst_a, inst_b in _do_find_collisions():
        logger.debug("Collision detected: %s + %s"%(inst_a.__class__.__name__, inst_b.__class__.__name__))
        inst_a.ev_collision(inst_b)

@pipe(list)
def _do_find_collisions():
    ''' Finds collisions among the current game_room's solid instances.
        It only generates collision events for instances with collisions == GameObject.CollisionType.ACTIVE,
            but these events can involve the ACTIVE instance colliding with a PASSIVE instacnce
        '''
    colliding_instances = copy(game_room.solid_instances)
    for i, inst_a in enumerate(colliding_instances):
        if inst_a.collisions == SolidObject.CollisionType.ACTIVE:
            for inst_b in colliding_instances[i+1:]:
                if inst_a == inst_b:
                    raise Exception("Programmer Logic error; you shouldn't be seeing this message (this is a bug in the game engine; there's probably an instance that is on the instance list twice)") # TODO make sure this actually throws this error if there are duplicates
                if (
                        inst_a.rect != None and inst_b.rect != None
                        and check_rect_overlap(inst_a.rect, inst_b.rect)
                ):
                    yield (inst_a, inst_b)

# Convinience functions:

def terminate():
    game_room.ev_room_end() # TODO fix infinite terminate/ev_destroy loop that is possible (e.g. in snake.py)
    pg.quit() # TODO redundant because of the try-catch (?)
    sys.exit()

@pipe(list)
def get_instances_at_position(pos):
    """ Returns a list off all instances that are at the given position
        Calculated by seeing what instances would collide with a point- so if an object is non-colliding, it won't show up here
        """
    for inst in copy(game_room.solid_instances):
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

def grid_view_slow(g_left, g_top, g_width, g_height):
    """
    TODO document this. Basically this returns a view of the instances on the game grid within the given rectangle (given in grid coordinates, not world coordinates)
    """
    assert g_width > 0
    assert g_height > 0
    return sp.array([[get_instances_at_position((g_left+dg_x, g_top+dg_y)*GRID) for dg_x in range(g_width)] for dg_y in range(g_height)])

# def grid_view(g_left, g_top, g_width, g_height): #TODO working here
#     assert g_width > 0
#     assert g_height > 0
#     rect = pg.Rect(g_left, g_top, g_width, g_height)
#     view = [[None]*g_width]*g_height
#     for inst in game_room.all_instances:
#         try:
#             g_x, g_y = inst.pos//GRID
#         except AttributeError: # Happens if inst.pos doesn't exist
#             continue
#         if rect.collidepoint(g_x, g_y):
#             view[g_y-g_top][g_x-g_left] = inst
#     return view

def floor_to_grid(pos):
    return (pos // GRID).astype(int) * GRID

def round_to_grid(pos):
    return sp.round_(pos / GRID).astype(int) * GRID

pg.font.init()
courier = pg.font.SysFont("Courier", 16)
def draw_text(screen, text, pos, font=courier, color=MyColor.WHITE, smooth=True): # TODO clean up/generalize this
    surf = font.render(text, smooth, color)
    screen.blit(surf, pos)

random_int = sp.random.randint

# TODO make this work somehow. It's all messed up currently. Right now you as a game programmer will never have to use input_manager.register_key_handler since it's done automatically in GameObject.__init__()
# This decorator will register its wrapped function to recieve engine key events
# @decorator
# def keyhandler(fxn):
#     for key in keys:
#         input_manager.register_key_handler(fxn)
#     return fxn
class InputManager(object):
    """My custom input manager. It manages key events. I plan to add support for mouse events too"""
    class Constants:
        PRESSED = 1
        HELD = 2
        RELEASED = 3

    def __init__(self):
        self.key_handlers = []
        # self.mouse_handlers = [] # TODO <add mouse support>

        # Entry format: {key or button: PRESSED or HELD or RELEASED}
        self.key_statuses = {}
        # self.mouse_button_statuses = {} # TODO <add mouse support>

    def filter_events(self, events):
        """
        This is the main function you call. TODO document better
        """
        # Filter keyboard events out of events
        for ev in events:
            if ev.type in [KEYDOWN, KEYUP]:
                self.process_key_event(ev)
        self.process_held_keys()

        # for ev in events:
        #     if ev.type in [MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP]: # TODO <add mouse support>
        #         self.process_mouse_event(ev)
        #         events.remove(ev)
        # self.process_held_mouse_buttons() # TODO <add mouse support>

        return filter(lambda ev: ev.type not in [KEYDOWN, KEYUP], events) # TODO try to do this better. you CANNOT use events.remove(ev)- it's buggy

    # Keyboard methods:

    def register_key_handler(self, fxn):
        self.key_handlers.append(fxn)

    def process_held_keys(self):
        for key in self.key_statuses:
            if self.key_statuses[key] == InputManager.Constants.PRESSED:
                self.key_statuses[key] = InputManager.Constants.HELD
            if self.key_statuses[key] == InputManager.Constants.HELD:
                self.notify_key_handlers(key)

    def process_key_event(self, ev):
        key = ev.key
        status = self.key_statuses[key] = {
            KEYDOWN: InputManager.Constants.PRESSED,
            KEYUP: InputManager.Constants.RELEASED
        }[ev.type]

        self.notify_key_handlers(key)

    def notify_key_handlers(self, key):
        logger.debug("Key %d in state %d", key, self.key_statuses[key])
        for handler in self.key_handlers:
            handler(key, self.key_statuses[key])

    # Mouse Button methods:
    # TODO make this all work. it needs to track the position as it gets dragged around
input_manager = InputManager()

# TODO Generalize this. There's lots of stuff that will break when you add multiple rooms. (e.g. the main() game loop will break)
class GameRoom(object):

    @property
    def all_instances(self):
        return self._all_instances

    @property
    def solid_instances(self):
        return filter(lambda inst: isinstance(inst, SolidObject), self.all_instances)

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

    def __init__(self, bgcolor=MyColor.GRAY, dimensions=(640, 480)):
        """ Do not use this to create rooms; use GameRoom.make_room() instead
        """
        self._instances_to_create = []
        self._all_instances = []
        self.bgcolor = bgcolor
        self.dimensions = sp.array(dimensions)

    def create(self, class_, *args, **kwargs):
        """ Use this to create GameObjects
        """
        # TODO add a check to make sure the inst is callable? or I suppose it'll error automatically
        # The order of the following two lines is arbitrary but very important:
        inst = class_(*args, **kwargs)
        self.all_instances.append(inst)
        return inst

    def destroy(self, inst):
        """ Use this to destroy GameObjects
        """
        # The order of the following two lines is arbitrary but very important:
        self.all_instances.remove(inst)
        inst.ev_destroy()

    def ev_room_end(self):
        map(self.destroy, copy(self.all_instances))

    def populate_room(self):
        raise NotImplementedError("This should have be overridden")

# TODO make alarms deorators. you can start them with my_alarm_func.activate
# TODO make this class structed symmetrically with InputManager. Maybe have two classes: AlarmManager and Alarm. Or change InputManager
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
        if activation_time <= 0:
            raise RuntimeError("Alarm cannot be set to a negative activation time")
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

    def reset(self, new_activation_time=None):
        if new_activation_time is not None:
            self.activation_time = int(new_activation_time)
        self.time_left = self.activation_time

class GameObject(object):
    color = MyColor.WHITE

    def __init__(self):
        logger.debug("%s: default __init__()"%self.__class__.__name__)
        input_manager.register_key_handler(lambda *args: self.ev_key(*args)) # TODO IMPORTANT This registers the event for all subclasses, so you never need to use register_key_handler yourself. TODO this is too complicated; the whole system needs to be changed :/

    def ev_key(self, key, state):
        pass
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
        pass
    def ev_destroy(self):
        logger.debug("%s: default ev_destroy()"%self.__class__.__name__)

class SolidObject(GameObject):
    class CollisionType(object):
        """ See _do_find_collisions() for an explanation of these codes
        """
        PASSIVE = 1
        ACTIVE = 2
    collisions = CollisionType.PASSIVE
    dimensions = copy(GRID)

    def __init__(self, pos):
        super(SolidObject, self).__init__()
        self.rect = pg.Rect(pos, self.dimensions)

    @property
    def pos(self):
        assert self.rect.topleft == (self.rect.x, self.rect.y)
        return sp.array((self.rect.x, self.rect.y))
        # return sp.array(self.rect.topleft)
    @pos.setter
    def pos(self, value):
        self.rect.x, self.rect.y = value

    @property
    def x(self):
        return self.rect.x
    @x.setter
    def x(self, value):
        self.rect.x = value

    @property
    def y(self):
        return self.rect.y
    @y.setter
    def y(self, value):
        self.rect.y = value


    @property
    def center_pos(self):
        return sp.array(self.rect.center)
    @center_pos.setter
    def center_pos(self, value):
        self.rect.center = value

    @property
    def center_x(self):
        return self.rect.centerx
    @center_x.setter
    def center_x(self, value):
        self.rect.centerx = value

    @property
    def center_y(self):
        return self.rect.centery
    @center_y.setter
    def center_y(self, value):
        self.rect.centery = value

    def ev_draw(self, screen):
        pg.draw.rect(screen, self.color, self.rect)

class GridObject(SolidObject):
    pass



class GhostObject(GameObject): # TODO does this have pos? i think it does- kill it
    """ Represents a GameObject that has no position, rectangle, or collisions
    """
    pass

class GameController(GhostObject):
    def process_event(self, ev):
        if ev.type == QUIT:
            terminate()

    def ev_key(self, key, status):
        if key == K_ESCAPE and status == InputManager.Constants.PRESSED:
            terminate()
