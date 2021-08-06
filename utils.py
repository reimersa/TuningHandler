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
