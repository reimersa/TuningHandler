
class XMLConfigMaker:

    xml_blueprint=

    def __init__(self, hw_config, chip_config, scan_config):
        self._scan_config = scan_config
        self._hw_config = hw_config
        self._chip_settings = chip_config
        self._xml_obj = xmlInfo(self.xml_blueprint)

        self._config_daq_settings()
        self._add_modules_to_config()
        self._setup_chips_per_module()

    def get_xml_file_name(self):
        ring = self._hw_config.get_ring_name()
        scan = self._scan_config.get_scan_name()
        return os.path.join(self._xml_dir, f'CMSIT_disk{ring}_{scan}.xml'

    def save(self):
        filename= self.get_xml_file_name()
        self._xml_obj.save_xml_as(filename)

    #Private Member functions for convenience
    def _config_daq_settings(self):
        for key, val in self.scan_settings.get_daq_settings():
            self._xml_obj.set_daq_settings( key, val )

    def _add_modules_to_config(self):
        active_ports = self._hw_config.get_active_ports()
        text_config_dir = self._hw_config.text_dir
        for port_id in active_ports:
            if port_id == 0: 
                continue
            self._xml_obj.copy_module_by_moduleid(0, port_id)

            self._xml_obj.set_txtfilepath_by_moduleid(port_id, text_config_dir )
        self._xml_object.keep_only_modules_by_moduleid( active_ports )

    def _setup_chips_per_module(self):
        active_modules = self._hw_config.get_active_modules()
        for moduleId in active_modules:
            active_chips = self._hw_config.get_active_chips( moduleId )
            for chipId in active_chips:
                self._config_chip_default( chipId, moduleId )
                self._config_chip_specific( chipId, moduleId )
        self._xml_obj.keep_only_chips_by_moduleName(moduleId, active_chips)

    def _config_chip_default( self, chipId, moduleId ):
        portId = self._hw_config.get_port_by_module( moduleId )
        if not chipId == 0:
            self._xml_obj.copy_chip_by_moduleid(portId, 0, chipId)
            data_lane = self._hw_config.get_chip_lane( moduleId, chipId ) 
        self._xml_obj.set_chip_attribute_by_moduleid(portId, chipId, 'Lane', data_lane)

        xmlobject.set_chip_attribute_by_moduleid(portId, chipId, 'configfile', f'CMSIT_RD53_{moduleId}_chip{chipId}_default.txt')

    def _config_chip_specific( moduleId, chipId):
        chip_settings = self._chip_settings.get_settings(moduleId, chipId)
        for key, val in settings.items():
            xmlobject.set_chip_setting_by_modulename(moduleId, chipId, key, val)


class HWConfig(ABC):

    def __init__(self, config_file, name):

    def _is_consistent(self):
        for module in self.get_active_modules():
            for port in self.get_port_by_module( module ):
                if not port in self.get_all_ports():
                    return False
        for port in get_active_ports(self):
            if not port in self.get_all_ports():
                return False

    def get_all_ports(self):

    def get_all_positions(self):

    def get_active_positions(self):

    def get_position_by_module(self):

    def get_active_ports(self):

    def get_active_modules(self):

    def get_port_by_module(self):

    def get_active_chips(self, module):

    def get_chip_line(self, moduleId, chipId):

    def get_ring_name(self):

    @property
    def text_dir(self):


class HWConfigJSON():

    def __init__(self, config_file, name):
        self._filename = config_file
        with open(config_file, 'r') as f:
            dct = safe_load(f)
        self._ports = dct[ports]
        self._ring_name = name
        self._modules = dct[name]['modules']
        self._positions = dct[name]['positions']
        self._is_consistent()

    def get_all_ports(self):
        return self._ports

    def get_active_ports(self):
        ports = []
        for module in self.get_active_modules():
            ports.append( self.get_port_by_module( module ) )

    def get_active_modules(self):
        return list[ self._modules.keys() ]

    def get_port_by_module(self, module):
        return self._modules[module]['port']

    def get_all_positions(self):
        return list[ self._positions.keys() ]

    def get_active_positions(self):
        positions = []
        for module in self.get_active_modules():
            positions.append( self.get_position_by_module( module )
        return positions

    def get_position_by_module(self, module):
        return self._modules[module]['position']


    def get_active_chips(self, module):
        return self._modules[module]['chips']

    def get_lane_by_module(self, module, chip):
        position = self.get_position_by_module( module )
        lane = self.get_lane_by_position( position, chip )
        return lane

    def get_lane_by_position(self, position, chip):
        return self._positions[position]['lanes'][chip]

    def get_ring_name(self):
        return self._ring_name

    def get_chip_settings(self, module, chipId):
        chip_settings = self._get_chipsettings_from_json()
        if str(chip) in chip_settings[module]:
            settings = chip_settings[module][str(chipId)]
        return chip_settings

    def _get_chipsettings_from_json(self):

    @property
    def text_dir(self):

class JSONConfig:

    def __init__(self, filename):
        self._filename = filename
        self._settings = self._get_chipsettings_from_json( filename )

    def _get_settings_from_json(self):
        with open( self._filename, 'r') as f:
            settings = safe_load(f)
        return settings

    def get_config(self):
        return self._settings

class ScanConfig(JSONConfig): 

    def __init__(self, *args, scan_type):
        super().__init__(*args)
        self._scan = scan_type
        self._settings = self._settings[scan_type]

    def get_daq_settings(self):
        return self.get_config()

    def get_scan_name(self):
        return self._scan


class ChipConfig(JSONConfig):

    def get_chip_settings(self, module, chipId):
        all_settings = self._settings
        if str(chip) in all_settings[module]:
            chip_settings = all_settings[module][str(chipId)]
        return chip_settings


        
