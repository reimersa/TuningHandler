#! /usr/bin/env python3
import os, re, glob
import time, math
import numpy as np
import shutil as sh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import OrderedDict


import json
from yaml import safe_load

import ROOT
from ROOT import TFile, TH1D, TCanvas, TIter

from datetime import datetime, timedelta

from XMLInfo import *
from settings.typesettings import *

import tuning_db as tdb
import pandas as pd

import plotting as pl
import argparse
#from settings.chipsettings import *


xmlfolder = 'xml/'
txtfolder = 'txt/'
logfolder = 'log/'
plotfolder = 'plots/'
ber_dbfile  = 'ber_db/ber.json'
tuning_dbfile = 'tuning_db/tuning.json'
xmlfile_blueprint = '/home/uzh-tepx/Ph2_ACF/settings/CMSIT.xml'
# xmlfile_blueprint = 'xml/CMSIT.xml'
txtfile_blueprint = '/home/uzh-tepx/Ph2_ACF/settings/RD53Files/CMSIT_RD53.txt'
#txtfile_blueprint = 'txt/CMSIT_RD53.txt'


chiplist = [0, 1, 2, 3]
modulelist = ['mod3', 'mod4', 'mod6', 'mod7', 'mod9', 'mod10', 'mod11', 'mod12', 'modT01', 'modT02', 'modT03', 'modT04', 'modT08', 'modT09', 'modT10','modT11', 'modT12', 'modT14']


ids_and_chips_per_module_R1 = {
    #'mod10': (3, [0,1,2]), 
    #'mod12': (4, [0, 1, 2]),
    'mod9' : ( 3, [0,1,2]),
    'modT03' : (4, [0,1,2]),
    'mod10' : (2, [0,1,2]),
    'mod7': (0,  [ 1, 2]),
    #'mod10': (0, [1, 2]),
    #'mod12' : (1, [0, 1, 2] )
    'mod11': (1, [0, 1, 2]), #new
}

positions_per_module_R1 = OrderedDict({ #OrderedDict keeps initialization order for python 3.6+
    'mod11':  'R15',
    'mod7':   'R14',
    'mod10':  'R13',
    'modT03': 'R12',
    'mod9':   'R11'
})


ids_and_chips_per_module_R3 = {
    #'modT09': (1, [3]),  #checked
    #'mod9':   (3, [3]), #checked
    'mod11':  (6, [3]), #checked
    #'mod7': (4, [3]), #cheked
    'mod12':  (5,[3]),#checked
    #'mod10':  (7, [3]), #checked
}
positions_per_module_R3 = {
    #'modT09': 'R35', #checked
    'mod9':   'R31', #checked
    'mod11':  'R38', #checked
    'mod7':   'R37', #checked
    'mod12':  'R39', #checked
    'mod10':  'R36', #checked
}


ids_and_chips_per_module_SAB = {
    #'mod7': (1, [3])
    'modT14': (1, [1, 2, 3])
}
        
#A dictionary of different scans with settings which are (TAP0 list, TAP1 list, TAP2 list).
ber_scan_types = { 'TAP0'   : ( [1000,900,800,700,600,500,400,300,200],[0],[0] ),
               'Single' : ( [1000], [0], [0] ),
               'Full'   : ( [1000,900,800,700,600,500,400,300,200],[-120,-80,-40,0,40,80,120],[-120,-80,-40,0,40,80,120])
             }
        
def get_module_position( module, ring):

    if ring_id == 'singleQuad': 
        ids_and_chips = ids_and_chips_per_module_SAB
        positions_per_module = {list(ids_and_chips)[0]: 'singleQuad'} # can only be one module
    elif ring_id == 'R1': 
        ids_and_chips = ids_and_chips_per_module_R1
        positions_per_module = positions_per_module_R1
    elif ring_id == 'R3': 
        ids_and_chips = ids_and_chips_per_module_R3
        positions_per_module = positions_per_module_R3
    else: raise ValueError('Invalid \'ring_id\' specified: %s' % (ring_id))

    if not module in positions_per_module:
        raise ValueError('Invalid module specified: {module}. Modules in ring {ring} are {positions_per_module}')
    return positions_per_module[module]
   

def get_scan_taps( scan_name ):
    if scan_name in ber_scan_types:
        return ber_scan_types[scan_name]
    else:
        raise KeyError(f'''Could not find scan by name of {scan_name} in the list of scan types. 
                        Known scans are {ber_scan_types.keys()}''')

