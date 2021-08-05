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

    def __init__(self, scan_type, xml_file, 
            parsers=[p.Parser([])], 
            updater=s.NothingUpdater(),
            persistifier=l.PrintPersistifier(),
            log_folder='log/'):
        self._type = scan_type
        self._xml_file = xml_file
        self._parsers = parsers
        self._updater = updater
        self._persistifier = persistifier
        self._log_folder = log_folder

    def run_simple(self):
        log_file = os.path.join(self._log_folder,f'Run{uu.get_next_runnr()}_{self._type}.log')
        cmd = f'CMSITminiDAQ -f {self._xml_file} -c {self._type}'
        log_cmd = f'| tee {log_file}'
        os.system(f'{cmd} {log_cmd}')
        return log_file

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

    #execute = CMSITDAQScan( 'pixelalive', 'xml/CMSIT_diskR3_scurve.xml')
    parsers = [p.Parser([p.RunNumberGetter('RunNumber')]), p.LogFileParser([p.InitMaskedPixGetter('MaskedPixels')]) ]
    mon_parsers = [ p.LogFileParser([p.VoltageGetter('Voltages'),p.TemperatureGetter('Temps') ]) ]
    updater = s.NothingUpdater()
    persistifier = l.PrintPersistifier()
    #run_scan( execute, parsers, updater, persistifier)
    
    my_scan = ScanWithMonitoring('pixelalive','xml/CMSIT_diskR3_scurve.xml',mon_parsers=mon_parsers, parsers=parsers, persistifier=l.PrintPersistifier() )
    my_scan.run_all()
