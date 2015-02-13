import scipy as sp
import pygame as pg

import MyColors
import Objects

# TODO: Test a multipl-room game
class GameRoom(object):

    @property
    def all_instances(self):
        return self._all_instances

    @property
    def solid_instances(self): # TODO: maybe track these separately for speed? This gets called in the collision detection algorithm, so it's probably a good thing to optimize
        return {inst for inst in self.all_instances if isinstance(inst, Objects.SolidObject)}

    def __init__(self, populate_room_fxn, bgcolor=MyColors.GRAY, grid_size=(32, 32), dimensions=(640, 480)):
        self.populate_room = populate_room_fxn
        self.bgcolor = bgcolor
        self.grid = sp.array(grid_size)
        self.rect = pg.Rect((0,0), dimensions)

        self._all_instances = set()

    def create(self, class_, *args, **kwargs):
        """ Use this to create GameObjects
        """
        # The order of the following two lines is arbitrary but very important:
        inst = class_(*args, **kwargs)
        self.all_instances.add(inst)
        return inst

    def destroy(self, inst):
        """ Use this to destroy GameObjects
        """
        # The order of the following two lines is arbitrary but very important:
        inst.ev_destroy()
        self.all_instances.remove(inst)

    # TODO: maybe extend this to accept a set of objects to destory simultaneously? That may be a terrible, bloaty idea
    def destroy_all(self):
        """ Use this to destroy every GameObject in the room
        """
        for inst in self.all_instances:
            inst.ev_destroy()
        self._all_instances = []

    def ev_room_start(self):
        self.populate_room()
        for inst in self.all_instances:
            inst.ev_room_start()

    def ev_room_end(self):
        for inst in self.all_instances:
            inst.ev_room_end()
        self._all_instances = [] # TODO: add optional persistence
