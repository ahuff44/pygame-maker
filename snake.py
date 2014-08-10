import engine

import pygame as pg
from pygame.locals import * # TODO remove eventually; currently needed for MOUSEBUTTONUP etc. (I think- this is an untested claim)

import scipy as sp
from copy import copy
from time import sleep

import functools as ft
import itertools as itt


class Controller(object):
    def __init__(self):
        self.x = 16
        self.y = 16

    @property
    def rect(self):
        return pg.Rect(0,0,0,0)

    def process_event(self, ev):
        if self.is_quit_event(ev):
            engine.terminate()

        #mouse interaction:
        # elif ev.type == MOUSEBUTTONUP:
        #     if ev.button == 1: #left click
        #         engine.game_room.create(Food, ev.pos)
        #         pass
        # elif ev.type == MOUSEMOTION: # TODO should this be in the engine somewhere?
        #     global MOUSE_POS # TODO definitely wrong
        #     MOUSE_POS = sp.array(ev.pos)
    def ev_collision(self, other):
        pass
    def ev_step_begin(self):
        pass
    def ev_step(self):
        pass
    def ev_step_end(self):
        pass
    def ev_boundary_collision(self, side):
        pass
    def ev_outside_room(self):
        pass
    def ev_draw(self, DISPLAY_SURF):
        # radius = 5
        # pg.draw.circle(DISPLAY_SURF, engine.Colors.CYAN, [self.x, self.y], radius)
        pass

    @staticmethod
    def is_quit_event(ev):
        return (
            ev.type == QUIT
            or (ev.type == KEYUP and ev.key == K_ESCAPE)
        )

def create_room():
    room = engine.Room()
    room.precreate(Controller)
    room.precreate(Snake, [128, 128])
    for _ in range(6):
        room.precreate(Food)
    return room

class Snake(object):
    MOVE_DELAY = 4
    IMG_X = engine.GRID_X
    IMG_Y = engine.GRID_Y

    COLOR = engine.Colors.GREEN

    @property
    def rect(self):
        return pg.Rect(self.x, self.y, Snake.IMG_X, Snake.IMG_Y)

    def __init__(self, pos): #todo engine: we'll nee to separate __init__ and create events in order to be able to say friend=instance_create(FriendClass)
        self.x, self.y = pos

        engine.Alarm.all_alarms.append(engine.Alarm(lambda: self.move(), Snake.MOVE_DELAY, repeat=True))

        self.dir = engine.RIGHT
        self.next_dir = engine.RIGHT

        self.neck = None
        self.just_eaten = True

    # def calc_neck_position(self):
    #     neck_x, neck_y = self.x, self.y
    #     if self.dir == engine.RIGHT:
    #         neck_x -= engine.GRID_X
    #     elif self.dir == engine.LEFT:
    #         neck_x += engine.GRID_X
    #     elif self.dir == engine.DOWN:
    #         neck_y -= engine.GRID_Y
    #     elif self.dir == engine.UP:
    #         neck_y += engine.GRID_Y
    #     return (neck_x, neck_y)

    def move(self):
        self.dir = self.next_dir
        if self.just_eaten:
            old_neck = self.neck
            self.neck = engine.game_room.create(SnakeBody, (self.x, self.y), old_neck)

            self.just_eaten = False
        else:
            self.neck.crawl_to(self.x, self.y)

        if self.dir == engine.RIGHT:
            self.x += Snake.IMG_X
        elif self.dir == engine.LEFT:
            self.x -= Snake.IMG_X
        elif self.dir == engine.DOWN:
            self.y += Snake.IMG_Y
        elif self.dir == engine.UP:
            self.y -= Snake.IMG_Y
        else:
            assert False

    def ev_collision(self, other):
        if isinstance(other, Food):
            self.just_eaten = True
            engine.game_room.destroy(other)
        if isinstance(other, SnakeBody):
            engine.game_room.destroy(self)

    def ev_step_begin(self):
        pass
    def ev_step(self):
        pass
    def ev_step_end(self):
        pass
    def ev_boundary_collision(self, side):
        pass
    def ev_outside_room(self):
        engine.game_room.destroy(self)

    def ev_destroy(self):
        print "Ouch!"
        sleep(1)
        engine.terminate()

    def process_event(self, ev):
        if ev.type == KEYDOWN:
            if ev.key in [K_LEFT, K_a]:
                if self.dir != engine.RIGHT:
                    self.next_dir = engine.LEFT # We need to buffer this as next_dir so that you can't kill yourself by pressing two buttons really quickly and doubling back on yourself
            if ev.key in [K_RIGHT, K_d]:
                if self.dir != engine.LEFT:
                    self.next_dir = engine.RIGHT
            if ev.key in [K_UP, K_w]:
                if self.dir != engine.DOWN:
                    self.next_dir = engine.UP
            if ev.key in [K_DOWN, K_s]:
                if self.dir != engine.UP:
                    self.next_dir = engine.DOWN

    def ev_draw(self, DISPLAY_SURF):
        pg.draw.rect(DISPLAY_SURF, Snake.COLOR, self.rect)

