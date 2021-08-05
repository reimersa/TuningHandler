from abc import ABC, abstractmethod
import json 
from yaml import safe_load

class ConfigUpdater(ABC):

    @abstractmethod
    def update(self, scan_output):
        pass

class NothingUpdater(ConfigUpdater):
    
    def update(self, scan_output):
        pass

class ThresholdUpdater(ConfigUpdater):
    """Updates Chip Thresholds in json file with new Values."""

    def __init__(self, json_filename):
        self._json = json_filename


    def update(self, thresholds):
        settings = self.get_chipsettings_from_json()
        for chip in thresholds.keys():
            settings[module][str(chip)]['Vthreshold_LIN'] = str(thresholds[chip])
        write_chipsettings_to_json(settings)

    def write_chipsettings_to_json(settings):
        with open(self._json, 'w') as j:
            json.dump(obj=settings, fp=j, indent=2, sort_keys = True)
        
    def get_chipsettings_from_json():
        result = {}
        with open(self._json, 'r') as j:
            result = safe_load(j)
        return result
 
