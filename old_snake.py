from __future__ import division

from copy import copy
import pygame as pg
import scipy as sp
from numpy.linalg import norm
import sys
import random

from pygame.locals import *


FPS = 30
WINDOW_WIDTH = 640
WINDOW_HEIGHT= 480
GRID_X = 16
GRID_Y = 16

RIGHT  = 0
TOP    = 1
LEFT   = 2
BOTTOM = 3

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

bgColor = DARKGRAY


def main():

    pg.init()
    FPSCLOCK = pg.time.Clock()
    DISPLAYSURF = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pg.display.set_caption('Snake!')

    try:
        all_instances = init_room()
        while True: # Main game loop
            current_instances = tuple(all_instances) # create a temp list; this ensures that objects created in this step will NOT have a step event called
            for inst in current_instances:
                inst.ev_step_begin()
            events = pg.event.get()
            #todo enginde idea: have it hold a table of keys and whether or not they're pressed, down, or released
            # for inst in current_instances:
                # inst.process_events(events)
            for ev in events:
                if ev.type == QUIT or \
                        (ev.type == KEYUP and ev.key == K_ESCAPE):
                    terminate()
                    # eventually take this out and make you implement it yourself?
                for inst in current_instances:
                    inst.process_event(ev)
            for a, b in get_collisions(current_instances):
                a.ev_collision(b)
                b.ev_collision(a)
            for inst in current_instances:
                inst.ev_step()
            do_boundary_collisions(current_instances)
            do_outside_room_events(current_instances)
            for inst in current_instances:
                inst.pos_prev = copy(inst.pos)
                inst.pos = copy(inst.pos_next)
            for inst in current_instances:
                inst.ev_step_end()
                #order?

            DISPLAYSURF.fill(bgColor)
            for inst in current_instances:
                inst.ev_draw(DISPLAYSURF)

            pg.display.update()
            FPSCLOCK.tick(FPS)
    except:
        pg.quit()
        raise # pass the exception to the cmd line, which will print it for us
'''
Reqs all objects to have pos, pos_prev, and pos_next. Change later to a class hierarchy
Currently Reqs objs to have all fxn implemented; change later using either 1) hierarchy or 2) try-catch
'''
#you can catch AttributeError when you call a nonexistant function







##############################################################################







def terminate():
    pg.quit() # redundant because of the try-catch
    sys.exit()

def init_room():
    all_instances = []
    all_instances.append(Snake([128, 128]))
    all_instances.append(Food())
    return all_instances

def get_instance_at_position(objects, x, y):
    for obj in objects:
        if do_rects_overlap(obj.rect, pg.Rect(x,y,0,0)):
            return obj
    return None

def do_rects_overlap(rect1, rect2):
    return do_intervals_overlap((rect1.left, rect1.right), (rect2.left, rect2.right)) \
       and do_intervals_overlap((rect1.top, rect1.bottom), (rect2.top, rect2.bottom))

def do_intervals_overlap(t1, t2):
    '''
        t1 and t2 are tuples (a, b) and (c, d)
        '''
    ((a,b), (c,d)) = (t1, t2)
    assert a<=b, 'Bad value'
    assert c<=d, 'Bad value'
    return not(a <= b < c <= d or c <= d < a <= b)

def do_boundary_collisions(instances):
    for inst in instances:
        if inst.rect.right >= WINDOW_WIDTH:
            inst.ev_boundary_collision(RIGHT)
        if inst.rect.left <= 0:
            inst.ev_boundary_collision(LEFT)
        if inst.rect.bottom >= WINDOW_HEIGHT:
            inst.ev_boundary_collision(BOTTOM)
        if inst.rect.top <= 0:
            inst.ev_boundary_collision(TOP)

def do_outside_room_events(instances):
    for inst in instances:
        if inst.rect.right < 0:
            inst.ev_outside_room(RIGHT)
        if inst.rect.left > WINDOW_WIDTH:
            inst.ev_outside_room(LEFT)
        if inst.rect.bottom < 0:
            inst.ev_outside_room(BOTTOM)
        if inst.rect.top > WINDOW_HEIGHT:
            inst.ev_outside_room(TOP)

