import engine

import pygame as pg
from pygame.locals import * # TODO remove eventually; currently needed for MOUSEBUTTONUP etc. (I think- this is an untested claim)

import scipy as sp
from copy import copy
from time import sleep

import functools as ft
import itertools as itt


class Controller(engine.GhostObject):
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

    @staticmethod
    def is_quit_event(ev):
        return (
            ev.type == QUIT
            or (ev.type == KEYUP and ev.key == K_ESCAPE)
        )

class Snake(engine.GameObject):
    collisions = engine.GameObject.CollisionType.ACTIVE
    sprite = engine.Sprite(engine.GRID_X, engine.GRID_Y, engine.Colors.GREEN)

    MOVE_DELAY = 4

    def __init__(self, pos): #todo engine: we'll nee to separate __init__ and create events in order to be able to say friend=instance_create(FriendClass)
        super(self.__class__, self).__init__(pos)

        engine.Alarm.all_alarms.append(engine.Alarm(lambda: self.move(), Snake.MOVE_DELAY, repeat=True))

        self.dir = engine.RIGHT
        self.next_dir = engine.RIGHT

        self.neck = None
        self.just_eaten = True

        self.length = 1

    def move(self):
        self.dir = self.next_dir
        if self.just_eaten:
            old_neck = self.neck
            self.neck = engine.game_room.create(SnakeBody, self.pos, old_neck)

            self.just_eaten = False
        else:
            self.neck.crawl_to(self.pos)

        if self.dir == engine.RIGHT:
            self.x += Snake.sprite.image_width
        elif self.dir == engine.LEFT:
            self.x -= Snake.sprite.image_width
        elif self.dir == engine.DOWN:
            self.y += Snake.sprite.image_height
        elif self.dir == engine.UP:
            self.y -= Snake.sprite.image_height
        else:
            assert False

    def ev_collision(self, other):
        if isinstance(other, Food):
            self.length += 1
            print "Length", self.length

            self.just_eaten = True
            engine.game_room.destroy(other)
        if isinstance(other, SnakeBody):
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

class SnakeBody(engine.GameObject):
    sprite = engine.Sprite(engine.GRID_X, engine.GRID_Y, engine.Colors.BRIGHTGREEN)

    def __init__(self, pos, next_segment):
        super(self.__class__, self).__init__(pos)

        self.dir = engine.RIGHT

        self.next_segment = next_segment

    def crawl_to(self, pos):
        """ Call this to move this snake body segment and the entire rest of the snake
            """
        old_pos = self.pos
        self.pos = pos
        if self.next_segment:
            self.next_segment.crawl_to(old_pos)

class Food(engine.GameObject):
    sprite = engine.Sprite(12, 12, engine.Colors.RED)

    def __init__(self, pos=None):
        print "Food __init__"
        if pos == None:
            while True:
                x = engine.random_int(engine.WINDOW_WIDTH // engine.GRID_X) * engine.GRID_X
                y = engine.random_int(engine.WINDOW_HEIGHT // engine.GRID_Y) * engine.GRID_Y
                pos = (x, y)
                pos_center = (x + engine.GRID_X//2, y + engine.GRID_Y//2)

                if len(engine.get_instances_at_position(pos_center)) == 0:
                    break
                else:
                    print "FOOD placement collision; retrying...\n"
        super(self.__class__, self).__init__(pos)
        # self.pos = pos

    def ev_destroy(self): # NOTE: this here is a good reason why we need ev_destroy instead of just __del__ (I think; you could get an infinite loop when quitting the game)
        super(self.__class__, self).ev_destroy()
        engine.game_room.create(Food)



def create_room():
    room = engine.Room()
    room.precreate(Controller)
    room.precreate(Snake, (128, 128))
    for _ in range(6):
        room.precreate(Food)
    return room

if __name__ == '__main__':
    engine.main('Snake', create_room())