def setup_and_run_ber( run_time=3, ring_id='R1', test_only=False, scan_type='TAP0' ):

    if ring_id == 'singleQuad': 
        ids_and_chips = ids_and_chips_per_module_SAB
        positions_per_module = {list(ids_and_chips)[0]: 'singleQuad'} # can only be one module
    elif ring_id == 'R1': 
        ids_and_chips = ids_and_chips_per_module_R1
        positions_per_module = positions_per_module_R1
    elif ring_id == 'R3': 
        ids_and_chips = ids_and_chips_per_module_R3
        positions_per_module = positions_per_module_R3
    else: raise ValueError('Invalid \'ring_id\' specified: %s' % (ring_id))
    
    # now run many BER tests
    tap_settings = []
    scan_taps = get_scan_taps(scan_type)
    for tap0 in scan_taps[0]:
        for tap1 in scan_taps[1]:
            for tap2 in scan_taps[2]: 
                tap_settings.append((tap0, tap1, tap2))
                
    #positions       = ['R15','R14','R13','R12','R11'] #['R11','R12','R13','R14','R15'] #['0']
    logfolder_for_ber = logfolder #+ 'diskR1_5modules_R14_R15_HV35_long/' #'singleAdapterBoard/' #'diskR1_5modules_allRingsPowered_mod7/'
    module_info_for_ber =  ids_and_chips
    modules_for_ber = module_info_for_ber.keys()
    chips_per_module= {}
    for mod in module_info_for_ber: 
        chips_per_module[mod] = module_info_for_ber[mod][1] 
    
    tap_settings_per_module_and_chip = {}
    for moduleidx, module in enumerate(modules_for_ber):
        settings_per_chip = {}
        for chip in chips_per_module[module]:
            if not chip in settings_per_chip.keys():
                settings_per_chip[chip] = []
            for s in tap_settings:
                t0 = s[0]
                t1 = s[1]
                t2 = s[2]

                settings_per_chip[chip].append((t0, t1, t2))

                tap_settings_per_module_and_chip[module] = settings_per_chip
    
    db = None if test_only else tdb.TuningDataBase(ber_dbfile)
    
    last_index = run_ber_scan(modules = module_info_for_ber, 
                              chips_per_module = chips_per_module, 
                              ring = ring_id, positions_per_module=positions_per_module, 
                              tap_settings_per_module_and_chip = tap_settings_per_module_and_chip, 
                              mylogfolder = logfolder_for_ber, 
                              value=run_time, 
                             db=db)
    print(f'Finished Scan {last_index}')
    

def ask_for_name(db):
    print('Would you like to give this scan a name? [y/n]')
    answer = input()
    if answer == 'y':
        print('please type the name for this scan:')
        while True:
            try_name = input()
            already_exists = tdb.has_named_scan(db, try_name)
            if not already_exists:
                print(f'The name {try_name} is unique! continuing')
                return try_name
            else:
                print(f'the name {try_name} already exists in the database, please choose another name:')

    elif answer == 'n':
        print('information was declared incorrect, not running tuning, please fix the desired settings')
        return None
    else:
        print('response not understood, please use "y" or "n", not running tuning.')
        return None



def confirm_settings( modules, chips, ring, positions, n_settings, value, db):
    print('Please verify the following information is correct for the scans:')
    print(f'module settings: {modules},\nchip settings: {chips},\nring: {ring},\nThe List of positions with powered modules is: {positions}')
    extra_seconds = 12 if db is not None else 3 #we only do temp pre-scan when recording to db
    run_time = timedelta(seconds = n_settings*(value+extra_seconds) ) #could try to add in extra time
    #readable_run_time = run_time.strftime('%H:%M:%S')
    print(f'Will run {n_settings} settings for {value} seconds each. A minimimum run time of {run_time}, assuming {extra_seconds}s overhead time per scan.')
    end_time = (datetime.now() + run_time).strftime('%d/%m %H:%M')
    print(f'The run will finish AFTER {end_time}')
    if db is None:
        print(''''********** NO DATABASE **********\nNo database was specified, results will not be logged to any database.''')
    else:
        print(f'Logging results to database {db.db_filename()}')
    time.sleep(2)
    print('Continue with this run? enter "y/n"')
    answer = input()
    if answer == 'y':
        print('information confirmed, running tuning')
        return True
    elif answer == 'n':
        print('information was declared incorrect, not running tuning, please fix the desired settings')
        return False
    else:
        print('response not understood, please use "y" or "n", not running tuning.')
        return False

def run_threshold_tuning(module, ring, plotfoldername, intermediate_scurves=False, db=None):
    reset_xml_files()
    reset_txt_files()
    
    module_per_id = {}
    if ring == 'R1':
        id_per_module = ids_and_chips_per_module_R1
    elif ring == 'R3':
        id_per_module = ids_and_chips_per_module_R3
    elif ring == 'singleQuad':
        id_per_module = ids_and_chips_per_module_SAB
    else: raise ValueError('Invalid value of \'ring\': %s' % (ring))
    for modkey in id_per_module:
        id = id_per_module[modkey][0]
        module_per_id[id] = modkey
        
    # reset all VThreshold_LINs to 400
    for module in id_per_module:
        fresh_thresholds = {}
        for chip in id_per_module[module][1]:
            fresh_thresholds[chip] = '400'
        set_thresholds_for_module(module=module, thresholds=fresh_thresholds)
    print('Reset all VThreshold_LIN to 400.')
    
    reset_xml_files()
    run_calibration(ring=ring, module=module, calib='pixelalive',db=db)
    if intermediate_scurves:
        run_calibration(ring=ring, module=module, calib='scurve')

    run_calibration(ring=ring, module=module, calib='threqu',db=db)
    if intermediate_scurves:
        run_calibration(ring=ring, module=module, calib='scurve')

    run_calibration(ring=ring, module=module, calib='noise',db=db)
    if intermediate_scurves:
        run_calibration(ring=ring, module=module, calib='scurve')

    run_calibration(ring=ring, module=module, calib='thradj',db=db)
        
        
    thresholds_per_id_and_chip = get_thresholds_from_last()
    for id in thresholds_per_id_and_chip:
        set_thresholds_for_module(module=module_per_id[id], thresholds=thresholds_per_id_and_chip[id])
        print('set the following thresholds for module %s with id %s: '% (module_per_id[id], str(id)), thresholds_per_id_and_chip[id])
        
    reset_xml_files()
    if intermediate_scurves:
        run_calibration(ring=ring, module=module, calib='scurve')

    run_calibration(ring=ring, module=module, calib='threqu',db=db)
    if intermediate_scurves:
        run_calibration(ring=ring, module=module, calib='scurve')

    run_calibration(ring=ring, module=module, calib='noise',db=db)
    run_calibration(ring=ring, module=module, calib='scurve', db=db)
    pl.plot_scurve_results(runnr=get_last_runnr(), module_per_id=module_per_id, plotfoldername=plotfoldername)

