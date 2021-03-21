import pandas as pd
import os

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
        new_df['is_from_file'] = True
        self.add_data( new_df )

    def add_new_data(self, info ):
        "Add new data which is not saved to file"
        new_df = pd.DataFrame(info)
        new_df['is_from_file'] = False
        self.add_data( new_df )
        
    def add_data( self, info):
        "Append the data in place, with minor type checking"
        #Maybe faster not to convert if info is already a DataFrame or Pandas Series
        new_df = pd.DataFrame( info )
        new_df['Pos'] = new_df.astype(str)
        self.__dict__.update( self.append( new_df ).__dict__ )

    def without_metadata(self):
        "return copy without any of the metadata about file persistence"
        return self.loc[:, self.columns != 'is_from_file' ]

    def number_of_entries( self):
        "get the number of entries"
        return len(self.index)

    def write(self, filename):
        "Write the info to json file"
        self.to_json(filename, orient='records')
