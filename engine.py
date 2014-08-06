#engine: test speed of pygame.sprite.collide_rect

from __future__ import division

from copy import copy
import pygame as pg
import scipy as sp
# from numpy.linalg import norm
import sys

from pygame.locals import *


RIGHT = 0
UP    = 1
LEFT  = 2
DOWN  = 3


FPS = 30
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
GRID_X = 32
GRID_Y = 32

MOUSE_POS = [0, 0] #mutable
all_instances = []

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

    ALL = (GRAY, NAVYBLUE, WHITE, RED, GREEN, BLUE, \
                    YELLOW, ORANGE, PURPLE, CYAN)

bgColor = Colors.NAVYBLUE


def main(window_title, init_room_fxn):
    global MOUSE_POS
    global all_instances

    pg.init()
    FPS_CLOCK = pg.time.Clock()
    DISPLAY_SURF = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pg.display.set_caption(window_title)

    try:
        all_instances = init_room_fxn()
        while True: # Main game loop

            DISPLAY_SURF.fill(bgColor) #todo move to right before the draw events? I think that's how it's done in GM

            """
            Create a new list of all instances that exist *at this moment*
            This ensures that objects created *during* this step will NOT
                execute step events
            """
            temp_all_instances = tuple(all_instances)

            for inst in temp_all_instances:
                inst.ev_step_begin()

            events = pg.event.get() # TODO do I also need to call pygame.event.poll()?
            #todo enginde idea: have it hold a table of keys and whether or not they're pressed, down, or released
            for ev in events:
                for inst in temp_all_instances:
                    inst.process_event(ev)

            _do_collisions(temp_all_instances)

            for inst in temp_all_instances:
                inst.ev_step()

            _do_boundary_collisions(temp_all_instances)
            _do_outside_room_events(temp_all_instances)

            for inst in temp_all_instances:
                inst.pos_prev = copy(inst.pos)

            for inst in temp_all_instances:
                inst.ev_step_end()
                # TODO order?

            for inst in temp_all_instances:
                inst.ev_draw(DISPLAY_SURF)

            pg.display.update() # TODO difference between this and pg.display.flip()?
            FPS_CLOCK.tick(FPS)
    except:
        pg.quit()
        raise # pass the exception to the cmd line, which will print it for us


def terminate():
    pg.quit() # redundant because of the try-catch
    sys.exit()

def _do_boundary_collisions(instances):
    for inst in instances:
        side = get_boundary_touching(inst.rect)
        if side != None:
            inst.ev_boundary_collision(side)

def get_boundary_touching(rect):
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
        if is_outside_room(inst.rect):
            inst.ev_outside_room()

def is_outside_room(rect):
    return not check_rect_overlap(rect, pg.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

def get_instances_at_position(instances, pos):
    inst_list = []
    for inst in instances:
        if inst.rect != None and check_rect_overlap(inst.rect, pg.Rect(pos[0], pos[1], 0, 0)):
            inst_list.append(inst)
    return inst_list

def check_rect_overlap(rect1, rect2): # TODO move into your own rect class?
    return (
            check_interval_overlap((rect1.left, rect1.right), (rect2.left, rect2.right))
            and check_interval_overlap((rect1.top, rect1.bottom), (rect2.top, rect2.bottom))
    )

def check_interval_overlap(t1, t2):
    '''
        Returns whether $[a,b]$ interected with $[c,d]$ is not the empty set,
            where t1 and t2 are tuples (a, b) and (c, d);
        '''
    (a, b) = t1
    (c, d) = t2
    assert a <= b, 'Malformed interval'
    assert c <= d, 'Malformed interval'
    return not(a <= b < c <= d or c <= d < a <= b)

def _do_collisions(instances):
    temp_has_collided = set() # a record of all instances that have colllided this step
    for inst_a, inst_b in _do_find_collisions(temp_all_instances):
        print "COLL: ", inst_a.__class__.__name__, inst_b.__class__.__name__
        inst_a.ev_collision(inst_b)
        inst_b.ev_collision(inst_a)
        temp_has_collided.add(inst_a)
        temp_has_collided.add(inst_b)
    for inst in temp_has_collided:
        inst.ev_postcollision()

def _do_find_collisions(instances):
    ''' Checks for collisions among the instances.
        Naively checks each element against every other element (O(n^2))
            TODO optimize somehow?
        Will NOT generate symmetric collisions;
            ie if (a,b) is on the list then (b,a) will NOT also be
        '''
    collisions_list = []
    for i, inst_a in enumerate(instances):
        for inst_b in instances[i+1:]:
            if inst_a == inst_b:
                raise Exception("Programmer Logic error; you shouldn't be seeing this message (this is a bug in the game engine)")
            if (
                    inst_a.rect != None and inst_b.rect != None
                    and check_rect_overlap(inst_a.rect, inst_b.rect)
            ):
                collisions_list.append( (inst_a, inst_b) )
    return tuple(collisions_list)

def destroy(inst):
    all_instances.remove(inst)

# Math:

def clamp(x, a, b):
    ''' Clamps the value of x to be between a and b:
            Returns x if $x \in [a, b]$
            Returns a if $x < a$
            Returns b if $x > b$
        '''
    return min(max(a, x), b)

random_int = sp.random.randint

# class GameObject(object):
