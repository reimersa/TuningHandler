from dataclasses import dataclass, field, fields, asdict
from typing import Optional

import utils as uu
import json
import pandas as pd


@dataclass(order=True)
class Module:
    name: str
    chips : list[int] = field(default_factory=list([0,1,2,3]))

    def __post_init__(self): #since chips are sometimes stored in json as strings
        chips = [] 
        for chip in self.chips:
            chips.append( uu.safe_convert(chip, int, "ChipId") )
        self.chips = chips

@dataclass(order=True)
class Position:
    ring: Optional[str] = None
    position: Optional[str] = None
    data_lanes: list[int] = field(default_factory=list([0,1,2,3]))
    
@dataclass(order=True)
class FrontEnd:
    module: Optional[Module] = None
    position: Optional[Position] = None
    port: Optional[int] = None
    active_chips: Optional[list] = None
    active: bool = True

    def __post_init__(self):
        #Set active lanes to all allowable ones by default
        if self.active_chips is None:
            self.active_chips = self.get_good_lanes()

    def get_good_lanes(self):
        chip_list = [ chipId for chipId in self.module.chips if chipId in self.position.data_lanes ]
        return chip_list

    def as_flat_dict(self):
        dct = asdict(self)
        to_del = []
        to_update = {}
        for key, val in dct.items():
            if isinstance(val, dict):
                to_del.append(key)
                to_update.update(val)

        for key_to_del in to_del:
            del dct[key_to_del]
        dct.update(to_update)

        return dct
        

class ModuleDoesNotExistError(Exception):
    pass

@dataclass
class ModuleDict:
    modules: dict[Module] = field(default_factory=dict)
    
    def get_module(self, mod):
        if not mod in self.modules:
            raise ModuleDoesNotExistError(f'''Module {mod} does not exist in the module dictionary.
the list of modules is:
{self.modules}''')
        return self.modules[mod]

    def select_by_module(self, modules): 
        dct = { mod for mod in self.modules if mod.name in modules }
        return ModuleDict( dct )

    def list_all_modules(self):
        return [ name for name in self.modules.keys() ]


@dataclass
class PositionDict:
    positions: dict[Position] = field(default_factory=dict)
    
    def get_position(self, pos):
        return self.positions.get(pos, None)

    def select_by_rings(self, rings):
        dct = { pos for pos in self.positions if pos.ring in rings }
        return PositionDict(dct)

    def list_all_rings(self):
        rings = []
        for pos in self.positions:
            if pos.ring not in rings:
                rings.append(ring)
        return rings

### helper functions
def get_moduledict_from_json( config_file ):
    with open(config_file, 'r') as f: 
        mod_dict = json.load(f)
    all_modules = ModuleDict({ m : Module(m, list(d.keys()) ) for m, d in mod_dict.items() })
    return all_modules

def get_modulelist_from_json( config_file):
    with open(config_file, 'r') as f:
        mod_dict = json.load(f)
    all_modules = [ {"name":mod, "chips":list(chip_info.keys()) } for mod, chip_info in mod_dict.items() ]
    return all_modules 

def get_positiondict_from_json( config_file, rings=None ):
    '''Get all positions associated with a set of rings. If no rings are specified, get all positions with all rings'''

    with open(config_file,'r') as f:
        pos_dict = json.load(f)

    if rings is None:
        rings = list( pos_dict.keys() )  

    all_positions = {}
    for ring in rings:
        these_positions = {p:Position(ring=ring, position=p, **d) for p, d in pos_dict[ring].items()}
        all_positions.update(these_positions)
    return PositionDict(all_positions)

def get_module_connections( config_file):
    with open(config_file, 'r') as f:
        connections = json.load(f)
    return connections

def create_frontend_list( modules, positions, connections):
    '''Make a list of the FrontEnd Objects given input dictionaries of Modules, Positions and their Connections'''

    front_ends = []
    for fe_dct in connections:
        mod = modules.get_module( fe_dct["module"] ) #should return error if module doesnt exist
        pos = positions.get_position(fe_dct["position"] )
        if pos is None: #ignore positions not in the setup
            continue
        port = fe_dct["port"]
        front_ends.append(  FrontEnd( module=mod, position=pos, port=port)  )
    return front_ends 


