import pandas as pd
import os
import shutil

class FileNotFoundError(Exception):
    """Raised when a file is expected to exist isn't found."""
    pass
    

class TuningDataFrame(pd.DataFrame):
    
    #This is important for subclassing DataFrames
    @property
    def _constructor(self):

        def _c(*args, **kwargs):
            return TuningDataFrame(*args, **kwargs).__finalize__(self)

        return _c

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_from_file( self, fname ):
        "Read data in from saved file"
        new_df = pd.read_json( fname, orient='records', lines=True )
        self.add_data( new_df )

    def add_new_data(self, info ):
        "Add new data which is not saved to file"
        new_df = pd.DataFrame(info)
        #new_df['is_from_file'] = False
        self.add_data( new_df )
        
    def add_data( self, info):
        "Append the data in place, with minor type checking"
        #Maybe faster not to convert if info is already a DataFrame or Pandas Series
        new_df = pd.DataFrame( info )
        new_df['Pos'] = new_df['Pos'].astype(str)
        self.__dict__.update( self.append( new_df, ignore_index=True ).__dict__ )

    #def without_metadata(self):
    #    "return copy without any of the metadata about file persistence"
    #    return self.loc[:, self.columns != 'is_from_file' ]

    def number_of_entries( self):
        "get the number of entries"
        return len(self.index)

    def write(self, filename):
        "Write the info to json file"
        self.to_json(filename, orient='records', lines=True)

    def overwrite(self, filename):
        "overwrite an existing file. Makes a  backup in case. Returns backup name."
        #store a backup, just in case
        backup_name = ''
        if os.path.exists(filename):
            backup_name = filename.rstrip('.json') + '.backup.json'
            created_file = shutil.copyfile( filename, backup_name )

            if not os.path.exists(backup_name):
                raise FileNotFountError(f"tried to create backup file {backup_name} for file {filename}, but {backup_name} not found")
            os.remove(filename)
            
        self.write( filename )
        return backup_name

    def add_to_file(self, filename):
        "update a file, adding new data. Makes a backup, in case. Returns backup name."
        if os.path.exists(filename):
            self.add_from_file( filename )
            backup_filename = self.overwrite( filename )
        else:
            self.write( filename )
            backup_filename = ''
        return  backup_filename


class TuningDataBase():

    def __init__(self, fname):
        self._fname = fname
        self._index_file_name = os.path.join(self.db_dirname(),'next_index.txt')
        self._new_info_df = TuningDataFrame()
        self._stored_info_df = TuningDataFrame()

    def update(self):
            self._new_info_df.add_to_file( self._fname )
            self._new_info_df = TuningDataFrame()

    def add_data(self, data):
            self._new_info_df.add_data( data )

    def db_filename(self):
        return self._fname

    def db_dirname(self):
        return os.path.dirname(self._fname)

    def get_info(self):
        self._stored_info_df.add_from_file( self._fname )
        df_copy = self._stored_info_df.copy()
        self._stored_info_df = TuningDataFrame()
        return df_copy
        

    def get_next_index(self):
        #file 'RunNumber.txt' contains number the next run would have, nothing else.
        new_file = False
        if os.path.exists(self._index_file_name):
            open_arg = 'r+'
        else: 
            open_arg = 'w'
            new_file = True

        index = 0
        with open(self._index_file_name, open_arg) as f:
            if not new_file:
                index = int(f.readlines()[0]) 
                f.seek(0)
            f.write(f'{index+1}')
            f.truncate()
        return index

def has_named_scan(db, name):
    df = db.get_info()
    if 'name' in df.columns:
        names = df['name'].unique()
        if name in names:
            return True
    return False

def calculate_bit_error_rates( df ):
    '''Calculate a new row of the dataframe giving the Bit Error Rates
    From the total number of frames and errors'''
    return df['NBER'].clip(1)/df['NFrames']

def combine_ber_measurements( df, group_on ):
    '''For independent measurements taken under (supposedly) equivalent settings, combine
    the number of frames and errors to create a single combined measurement. equivalent
    measurements are defined by the group_on array.'''

    return df.groupby( group_on ).sum(['NFrames','NBER']).reset_index()

