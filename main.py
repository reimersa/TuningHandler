from abc import ABC, abstractmethod
import os 

import parser as p
import logging as l
import update_settings as s
import utils as uu
from XMLInfo import *
        
def run_scan( executer, parsers, updater, persistifier):

    scan_output = executer.run()
    parsed_data = {}
    for parser in parsers:
        parsed_data.update(parser.parse(scan_output))
    updater.update( scan_output )
    persistifier.update( parsed_data )

class Producer(ABC):
    """Abstract class which produces some data"""

    @abstractmethod
    def get_data(self):
        pass

class CMSITDAQProducer(Producer):
    """Class for running CMSITDAQ scans, with terminal output saved to a log and returned."""

    def __init__(self, scan_type, xml_file, log_folder):
        self._type = scan_type
        self._xml_file = xml_file
        self._log_folder = log_folder

    def get_data(self):
        log_file = os.path.join(self._log_folder,f'Run{uu.get_next_runnr()}_{self._type}.log')
        cmd = f'CMSITminiDAQ -f {self._xml_file} -c {self._type}'
        log_cmd = f'| tee {log_file}'
        os.system(f'{cmd} {log_cmd}')
        return log_file

    def get_log_file(self, runnr=None):
        if runnr is None:
            runnr = uu.get_next_runnr()
        return os.path.join(self._log_folder,f'Run{uu.get_next_runnr()}_{self._type}.log')
    

class LastLogProducer(CMSITDAQProducer):
    """WIP: Class for Retrieving scan Log without actually running the scan"""

    def get_data(self):
        log_file = os.path.join('log','example_ber_R7_mod987654321_chip12_pos200_2000_1800_90000.log')
        return log_file


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
            log_folder='log/'):
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
        xml_file = self._make_monitoring_xml()
        self._mon_scan = CMSITDAQScan( 'physics', xml_file, **kwargs)

    def _make_monitoring_xml(self):
        xml_object = XMLInfo( self._xml_file) 
        tmp_xml_file = f'{self._xml_file}.tmp_for_temp.xml'
        xml_object.enable_monitoring()
        xml_object.save_xml_as( tmp_xml_file )
        return tmp_xml_file

    def run(self):
        info = self._mon_scan.run()
        main_info = super().run()
        info.update(main_info)
        return info


if __name__ == '__main__':

    producer = CMSITDAQProducer('pixelalive','xmlCMSIT_diskR3_scurve.xml','log/')
    parsers = [p.Parser([p.RunNumberGetter('RunNumber')]), p.LogFileParser([p.InitMaskedPixGetter('MaskedPixels')]) ]
    mon_parsers = [ p.LogFileParser([p.VoltageGetter('Voltages'),p.TemperatureGetter('Temps') ]) ]
    updater = s.NothingUpdater()
    persistifier = l.PrintPersistifier()
    
    my_scan = ScanWithMonitoring(producer,mon_parsers=mon_parsers, parsers=parsers, persistifier=l.PrintPersistifier() )
    my_scan.run_all()
