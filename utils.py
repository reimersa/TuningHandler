import re
import os

def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)

def get_last_runnr():
    #file 'RunNumber.txt' contains number the next run would have, nothing else.
    with open('RunNumber.txt', 'r') as f:
        runnr = int(f.readlines()[0]) - 1
    return runnr

def get_next_runnr():
    return get_last_runnr() + 1

def get_last_scan_file(scan_type):
        # last run has highest run-number and must have 'ThrAdjustment' in name
        files = [f for f in glob.glob(os.path.join('Results', '*.root')) if scan_type in f]
    
        # list is unordered
        runnrs = [int(n.split('_')[0].split('Run')[1]) for n in files]
        maxidx = runnrs.index(max(runnrs))
        lastfilename = files[maxidx]
        return lastfilename
        
def safe_convert( str_value, to_type, value_name):
    converted = None
    try:
       converted = to_type( str_value )
    except Exception as e:
        print(f'''ERROR: failed to convert the value of {value_name} from a string to {to_type.__name__}. 
                The string value is {str_value}:\n
                This may cause loss of data for this scan point. The original error was:\n{e}.''')
       
    return converted


def get_log_name(log_dir, runnr, scan_type):
    return os.path.join(log_dir, f'Run{runnr}_{scan_type}.log')

def get_log_runnr( log_filename):
    return os.path.basename(log_filename).lstrip('Run').split('_')[0]

def get_log_scantype( log_filename):
    return os.path.basename(log_filename).rstrip('.log').split('_')[-1]


def flatten_dict_per_chip( dct ):

    print(f'flattening: {dct}')
    global_data = {}
    chip_data = {}
    for key, val in dct.items():
        if not is_chip_data(val):
            global_data[key] = val
        else:
            for chipId, chip_info in val.items():
                if not chipId in chip_data:
                    chip_entry = get_chip_info( chipId )
                    chip_data[chipId] = chip_entry
                if isinstance(chip_info, dict):
                    chip_data[chipId].update( chip_info ) 
                else:
                    chip_data[chipId][key] = chip_info

    per_chip_entries = []
    for chipId, all_chip_info in chip_data.items():
        entry = all_chip_info
        entry.update(global_data)
        per_chip_entries.append(entry)

    return per_chip_entries

def is_chip_data( val ):
    """should be a dictionary with chipIds as the keys, the chipId is stored as a tuple with 4 entries"""
    is_chip = False
    if not isinstance(val, dict):
        return
    else:
        for key in val.keys():
            if not isinstance(key, tuple):
                return
            elif not len(key) == 4:
                return
    return True
            
def get_chip_info( chipId):
    dct = {'chip': chipId[0],
           'hybrid': chipId[1],
           'board' : chipId[2],
           'optical_group': chipId[3]} 
    return dct
        
