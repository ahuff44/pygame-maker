from pygame.locals import *

from Decorators import postprocess
from copy import copy


# TODO: change this so that this is part of a mixin basically. Right now you as a game programmer will never have to use input_manager.register_key_handler since it's done automatically in GameObject.__init__()

PRESSED = 0
RELEASED = -1

class InputManager(object):
    """My custom input manager. It manages key events. I plan to add support for mouse events too"""

    def __init__(self):
        self.key_handlers = []
        # self.mouse_handlers = [] # TODO: <add mouse support>

        self.keys_held = {} # The keys that are currently held down, and the number of frames they've been held down
        # self.mouse_button_statuses = {} # TODO: <add mouse support>

    @postprocess(list)
    def filter_events(self, events):
        """
        This is the main function you would call in this class.
        It takes in a list of events, at acts on the ones it recognizes (mouse and keyboard events).
        It yields back any events it doesn't recognize
        TODO: wait why am i even filtering? I guess so there's only one way to use keyboard events. this had better not be a huge time sink. profile this code
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
            self.keys_held[key] = PRESSED
            self.notify_key_handlers(key)
        elif ev.type == KEYUP:
            self.keys_held[key] = RELEASED # TODO: make sure this won't error if you do type-to-learn style alt-hacking
            self.notify_key_handlers(key)

    def process_held_keys(self):
        for key in copy(self.keys_held.keys()):
            val = self.keys_held[key]
            if val == RELEASED:
                del self.keys_held[key]
            else:
                self.keys_held[key] += 1
                if val != PRESSED:
                    self.notify_key_handlers(key)

    def notify_key_handlers(self, key):
        """ This notifies all registered key handlers that the specified key has been pressed, and also tells them how long it has been pressed for
        """
        for handler in self.key_handlers:
            handler(key, self.keys_held[key])

    # Mouse Button methods:
    # TODO: <add mouse support>. It needs to track the position as it gets dragged around

manager = InputManager()