def get_collisions(instances):
    ''' Checks for collisions among elements of instances
        Naively checks each element against every other element
        Will NOT generate symmetric collisions;
            ie if (a,b) is on the list then (b,a) will NOT also be
        '''
    collisions_list = []
    for i, a in enumerate(instances):
        for b in instances[i+1:]:
            if a == b:
                raise Exception('uh oh logic error')
            if do_rects_overlap(a.rect, b.rect):
                collisions_list.append((a, b))
    return tuple(collisions_list)

def bound(a, b, x):
    '''Returns x if x in [a,b]
        Returns a if x < a
        Returns b if x > b
        '''
    return min(max(a, x), b)







##############################################################################







class Snake(object):
    UP    = sp.array([0, -1])
    DOWN  = sp.array([0, 1])
    LEFT  = sp.array([-1, 0])
    RIGHT = sp.array([1, 0])

    MOVE_DELAY = 4
    IMG_X = GRID_X
    IMG_Y = GRID_Y

    COLOR = GREEN
    def __init__(self, pos): #todo engine: we'll nee to separate __init__ and create events in order to be able to say friend=instance_create(FriendClass)
        pos = sp.array(pos)  #todo use this in parent object: , dtype=float)

        self.pos = pos
        self.pos_prev = pos
        self.pos_next = pos

        self.alarm = Snake.MOVE_DELAY

        self.dir = Snake.UP

        self.update_rect()

    def update_rect(self):
        self.rect = pg.Rect(self.pos[0], self.pos[1], Snake.IMG_X, Snake.IMG_Y)
        # todo is there a better way to do this, just updating the position? I think there is...

    def ev_step_begin(self):
        self.alarm -= 1
        if self.alarm <= 0:
            self.pos_next += self.dir * (Snake.IMG_X, Snake.IMG_Y)
            self.alarm = Snake.MOVE_DELAY

    def ev_step(self):
        pass

    def ev_collision(self, other):
        print "Yum!"

    def ev_step_end(self):
        pass

    def ev_boundary_collision(self, side):
        pass

    def ev_outside_room(self, side):
        pass

    def process_event(self, ev):
        if ev.type == KEYDOWN:
            if ev.key == K_LEFT:
                if any(self.dir != Snake.RIGHT):
                    self.dir = Snake.LEFT
            if ev.key == K_RIGHT:
                if any(self.dir != Snake.LEFT):
                    self.dir = Snake.RIGHT
            if ev.key == K_UP:
                if any(self.dir != Snake.DOWN):
                    self.dir = Snake.UP
            if ev.key == K_DOWN:
                if any(self.dir != Snake.UP):
                    self.dir = Snake.DOWN
    def ev_draw(self, DISPLAYSURF):
        self.update_rect()
        pg.draw.rect(DISPLAYSURF, Snake.COLOR, self.rect)


class Food(object):
    IMG_X = 12
    IMG_Y = 12
    COLOR = RED
    def __init__(self, pos=None):
        if pos == None:
            x = int(sp.rand() * WINDOW_WIDTH/GRID_X)*GRID_X
            y = int(sp.rand() * WINDOW_HEIGHT/GRID_Y)*GRID_Y
            pos = sp.array([x, y])
        else:
            pos = sp.array(pos)

        self.pos = pos
        self.pos_prev = pos
        self.pos_next = pos

        self.update_rect()

    def update_rect(self):
        self.rect = pg.Rect(self.pos[0] + (GRID_X-Food.IMG_X)/2,
                     self.pos[1] + (GRID_Y-Food.IMG_Y)/2,
                     Food.IMG_X,
                     Food.IMG_Y)
        # todo is there a better way to do this, just updating the position? I think there is...

    def ev_collision(self, other):
        print "ouch!"
    def ev_step_end(self):
        pass
    def ev_step(self):
        pass
    def ev_step_begin(self):
        pass
    def process_event(self, ev):
        pass
    def ev_draw(self, DISPLAYSURF):
        self.update_rect()
        pg.draw.rect(DISPLAYSURF, Food.COLOR, self.rect)




if __name__ == '__main__':
    main()
