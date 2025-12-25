class State:
    def __init__(self):
        self.cache = {}
        self.display_map = State.microbit_empty_display_map()

    def display_map_clear(self):
        self.display_map = State.microbit_empty_display_map()

    def set_list(self, state_list):
        self.display_map = state_list

    def set_pixel(self, x, y, value):
        self.display_map[((x * 5) + y - 6)] = value

    def display_map_normalize(self):
        return ["true" if ((pixel == 1) or (pixel is True)) else "false" for pixel in self.display_map]

    def display_map_as_string(self, state_list=None):
        if state_list is not None:
            self.set_list(state_list)

        return "/".join(self.display_map_normalize())

    def set(self, name, value):
        if value is None:
            if name in self.cache:
                self.cache.pop(name)
        else:
            self.cache[name] = value

        return value

    def get(self, name):
        if name in self.cache:
            return self.cache[name]

        return None

    @staticmethod
    def microbit_empty_display_map():
        return [0] * 25