def get_last_runnr():
    #file 'RunNumber.txt' contains number the next run would have, nothing else.
    with open('RunNumber.txt', 'r') as f:
        runnr = int(f.readlines()[0]) - 1
    return runnr

def set_thresholds_for_module(module, thresholds):
    # get chipsettings, change VThreshold_LIN, write chipsettings
    # 'thresholds' is a dictionary with one entry per chip, maximum 4 entries
    if len(thresholds.keys()) > 4: raise AttributeError('Threshold dictionary is too long for a single module.')
    settings = get_chipsettings_from_json()
    for chip in thresholds.keys():
        settings[module][str(chip)]['Vthreshold_LIN'] = str(thresholds[chip])
    write_chipsettings_to_json(settings)
    


def get_thresholds_from_last():
    # last run has highest run-number and must have 'ThrAdjustment' in name
    files = [f for f in glob.glob(os.path.join('Results', '*.root')) if 'ThrAdjustment' in f]
    
    # list is unordered
    runnrs = [int(n.split('_')[0].split('Run')[1]) for n in files]
    maxidx = runnrs.index(max(runnrs))
    lastfilename = files[maxidx]
    print(lastfilename)
    infile = TFile(lastfilename, 'READ')
    foldername = 'Detector/Board_0/OpticalGroup_0/'
    infile.cd(foldername)
    dir = ROOT.gDirectory
    iter = TIter(dir.GetListOfKeys())
    modules = [key.GetName() for key in ROOT.gDirectory.GetListOfKeys()]
    
    thresholds_per_id_and_chip = {}
    for module in modules:
        thresholds_per_id_and_chip[int(module.split('_')[1])] = {}
        histpath = foldername + module
        infile.cd()
        infile.cd(histpath)
        chips = [key.GetName() for key in ROOT.gDirectory.GetListOfKeys()]
        print(module, chips)
        
        for chip in chips:
            mod_dummy = module
            chip_dummy = chip
            fullhistpath = os.path.join(histpath, chip)
            infile.cd()
            infile.cd(fullhistpath)
            
            objs = [key.GetName() for key in ROOT.gDirectory.GetListOfKeys()]
            infile.cd()
            for objname in objs:
                if not 'Threhsold' in objname: continue
                canvas = infile.Get(os.path.join(fullhistpath, objname))
                hist = canvas.GetPrimitive(objname)
                vthresh = int(hist.GetBinCenter(hist.GetMaximumBin()) - hist.GetBinWidth(hist.GetMaximumBin())/2.)
                thresholds_per_id_and_chip[int(module.split('_')[1])][int(chip.split('_')[1])] = vthresh
    del infile
    return thresholds_per_id_and_chip
                
    

def write_chipsettings_to_json(settings):
    jsonname = os.path.join('settings','chipsettings.json')
    with open(jsonname, 'w') as j:
        json.dump(obj=settings, fp=j, indent=2, sort_keys = True)
        
def get_chipsettings_from_json():
    jsonname = os.path.join('settings','chipsettings.json')
    result = {}
    with open(jsonname, 'r') as j:
        result = safe_load(j)
    return result
    



def run_programming(ring, module):
    xmlfilename = get_xmlfile_name(ring=ring, module=module, calib='scurve')
    command = 'CMSITminiDAQ -f %s -p' % (os.path.join(xmlfolder, xmlfilename))
    print(command)
    os.system(command)
    
def run_reset(ring, module):
    xmlfilename = get_xmlfile_name(ring=ring, module=module, calib='scurve')
    command = 'CMSITminiDAQ -f %s -r' % (os.path.join(xmlfolder, xmlfilename))
    print(command)
    os.system(command)
    