class SnakeBody(object):
    IMG_X = engine.GRID_X
    IMG_Y = engine.GRID_Y

    COLOR = engine.Colors.BRIGHTGREEN

    @property
    def rect(self):
        return pg.Rect(self.x, self.y, SnakeBody.IMG_X, SnakeBody.IMG_Y)

    def __init__(self, pos, next_segment):
        self.x, self.y = pos

        self.dir = engine.RIGHT

        self.next_segment = next_segment

    def crawl_to(self, x, y):
        """ Call this to move this snake body segment and the entire rest of the snake
            """
        old_x, old_y = self.x, self.y
        self.x, self.y = x, y
        if self.next_segment:
            self.next_segment.crawl_to(old_x, old_y)

    # GameObject methods:

    def ev_step(self):
        pass
    def ev_collision(self, other):
        print "SnakeBody + ", other.__class__.__name__
    def ev_step_begin(self):
        pass
    def ev_step_end(self):
        pass
    def ev_boundary_collision(self, side):
        pass
    def ev_outside_room(self):
        pass
    def process_event(self, ev):
        pass
    def ev_destroy(self):
        pass

    def ev_draw(self, DISPLAY_SURF):
        pg.draw.rect(DISPLAY_SURF, SnakeBody.COLOR, self.rect)
        # radius = 32 # TODO delete
        # pg.draw.circle(DISPLAY_SURF, engine.Colors.CYAN, [self.x, self.y], radius)

class Food(object):
    IMG_X = 12 # image width
    IMG_Y = 12 # image height

    COLOR = engine.Colors.RED

    @property
    def rect(self):
        return pg.Rect(
                self.x + (engine.GRID_X-Food.IMG_X)/2,
                self.y + (engine.GRID_Y-Food.IMG_Y)/2,
                Food.IMG_X,
                Food.IMG_Y
        )

    def __init__(self, pos=None):
        if pos == None:
            while True:
                x = engine.random_int(engine.WINDOW_WIDTH // engine.GRID_X) * engine.GRID_X
                y = engine.random_int(engine.WINDOW_HEIGHT // engine.GRID_Y) * engine.GRID_Y
                pos = (x, y)
                pos_center = (x + engine.GRID_X//2, y + engine.GRID_Y//2)

                if len(engine.get_instances_at_position(pos_center)) == 0:
                    break
                else:
                    print "FOOD placement collsiion; retrying...\n"

        self.x, self.y = pos

    def ev_collision(self, other):
        pass
    def ev_step_end(self):
        pass
    def ev_step(self):
        pass
    def ev_step_begin(self):
        pass
    def process_event(self, ev):
        pass
    def ev_destroy(self): # NOTE: this here is a good reason why we need ev_destroy instead of just __del__ (I think; you could get an infinite loop when quitting the game)
        engine.game_room.create(Food)

    def ev_draw(self, DISPLAY_SURF):
        pg.draw.rect(DISPLAY_SURF, Food.COLOR, self.rect)

if __name__ == '__main__':
    engine.main('Snake', create_room())
