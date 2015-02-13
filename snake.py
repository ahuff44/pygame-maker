#!/usr/bin/env python
from __future__ import division

from pygame.locals import * # TODO: remove eventually; currently needed for MOUSEBUTTONUP etc.

import scipy as sp
from copy import copy
from time import sleep

import functools as ft
import itertools as itt

import Engine
import Objects
import InputManager
import Rooms
import Alarms
import MyColors
import MyLogger


class Snake(Objects.SolidObject):
    collisions = Objects.CollisionType.ACTIVE
    color = MyColors.GREEN

    MOVE_DELAY = 4

    def __init__(self, pos): #todo: Engine: we'll nee to separate __init__ and create events in order to be able to say friend=instance_create(FriendClass)
        super(Snake, self).__init__(pos)

        Alarms.manager.schedule(Alarms.Alarm(lambda: self.move(), Snake.MOVE_DELAY, repeat=True))

        self.dpos = Engine.RIGHT
        self.next_dpos = Engine.RIGHT

        self.neck = None
        self.just_eaten = True

        self.length = 1

    def move(self):
        self.dpos = self.next_dpos
        if self.just_eaten:
            old_neck = self.neck
            self.neck = Engine.current_room.create(SnakeBody, self.pos, old_neck)
            self.length += 1

            self.just_eaten = False
        else:
            self.neck.crawl_to(self.pos)

        self.pos += self.rect.size * self.dpos

    def ev_collision(self, other):
        if isinstance(other, Food):
            self.just_eaten = True
            Engine.current_room.destroy(other)
        if isinstance(other, SnakeBody):
            Engine.current_room.destroy(self)

    def ev_keyboard(self, key, press_time):
        if press_time == InputManager.PRESSED:
            if key in [K_LEFT, K_a]:
                if not all(self.dpos == Engine.RIGHT):
                    self.next_dpos = Engine.LEFT # We need to buffer this as next_dpos so that you can't kill yourself by pressing two buttons really quickly and doubling back on yourself
            elif key in [K_RIGHT, K_d]:
                if not all(self.dpos == Engine.LEFT):
                    self.next_dpos = Engine.RIGHT
            elif key in [K_UP, K_w]:
                if not all(self.dpos == Engine.DOWN):
                    self.next_dpos = Engine.UP
            elif key in [K_DOWN, K_s]:
                if not all(self.dpos == Engine.UP):
                    self.next_dpos = Engine.DOWN

    def ev_draw(self, screen):
        super(Snake, self).ev_draw(screen)
        Engine.draw_text(screen, "Length: %d"%self.length, (2, 2))

    def ev_destroy(self):
        Engine.end_game()

    def ev_room_end(self):
        print "Game Over"
        print "\tLength:", self.length

class SnakeBody(Objects.SolidObject):
    color = MyColors.BRIGHT_GREEN

    def __init__(self, pos, next_segment):
        super(SnakeBody, self).__init__(pos)
        self.next_segment = next_segment

    def crawl_to(self, pos):
        """ Call this to move this snake body segment and the entire rest of the snake
            """
        old_pos = copy(self.pos)
        self.pos = copy(pos)
        if self.next_segment:
            self.next_segment.crawl_to(old_pos)

class Food(Objects.SolidObject):
    color = MyColors.RED

    def __init__(self):
        super(Food, self).__init__((0, 0), Engine.current_room.grid//2)

        # Find a place to be in the room
        room_width, room_height = Engine.current_room.rect.size
        grid_x, grid_y = Engine.current_room.grid
        while True:
            pos = sp.array((
                Engine.random_int(room_width // grid_x),
                Engine.random_int(room_height // grid_y)
            )) * Engine.current_room.grid

            possible_center_pos = pos + Engine.current_room.grid//2
            if len(Engine.get_instances_at_position(possible_center_pos)) == 0:
                break
            else:
                MyLogger.logger.info("FOOD placement collision; retrying...")
        self.center_pos = possible_center_pos

    def ev_destroy(self): # NOTE: this here is a good reason why we need ev_destroy instead of just __del__ (I think; you could get an infinite loop when quitting the game)
        super(Food, self).ev_destroy()
        Engine.current_room.create(Food)

def populate_room(room):
    room.create(Objects.GameController)
    room.create(Snake, (128, 128))
    for _ in range(6):
        room.create(Food)
room = Rooms.GameRoom(populate_room, bgcolor=MyColors.NAVY_BLUE)

if __name__ == '__main__':
    Engine.main('Snake', room)