def run_calibration(ring, module, calib, logfolder='log/', db=None):
    xmlfilename = get_xmlfile_name(ring=ring, module=module, calib=xmltype_per_calibration[calib])
    run_number = get_last_runnr() + 1
    print(run_number)
    logfilename=os.path.join(logfolder, f'Run{run_number}_{calib}.log')
    if calib == 'physics':
        xml_object = XMLInfo( os.path.join(xmlfolder, xmlfilename) ) 
        tmp_xml_file = f'{xmlfilename}.tmp_for_mon.xml'
        xml_object.enable_monitoring()
        xml_object.save_xml_as( os.path.join(xmlfolder, tmp_xml_file ))
        xmlfilename = tmp_xml_file

    if not db is None: #Read temperatures and voltages for posterity
        xml_object = XMLInfo( os.path.join(xmlfolder, xmlfilename) ) 
        module_info = xml_object.get_module_info()
        hybrid_chip_dct = {}
        for mod, info in module_info.items():
            hybrid_chip_dct[info['hybridId']] = info['chips']
        temps_and_voltages = read_temps_and_voltages(hybrid_chip_dct, os.path.join(xmlfolder, xmlfilename) )
        run_number += 1 # will run a scan in the line above, so the number we read in the beginning is now wrong

    xml_full_path = os.path.join(xmlfolder, xmlfilename)
    command = f'CMSITminiDAQ -f {xml_full_path} -c {calib} | tee {logfilename}' 
    print(command)
    start_time = datetime.now()
    os.system(command)

    if not db is None:
        scan_index = db.get_next_index()
        all_scan_info = []
        for mod, mod_info in module_info.items():
            hybrid_id = mod_info['hybridId']
            for chip in mod_info['chips']:
                pos = get_module_position(mod, ring)
                scan_info =  {'ScanIndex': scan_index, 'ScanType': calib, 'Ring': ring, 
                        'Pos': pos, 'RunNumber':run_number, 'Module':mod, 'Chip': chip, 'start_time':start_time, 'start_time_human':get_human_time(start_time), 'IsArchived':False} 
                calib_info = read_calibration_log( chip, logfilename, hybrid=hybrid_id )
                scan_info.update(calib_info)
                chip_temps_and_voltages = temps_and_voltages[hybrid_id][chip]
                scan_info.update(chip_temps_and_voltages)
                all_scan_info += [ scan_info ]
                print(all_scan_info)
        db.add_data( all_scan_info )
        db.update()

    if calib == 'physics':
        cleanup_command =  f'rm {os.path.join(xmlfolder, tmp_xml_file )}'
        os.system(cleanup_command)
        time.sleep(1)
 


def get_results_from_logfile( fname ):

    nframes = -1
    nber    = -1
    speed   = -1
    with open( fname, 'r') as f:

        lines = None
        try:
            lines = f.readlines()
        except Exception as e:
            print(f'''Caught an exception while reading BER log file {fname}.
                    BER will not be read for this run, will set to nframes={nframes}, nber={nber}.
                    The error was:\n{e}''')

        if lines is not None:

            for l in lines:
                l = escape_ansi(l)
                if 'Final number of PRBS frames sent:' in l:
                    nframes = safe_convert( l.split(' ')[-1], int, 'NFrames')
                elif 'Final counter:' in l:
                    nber = safe_convert( l.split(' ')[-4], int, 'NBER') #Changed with a new version of PH2ACF
                elif 'Up-link speed:' in l:
                    speed = safe_convert( l.split(' ')[-2], float, 'Up-link Sp(eed')
                    units = l.split(' ')[-1].strip() #should be either Gbit/s or Mbit/s 
                    if units == 'Gbit/s':
                    	pass #use 'Gbit/s as default unit'
                    elif units == 'Mbit/s':
                    	speed /= 1000
                    else:
                    	print(f'ERROR: Could not get the units of the uplink speed! did not pass any of the known cases! found: {units}.')
                    	

    return (nframes, nber, speed)

def get_settings_from_logfile( fname ):
    basename_no_ext = os.path.splitext(os.path.basename( fname ))[0]
    fields = basename_no_ext.split("_")

    #index from the back so things can be added to the front
    settings = {
        'TAP2' : safe_convert(fields[-1], int, 'TAP2'),    
        'TAP1' : safe_convert(fields[-2], int, 'TAP1'),
        'TAP0' : safe_convert(fields[-3], int, 'TAP0'),
        'Pos'  : fields[-4].strip('pos'),
        'Chip' : safe_convert(fields[-5].strip('chip'), int, 'Chip' ),
        'Module' : fields[-6],
        'Ring'   : fields[-7]
        }
    return settings

def get_all_info_from_logfile( fname ):

    all_info = get_settings_from_logfile( fname )
    nframes, nber, uplink_speed = get_results_from_logfile( fname )
    all_info.update( { 'NFrames' : nframes, 'NBER' : nber, 'UpLinkSpeedGbs': uplink_speed } )

    return all_info

def read_temps_and_voltages( dct, xml_file, board=0, optical_group=0 ):
  
        xml_object = XMLInfo( xml_file) 
        tmp_xml_file = f'{xml_file}.tmp_for_temp.xml'
        xml_object.enable_monitoring()
        xml_object.save_xml_as( tmp_xml_file )
        log_file_name = 'tmp_log_for_temperature_readout.txt'
        monitoring_command = f'CMSITminiDAQ -f {tmp_xml_file} -c physics | tee {log_file_name}'

        # execute the OS command
        print(monitoring_command)
        os.system(monitoring_command)
        time.sleep(1)
        
        temps_and_voltages = {}
        for hybrid, chips in dct.items():
            if len(chips) < 1: continue
            temps_and_voltages[hybrid] = {}
            for chip in chips:
                result = read_monitoring_log(chip, log_file_name, board, optical_group, hybrid)
                print(f'For hybrid {hybrid} and chip {chip} the temps and voltages are  {result}')
                temps_and_voltages[hybrid][chip] = result

        #remove temp files
        cleanup_command =  f'rm {log_file_name} {tmp_xml_file}'
        os.system(cleanup_command)
        time.sleep(1)

        return temps_and_voltages
     


