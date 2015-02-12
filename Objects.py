import scipy as sp
import pygame as pg
from pygame.locals import *

from copy import copy
import MyColors
import Engine
import MyLogger
import InputManager

class CollisionType(object):
    """ See _do_find_collisions() for an explanation of these codes
    """
    NONE = 0
    PASSIVE = 1
    ACTIVE = 2

class GameObject(object):
    # All subclasses must define a variable "collisions" that is a member of my CollisionType pseudo-enum
    color = MyColors.WHITE

    def __init__(self):
        MyLogger.logger.debug("%s: default __init__()"%self.__class__.__name__)
        InputManager.manager.register_key_handler(lambda *args: self.ev_keyboard(*args)) # TODO: IMPORTANT This registers the event for all subclasses, so you never need to use register_key_handler yourself. TODO: this is too complicated; the whole system needs to be changed :/
        # self.__register_collisions() # TODO Feb 2015 not sure what this is referring to; grep finds no matches in this folder

    def ev_keyboard(self, key, state):
        pass
    def ev_step_begin(self):
        pass
    def process_event(self, ev):
        pass
    def ev_step(self):
        pass
    def ev_collision(self, other):
        """ Checks to make sure the game programmer hasn't messed up by giving a ev_collision method to an object that doesn't do collisions"""
        derived_fxn = self.__class__.ev_collision.__func__
        base_fxn = Klass.ev_collision.__func__
        if not self.collisions and derived_fxn is not base_fxn:
            raise RuntimeError("The object (of type %s (%s)) has no collisions yet it has an ev_collision event"%(type(self), klass.__name__))

    def ev_boundary_collision(self):
        pass
    def ev_outside_room(self):
        MyLogger.logger.debug("%s: default ev_outside_room()"%self.__class__.__name__)
        Engine.current_room.destroy(self)
    def ev_step_end(self):
        pass
    def ev_draw(self, screen):
        pass
    def ev_destroy(self):
        MyLogger.logger.debug("%s: default ev_destroy()"%self.__class__.__name__)

class SolidObject(GameObject):

    collisions = CollisionType.PASSIVE
    dimensions = copy(Engine.GRID)

    def __init__(self, pos):
        super(SolidObject, self).__init__()
        self.rect = pg.Rect(pos, self.dimensions)

    @property
    def pos(self):
        assert self.rect.topleft == (self.rect.x, self.rect.y), "pygame's api sucks again"
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



class GhostObject(GameObject): # TODO: does this have pos? i think it does- kill it
    """ Represents a GameObject that has no position, rectangle, or collisions
    """
    pass

class GameController(GhostObject):
    def process_event(self, ev):
        if ev.type == QUIT:
            terminate()

    def ev_keyboard(self, key, status):
        if key == K_ESCAPE and status == InputManager.Constants.PRESSED:
            Engine.terminate()
