from abc import ABC, abstractmethod

import parser as p
import producer as prod
import logging as l
import update_settings as s
import scan as rc

import utils as uu
        
if __name__ == '__main__':

    producer = prod.CMSITDAQProducer('pixelalive','xml/CMSIT_diskR3_scurve.xml','log/')
    parsers = [p.Parser([p.RunNumberGetter('RunNumber'),p.ScanTypeGetter('ScanType')]), p.LogFileParser([p.InitMaskedPixGetter('MaskedPixels')]) ]
    mon_parsers = [ p.LogFileParser([p.VoltageGetter('Voltages'),p.TemperatureGetter('Temps') ]) ]
    updater = s.NothingUpdater()
    persistifier = l.PrintPersistifier()
    
    my_scan = rc.ScanWithMonitoring(producer, parsers=parsers, persistifier=l.PrintPersistifier() )
    my_scan.run_all()
