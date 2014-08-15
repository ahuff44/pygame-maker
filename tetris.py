import engine
from pygame.locals import *

import scipy as sp
import random


def _make_side(dimensions):
    class Side(engine.GameObject):
        """A boundary around the play area"""
        sprite = engine.Sprite(dimensions, engine.Colors.DARK_GRAY)
    return Side
arena_width, arena_height = (10, 15)*engine.GRID
SideSide = _make_side((engine.GRID[0], arena_height))
BottomSide = _make_side((arena_width, engine.GRID[1]))

HUD_width = 160

def populate_room(self):
    self.create(Controller)
    self.create(SideSide, (0, 0))
    self.create(SideSide, (arena_width-engine.GRID[0], 0))
    self.create(BottomSide, (0, arena_height-engine.GRID[1]))
room = engine.GameRoom.make_room(populate_room, dimensions=(arena_width+HUD_width, arena_height))

class Controller(engine.GameController):
    MOVE_DELAY = 15

    def __init__(self):
        super(self.__class__, self).__init__()
        self.move_alarm = engine.Alarm.new_alarm(lambda: self.move_block_group(), Controller.MOVE_DELAY, repeat=True)
        self.block_group = engine.game_room.create(BlockGroup)

    def move_block_group(self):
        if not self.block_group.move(engine.DOWN):
            self.use_next_block_group()

    def use_next_block_group(self):
        """ Destroys the current BG, checks for lines, and creates a new BG
        """
        self.test_for_lines()
        engine.game_room.destroy(self.block_group)
        self.block_group = engine.game_room.create(BlockGroup)


    # TODO working here
    # TODO make rotating work cleaner- maybe add in those L, >, etc
    # TODO This needs a huge overhaul; maybe a property that returns a 2D array of Blocks/None
    # TODO get rid of all instances of "+= engine.GRID" and make it all "+= 1" somehow
    @staticmethod
    def _get_lines():
        """
        See Controller.test_for_lines()
        """
        grid_x, grid_y = engine.GRID
        top = 0
        bottom = arena_height - 2*grid_x
        for yy in range(0, bottom+grid_y, grid_y):
            def this_line():
                left = grid_x
                right = arena_width - 2*grid_x
                for xx in range(left, right+grid_x, grid_x):
                    yield (xx, yy) + engine.GRID//2
            yield this_line
    def test_for_lines(self):
        for line_gen in Controller._get_lines():
            pos_list = list(line_gen())
            if all(engine.get_instances_at_position(pos) for pos in pos_list):
                for pos in pos_list:
                    for inst in engine.get_instances_at_position(pos):
                        engine.game_room.destroy(inst)



    def process_event(self, ev):
        super(self.__class__, self).process_event(ev)
        if ev.type == KEYDOWN:
            if ev.key == K_LEFT:
                self.block_group.move(engine.LEFT)
            elif ev.key == K_RIGHT:
                self.block_group.move(engine.RIGHT)
            # elif ev.key in [K_UP, K_w]: # DEBUG
            #     self.move(engine.UP)
            elif ev.key == K_DOWN: # This one is special; it resets the drop timer and forces a new block group to spawn if it fails
                if self.block_group.move(engine.DOWN):
                    self.move_alarm.reset()
                else:
                    self.use_next_block_group()
            elif ev.key == K_a:
                self.block_group.rotate(-1)
            elif ev.key == K_d:
                self.block_group.rotate(1)

class BlockGroup(engine.GhostObject):
    def __init__(self, pos=(arena_width//2, 0)):
        self.group = self.generate_blocks(pos)

    def generate_blocks(self, pos):
        """ Generates a random configuration of blocks
        The possible configurations are:
             -------------------------------------------
            |  0   | 1  | 2    | 3   | 4   | 5   | 6    |
            |  +o+ | o+ | +o++ | +o+ | +o+ |  o+ | +o   |
            |   +  | ++ |      | +   |   + | ++  |  ++  |
             -------------------------------------------
            KEY: '+'s are blocks, 'o's are the block that the configuration is centered on
                TODO updating: make 1 3 and 4 rotate around 1/2 blocks
        """
        # e.g. left, right, down-right, right-right...
        L  = engine.LEFT
        R  = engine.RIGHT
        D  = engine.DOWN

        configs = [
            [L, R, D],
            [R, D, D+R],
            [L, R, R+R],
            [L, R, D+L],
            [L, R, D+R],
            [R, D+L, D],
            [L, D, D+R]
        ]
        cfg = random.choice(configs)

        group = [engine.game_room.create(Block, pos)]
        for dpos in cfg:
            block_pos = pos + engine.GRID*dpos
            group.append(engine.game_room.create(Block, block_pos))
        return group

    def rotate(self, direction):
        """ Rotates the block group around the center block
        direction = 1 --> clockwise
        direction = -1 --> counterclockwise
        """
        assert direction in [-1, 1]
        rotation_matrix = sp.array([[0, -1], [1, 0]]) * direction
        head = self.group[0]
        for block in self.group[1:]:
            relative_pos = block.pos - head.pos
            relative_pos = sp.dot(rotation_matrix, relative_pos)
            block.pos = head.pos + relative_pos
        # TODO check for hitting walls

    def move(self, dpos):
        """ Tries to move the block group down by one
        Returns whether the move was successful
        """
        is_success = all(block.can_move(dpos, self.group) for block in self.group)

        if is_success:
            for block in self.group:
                block.move(dpos)
        return is_success

    def ev_destroy(self):
        for block in self.group:
            block.settle()

class Block(engine.GameObject):
    collisions = engine.GameObject.CollisionType.ACTIVE # The instances start ACTIVE but become PASSIVE when they land
    sprite = engine.Sprite(engine.GRID, engine.Colors.BRIGHT_BLUE)
    settled_sprite = engine.Sprite(engine.GRID, engine.Colors.BLUE)

    def can_move(self, dpos, allowed_instances):
        next_pos_center = self.pos + engine.GRID*dpos + engine.GRID//2
        # If there are any instances at the next position, they must all be on the allowed instances list:
        return all(
            inst in allowed_instances
            for inst in engine.get_instances_at_position(next_pos_center)
        )

    def move(self, dpos):
        self.pos += engine.GRID*dpos

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
