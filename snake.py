#engine: test speed of pygame.sprite.collide_rect

from __future__ import division

from copy import copy
import pygame as pg
import scipy as sp
# from numpy.linalg import norm
import sys
import random

from pygame.locals import *


FPS = 30
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
GRID_X = 32
GRID_Y = 32

MOUSE_POS = [0, 0] #mutable
all_instances = []

RIGHT = 0
UP    = 1
LEFT  = 2
DOWN  = 3

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


def main():
    global MOUSE_POS
    global all_instances

    pg.init()
    FPS_CLOCK = pg.time.Clock()
    DISPLAY_SURF = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pg.display.set_caption('Snake')

    try:
        all_instances = init_room()
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

            events = pg.event.get()
            #todo enginde idea: have it hold a table of keys and whether or not they're pressed, down, or released
            for ev in events:
                for inst in temp_all_instances:
                    inst.process_event(ev)

            temp_has_collided = set() # a record of all instances that have colllided this step
            for inst_a, inst_b in get_collisions(temp_all_instances):
                print "COLL: ", inst_a.__class__.__name__, inst_b.__class__.__name__
                inst_a.ev_collision(inst_b)
                inst_b.ev_collision(inst_a)
                temp_has_collided.add(inst_a)
                temp_has_collided.add(inst_b)
            for inst in temp_has_collided:
                inst.ev_postcollision()

            for inst in temp_all_instances:
                inst.ev_step()

            do_boundary_collisions(temp_all_instances)
            do_outside_room_events(temp_all_instances)

            for inst in temp_all_instances:
                inst.pos_prev = copy(inst.pos)

            for inst in temp_all_instances:
                inst.ev_step_end()
                # TODO order?

            for inst in temp_all_instances:
                inst.ev_draw(DISPLAY_SURF)

            pg.display.update()
            FPS_CLOCK.tick(FPS)
    except:
        pg.quit()
        raise # pass the exception to the cmd line, which will print it for us


def terminate():
    pg.quit() # redundant because of the try-catch
    sys.exit()

def do_boundary_collisions(instances):
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

def do_outside_room_events(instances):
    for inst in instances:
        if is_outside_room(inst.rect):
            inst.ev_outside_room()

def is_outside_room(rect):
    return not do_rects_overlap(rect, pg.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

def get_instance_at_position(instances, pos):
    # TODO rethink this: it's order dependent. maybe you should return a list of *all* instances at the position?
    for inst in instances:
        if inst.rect != None and do_rects_overlap(inst.rect, pg.Rect(pos[0], pos[1], 0, 0)):
            return inst
    return None

def do_rects_overlap(rect1, rect2):
    return (
            do_intervals_overlap((rect1.left, rect1.right), (rect2.left, rect2.right))
            and do_intervals_overlap((rect1.top, rect1.bottom), (rect2.top, rect2.bottom))
    )

def do_intervals_overlap(t1, t2):
    '''
        Returns whether $[a,b]$ interected with $[c,d]$ is not the empty set,
            where t1 and t2 are tuples (a, b) and (c, d);
        '''
    (a,b) = t1
    (c,d) = t2
    assert a<=b, 'Malformed interval'
    assert c<=d, 'Malformed interval'
    return not(a <= b < c <= d or c <= d < a <= b)

def get_collisions(instances):
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
                    and do_rects_overlap(inst_a.rect, inst_b.rect)
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

def random_int(low, high):
    """ Returns a random integer in the range $$.
        """




class Controller(object):
    def __init__(self):
        self.pos = sp.array((16, 16))
        self.pos_prev = copy(self.pos)

        self.update_rect()
    def process_event(self, ev):
        if self.is_quit_event(ev):
            terminate()

        #mouse interaction:
        elif ev.type == MOUSEBUTTONUP:
            if ev.button == 1: #left click
                # all_instances.append(Food(ev.pos))
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
        pg.draw.circle(DISPLAY_SURF, Colors.CYAN, self.pos, radius)

    # @staticmethod
    def is_quit_event(self, ev):
        return (
            ev.type == QUIT
            or (ev.type == KEYUP and ev.key == K_ESCAPE)
        )


def init_room():
    global all_instances
    all_instances = []
    all_instances.append(Controller())
    all_instances.append(Snake([128, 128]))
    for _ in range(6):
        all_instances.append(Food())
    return all_instances





#specific to this game:





class Snake(object):
    MOVE_DELAY = 4
    IMG_X = GRID_X
    IMG_Y = GRID_Y

    COLOR = Colors.GREEN
    def __init__(self, pos): #todo engine: we'll nee to separate __init__ and create events in order to be able to say friend=instance_create(FriendClass)
        self.pos = sp.array(pos) #todo use this in parent object: , dtype=float)
        self.pos_prev = copy(self.pos)

        self.alarm = Snake.MOVE_DELAY

        self.dir = RIGHT

        self.update_rect()

    def update_rect(self):
        self.rect = pg.Rect(self.pos[0], self.pos[1], Snake.IMG_X, Snake.IMG_Y)
        # todo is there a better way to do this, just updating the position? I think there is...

    def ev_step(self):
        self.alarm -= 1
        if self.alarm <= 0:
            if self.dir == RIGHT:
                self.pos[0] += Snake.IMG_X
            elif self.dir == LEFT:
                self.pos[0] -= Snake.IMG_X
            elif self.dir == DOWN:
                self.pos[1] += Snake.IMG_Y
            elif self.dir == UP:
                self.pos[1] -= Snake.IMG_Y
            self.alarm = Snake.MOVE_DELAY

    def ev_collision(self, other):
        print "Snake +", other.__class__.__name__
        if other.__class__ == Food:
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
                if self.dir != RIGHT:
                    self.dir = LEFT
            if ev.key == K_RIGHT:
                if self.dir != LEFT:
                    self.dir = RIGHT
            if ev.key == K_UP:
                if self.dir != DOWN:
                    self.dir = UP
            if ev.key == K_DOWN:
                if self.dir != UP:
                    self.dir = DOWN

    def ev_draw(self, DISPLAY_SURF):
        self.update_rect()
        pg.draw.rect(DISPLAY_SURF, Snake.COLOR, self.rect)


class Food(object):
    IMG_X = 12
    IMG_Y = 12
    COLOR = Colors.RED
    def __init__(self, pos=None):
        if pos == None:
            while x = int(sp.rand() * WINDOW_WIDTH/GRID_X)*GRID_X # todo ref random or sp.random instead
            y = int(sp.rand() * WINDOW_HEIGHT/GRID_Y)*GRID_Y
            self.pos = sp.array([x, y])
        else:
            self.pos = sp.array(pos)

        self.pos_prev = copy(pos)

        self.update_rect()

    def update_rect(self):
        self.rect = pg.Rect(
                self.pos[0] + (GRID_X-Food.IMG_X)/2,
                self.pos[1] + (GRID_Y-Food.IMG_Y)/2,
                Food.IMG_X,
                Food.IMG_Y
        )
        # todo is there a better way to do this, just updating the position? I think there is...

    def ev_collision(self, other):
        if other.__class__ == Snake:
            destroy(self)

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
    main()

