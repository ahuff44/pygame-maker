import engine

import pygame as pg
from pygame.locals import * # TODO remove eventually; currently needed for MOUSEBUTTONUP etc. (I think- this is an untested claim)

import scipy as sp
from copy import copy

import functools as ft
import itertools as itt


class Controller(object):
    def __init__(self):
        self.pos = sp.array((16, 16))
        self.pos_prev = copy(self.pos)

        self.update_rect()
    def process_event(self, ev):
        if self.is_quit_event(ev):
            engine.terminate()

        #mouse interaction:
        elif ev.type == MOUSEBUTTONUP:
            if ev.button == 1: #left click
                # engine.all_instances.append(Food(ev.pos))
                pass
        elif ev.type == MOUSEMOTION:
            global MOUSE_POS
            MOUSE_POS = sp.array(ev.pos)

        #keyboard interaction
        elif ev.type == KEYDOWN:
            if ev.key == K_p:
                print "example key"

    def ev_collision(self, other):
        pass
    def ev_postcollision(self):
        print "Controller post"
    def ev_step_begin(self):
        pass
    def ev_step(self):
        # print "Step"
        pass
    def ev_step_end(self):
        pass
    def ev_boundary_collision(self, side):
        pass
    def ev_outside_room(self):
        pass
    def update_rect(self):
        self.rect = pg.Rect(self.pos[0], self.pos[1], 0, 0)
    def ev_draw(self, DISPLAY_SURF):
        radius = 5
        pg.draw.circle(DISPLAY_SURF, engine.Colors.CYAN, self.pos, radius)

    @staticmethod
    def is_quit_event(ev):
        return (
            ev.type == QUIT
            or (ev.type == KEYUP and ev.key == K_ESCAPE)
        )


def init_room():
    all_instances = []
    all_instances.append(Controller())
    all_instances.append(Snake([128, 128]))
    for _ in range(6):
        all_instances.append(Food())
    return all_instances

class Snake(object):
    MOVE_DELAY = 4
    IMG_X = engine.GRID_X
    IMG_Y = engine.GRID_Y

    COLOR = engine.Colors.GREEN
    def __init__(self, pos): #todo engine: we'll nee to separate __init__ and create events in order to be able to say friend=instance_create(FriendClass)
        self.pos = sp.array(pos) #todo use this in parent object: , dtype=float)
        self.pos_prev = copy(self.pos)

        self.alarm = Snake.MOVE_DELAY

        self.dir = engine.RIGHT

        self.update_rect()

    def update_rect(self):
        self.rect = pg.Rect(self.pos[0], self.pos[1], Snake.IMG_X, Snake.IMG_Y)
        # todo is there a better way to do this, just updating the position? I think there is...

    def ev_step(self):
        self.alarm -= 1
        if self.alarm <= 0:
            if self.dir == engine.RIGHT:
                self.pos[0] += Snake.IMG_X
            elif self.dir == engine.LEFT:
                self.pos[0] -= Snake.IMG_X
            elif self.dir == engine.DOWN:
                self.pos[1] += Snake.IMG_Y
            elif self.dir == engine.UP:
                self.pos[1] -= Snake.IMG_Y
            self.alarm = Snake.MOVE_DELAY

    def ev_collision(self, other):
        print "Snake + ", other.__class__.__name__
        if isinstance(other, Food):
            print "Yum!"

    def ev_postcollision(self):
        print "Snake post"

    def ev_step_begin(self):
        pass

    def ev_step_end(self):
        pass

    def ev_boundary_collision(self, side):
        pass

    def ev_outside_room(self):
        pass

    def process_event(self, ev):
        if ev.type == KEYDOWN:
            if ev.key == K_LEFT:
                if self.dir != engine.RIGHT:
                    self.dir = engine.LEFT
            if ev.key == K_RIGHT:
                if self.dir != engine.LEFT:
                    self.dir = engine.RIGHT
            if ev.key == K_UP:
                if self.dir != engine.DOWN:
                    self.dir = engine.UP
            if ev.key == K_DOWN:
                if self.dir != engine.UP:
                    self.dir = engine.DOWN

    def ev_draw(self, DISPLAY_SURF):
        self.update_rect()
        pg.draw.rect(DISPLAY_SURF, Snake.COLOR, self.rect)


class Food(object):
    IMG_X = 12 # image width
    IMG_Y = 12 # image height
    COLOR = engine.Colors.RED
    def __init__(self, pos=None):
        if pos == None:
            all_other_food = filter(lambda inst: isinstance(inst, Food), engine.all_instances)
            # print all_other_food # TODO this all has to move into a create event
            # all_other_food.remove(self)
            while True:
                x = int(sp.rand() * engine.WINDOW_WIDTH/engine.GRID_X)*engine.GRID_X # todo ref random or sp.random instead
                y = int(sp.rand() * engine.WINDOW_HEIGHT/engine.GRID_Y)*engine.GRID_Y
                pos = (x, y)
                if len(engine.get_instances_at_position(all_other_food, pos)) == 0:
                    break
        self.pos = sp.array(pos)

        self.pos_prev = copy(pos)

        self.update_rect()

    def update_rect(self):
        self.rect = pg.Rect(
                self.pos[0] + (engine.GRID_X-Food.IMG_X)/2,
                self.pos[1] + (engine.GRID_Y-Food.IMG_Y)/2,
                Food.IMG_X,
                Food.IMG_Y
        )
        # todo is there a better way to do this, just updating the position? I think there is...

    def ev_collision(self, other):
        if isinstance(other, Snake):
            engine.destroy(self)
            engine.all_instances.append(Food())

    def ev_postcollision(self):
        print "Food post"

    def __del__(self):
        print "deleting"
        pass

    def ev_step_end(self):
        pass
    def ev_step(self):
        pass
    def ev_step_begin(self):
        pass
    def process_event(self, ev):
        pass
    def ev_draw(self, DISPLAY_SURF):
        self.update_rect()
        pg.draw.rect(DISPLAY_SURF, Food.COLOR, self.rect)



if __name__ == '__main__':
    engine.main('Snake', init_room)