def safe_convert( str_value, to_type, value_name):
    converted = None
    try:
       converted = to_type( str_value )
    except Exception as e:
        print(f'''ERROR: failed to convert the value of {value_name} from a string to {to_type.__name__}. 
                The string value is {str_value}:\n
                This may cause loss of data for this scan point. The original error was:\n{e}.''')
       
    return converted

def read_monitoring_log(chip, log_file, board=0, optical_group=0, hybrid=0):
    '''Read the chip temperatures and VDDD/VDDA output values from the log.'''

    #board, optical group, hybrid, chi[
    expected_chip_id = [ board, optical_group, hybrid, chip ]
    current_chip_id = [-1,-1,-1,-1]
    temps_and_voltages = {}
    with open( log_file, 'r') as f:
        lines = None
        try:
            lines = f.readlines()
        except Exception as e:
            print(f'''Caught an exception while reading monitoring log file {fname}.
                    temperatures and voltages will be reported as {temps_and_voltages}.
                    The error was:\n{e}''')

        if lines is not None:    

            for l in lines:
                if l is None: 
                    continue
                l = escape_ansi(l)

                if 'Monitor data for' in l: #Identifying the chip
                    m = re.search('(?P<board>\d*)/(?P<og>\d*)/(?P<hybrid>\d*)/(?P<chip>\d*)', l )
                    if m is not None:
                        ids = [  safe_convert( m.group(obj), int, obj) for obj in ['board','og','hybrid','chip'] ]
                        if not None in ids:
                            current_chip_id = ids
                    else:
                        #this shouldn't ever happen
                        print(f'WARNING: There may be an issue with the regex parsing of chip IDs')

                elif current_chip_id == expected_chip_id and 'TEMPSENS_' in l: #temperatures
                    m = re.search('(?P<sensid>TEMPSENS_\d):(?P<temp>[^+]*)', l)
                    if m is not None:
                        sens = m.group('sensid')
                        temp = safe_convert( m.group('temp').strip(), float, 'temp') 
                        if temp is None: continue
                        temps_and_voltages[sens] = temp
                    else:
                        #This shouldn't ever happen
                        print(f'WARNING: There may be an issue with the regex parsing of temperatures')

                elif current_chip_id == expected_chip_id and 'VOUT_' in l: #shuntLDO values
                    m = re.search('(?P<Vtype>VOUT[^:\s]*ShuLDO):(?P<voltage>[^+]*)', l)
                    if m is not None:
                        vsource = m.group('Vtype')
                        voltage = safe_convert( m.group('voltage').strip(), float,  'voltage')
                        if voltage is None: continue
                        
                        voltage *= 2 #multiply by 2 because for some reason the printed values are half of the actual ones?
                        temps_and_voltages[vsource] = voltage
                    else:
                        #there are some messages printed about the VOUT which don't actually containt the info, we want 
                        #"	--> Hybrid voltage: 0.000 V (corresponds to half VOUT_dig_ShuLDO of the chip)"
                        pass


    return temps_and_voltages


def read_calibration_log(chip, log_file, hybrid=0):
    '''Read the chip temperatures and VDDD/VDDA output values from the log.'''

    expected_chip_id = [ hybrid, chip ]
    current_chip_id = [-1,-1]
    calib_info = {}
    with open( log_file, 'r') as f:
        lines = None
        try:
            lines = f.readlines()
        except Exception as e:
            print(f'''Caught an exception while reading monitoring log file {fname}.
                    temperatures and voltages will be reported as {temps_and_voltages}.
                    The error was:\n{e}''')

        if lines is not None:    

            for l in lines:
                if l is None: 
                    continue
                l = escape_ansi(l)

                if 'Configuring chip of hybrid:' in l: #Identifying the hybrid
                    current_chip_id[0] = safe_convert(l.split()[-1], int, 'hybridId')

                elif 'Configuring RD53:' in l: #Identifying the chip
                    current_chip_id[1] = safe_convert(l.split()[-1], int, 'chipId')

                elif current_chip_id == expected_chip_id and 'Number of masked pixels:' in l: #masked pixels
                    calib_info['InitMaskedPix'] = safe_convert(l.split()[-1], int, 'maskedPixels')

    return calib_info


def get_num_settings( tap_settings ):
    n_settings = 0
    for mod, chip_dict in tap_settings.items():
        for chip, settings_list in chip_dict.items():
            n_settings += len(settings_list)
    return n_settings
    

