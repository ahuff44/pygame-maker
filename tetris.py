#!/usr/bin/env python

import engine
import pygame as pg
from pygame.locals import *

import sys
import logging

import scipy as sp
import random

logger = logging.getLogger(__name__) # TODO figure out how to get this to work
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(name)s %(levelname)8s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("tetris.py hello")

def _make_side(g_dimensions):
    class Side(engine.GameObject):
        """A boundary around the play area"""
        sprite = engine.Sprite(engine.GRID*g_dimensions, engine.Colors.DARK_GRAY)
    return Side
g_arena_width, g_arena_height = (8, 14)
SideSide = _make_side((1, g_arena_height))
BottomSide = _make_side((g_arena_width+2, 1))

g_HUD_width = 5

def populate_room(self):
    self.create(Controller)
    self.create(SideSide, engine.GRID*(0, 0))
    self.create(SideSide, engine.GRID*(g_arena_width+1, 0))
    self.create(BottomSide, engine.GRID*(0, g_arena_height))
room = engine.GameRoom.make_room(populate_room, dimensions=engine.GRID*(g_arena_width+2+g_HUD_width, g_arena_height+1))

class Controller(engine.GameController):
    MOVE_DELAY = 15

    def __init__(self):
        super(self.__class__, self).__init__()
        self.move_alarm = engine.Alarm.new_alarm(lambda: self.lower_block_group(), Controller.MOVE_DELAY)
        self.block_group = engine.game_room.create(BlockGroup)
        self.is_held = {K_DOWN: False, K_LEFT: False, K_RIGHT: False} # TODO
        self.score = 0

    def use_next_block_group(self):
        """ Destroys the current BG, checks for lines, and creates a new BG
        """
        self.test_for_lines()
        engine.game_room.destroy(self.block_group)
        self.block_group = engine.game_room.create(BlockGroup)


    # TODO get rid of all instances of "+= engine.GRID" and make it all "+= 1" somehow
    def test_for_lines(self):
        grid_x, grid_y = engine.GRID
        g_top = 0
        g_left = 1
        g_bottom = g_arena_height
        g_right = g_arena_width + 1

        g_width = g_right - g_left
        g_height = g_bottom - g_top

        # print engine.grid_view(g_top, g_left, g_width, g_height) # DEBUG
        lines = 0
        for g_y, row in enumerate(engine.grid_view(g_top, g_left, g_width, g_height)):
            if all(len(inst_list) for inst_list in row): # If there's a complete line
                lines += 1
                for inst_list in row:
                    map(engine.game_room.destroy, inst_list)
                # Shift all higher blocks down:
                for row in reversed(engine.grid_view(g_top, g_left, g_width, g_y)):
                    for inst_list in row:
                        for inst in inst_list:
                            inst.y += engine.GRID[1]
        self.score += [0, 1, 3, 5, 10][lines] # NOTE: this would break if it were possible to get more than 4 lines at once

    # about to work on this:
    # @engine.keyhandler(K_DOWN, K_SPACE)
    # def handle_k_down(self, key, press_length):
    #     if press_length == engine.KeyStatus.KEY_PRESS:
    #         pass
    #     elif status == engine.KeyStatus.KEY_HELD:
    #         pass
    #     elif status == engine.KeyStatus.KEY_RELEASE:
    #         pass

    def ev_step(self):
        # TODO
        if self.is_held[K_DOWN]: # This one is special; it resets the drop timer and forces a new block group to spawn if it fails
            self.lower_block_group()
        if self.is_held[K_LEFT]:
            self.block_group.attempt_move(engine.LEFT)
        if self.is_held[K_RIGHT]:
            self.block_group.attempt_move(engine.RIGHT)

    # NOTE: this is on an alarm
    def lower_block_group(self):
        is_success = self.block_group.attempt_move(engine.DOWN)

        if not is_success:
            self.use_next_block_group()
        self.move_alarm.reset()

        return is_success

    def process_event(self, ev):
        super(self.__class__, self).process_event(ev)
        if ev.type == KEYDOWN:
            if ev.key in [K_LEFT, K_RIGHT, K_DOWN]:
                self.is_held[ev.key] = True # TODO refactor into engine
            elif ev.key == K_a:
                self.block_group.attempt_rotate(-1)
            elif ev.key == K_d:
                self.block_group.attempt_rotate(1)
            elif ev.key == K_s:
                while self.lower_block_group():
                    pass
        elif ev.type == KEYUP and ev.key in [K_LEFT, K_RIGHT, K_DOWN]:
            self.is_held[ev.key] = False
        elif ev.type == MOUSEBUTTONDOWN:
            print map(lambda inst: inst.__class__.__name__, engine.get_instances_at_position(ev.pos))

    def ev_draw(self, screen):
        super(self.__class__, self).ev_draw(screen)
        engine.draw_text(screen, "Score: %d"%self.score, engine.GRID*(g_arena_width+2, 0))

