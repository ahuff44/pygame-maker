import scipy as sp
import pygame as pg

import MyColors
import Objects

# TODO: Generalize this. There's lots of stuff that will break when you add multiple rooms. (e.g. the main() game loop will break)
class GameRoom(object):

    @property
    def all_instances(self):
        return self._all_instances

    @property
    def solid_instances(self): # TODO: track this separately for speed
        return {inst for inst in self.all_instances if isinstance(inst, Objects.SolidObject)}

    def __init__(self, populate_room_fxn, bgcolor=MyColors.GRAY, grid_size=(32, 32), dimensions=(640, 480)):
        self.populate_room = lambda: populate_room_fxn(self) # TODO: see if there's a better way to make this work; I want to be able to say room.populate_room = populate_room but then self isn't auto-passed in for some reason
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

    def destroy_all(self):
        """ Use this to destroy every GameObject in the room
        """
        for inst in self.all_instances:
            inst.ev_destroy()
        self._all_instances = []

    def ev_room_end(self):
        # TODO: implement object room events
        for inst in self.all_instances:
            inst.ev_room_end()
        self._all_instances = [] # TODO: add optional persistence

    def populate_room(self):
        raise NotImplementedError("This should have be overridden by the function you passed in to this room's constructor")
