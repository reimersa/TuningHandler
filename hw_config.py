

class ModuleConfig:
    """Simple data class to hold some information about a module."""

    def __init__(self, chips=[0,1,2,3], position=None, port=None):
        self._chips = chips
        self._position = position
        self._port = port

    def get_position(self):
        return self._position

    def get_chips(self):
        return self._chips

    def get_port(self):
        return self._port

