#!/usr/bin/env python
from __future__ import division

import scipy as sp
import sys
from time import sleep
from copy import copy
import random

import pygame as pg
from pygame.locals import *

import MyLogger
import Engine
import MyColors
import Objects
import Alarms
import Rooms

def _make_side(g_dimensions):
    class Side(Objects.SolidObject):
        """A boundary around the play area"""
        dimensions = Engine.GRID*g_dimensions
        color = MyColors.DARK_GRAY
    return Side
g_arena_width, g_arena_height = (10, 16)
SideSide = _make_side((1, g_arena_height))
BottomSide = _make_side((g_arena_width+2, 1))

g_HUD_width = 6

def populate_room(room):
    room.create(Controller)
    room.create(SideSide, Engine.GRID*(0, 0))
    room.create(SideSide, Engine.GRID*(g_arena_width+1, 0))
    room.create(BottomSide, Engine.GRID*(0, g_arena_height))
room = Rooms.GameRoom(populate_room, dimensions=Engine.GRID*(g_arena_width+2+g_HUD_width, g_arena_height+1))

class Controller(Objects.GameController):
    PIECE_START_POS = Engine.GRID*(g_arena_width//2, 1)
    PIECE_WAIT_POS = Engine.GRID*(g_arena_width+2 + g_HUD_width//2 - 1, 3)

    def __init__(self):
        super(Controller, self).__init__()

        self.score = 0
        self.total_lines = 0

        self.update_move_delay()

        # Register methods
        self.move_piece_alarm = Alarms.Alarm(lambda: self.lower_piece(), self.move_delay)
        Alarms.manager.schedule(self.move_piece_alarm)

        self.piece = Engine.current_room.create(Piece, Controller.PIECE_START_POS)
        self.next_piece = Engine.current_room.create(Piece, Controller.PIECE_WAIT_POS)

    def use_next_piece(self):
        """ Destroys the current piece, checks for lines, and creates a new piece
        """
        self.process_lines()
        Engine.current_room.destroy(self.piece)

        self.piece = self.next_piece
        if not self.piece.attempt_move_to(Controller.PIECE_START_POS): # Lose
            Engine.terminate()

        self.next_piece = Engine.current_room.create(Piece, Controller.PIECE_WAIT_POS)

    # TODO: get rid of all instances of "+= Engine.GRID" and make it all "+= 1" somehow
    def process_lines(self):
        grid_x, grid_y = Engine.GRID
        g_top = 0
        g_left = 1
        g_bottom = g_arena_height
        g_right = g_arena_width + 1

        g_width = g_right - g_left
        g_height = g_bottom - g_top

        # print map(lambda row: map(lambda inst: inst.__class__.__name__, row), Engine.grid_view(g_left, g_top, g_width, g_height)) # DEBUG::
        # return

        lines = 0
        for g_y, row in enumerate(Engine.grid_view_slow(g_left, g_top, g_width, g_height)):
            if all(len(inst_list) for inst_list in row): # If there's a complete line
                lines += 1
                for inst_list in row:
                    map(Engine.current_room.destroy, inst_list)
                # Shift all higher blocks down:
                for row in reversed(Engine.grid_view_slow(g_left, g_top, g_width, g_y)):
                    for inst_list in row:
                        for inst in inst_list:
                            inst.y += Engine.GRID[1]
        self.score += [0, 10, 30, 50, 100][lines] # NOTE: this would break if it were possible to get more than 4 lines at once
        self.total_lines += lines
        if lines == 4:
            Engine.current_room.create(TetrisMessage)
        self.update_move_delay()

    def update_move_delay(self):
        self.move_delay = max(1, 30 - 3*(self.total_lines//10))
        # int(Engine.clamp(30*sp.exp(-nearest_10/50), 1, 30))

    # NOTE: this is on an alarm
    def lower_piece(self):
        is_success = self.piece.attempt_move_relative(Engine.DOWN)

        if not is_success:

            # # TODO: working here. based on cprofile and runsnake, it looks like you'll want to optimize grid_view(). I mean duh, it's O(n**2). Implement a whole new CollisionType.GRID maybe? idk if that's too much bloat
            # if self.total_lines > 50:
            #     import cProfile
            #     cProfile.runctx("self.use_next_piece()", globals(), locals(), "out%d.profile"%self.total_lines)
            # else:
            #      self.use_next_piece()

            self.use_next_piece()

        self.move_piece_alarm.reset(self.move_delay)

        return is_success

    def ev_keyboard(self, key, status):
        super(Controller, self).ev_keyboard(key, status)
        if status == Engine.InputManager.Constants.PRESSED:
            if key == K_a:
                self.piece.attempt_rotate(-1)
            elif key == K_d:
                self.piece.attempt_rotate(1)
            elif key == K_s: # Drop the piece as far as it can go
                while self.lower_piece():
                    # You get more score the higher you drop it from
                    self.score += 2
            elif key == K_LEFT:
                self.piece.attempt_move_relative(Engine.LEFT)
            elif key == K_RIGHT:
                self.piece.attempt_move_relative(Engine.RIGHT)
        elif status == Engine.InputManager.Constants.HELD:
            if key == K_DOWN: # This one is special; it resets the drop timer and forces a new piece to spawn if it fails
                # You score points for pressing K_DOWN
                self.score += 1
                self.lower_piece()

    def process_event(self, ev):
        super(Controller, self).process_event(ev)
        if ev.type == MOUSEBUTTONDOWN:
            # print map(lambda inst: inst.__class__.__name__, Engine.get_instances_at_position(ev.pos))
            print Engine.get_instances_at_position(ev.pos)

    def ev_draw(self, screen):
        super(Controller, self).ev_draw(screen)
        Engine.draw_text(screen, "Score: %d"%self.score, Engine.GRID*(g_arena_width+2, 0))
        Engine.draw_text(screen, "Lines: %d"%self.total_lines, Engine.GRID*(g_arena_width+2, 1))

    def ev_destroy(self):
        print "Tough luck!"
        print "\tTotal Lines:", self.total_lines
        print "\tScore:", self.score

class TetrisMessage(Objects.GhostObject):
    """A banner than tells the player she got a tetris"""
    font = pg.font.SysFont(None, 72)
    msg = "TETRIS!"
    center = (font.size(msg)[0]//2, 0)

    def __init__(self, pos=Engine.GRID*(1 + g_arena_width//2, g_arena_height//2)):
        super(TetrisMessage, self).__init__()
        self.pos = pos

        # Register alarms
        Alarms.manager.schedule(Alarms.Alarm(lambda: self.change_color(), 20))
        Alarms.manager.schedule(Alarms.Alarm(lambda: Engine.current_room.destroy(self), 30))

        self.color = MyColors.BRIGHT_GREEN

    def change_color(self):
        self.color = MyColors.GREEN

    def ev_draw(self, screen):
        Engine.draw_text(screen, "TETRIS!", self.pos-TetrisMessage.center, font=TetrisMessage.font, color=self.color)

class Piece(Objects.GhostObject):
    COLORS = [
        (MyColors.BRIGHT_RED, MyColors.RED),
        (MyColors.BRIGHT_ORANGE, MyColors.ORANGE),
        (MyColors.BRIGHT_YELLOW, MyColors.YELLOW),
        (MyColors.BRIGHT_GREEN, MyColors.GREEN),
        (MyColors.BRIGHT_BLUE, MyColors.BLUE),
        (MyColors.BRIGHT_PURPLE, MyColors.PURPLE)
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
        L  = Engine.LEFT
        R  = Engine.RIGHT
        D  = Engine.DOWN

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
        self.relative_rotation_center = (sp.array(self.relative_rotation_center)*Engine.GRID).astype(int)

        colors = random.choice(Piece.COLORS)
        group = [Engine.current_room.create(Block, pos, colors)]
        for dpos in relative_positions:
            block_pos = pos + Engine.GRID*dpos
            group.append(Engine.current_room.create(Block, block_pos, colors))
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

        is_success = all(Engine.is_free(pos, self.group) for pos in new_positions)

        if is_success:
            for c_pos, block in zip(new_positions, self.group):
                block.center_pos = c_pos

            # Rotate the rotation center
            self.relative_rotation_center = sp.dot(rotation_matrix, self.relative_rotation_center)
        return is_success

    # TODO: this is super gross because of g_ / non g_ interaction. Standardize
    def attempt_move_to(self, pos):
        g_dpos = (pos - self.group[0].pos) // Engine.GRID
        return self.attempt_move_relative(g_dpos)

    def attempt_move_relative(self, g_dpos):
        """ Tries to move the piece down by one
        Returns whether the move was successful
        """
        is_success = all(Engine.is_free(block.pos + Engine.GRID*g_dpos, self.group) for block in self.group)

        if is_success:
            for block in self.group:
                block.pos += Engine.GRID*g_dpos
        return is_success

    # def ev_draw(self, screen):
    #     super(Piece, self).ev_draw(screen)
    #     pg.draw.circle(screen, MyColors.RED, self.center_pos, 4)

    def ev_destroy(self):
        for block in self.group:
            block.settle()

class Block(Objects.SolidObject):
    dimensions = copy(Engine.GRID)

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
    Engine.main("Tetris", room)
