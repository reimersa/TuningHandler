
#TODO complete list
daqsettings_per_xmltype = {'scurve': {
                               'nEvents': '100',
                               'nEvtsBurst': '100',
                               },
                           'noise': {
                               'nEvents': '10000000',
                               'nEvtsBurst': '10000',
                               'INJtype': '0',
                               'nClkDelays': '20'
                               },
                           'source': {
                               'nEvents': '100000000',
                               'nEvtsBurst': '10000',
                               'INJtype': '0',
                               'nClkDelays': '10'
                               }
                           }
                           
                           
xmltype_per_calibration = {'physics': 'scurve',
                           'scurve': 'scurve',
                           'pixelalive': 'scurve',
                           'noise': 'noise',
                           'threqu': 'scurve',
                           'thradj': 'scurve',
                           'voltagetuning': 'scurve',
}