def run_ber_scan(modules, chips_per_module, ring, positions_per_module, tap_settings_per_module_and_chip, mylogfolder, mode='time', value=10, db=None):

    n_settings = get_num_settings(tap_settings_per_module_and_chip) 
    settings_are_correct = confirm_settings( modules, chips_per_module, ring, positions_per_module, n_settings, value, db)
    if not settings_are_correct:
        print('Settings were not confirmed as correct, not running BER scan')
        return

    scan_index = db.get_next_index() if db is not None else -1
    print(f'Scan Index will be {scan_index}.')

    name = None
    if db is not None:
        name = ask_for_name(db)

    #make sure the log can be written in the appropriate directory
    if not os.path.exists(mylogfolder):
        os.mkdir(mylogfolder)



    module_info = modules
    modules = modules.keys()
    for moduleidx, module in enumerate(modules):
        for chip in chips_per_module[module]:
            tap_settings = tap_settings_per_module_and_chip[module][chip]
            if ring == 'singleQuad':
                if not len(modules) == 1:
                    raise AttributeError('Trying to run BER in singleQuad mode with mode than one module')
                #module = modules[0]
                xmlfile_for_ber = os.path.join(xmlfolder, 'CMSIT_%s_%s_%s.xml' % (ring, module, 'ber'))
                reset_singleQuad_xml_files(type='ber', modules=modules, chips = chips_per_module[module])
                prepare_singleQuad_xml_files(type_name='ber', type_setting='scurve', modules=modules)
            elif ring == 'R1':
                xmlfile_for_ber = os.path.join(xmlfolder, 'CMSIT_disk%s_%s.xml' % (ring, 'ber'))
                reset_and_prepare_Ring_xml_file('ber', 'scurve', ids_and_chips_per_module_R1, ring)
            elif ring == 'R3':
                xmlfile_for_ber = os.path.join(xmlfolder, 'CMSIT_disk%s_%s.xml' % (ring, 'ber'))
                reset_and_prepare_Ring_xml_file('ber', 'scurve', ids_and_chips_per_module_R3, ring)
            xmlobject = XMLInfo(xmlfile_for_ber)
            print( module, chip)
            xmlobject.keep_only_modules_by_modulename([module])
            xmlobject.keep_only_chips_by_modulename(module, [chip])

            # assemble the OS command
            if mode == 'time': 
                xmlobject.set_daq_settings('byTime', '1')
            elif mode == 'frames': 
                xmlobject.set_daq_settings('byTime', '0')
            else: 
                raise AttributeError('Function \'run_ber_scan()\' received invalid argument for \'mode\': %s. Must be \'time\' or \'frames\'' % mode)
            xmlobject.set_daq_settings('framesORtime', str(value))



            # now, in a loop, set TAP values to scan through
            for tap0, tap1, tap2 in tap_settings:
                
                print(tap0, tap1, tap2)
                xmlobject.set_chip_setting_by_modulename(module, chip, 'CML_TAP0_BIAS', str(tap0))
                xmlobject.set_chip_setting_by_modulename(module, chip, 'CML_TAP1_BIAS', str(abs(tap1)) ) #inversion is in a separate config setting
                xmlobject.set_chip_setting_by_modulename(module, chip, 'CML_TAP2_BIAS', str(abs(tap2)) ) #inversion is in a separate Config setting
                xmlobject.set_chip_setting_by_modulename(module,chip,'CML_CONFIG_SER_EN_TAP', '0b11') #Enable tap1 and tap2
                #Need to set the inversion for tap1 and tap2 properly
                tap_inv = 0
                if tap1 < 0:
                    tap_inv += 1
                if tap2 < 0:
                    tap_inv += 2
                xmlobject.set_chip_setting_by_modulename(module,chip,'CML_CONFIG_SER_INV_TAP', '0b{:02b}'.format(tap_inv))
                xmlobject.save_xml_as(xmlfile_for_ber)
                
                log_file_name = os.path.join(mylogfolder, f'ber_{ring}_{module}_chip{chip}_pos{positions_per_module[module]}_{tap0}_{tap1}_{tap2}.log')
                command_ber = f'CMSITminiDAQ -f {xmlfile_for_ber} -c bertest 2>&1 | tee {log_file_name}' 

                
                if db is not None:
                    print(f'checking temperatures before running the scan')
                    hybrid_no = int(module_info[module][0])
                    hybrid_chip_dict = { hybrid_no : [ chip ] }
                    temps_and_voltages = read_temps_and_voltages(hybrid_chip_dict, xmlfile_for_ber)[hybrid_no][chip]
                    print(f'the temperatures and voltages are {temps_and_voltages}')

                # execute the OS command
                start_time = datetime.now()
                print(command_ber)
                os.system(command_ber)
                end_time = datetime.now()
                time.sleep(2)

                if db is not None:
                    run_info = get_all_info_from_logfile( log_file_name )
                    run_info.update( {'FC7_Hybrid_id': hybrid_no } )

                    this_position = positions_per_module[module]
                    other_positions = []
                    for k in positions_per_module:
                        other_positions.append(positions_per_module[k])
                    other_positions.remove(this_position)
                    run_info.update( {'other_powered_modules': other_positions} ) #storing the array object should be fine

                    tz_info     = start_time.astimezone().strftime('UTC%z')
                    run_info.update( {'scan_index': scan_index, 'start_time': start_time, 'end_time': end_time } )
                    run_info.update( { 'start_time_human': get_human_time(start_time), 
                                       'end_time_human': get_human_time(end_time), 
                                       'time_zone_human':tz_info } 
                                   )
                    run_info.update( temps_and_voltages )
                    if name is not None:
                        run_info.update( { 'name' : name } )
                    db.add_data( [ run_info ] )
                    db.update()

    return scan_index               
        


def get_human_time( the_time):
    time_format = '%d/%m/%Y %H:%M:%S'
    return the_time.strftime(time_format)


def reset_all_settings():
    reset_txt_files()
    reset_xml_files()


