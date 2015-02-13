# TODO: unify terminology

from __future__ import division

__version__ = 0.1

from copy import copy
import pygame as pg
import scipy as sp
import itertools as itt

from collections import defaultdict

import sys

from pygame.locals import *

# Built-ins:
# variables named "dpos" usually refer to these
RIGHT = sp.array(( 1,  0))
UP    = sp.array(( 0, -1))
LEFT  = sp.array((-1,  0))
DOWN  = sp.array(( 0,  1))

TARGET_FPS = 30

FPS_CLOCK = pg.time.Clock()


from Decorators import postprocess

import Alarms
import MyColors
import Objects
import MyLogger
import InputManager



def main(window_title, first_room):
    global current_room
    current_room = first_room

    pg.init()
    screen = pg.display.set_mode(first_room.rect.size)
    pg.display.set_caption(window_title)

    try:
        current_room.populate_room()
        while True: # Main game loop
            game_tick(screen)
    except:
        pg.quit()
        raise # pass the exception to the cmd line, which will print it for us

def game_tick(screen):
    global current_room

    screen.fill(current_room.bgcolor) #todo: move to right before the draw events?

    for inst in copy(current_room.all_instances):
        inst.ev_step_begin()

    Alarms.manager.game_tick()

    events = pg.event.get()
    events = InputManager.manager.filter_events(events) # Filter out and process input events
    for ev in events:
        for inst in copy(current_room.all_instances):
            inst.process_event(ev)

    for inst in copy(current_room.all_instances):
        inst.ev_step()

    _do_collisions()
    _do_boundary_collisions()
    _do_outside_room_events()

    for inst in copy(current_room.all_instances):
        inst.ev_step_end()
        # TODO: order?

    for inst in copy(current_room.all_instances):
        inst.ev_draw(screen)

    _draw_fps_text(screen)
    pg.display.update() # TODO: difference between this and pg.display.flip()?
    FPS_CLOCK.tick(TARGET_FPS)


def _do_boundary_collisions():
    for inst in copy(current_room.solid_instances):
        if inst.rect is not None and check_boundary_collision(inst.rect):
            inst.ev_boundary_collision()

def check_boundary_collision(rect):
    # TODO test
    room_rect = current_room.rect
    return room_rect.colliderect(rect) and (room_rect.union(rect) != room_rect)

def _do_outside_room_events():
    for inst in copy(current_room.solid_instances):
        if inst.rect is not None:
            if is_outside_room(inst.rect):
                inst.ev_outside_room()

def is_outside_room(rect):
    return not check_rect_overlap(rect, current_room.rect)

def check_rect_overlap(rect1, rect2):
    return rect1.colliderect(rect2)

def _do_collisions():
    for inst_a, inst_b in _do_find_collisions():
        MyLogger.logger.debug("Collision detected: %s + %s"%(inst_a.__class__.__name__, inst_b.__class__.__name__))
        inst_a.ev_collision(inst_b)

@postprocess(list)
def _do_find_collisions():
    ''' Finds collisions among the current current_room's solid instances.
        It only generates collision events for instances with collisions == GameObject.CollisionType.ACTIVE,
            but these events can involve the ACTIVE instance colliding with a PASSIVE instacnce
        '''
    colliding_insts = current_room.solid_instances
    active_insts = [inst for inst in colliding_insts if inst.collisions == Objects.CollisionType.ACTIVE]
    for inst_a, inst_b in itt.product(active_insts, colliding_insts):
            if (
                    inst_a is not inst_b
                    and
                    inst_a.rect is not None and inst_b.rect is not None
                    and
                    check_rect_overlap(inst_a.rect, inst_b.rect)
            ):
                yield (inst_a, inst_b)

# Convinience functions:

def terminate():
    """ This is a sloppy quit, bringing things down ASAP. You should probably use end_game() instead
    """
    pg.quit() # TODO: redundant because of the try-catch (?)
    sys.exit()

def end_game():
    current_room.ev_room_end() # TODO: fix infinite terminate/ev_destroy loop that is possible (e.g. in snake.py)
    terminate()

@postprocess(list)
def get_instances_at_position(pos):
    """ Returns a list off all instances that are at the given position
        Calculated by seeing what instances would collide with a point- so if an object is non-colliding, it won't show up here
        """
    for inst in current_room.solid_instances:
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

def grid_view_slow(g_left, g_top, g_width, g_height):
    """
    TODO document this. Basically this returns a view of the instances on the game grid within the given rectangle (given in grid coordinates, not world coordinates)
    """
    assert g_width > 0
    assert g_height > 0
    return sp.array([[get_instances_at_position((g_left+dg_x, g_top+dg_y)*current_room.grid) for dg_x in range(g_width)] for dg_y in range(g_height)])

# def grid_view(g_left, g_top, g_width, g_height): #TODO: working here
#     assert g_width > 0
#     assert g_height > 0
#     rect = pg.Rect(g_left, g_top, g_width, g_height)
#     view = [[None]*g_width]*g_height
#     for inst in current_room.all_instances:
#         try:
#             g_x, g_y = inst.pos//current_room.grid
#         except AttributeError: # Happens if inst.pos doesn't exist
#             continue
#         if rect.collidepoint(g_x, g_y):
#             view[g_y-g_top][g_x-g_left] = inst
#     return view

def clamp(x, a, b):
    ''' Clamps the value of x to be between a and b:
            Returns x if $x \in [a, b]$
            Returns a if $x < a$
            Returns b if $x > b$
        '''
    return min(max(a, x), b)

def floor_to_grid(pos):
    return (pos // current_room.grid).astype(int) * current_room.grid

def round_to_grid(pos):
    return sp.round_(pos / current_room.grid).astype(int) * current_room.grid

pg.font.init()
courier = pg.font.SysFont("Courier", 16)
def draw_text(screen, text, pos, font=courier, color=MyColors.WHITE, smooth=True): # TODO: clean up/generalize this
    surf = font.render(text, smooth, color)
    screen.blit(surf, pos)

def _draw_fps_text(screen):
    color = (FPS_CLOCK.get_fps() > (2*TARGET_FPS)//3) and MyColors.WHITE or MyColors.BRIGHT_RED
    pos = (current_room.rect.width - 60,  current_room.rect.height - 16)
    draw_text(screen, str(int(FPS_CLOCK.get_fps()))+" fps", pos, color=color)

random_int = sp.random.randint