@dataclass
class EmptyDataClass:
    pass
    
class DataClassFrame(pd.DataFrame):
    '''Container for DataClasses, using pandas dataframe accessibility to access the data elements of the collection.'''

    _classType = EmptyDataClass
    _expand = None
    _prefixes = None

    class MissingColumnsError(Exception):
        pass

    #This is important for subclassing DataFrames
    @property
    def _constructor(self):

        def _c(*args, **kwargs):
            return self.__class__(*args, validate=False, **kwargs).__finalize__(self)

        return _c

    def __init__(self, *args, validate=True, **kwargs):
        super().__init__(*args, **kwargs)
        if validate:
            self._expand_cols()
            self._validate()

    def _validate(self):
        required_cols = self._get_required_cols()
        if len(self) == 0:
            self._ensure_columns(required_cols)
        else:
            missing_cols = [ col for col in required_cols if not col in self.columns ] 
            if len(missing_cols)>0:
                pass
                #raise self.MissingColumnsError(f'''ModuleGroup could not be created from Dataframe, missing columns: {missing_cols}. Dataframe is {self}''')

    def _expand_cols(self):
        if self._expand is None:
            return
        to_remove = []
        to_join = []
        for col in self.columns:
            if col in self._expand:
                to_join.append( self._expand_column( col ) )
                to_remove.append(col)

        for col in to_remove:
            self.pop( col )
        for df in to_join:
            joined = self.join( df )
            self.__dict__.update(joined.__dict__)
        
    def _expand_column( self, col ):
        list_of_records = self[[col]].to_dict(orient='list')[col]
        col_df = self._expand[col]( list_of_records )
        renaming_dict = { new_col:self._new_col_name( col, new_col) for new_col in col_df.columns }
        col_df.rename( columns=renaming_dict, inplace=True )
        return col_df
        

    @classmethod
    def _get_required_cols(cls):
        if cls._expand is None:
            cols = [ field.name for field in fields(cls._classType) ]
        else:
            field_info = { field.name : field.type for field in fields(cls._classType) }
            cols = []
            for name, classtype in field_info.items():
                if name in cls._expand:
                    for col in cls._expand[name]._get_required_cols():
                        cols.append(cls._new_col_name(name, col))
                else:
                    cols.append(name)
        return cols 

    @classmethod
    def _new_col_name(cls, old_col, field):
        prefix = cls._get_prefix(old_col)
        return f'{prefix}{field}'

    @classmethod
    def _get_prefix(cls, col):
        ret = f'{col}_'
        if cls._prefixes is None:
            pass
        else:
            if col in cls._prefixes:
                ret = cls._prefixes[col]
        return ret

    def _ensure_columns(self, cols):
        self.assign( **{col:[] for col in cols} )
    
    def _select_expanded_class(self, key):
        col_suffixes = self._expand[key]._get_required_cols()
        col_dct = {}
        for new_name in col_suffixes:
            old_name = self._new_col_name(key, new_name ) 
            col_dct[old_name] = new_name
        df = self.loc[:, list(col_dct.keys()) ] 
        df.rename(columns = col_dct, inplace=True)
        return self._expand[key](df)
    

    def write(self, filename):
        "Write the info to json file"
        self.to_json(filename, orient='records', lines=True)

    @classmethod
    def read(cls, filename):
        "Read config from json file"
        from_json = pd.read_json(filename, orient='records',lines=True)
        return cls(from_json)

class ModuleDataFrame(DataClassFrame):
    _classType = Module
    
class PositionDataFrame(DataClassFrame):
    _classType = Position 

class HWConfig(DataClassFrame):
    _classType = FrontEnd
    _expand = {'module': ModuleDataFrame, 'position': PositionDataFrame }
    _prefixes = {'module':'','position':''}
        
    def modules(self):
        return self._select_expanded_class('module')

    def positions(self):
        return self._select_expanded_class('position')

    def rings(self):
        return self.ring.unique()
