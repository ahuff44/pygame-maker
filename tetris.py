#!/usr/bin/env python
from __future__ import division

import engine
import pygame as pg
from pygame.locals import *

import sys
from time import sleep
from copy import copy
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
    class Side(engine.SolidObject):
        """A boundary around the play area"""
        dimensions = engine.GRID*g_dimensions
        color = engine.MyColor.DARK_GRAY
    return Side
g_arena_width, g_arena_height = (10, 16)
SideSide = _make_side((1, g_arena_height))
BottomSide = _make_side((g_arena_width+2, 1))

g_HUD_width = 6

def populate_room(self):
    self.create(Controller)
    self.create(SideSide, engine.GRID*(0, 0))
    self.create(SideSide, engine.GRID*(g_arena_width+1, 0))
    self.create(BottomSide, engine.GRID*(0, g_arena_height))
room = engine.GameRoom.make_room(populate_room, dimensions=engine.GRID*(g_arena_width+2+g_HUD_width, g_arena_height+1))

class Controller(engine.GameController):
    PIECE_START_POS = engine.GRID*(g_arena_width//2, 1)
    PIECE_WAIT_POS = engine.GRID*(g_arena_width+2 + g_HUD_width//2 - 1, 3)

    def __init__(self):
        super(Controller, self).__init__()

        self.score = 0
        self.total_lines = 0

        self.update_move_delay()

        # Register methods
        self.move_piece_alarm = engine.Alarm.new_alarm(lambda: self.lower_piece(), self.move_delay)

        self.piece = engine.game_room.create(Piece, Controller.PIECE_START_POS)
        self.next_piece = engine.game_room.create(Piece, Controller.PIECE_WAIT_POS)

    def use_next_piece(self):
        """ Destroys the current piece, checks for lines, and creates a new piece
        """
        self.process_lines()
        engine.game_room.destroy(self.piece)

        self.piece = self.next_piece
        if not self.piece.attempt_move_to(Controller.PIECE_START_POS): # Lose
            engine.terminate()

        self.next_piece = engine.game_room.create(Piece, Controller.PIECE_WAIT_POS)

    # TODO get rid of all instances of "+= engine.GRID" and make it all "+= 1" somehow
    def process_lines(self):
        grid_x, grid_y = engine.GRID
        g_top = 0
        g_left = 1
        g_bottom = g_arena_height
        g_right = g_arena_width + 1

        g_width = g_right - g_left
        g_height = g_bottom - g_top

        # print map(lambda row: map(lambda inst: inst.__class__.__name__, row), engine.grid_view(g_left, g_top, g_width, g_height)) # DEBUG
        # return

        lines = 0
        for g_y, row in enumerate(engine.grid_view_slow(g_left, g_top, g_width, g_height)):
            if all(len(inst_list) for inst_list in row): # If there's a complete line
                lines += 1
                for inst_list in row:
                    map(engine.game_room.destroy, inst_list)
                # Shift all higher blocks down:
                for row in reversed(engine.grid_view_slow(g_left, g_top, g_width, g_y)):
                    for inst_list in row:
                        for inst in inst_list:
                            inst.y += engine.GRID[1]
        self.score += [0, 10, 30, 50, 100][lines] # NOTE: this would break if it were possible to get more than 4 lines at once
        self.total_lines += lines
        if lines == 4:
            engine.game_room.create(TetrisMessage)
        self.update_move_delay()

    def update_move_delay(self):
        self.move_delay = max(1, 30 - 3*(self.total_lines//10))
        # int(engine.clamp(30*sp.exp(-nearest_10/50), 1, 30))

    # NOTE: this is on an alarm
    def lower_piece(self):
        is_success = self.piece.attempt_move_relative(engine.DOWN)

        if not is_success:

            # # TODO working here. based on cprofile and runsnake, it looks like you'll want to optimize grid_view(). I mean duh, it's O(n**2). Implement a whole new CollisionType.GRID maybe? idk if that's too much bloat
            # if self.total_lines > 50:
            #     import cProfile
            #     cProfile.runctx("self.use_next_piece()", globals(), locals(), "out%d.profile"%self.total_lines)
            # else:
            #      self.use_next_piece()

            self.use_next_piece()

        self.move_piece_alarm.reset(self.move_delay)

        return is_success

    def ev_key(self, key, status):
        super(Controller, self).ev_key(key, status)
        if status == engine.InputManager.Constants.PRESSED:
            if key == K_a:
                self.piece.attempt_rotate(-1)
            elif key == K_d:
                self.piece.attempt_rotate(1)
            elif key == K_s: # Drop the piece as far as it can go
                while self.lower_piece():
                    # You get more score the higher you drop it from
                    self.score += 2
            elif key == K_LEFT:
                self.piece.attempt_move_relative(engine.LEFT)
            elif key == K_RIGHT:
                self.piece.attempt_move_relative(engine.RIGHT)
        elif status == engine.InputManager.Constants.HELD:
            if key == K_DOWN: # This one is special; it resets the drop timer and forces a new piece to spawn if it fails
                # You score points for pressing K_DOWN
                self.score += 1
                self.lower_piece()

    def process_event(self, ev):
        super(Controller, self).process_event(ev)
        if ev.type == MOUSEBUTTONDOWN:
            # print map(lambda inst: inst.__class__.__name__, engine.get_instances_at_position(ev.pos))
            print engine.get_instances_at_position(ev.pos)

    def ev_draw(self, screen):
        super(Controller, self).ev_draw(screen)
        engine.draw_text(screen, "Score: %d"%self.score, engine.GRID*(g_arena_width+2, 0))
        engine.draw_text(screen, "Lines: %d"%self.total_lines, engine.GRID*(g_arena_width+2, 1))

    def ev_destroy(self):
        print "Tough luck!"
        print "\tTotal Lines:", self.total_lines
        print "\tScore:", self.score

class TetrisMessage(engine.GhostObject):
    """A banner than tells the player she got a tetris"""
    font = pg.font.SysFont(None, 72)
    msg = "TETRIS!"
    center = (font.size(msg)[0]//2, 0)

    def __init__(self, pos=engine.GRID*(1 + g_arena_width//2, g_arena_height//2)):
        super(TetrisMessage, self).__init__()
        self.pos = pos

        # Register alarms
        engine.Alarm.new_alarm(lambda: self.change_color(), 20)
        engine.Alarm.new_alarm(lambda: engine.game_room.destroy(self), 30)

        self.color = engine.MyColor.BRIGHT_GREEN

    def change_color(self):
        self.color = engine.MyColor.GREEN

    def ev_draw(self, screen):
        engine.draw_text(screen, "TETRIS!", self.pos-TetrisMessage.center, font=TetrisMessage.font, color=self.color)

class Piece(engine.GhostObject):
    COLORS = [
        (engine.MyColor.BRIGHT_RED, engine.MyColor.RED),
        (engine.MyColor.BRIGHT_ORANGE, engine.MyColor.ORANGE),
        (engine.MyColor.BRIGHT_YELLOW, engine.MyColor.YELLOW),
        (engine.MyColor.BRIGHT_GREEN, engine.MyColor.GREEN),
        (engine.MyColor.BRIGHT_BLUE, engine.MyColor.BLUE),
        (engine.MyColor.BRIGHT_PURPLE, engine.MyColor.PURPLE)
    ]

    @property
    def center_pos(self):
        return self.group[0].center_pos + self.relative_rotation_center

    def __init__(self, pos):
        self.group = self.generate_blocks(pos)

    def generate_blocks(self, pos):
        """ Generates a random configuration of blocks
        The possible configurations are:
             -------------------------------------------
            |  0   | 1  | 2    | 3   | 4   | 5   | 6    |
            |  +o+ | oL | +oL+ | +o+ | +o+ |  o+ | +o   |
            |   +  | ++ |      | +   |   + | ++  |  ++  |
             -------------------------------------------
            KEY: '+'s are blocks, 'o's are the 'head' block that the configuration is centered on, unless there's an 'L'; then it's centered at the corner where the L is pointing
        """
        L  = engine.LEFT
        R  = engine.RIGHT
        D  = engine.DOWN

        configs = [ # Entry format: ([relative positions of blocks], center of rotation relative to the center of the head block)
            ([L, R, D], (0, 0)),
            ([R, D, D+R], (0.5, 0.5)),
            ([L, R, R+R], (0.5, 0.5)),
            ([L, R, D+L], (0, 0)),
            ([L, R, D+R], (0, 0)),
            ([R, D+L, D], (0, 0)),
            ([L, D, D+R], (0, 0))
        ]
        relative_positions, self.relative_rotation_center = random.choice(configs)
        self.relative_rotation_center = (sp.array(self.relative_rotation_center)*engine.GRID).astype(int)

        colors = random.choice(Piece.COLORS)
        group = [engine.game_room.create(Block, pos, colors)]
        for dpos in relative_positions:
            block_pos = pos + engine.GRID*dpos
            group.append(engine.game_room.create(Block, block_pos, colors))
        return group

    def attempt_rotate(self, direction):
        """ Rotates the piece around the center block. Returns whether the rotation was successful.
        direction = 1 --> clockwise
        direction = -1 --> counterclockwise
        """
        assert direction in [-1, 1]
        rotation_matrix = sp.array([[0, -1], [1, 0]]) * direction
        new_positions = []
        for block in self.group:
            relative_pos = block.center_pos - self.center_pos
            relative_pos = sp.dot(rotation_matrix, relative_pos)
            new_positions.append((self.center_pos + relative_pos).astype(int))

        is_success = all(engine.is_free(pos, self.group) for pos in new_positions)

        if is_success:
            for c_pos, block in zip(new_positions, self.group):
                block.center_pos = c_pos

            # Rotate the rotation center
            self.relative_rotation_center = sp.dot(rotation_matrix, self.relative_rotation_center)
        return is_success

    # TODO this is super gross because of g_ / non g_ interaction. Standardize
    def attempt_move_to(self, pos):
        g_dpos = (pos - self.group[0].pos) // engine.GRID
        return self.attempt_move_relative(g_dpos)

    def attempt_move_relative(self, g_dpos):
        """ Tries to move the piece down by one
        Returns whether the move was successful
        """
        is_success = all(engine.is_free(block.pos + engine.GRID*g_dpos, self.group) for block in self.group)

        if is_success:
            for block in self.group:
                block.pos += engine.GRID*g_dpos
        return is_success

    # def ev_draw(self, screen):
    #     super(Piece, self).ev_draw(screen)
    #     pg.draw.circle(screen, engine.MyColor.RED, self.center_pos, 4)

    def ev_destroy(self):
        for block in self.group:
            block.settle()

class Block(engine.SolidObject):
    dimensions = copy(engine.GRID)

    def __init__(self, pos, colors):
        super(Block, self).__init__(pos)
        color, self.settled_color = colors
        self.color = color

    def settle(self):
        """
        This is called by this Block's Piece when this Block hits the ground
        """
        self.color = self.settled_color

    def ev_outside_room(self):
        pass

if __name__ == '__main__':
    engine.main("Tetris", room)