def reset_txt_files(modules=modulelist, chips=chiplist):
    for module in modules:
        for chip in chips:
            targetname = os.path.join(txtfolder, 'CMSIT_RD53_%s_chip%i_default.txt' % (module, chip))
            sh.copy2(txtfile_blueprint, targetname)
    print('--> Reset txt files')
            
def reset_xml_files():

    if len(list(ids_and_chips_per_module_SAB)) != 1: raise ValueError('Exactly one module must be given in ids_and_chips_per_module_SAB, even if not used.')

    for type in daqsettings_per_xmltype:
        reset_singleQuad_xml_files(type=type, modules=modulelist)
        prepare_singleQuad_xml_files(type_name=type, type_setting=type, modules=list(ids_and_chips_per_module_SAB), chips=ids_and_chips_per_module_SAB[list(ids_and_chips_per_module_SAB)[0]][1])
        reset_and_prepare_Ring_xml_file(type, type, ids_and_chips_per_module_R1, 'R1')
        reset_and_prepare_Ring_xml_file(type, type, ids_and_chips_per_module_R3, 'R3')
    reset_and_prepare_Ring_xml_file('ber', 'scurve', ids_and_chips_per_module_R1, 'R1')
    reset_and_prepare_Ring_xml_file('ber', 'scurve', ids_and_chips_per_module_R3, 'R3')
    print('--> Reset XML files')

def reset_singleQuad_xml_files(type, modules=modulelist, chips=chiplist):
    xmlobject = XMLInfo(xmlfile_blueprint)
    xmlobject.set_module_attribute_by_moduleid(0, 'Id', 1)
    xmlobject.set_txtfilepath_by_moduleid(1, txtfolder)
    for chip in chips:
        if chip == 0: continue
        xmlobject.copy_chip_by_moduleid(1, 0, chip)
    for module in modules:
        targetname = os.path.join(xmlfolder,'CMSIT_singleQuad_%s_%s.xml' % (module, type))
        xmlobject.save_xml_as(targetname)

def reset_and_prepare_Ring_xml_file(type_name, type_setting, ids_and_chips_per_module, ring):

    xmlobject = XMLInfo(xmlfile_blueprint)

    for setting in daqsettings_per_xmltype[type_setting]:
        xmlobject.set_daq_settings(setting, daqsettings_per_xmltype[type_setting][setting])

    # set up all modules
    moduleids = []
    for mod in ids_and_chips_per_module:
        moduleids.append(ids_and_chips_per_module[mod][0])
    for id in moduleids:
        if not id == 0: xmlobject.copy_module_by_moduleid(0, id)
        xmlobject.set_txtfilepath_by_moduleid(id, txtfolder)
        
    xmlobject.keep_only_modules_by_moduleid(moduleids)

    # set up chips per module
    for module in ids_and_chips_per_module:
        id = ids_and_chips_per_module[module][0]
        chips = ids_and_chips_per_module[module][1]

        # first create all chips, then delete the unwanted ones
        for chip in [0,1,2,3]:
            if not chip == 0:
                xmlobject.copy_chip_by_moduleid(id, 0, chip)
            if ring == 'R1':
                xmlobject.set_chip_attribute_by_moduleid(id, chip, 'Lane', str(chip))
            elif ring == 'R3':
                xmlobject.set_chip_attribute_by_moduleid(id, chip, 'Lane', str(0))
            else: raise AttributeError('invalid ring specified: %s' % (str(ring)))
            xmlobject.set_chip_attribute_by_moduleid(id, chip, 'configfile', 'CMSIT_RD53_%s_chip%i_default.txt' % (module, chip))
            chip_settings = get_chipsettings_from_json()
            if str(chip) in chip_settings[module]:
                settings = chip_settings[module][str(chip)]
                for setting in settings:
                    xmlobject.set_chip_setting_by_modulename(module, chip, setting, settings[setting])
        xmlobject.keep_only_chips_by_moduleid(id, chips)

    targetname = os.path.join(xmlfolder,'CMSIT_disk%s_%s.xml' % (str(ring), type_name))
    xmlobject.save_xml_as(targetname)

#PREPARE
def prepare_singleQuad_xml_files(type_name, type_setting, modules=modulelist, chips=chiplist):
    for module in modules:
        xmlfilename = os.path.join(xmlfolder, 'CMSIT_singleQuad_%s_%s.xml' % (module, type_name))
        xmlobject = XMLInfo(xmlfilename)
        for setting in daqsettings_per_xmltype[type_setting]:
            xmlobject.set_daq_settings(setting, daqsettings_per_xmltype[type_setting][setting])
        for chip in chiplist:
            xmlobject.set_chip_attribute_by_moduleid(1, chip, 'Lane', str(chip)) # the lane corresponds to the chip ID on the single AB
            xmlobject.set_chip_attribute_by_moduleid(1, chip, 'configfile', 'CMSIT_RD53_%s_chip%i_default.txt' % (module, chip))
        chip_settings = get_chipsettings_from_json()
        chip_settings_thismodule = chip_settings[module]
        keepchips = []
        for chip in chips:
            settings = chip_settings_thismodule[str(chip)]
            for setting in settings:
                xmlobject.set_chip_setting_by_modulename(module, int(chip), setting, settings[setting])
        xmlobject.keep_only_chips_by_modulename(module, chips)
        xmlobject.save_xml_as(xmlfilename)



