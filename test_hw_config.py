import hw_config as hw

class ModuleDoesNotExistError(Exception):
    pass

if __name__=='__main__':

    all_modules = hw.get_moduledict_from_json('settings/chipsettings.json')
    ring = "R3"
    ring_positions = hw.get_positiondict_from_json('settings/positionsettings.json')
    connections = hw.get_module_connections('settings/connections.json')

    front_ends = hw.create_frontend_list( all_modules, ring_positions, connections)
    hw_config = hw.HWConfig(front_ends)
    print(hw_config.positions())
    print(hw_config.modules())
    print(hw_config.rings())
    print(hw_config[ hw_config.position == 'R31' ].modules())
    hw_config.write('test_hw.log')

    new_hw_config = hw.HWConfig().read('test_hw.log')
    print(new_hw_config)
