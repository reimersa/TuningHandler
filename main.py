from abc import ABC, abstractmethod

import parser as p
import producer as prod
import logging as l
import update_settings as s
import scan as rc

import utils as uu
        
if __name__ == '__main__':

    ring = 'R3'
    scan_type = 'pixelalive'
    hw_config  = HWConfigJSON('settings/hw_settings.json', ring)
    scan_config = ScanConfig('settings/scan_settings.json', scan_type)
    chip_config = ChipConfig('settings/chip_settings.json')

    xml_config = XMLConfig(HWConfig, ScanConfig, ChipConfig)

    producer = prod.LastLogProducer(scan_type, xml_config, 'log/')
    parsers = [p.Parser([p.RunNumberGetter('RunNumber'),p.ScanTypeGetter('ScanType')]), p.LogFileParser([p.InitMaskedPixGetter('MaskedPixels')]) ]
    mon_parsers = [ p.LogFileParser([p.VoltageGetter('Voltages'), p.TemperatureGetter('Temps') ]) ]
    updater = s.NothingUpdater()
    persistifier = l.PrintPersistifier()
    
    my_scan = rc.ScanWithMonitoring(producer, mon_parsers=mon_parsers, parsers=parsers, persistifier=l.PrintPersistifier() )
    my_scan.run_all()
