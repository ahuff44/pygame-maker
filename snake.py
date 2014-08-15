#!/usr/bin/env python

import engine

from pygame.locals import * # TODO remove eventually; currently needed for MOUSEBUTTONUP etc.

import scipy as sp
from copy import copy
from time import sleep

import functools as ft
import itertools as itt


class Snake(engine.GameObject):
    collisions = engine.GameObject.CollisionType.ACTIVE
    sprite = engine.Sprite(engine.GRID, engine.Colors.GREEN)

    MOVE_DELAY = 4

    def __init__(self, pos): #todo engine: we'll nee to separate __init__ and create events in order to be able to say friend=instance_create(FriendClass)
        super(self.__class__, self).__init__(pos)

        engine.Alarm.new_alarm(lambda: self.move(), Snake.MOVE_DELAY, repeat=True)

        self.dpos = engine.RIGHT
        self.next_dpos = engine.RIGHT

        self.neck = None
        self.just_eaten = True

        self.length = 1

    def move(self):
        self.dpos = self.next_dpos
        if self.just_eaten:
            old_neck = self.neck
            self.neck = engine.game_room.create(SnakeBody, self.pos, old_neck)
            self.length += 1

            self.just_eaten = False
        else:
            self.neck.crawl_to(self.pos)

        self.pos += Snake.sprite.dimensions * self.dpos

    def ev_collision(self, other):
        if isinstance(other, Food):
            self.just_eaten = True
            engine.game_room.destroy(other)
        if isinstance(other, SnakeBody):
            engine.game_room.destroy(self)

    def ev_destroy(self):
        print "Ouch!"
        sleep(0.25)
        engine.terminate()

    def process_event(self, ev):
        if ev.type == KEYDOWN:
            if ev.key in [K_LEFT, K_a]:
                if not all(self.dpos == engine.RIGHT):
                    self.next_dpos = engine.LEFT # We need to buffer this as next_dpos so that you can't kill yourself by pressing two buttons really quickly and doubling back on yourself
            elif ev.key in [K_RIGHT, K_d]:
                if not all(self.dpos == engine.LEFT):
                    self.next_dpos = engine.RIGHT
            elif ev.key in [K_UP, K_w]:
                if not all(self.dpos == engine.DOWN):
                    self.next_dpos = engine.UP
            elif ev.key in [K_DOWN, K_s]:
                if not all(self.dpos == engine.UP):
                    self.next_dpos = engine.DOWN

    def ev_draw(self, screen):
        super(self.__class__, self).ev_draw(screen)
        engine.draw_text(screen, "Length: %d"%self.length, (2, 2))

class SnakeBody(engine.GameObject):
    sprite = engine.Sprite(engine.GRID, engine.Colors.BRIGHT_GREEN)

    def __init__(self, pos, next_segment):
        super(self.__class__, self).__init__(pos)

        self.next_segment = next_segment

    def crawl_to(self, pos):
        """ Call this to move this snake body segment and the entire rest of the snake
            """
        old_pos = copy(self.pos)
        self.pos = copy(pos)
        if self.next_segment:
            self.next_segment.crawl_to(old_pos)

def _make_food_sprite(dimensions):
    center = (engine.GRID-dimensions)//2
    return engine.Sprite(dimensions, engine.Colors.RED, center)
class Food(engine.GameObject):
    sprite = _make_food_sprite((16, 16))

    def __init__(self, pos=None):
        print "Food __init__"
        if pos is None:
            room_width, room_height = engine.game_room.dimensions
            grid_x, grid_y = engine.GRID
            while True:
                pos = sp.array((
                    engine.random_int(room_width // grid_x),
                    engine.random_int(room_height // grid_y)
                )) * engine.GRID

                pos_center = pos + engine.GRID//2
                if len(engine.get_instances_at_position(pos_center)) == 0:
                    break
                else:
                    print "FOOD placement collision; retrying...\n"
        super(self.__class__, self).__init__(pos)

    def ev_destroy(self): # NOTE: this here is a good reason why we need ev_destroy instead of just __del__ (I think; you could get an infinite loop when quitting the game)
        super(self.__class__, self).ev_destroy()
        engine.game_room.create(Food)

def populate_room(self):
    self.create(engine.GameController)
    self.create(Snake, (128, 128))
    for _ in range(6):
        self.create(Food)
room = engine.GameRoom.make_room(populate_room)

if __name__ == '__main__':
    engine.main('Snake', room)