def get_xmlfile_name(ring, module, calib):
    modstr = ''
    ringstr = 'disk' + ring
    
    if ring == 'singleQuad':
        return '_'.join(['CMSIT', ring, module, calib]) + '.xml'
    else:
        return '_'.join(['CMSIT', 'disk' + ring, calib]) + '.xml'

def ensureDirectory(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
        if not os.path.exists(dirname):
            print('--> Failed to create directory \'%s\'' % dirname)

def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Run Tuning and BER Scan procedures')
    parser.add_argument('-t','--run-time', default=3, type=int, help='run time per setting in seconds. [default %(default)s]')
    parser.add_argument('--ber', action='store_true', default=False, help='run Bit Error Rate Scans [default: %(default)s]')
    parser.add_argument('--scan-type', choices=ber_scan_types.keys(), default='TAP0', help='BER Scan type (determines which TAP values to scan over. [default: %(default)s]')
    parser.add_argument('--test', action='store_true', default=False, help='FOR BER: run in test mode - do not log any results in the database. [default: %(default)s]')
    parser.add_argument('--rst-settings', dest='reset_settings', action='store_true', default=False, help='resest all text and xml files. [default: %(default)s]')
    parser.add_argument('--rst-backend',  dest='reset_backend',  action='store_true', default=False, help='reset backend board. [default: %(default)s]')
    parser.add_argument('--program',      dest='program',        action='store_true', default=False, help='run programming (CMSIT -p). [default: %(default)s]')
    parser.add_argument('--calibration',  dest='calibration',    action='store_true', default=False, help='run calibrations (physics and pixelalive). [default: %(default)s]')
    parser.add_argument('--vtuning',  dest='vtuning',    action='store_true', default=False, help='tune VDDD/A [default: %(default)s]')
    parser.add_argument('--scurve',  dest='scurve',    action='store_true', default=False, help='run a single scurve scan. [default: %(default)s]')
    parser.add_argument('--pixelalive',  dest='pixelalive',    action='store_true', default=False, help='run a single pixelalive scan. [default: %(default)s]')
    parser.add_argument('--thresholds',   dest='tune_thresholds', action='store_true', default=False, help='run threshold tuning. [default: %(default)s]')
    parser.add_argument('--all-scurves',  action='store_true', default=False, help='For threshold tuning: Run S-curves at all intermediate steps. [default: %(default)s]')
    parser.add_argument('-r','--ring',    dest='ring', choices=['R1','R3','R5','singleQuad'], default='R3',help='Ring (or SAB) to run run the test on')
    parser.add_argument('-m','--mod-for-tuning', choices=modulelist, default='modT09', help='Module used for tuning. [default: %(default)s]')
    parser.add_argument('--prefix', default='default', help='Prefix to use for plotting folder name, when running threshold tuning. [defaults %(default)s]')
    args = parser.parse_args()

    
    tuning_db = None if args.test else tdb.TuningDataBase(tuning_dbfile)
    ring_id = args.ring
    mod_for_tuning = args.mod_for_tuning
    prefix_plotfolder = f'{args.prefix}_{ring_id}_'
    if ring_id == 'singleQuad': 
        plotfolderpostfix = ''
    elif ring_id == 'R1': 
        plotfolderpostfix = '_'.join([mod for mod in ids_and_chips_per_module_R1.keys()])
    elif ring_id == 'R3': 
        plotfolderpostfix = '_'.join([mod for mod in ids_and_chips_per_module_R3.keys()])
    else: raise ValueError('Invalid \'ring_id\' specified: %s' % (ring_id))
   
    if args.reset_settings:
        reset_all_settings()
        print('Done resestting all settings.\n\n')

    if args.reset_backend:
        run_reset(ring=ring_id, module=mod_for_tuning)
        print('Done resestting backend.\n\n')

    if args.program:
        run_programming(ring=ring_id, module=mod_for_tuning)
        print('Done running programming.\n\n')

    if args.vtuning:
        run_calibration(ring=ring_id, module=mod_for_tuning, calib='voltagetuning')
        print('Done voltage tuning.')

    if args.calibration:
        run_calibration(ring=ring_id, module=mod_for_tuning, calib='physics', db=tuning_db)
        run_calibration(ring=ring_id, module=mod_for_tuning, calib='pixelalive', db=tuning_db)
        run_calibration(ring=ring_id, module=mod_for_tuning, calib='scurve', db=tuning_db)
        print('Done physics and pixel alive scan.\n\n')

    if args.scurve:
        run_calibration(ring=ring_id, module=mod_for_tuning, calib='scurve', db=tuning_db)
        print('Done scurve scan.\n\n')

    if args.pixelalive:
        run_calibration(ring=ring_id, module=mod_for_tuning, calib='pixelalive', db=tuning_db)
        print('Done scurve scan.\n\n')

        
    if args.tune_thresholds:
        run_threshold_tuning(module=mod_for_tuning, ring=ring_id, plotfoldername=prefix_plotfolder+plotfolderpostfix, intermediate_scurves =  args.all_scurves, db=tuning_db)
        print('Done threshold tuning. \n\n')
    
    if args.ber:
        setup_and_run_ber( args.run_time, args.ring, test_only = args.test, scan_type=args.scan_type)
        print('Done Bit Error Rate Test.\n\n')
