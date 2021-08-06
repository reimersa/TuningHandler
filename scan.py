from abc import ABC, abstractmethod

import parser as p
import logging as  l
import update_settings as s
from XMLInfo import *

class Scan(ABC):
    
    @abstractmethod
    def run(self):
        pass

class RunUpdateSaveScan(Scan):

    @abstractmethod
    def update_settings(self, info):
        pass

    @abstractmethod
    def save_info(self):
        pass

    def run_all(self):
        info = self.run()
        self.update_settings(info)
        self.save_info(info)
        

class CMSITDAQScan(RunUpdateSaveScan):
    """Class for running a CMSITDAQ scan, updating settings and saving the data."""

    def __init__(self, producer, 
            parsers=[p.Parser([])], 
            updater=s.NothingUpdater(),
            persistifier=l.PrintPersistifier(),
            log_dir='log/'):
        self._producer = producer
        self._parsers = parsers
        self._updater = updater
        self._persistifier = persistifier

    def run_simple(self):
        return self._producer.get_data()

    def run(self):
        log_file = self.run_simple()
        parsed_info = {}
        for parser in self._parsers:
            parsed_info.update( parser.parse(log_file) )
        return parsed_info

    def save_info(self, info):
        self._persistifier.update(info)

    def update_settings(self, info):
        self._updater.update(info)


class ScanWithMonitoring(CMSITDAQScan):
    """Class for Scans that requiring an initial CMSITDaq monitoring scan for retrieving some basic info."""

    def __init__(self, *args, mon_parsers=[p.Parser([])], **kwargs ):
        super().__init__(*args, **kwargs)
        mon_kwargs = kwargs
        mon_kwargs['parsers'] = mon_parsers
        mon_kwargs['updater'] = s.NothingUpdater()
        mon_kwargs['persistifier'] = l.DummyPersistifier()
        mon_prod = self._make_mon_producer()
        self._mon_scan = CMSITDAQScan(mon_prod, **mon_kwargs)
        print(self._mon_scan._producer.xml_file)
        

    def _make_mon_producer(self):
        xml_file = self._make_monitoring_xml()
        _mon_prod = deepcopy(self._producer)
        _mon_prod.xml_file  = xml_file
        _mon_prod.scan_type = 'physics'
        return _mon_prod

    def _make_monitoring_xml(self):
        orig_xml = self._producer.xml_file
        xml_object = XMLInfo( orig_xml ) 
        tmp_xml_file = f'{orig_xml}.tmp_for_monitoring.xml'
        xml_object.enable_monitoring()
        xml_object.save_xml_as( tmp_xml_file )
        return tmp_xml_file

    def run(self):
        info = self._mon_scan.run()
        main_info = super().run()
        info.update(main_info)
        return info

