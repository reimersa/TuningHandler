
class SoftwareConfig:

    def __init__(self, persistence):
        pass

class HardwareConfig:


class RunController:

    def __init__(self, hw_config):
        self._hw_config = hw_config

    def run_scan(self, scan, sw_config, logger, db):
        pass
    
class Scan:

    def __init__(self, user_interface):
        self._ui = user_interface

    def execute(self, logger, sw_config):

        post_event(self.event_name, data)
        pass

class Logger:

    def

class Database:

    def __init__(self, fname):
        self._fname = fname 

    def new_entry(self, info):
        pass

class UserInterface:



