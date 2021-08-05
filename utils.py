

def get_last_runnr():
    #file 'RunNumber.txt' contains number the next run would have, nothing else.
    with open('RunNumber.txt', 'r') as f:
        runnr = int(f.readlines()[0]) - 1
    return runnr

def get_last_scan_file(scan_type):
        # last run has highest run-number and must have 'ThrAdjustment' in name
        files = [f for f in glob.glob(os.path.join('Results', '*.root')) if scan_type in f]
    
        # list is unordered
        runnrs = [int(n.split('_')[0].split('Run')[1]) for n in files]
        maxidx = runnrs.index(max(runnrs))
        lastfilename = files[maxidx]
        return lastfilename
        
