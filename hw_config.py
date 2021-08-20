from dataclasses import dataclass, field
from typing import Optional

import utils as uu
import json


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

    def select_by_module(self, modules) 
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


