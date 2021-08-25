#!/usr/bin/env python

from mark_tuning_as_good import Archive
from root_reader import RootScanResult
from tuning_db import TuningDataBase
import plotting
from XMLInfo import ArchivedXMLInfo, XMLInfo

import os

def get_xml_filename(run_number, ring, module, scan_type, archive_dir='archive/'):
    archive = Archive(archive_dir)
    results_dir = archive.results_dir(run_number)
    disk_str = f'disk{ring}'
    if ring == 'singleQuad':
        disk_str = f'{ring}_{module}'
    xml_file = os.path.join(results_dir, f'Run{run_number:06d}_CMSIT_{disk_str}_{scan_type}.xml')
    xml_info = XMLInfo(xml_file)
    

def get_missing_ports(run_number, module, scan_type, archive):
    xml_info = ArchivedXMLInfo(run_number, scan_type, archive.results_dir(run_number))
    module_data = xml_info.get_module_info()
    return module_data[module]['hybridId']

def add_missing_hybrid_entries( tdb_df, archive ):

    missing_df = tdb_df[ tdb_df['Port'].isnull() ]
    for (run_number,scan_type, module), run_df in missing_df.groupby(['RunNumber','ScanType','Module']):
        mod_port = get_missing_ports(run_number, module, scan_type, archive )
        tdb_df.loc[ run_df.index, 'Port'] = mod_port
    return tdb_df
    
def get_target_threshold( run_number, ring, module, scan_type, archive_dir='archive/'): 
    xml_file = get_xml_filename( run_number, ring, module, scan_type, archive_dir )
    xml_info = XMLInfo(xml_file)
    target_threshold = xml_info.get_daq_settings['TargetThr']
    return target_threshold

def keep_only_archived_scurves( tdb_df ):
    tdb_df = tdb_df[ (tdb_df['ScanType'] == 'scurve') & (tdb_df['IsArchived'] ) ]
    return tdb_df


def get_noise_data( scan_result, chip, hybrid=0, optical_group=0, board=0):
    return get_vcal_and_ele_mean_and_stdev( 'Noise1D', scan_result, chip, hybrid, optical_group, board, name='Noise')

def get_threshold_data( scan_result, chip, hybrid=0, optical_group=0, board=0):
    return get_vcal_and_ele_mean_and_stdev( 'Threshold1D', scan_result, chip, hybrid, optical_group, board, name='Threshold')

def get_vcal_and_ele_mean_and_stdev( hist_type, scan_result, chip, hybrid=0, optical_group=0, board=0, name=None):
    name = name if name is not None else hist_type
    hist = scan_result.get_hist( hist_type, chip=chip, hybrid=hybrid)
    vcal_mean = hist.GetMean()
    vcal_stdev = hist.GetStdDev()
    vcal_to_e = scan_result.get_vcal_to_ele_function( hist_type, chip=chip, hybrid=hybrid)
    e_mean = vcal_to_e( vcal_mean )
    e_stdev = vcal_to_e( vcal_stdev )
    dct = {f'{name}Mean_VCal': vcal_mean , f'{name}StdDev_VCal': vcal_stdev, 
            f'{name}Mean_ele': e_mean, f'{name}StdDev_ele': e_stdev }
    return dct



def drop_nan_hybrid_entries( tdb_df ):
    tdb_df = tdb_df[ ~tdb_df['Port'].isnull() ]
    return tdb_df

def entry_in_scurve_df( df_entry, scurve_df ):
    if len(scurve_df) < 1: 
        return False
    run_number = df_entry['RunNumber']
    chip = df_entry['Chip']
    module = df_entry['Module']
    df_copy = scurve_df[ ((scurve_df['RunNumber'] == run_number) & 
                          (scurve_df['Chip'] == chip) &
                          (scurve_df['Module'] == module) ) ]
    return len(df_copy) > 0
    

def fill_db( archive_dir, tuning_db, scurve_db ):
    archive = Archive(archive_dir) 
    tuning_db = TuningDataBase(tuning_db)
    scurve_db = TuningDataBase(scurve_db)

    tdb_df = tuning_db.get_info()
    tdb_df = keep_only_archived_scurves( tdb_df )
    #tdb_df = drop_nan_hybrid_entries( tdb_df )
    tdb_df = add_missing_hybrid_entries( tdb_df, archive )
    
    scurve_df = scurve_db.get_info()

    scurve_info = ['RunNumber','Port','Module','Chip']
    for run_number, run_df in tdb_df[scurve_info].groupby(['RunNumber']):
        scan_result_dir = archive.results_dir( run_number )  
        scan_result = RootScanResult( run_number, 'SCurve', scan_result_dir )
        new_entries = [] 
        
        xml_info = ArchivedXMLInfo( run_number, 'SCurve', scan_result_dir )
        target_threshold = xml_info.get_daq_settings()['TargetThr']
        for idx, row in  run_df.iterrows():
            if entry_in_scurve_df( row, scurve_df ):
                continue
            row_dct = row.to_dict()
            row_dct.pop('Port')
            chip = int(row['Chip'])
            hybrid = int(row['Port'])
            noise_data = get_noise_data( scan_result, chip, hybrid )
            thresh_data = get_threshold_data( scan_result, chip, hybrid )
            thresh_data.update( {'TargetThreshold_ele':target_threshold } )
            row_dct.update( noise_data )
            row_dct.update( thresh_data )
            new_entries.append( row_dct )
        scurve_db.add_data( new_entries )
        scurve_db.update()

    scurve_df = scurve_db.get_info()
    scurve_df = scurve_df.merge( tdb_df, how='left', on=['RunNumber','Module','Chip'])
    print(tdb_df)
    print(scurve_df)
    scurve_df = scurve_df[ ~(scurve_df['Module'] == 'modT14') ]
    plotting.plot_scurve_noise(scurve_df)
    plotting.plot_scurve_noise_by_module(scurve_df)
    plotting.plot_scurve_width(scurve_df)
    plotting.plot_scurve_target_difference( scurve_df )
    

if __name__=='__main__':
    archive_dir = 'archive/'
    tuning_db = 'tuning_db/tuning.json'
    scurve_db = 'tuning_db/scurves.json'
    fill_db(archive_dir, tuning_db, scurve_db )
    #get_missing_ports(68925,'R1','scurve')           
    