class BlockGroup(engine.GhostObject):
    def __init__(self, pos=engine.GRID*(g_arena_width//2, 0)):
        self.group = self.generate_blocks(pos)

    def generate_blocks(self, pos):
        """ Generates a random configuration of blocks
        The possible configurations are:
             -------------------------------------------
            |  0   | 1  | 2    | 3   | 4   | 5   | 6    |
            |  +o+ | o+ | +o++ | +o+ | +o+ |  o+ | +o   |
            |   +  | ++ |      | +   |   + | ++  |  ++  |
             -------------------------------------------
            KEY: '+'s are blocks, 'o's are the 'head' block that the configuration is (roughly) centered on (see cut(1)(configs))
                TODO updating: make 1 3 and 4 rotate around 1/2 blocks
        """
        L  = engine.LEFT
        R  = engine.RIGHT
        D  = engine.DOWN

        configs = [ # Entry format: ([relative positions of blocks], center of rotation relative to head block)
            ([L, R, D], (0.5, 0.5)),
            ([R, D, D+R], (1, 1)),
            ([L, R, R+R], (1, 1)),
            ([L, R, D+L], (-1, 1)),
            ([L, R, D+R], (1, 1)),
            ([R, D+L, D], (1, 1)),
            ([L, D, D+R], (1, 1))
        ]
        relative_positions, self.relative_rotation_center = random.choice(configs)

        group = [engine.game_room.create(Block, pos)]
        for dpos in relative_positions:
            block_pos = pos + engine.GRID*dpos
            group.append(engine.game_room.create(Block, block_pos))
        return group

    def attempt_rotate(self, direction):
        """ Rotates the block group around the center block. Returns whether the rotation was successful.
        direction = 1 --> clockwise
        direction = -1 --> counterclockwise
        """
        assert direction in [-1, 1]
        rotation_matrix = sp.array([[0, -1], [1, 0]]) * direction
        head = self.group[0]
        rotation_center = head.pos
        new_positions = []
        for block in self.group:
            relative_pos = block.pos - rotation_center
            relative_pos = sp.dot(rotation_matrix, relative_pos)
            new_positions.append((rotation_center + relative_pos).astype(int))

        is_success = all(engine.is_free(pos, self.group) for pos in new_positions)

        if is_success:
            for pos, block in zip(new_positions, self.group):
                block.pos = pos
        return is_success

    def attempt_move(self, dpos):
        """ Tries to move the block group down by one
        Returns whether the move was successful
        """
        is_success = all(engine.is_free(block.pos + engine.GRID*dpos, self.group) for block in self.group)

        if is_success:
            for block in self.group:
                block.pos += engine.GRID*dpos
        return is_success

    def ev_draw(self, screen):
        super(self.__class__, self).ev_draw(screen)
        rotation_center = self.group[0].pos + engine.GRID*self.relative_rotation_center
        pg.draw.circle(screen, engine.Colors.RED, rotation_center.astype(int), 4)

    def ev_destroy(self):
        for block in self.group:
            block.settle()

class Block(engine.GameObject):
    collisions = engine.GameObject.CollisionType.ACTIVE # The instances start ACTIVE but become PASSIVE when they land
    sprite = engine.Sprite(engine.GRID, engine.Colors.BRIGHT_BLUE)
    settled_sprite = engine.Sprite(engine.GRID, engine.Colors.BLUE)

    def settle(self):
        """
        This is called by this Block's BlockGroup when this Block hits the ground
        """
        self.collisions = engine.GameObject.CollisionType.PASSIVE
        self.sprite = Block.settled_sprite

    def ev_outside_room(self):
        pass

if __name__ == '__main__':
    engine.main("Tetris", room)
