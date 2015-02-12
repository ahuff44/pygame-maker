from pygame.locals import *

from Decorators import postprocess


# TODO: make this work somehow. It's all messed up currently. Right now you as a game programmer will never have to use input_manager.register_key_handler since it's done automatically in GameObject.__init__()
# TODO: change this so that this is part of a mixin basically

class Constants:
    PRESSED, HELD, RELEASED = range(1, 3+1)

class InputManager(object):
    """My custom input manager. It manages key events. I plan to add support for mouse events too"""

    def __init__(self):
        self.key_handlers = []
        # self.mouse_handlers = [] # TODO: <add mouse support>

        self.keys_held = set() # The keys that are currently held down
        # self.mouse_button_statuses = {} # TODO: <add mouse support>

    @postprocess(list)
    def filter_events(self, events):
        """
        This is the main function you call. TODO: document better
        TODO: wait why am i even filtering? I guess so there's only one way to use keyboard events. this had better not be a huge time sink. test this
        """
        # Filter keyboard events out of events
        for ev in events:
            if ev.type in [KEYDOWN, KEYUP]:
                self.process_key_event(ev)
            else:
                yield ev
        self.process_held_keys()

        # for ev in events:
        #     if ev.type in [MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP]: # TODO: <add mouse support>
        #         self.process_mouse_event(ev)
        #         events.remove(ev)
        # self.process_held_mouse_buttons() # TODO: <add mouse support>

    # Keyboard methods:

    def register_key_handler(self, fxn):
        self.key_handlers.append(fxn)

    def process_key_event(self, ev):
        key = ev.key
        if ev.type == KEYDOWN:
            self.keys_held.add(key)
            self.notify_key_handlers(key, Constants.PRESSED)
        elif ev.type == KEYUP:
            self.keys_held.remove(key) # TODO: might error if you do type-to-learn style alt-hacking
            self.notify_key_handlers(key, Constants.RELEASED)

    def process_held_keys(self):
        for key in self.keys_held:
            self.notify_key_handlers(key, Constants.HELD)

    def notify_key_handlers(self, key, status):
        for handler in self.key_handlers:
            handler(key, status)

    # Mouse Button methods:
    # TODO: make this all work. it needs to track the position as it gets dragged around

manager = InputManager()
