# TODO: make this class structed symmetrically with InputManager. Maybe have two classes: AlarmManager and Alarm. Or change InputManager

class Alarm(object):
    """Alarm(fxn, activation_time, repeat).
    Executes the function after activation_time game ticks.
    If repeat is true, the alarm will reset itself every time the function is executed.
    """

    def __init__(self, fxn, activation_time, repeat=False):
        self._validate_time(activation_time)

        self.fxn = fxn
        self.activation_time = activation_time
        self.repeat = repeat

        self.time_left = activation_time

    def _game_tick(self):
        self.time_left -= 1
        if self.time_left == 0:
            self.fxn() # Perform the delayed action
            if self.repeat:
                self.reset()

    def time_since_last_activation(self):
        # TODO: test
        if self.time_left > 0:
            return self.activation_time - self.time_left
        else:
            return -self.time_left

    def reset(self, new_activation_time=None):
        if new_activation_time is not None:
            self.activation_time = int(new_activation_time)
        self.time_left = self.activation_time

    def _validate_time(self, activation_time):
        """ Errors if activation_time is not a positive integer, quietly exits otherwise
        """
        if not (activation_time > 0 and int(activation_time) == activation_time):
            raise RuntimeError("Alarm activation time must be a positive integer")

class AlarmManager(object): #TEMP: I changed Alarm -> AlarmManager

    all_alarms = [] # Data format: [Alarm alarm, ...]

    def schedule(self, alarm):
        """ alarm should be an Alarm object
        """
        self.all_alarms.append(alarm)

    def game_tick(self):
        """ The engine calls this function every game tick
            TODO: make this actually happen
        """
        for alarm in self.all_alarms:
            alarm._game_tick()

manager = AlarmManager()
