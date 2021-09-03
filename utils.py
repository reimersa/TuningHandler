import json 
import os


def safe_convert( str_value, to_type, value_name):
    '''Convert string to another type, raising a verbose error if conversion doesn't workr.'''
    converted = None
    try:
       converted = to_type( str_value )
    except Exception as e:
        print(f'''ERROR: failed to convert the value of {value_name} from a string to {to_type.__name__}. 
                The string value is {str_value}:\n
                This may cause loss of data for this scan point. The original error was:\n{e}.''')
       
    return converted


def ensureDirectory(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
        if not os.path.exists(dirname):
            print('--> Failed to create directory \'%s\'' % dirname)

#def get_masked_pix(runnr, log=None, db=None):
#    """Get the number of masked pixels during a run, try it first from the database if available,
#        if not, try the log file."""
#    masked_pix = None
#    if db is not None:
#        df = db.get_info()
#        if 'RunNumber' in df.columns:
#            if 'InitMaskedPix' in df.columns:
#                masked_pix = df[ df['RunNumber'] == runnr ]['InitMaskedPix']
#    if masked_pix is None:
#        if not log is None:
