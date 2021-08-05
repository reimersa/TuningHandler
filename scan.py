
class Scan:

    def __init__(self, name, sw_config):
        self._name = name
        self._sw_config = sw_config
        self._log_info = None

    def run_scan(self):
        scan_data = self.execute()
        self.post_event(self.event_name, scan_data )

    def execute(self):
        stdout = 
        pass
