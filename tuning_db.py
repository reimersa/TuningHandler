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
        new_df = pd.read_json( fname, orient='records' )
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
        new_df['Pos'] = new_df.astype(str)
        self.__dict__.update( self.append( new_df, ignore_index=True ).__dict__ )

    #def without_metadata(self):
    #    "return copy without any of the metadata about file persistence"
    #    return self.loc[:, self.columns != 'is_from_file' ]

    def number_of_entries( self):
        "get the number of entries"
        return len(self.index)

    def write(self, filename):
        "Write the info to json file"
        self.to_json(filename, orient='records')

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

    def update_file(self, filename):
        "update a file, adding new data. Makes a backup, in case. Returns backup name."
        self.add_from_file( filename )
        backup_filename = self.overwrite( filename )
        return  backup_filename
