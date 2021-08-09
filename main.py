from abc import ABC, abstractmethod

import parser as p
import producer as prod
import logging as l
import update_settings as s
import scan as rc

import utils as uu

import xml_config as xc
#from XMLInfo import xmlInfo
        
if __name__ == '__main__':

    ring = 'R3'
    scan_type = 'pixelalive'
    hw_config  = xc.HWConfigJSON('settings/hw_settings.json', ring)
    scan_config = xc.ScanConfig('settings/scan_settings.json', scan_type)
    chip_config = xc.ChipConfig('settings/chip_settings.json')

    xml_config = xc.XMLConfigMaker(hw_config, scan_config, chip_config)
    xml_config.save()

    producer = prod.LastLogProducer(scan_type, xml_config.get_xml_filename(), 'log/')
    parsers = [p.Parser([p.RunNumberGetter('RunNumber'),p.ScanTypeGetter('ScanType')]), p.LogFileParser([p.InitMaskedPixGetter('MaskedPixels')]) ]
    mon_parsers = [ p.LogFileParser([p.VoltageGetter('Voltages'), p.TemperatureGetter('Temps') ]) ]
    updater = s.NothingUpdater()
    persistifier = l.PrintPersistifier()
    
    my_scan = rc.ScanWithMonitoring(producer, mon_parsers=mon_parsers, parsers=parsers, persistifier=l.PrintPersistifier() )
    my_scan.run_all()
