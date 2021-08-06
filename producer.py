from abc import ABC, abstractmethod
from copy import deepcopy
import glob
import os

import utils as uu

class Producer(ABC):
    """Abstract class which produces some data"""

    @abstractmethod
    def get_data(self):
        pass


class CMSITDAQProducer(Producer):
    """Class for running CMSITDAQ scans, with terminal output saved to a log and returned."""

    def __init__(self, scan_type, xml_file, log_dir):
        self._type = scan_type
        self._xml_file = xml_file
        self._log_dir = log_dir

    def get_data(self):
        log_file = uu.get_log_name(self._log_dir, uu.get_next_runnr(), self._type)
        cmd = f'CMSITminiDAQ -f {self._xml_file} -c {self._type}'
        log_cmd = f'| tee {log_file}'
        os.system(f'{cmd} {log_cmd}')
        return log_file

    @property
    def xml_file(self):
        return self._xml_file

    @xml_file.setter 
    def xml_file(self, xml_file):
        self._xml_file = xml_file

    @property
    def scan_type(self):
        return self._type

    @scan_type.setter
    def scan_type(self, scan_type):
        self._type = scan_type

    @property
    def log_dir(self):
        return self._log_dir

    @log_dir.setter
    def log_dir(self, log_dir):
        self._log_dir = log_dir


class LastLogProducer(CMSITDAQProducer):
    """Class for Retrieving scan Log without actually running the scan"""

    def get_data(self):
        log_files = glob.glob( uu.get_log_name(self._log_dir, '*', self._type) )
        log_files.sort()
        if len(log_files) > 0:
            return log_files[-1]
        else:
            return ''
