#! /usr/bin/env python
import os, re
import time, math
import numpy as np
import shutil as sh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


from XMLInfo import *
from settings.typesettings import *
from settings.chipsettings import *


xmlfolder = 'xml/'
txtfolder = 'txt/'
logfolder = 'log/'
plotfolder = 'plots/'
xmlfile_blueprint = '/home/uzh-tepx/Ph2_ACF/settings/CMSIT.xml'
# xmlfile_blueprint = 'xml/CMSIT.xml'
txtfile_blueprint = '/home/uzh-tepx/Ph2_ACF/settings/RD53Files/CMSIT_RD53.txt'
#txtfile_blueprint = 'txt/CMSIT_RD53.txt'


chiplist = [0, 1, 2, 3]
modulelist = ['mod3', 'mod4', 'mod6', 'mod7', 'mod9', 'mod10', 'mod11', 'mod12', 'modT01', 'modT02', 'modT03', 'modT04']


ids_and_chips_per_module_R1 = {
    #'mod7': (1, [1])
    'mod7': (1, [1, 0, 2])
    #'mod4': (1, [0])
}

ids_and_chips_per_module_R3 = {
    'mod7': (1, [3])
}
















def main():

    reset_all_settings()


    # now run many BER tests
    tap_settings = []
#    for tap0 in [280, 300, 400]:
#    for tap0 in [450, 475, 500, 550, 600 ]:
    for tap0 in [450, 475, 500, 550 ]:
    #for tap0 in [700]:
        for tap1 in range(-150, 150+1, 25):
            for tap2 in range(-150, 150+1, 25):
                tap_settings.append((tap0, tap1, tap2))
                
                

    ring            = 'R1'
    positions       = ['5']
    modules_for_ber = ids_and_chips_per_module_R1.keys()
    chips_per_module= {}
    for mod in ids_and_chips_per_module_R1:
    	chips_per_module[mod] = ids_and_chips_per_module_R1[mod][1]
    	
    
    tap_settings_per_module_and_chip = {}
    for moduleidx, module in enumerate(modules_for_ber):
    	settings_per_chip = {}
    	for chip in chips_per_module[module]:
    	    if not chip in settings_per_chip.keys():
    		settings_per_chip[chip] = []	
    		for s in tap_settings:
    		    t0 = s[0]
    		    t1 = s[1]
    		    t2 = s[2]
    		    if module == 'mod7' and chip == 1:
    			t0 = min(t0+130, 1023)
    		    if module == 'mod7' and chip == 2:
    			t0 = min(t0-60, 1023)

    		    settings_per_chip[chip].append((t0, t1, t2))

    	        tap_settings_per_module_and_chip[module] = settings_per_chip

#            import pdb; pdb.set_trace()
            #print module, chip, tap_settings_per_module_and_chip[module][chip]
            #plot_ber_results(module=module, chip=chip, ring=ring, position=positions[moduleidx], tap_settings=tap_settings_per_module_and_chip[module][chip])
            
#    print tap_settings_per_module_and_chip
    		
    
#    run_ber_scan(modules=modules_for_ber, chips_per_module=chips_per_module, ring=ring, positions=positions, tap_settings_per_module_and_chip=tap_settings_per_module_and_chip, value=84)

    #for moduleidx, module in enumerate(modules_for_ber):
    #    for chip in chips_per_module[module]:
    #        pass
    #        plot_ber_results(module=module, chip=chip, ring=ring, position=positions[moduleidx], tap_settings=tap_settings_per_module_and_chip[module][chip])
















def plot_ber_results(module, chip, ring, position, tap_settings, groupby = 'TAP0'):

    # group by tap0
    tapdict = {}
    xvalues = []
    yvalues = []
    for tap0, tap1, tap2 in sorted(tap_settings):
        logfilename = os.path.join(logfolder, 'ber_%s_%s_chip%i_pos%s_%i_%i_%i.log' % (ring, module, chip, str(position), tap0, tap1, tap2))
        nframes = -1
        nber    = -1

        with open(logfilename, 'r') as f:
            lines = f.readlines()
            for l in lines:
                l = escape_ansi(l)
                if 'Final number of PRBS frames sent:' in l:
                    nframes = int(l.split(' ')[-1])
                elif 'Final BER counter:' in l:
                    nber = int(l.split(' ')[-1])
        if groupby == 'TAP0':
            if not tap0 in tapdict.keys():
                tapdict[tap0] = {(tap1, tap2): (nframes, nber)}
            else:
                tapdict[tap0][(tap1, tap2)] = ((nframes, nber))
            if not tap1 in xvalues: xvalues.append(tap1)
            if not tap2 in yvalues: yvalues.append(tap2)
        elif groupby == 'TAP1':
            if not tap0 in tapdict.keys():
                tapdict[tap1] = {(tap0, tap2): (nframes, nber)}
            else:
                tapdict[tap1][(tap0, tap2)] = ((nframes, nber))
            if not tap0 in xvalues: xvalues.append(tap0)
            if not tap2 in yvalues: yvalues.append(tap2)
        elif groupby == 'TAP2':
            if not tap2 in tapdict.keys():
                tapdict[tap2] = {(tap0, tap1): (nframes, nber)}
            else:
                tapdict[tap2][(tap0, tap1)] = ((nframes, nber))
            if not tap0 in xvalues: xvalues.append(tap0)
            if not tap1 in yvalues: yvalues.append(tap1)

    #make numpy arrays
    ber_and_minval_arrays = {}
    minvalue_arrays = {}
    for key in tapdict.keys():
        ordered_list = []
        minvalues = []
        for(key1, key2) in sorted(tapdict[key].keys()):
            nframes = tapdict[key][(key1, key2)][0]
            ber_abs = tapdict[key][(key1, key2)][1]
            print key1, key2, ber_abs

            if nframes <= 0 or ber_abs < 0:
                ber_rel = -1
                minvalue = -1
            else:
                minvalue = np.float64(1)/np.float64(nframes)
                ber_rel = np.float64(max(minvalue, (np.float64(ber_abs) / np.float64(nframes))))
            	print 'components: ', np.float64(ber_abs), np.float64(nframes), minvalue, np.float64(1), minvalue, ber_rel
            	
            ordered_list.append((ber_rel, minvalue))
        ber_and_minval_arrays[key] = (np.array([tup[0] for tup in ordered_list], dtype=np.float64).reshape(len(xvalues), len(yvalues)), np.array([tup[1] for tup in ordered_list], dtype=np.float64).reshape(len(xvalues), len(yvalues)))
        print ber_and_minval_arrays[key]

        fig, ax = plt.subplots(figsize=(12,4))
        z_max = 1E-5
        cmap = plt.cm.get_cmap('Purples', 300)
        im = ax.imshow(np.swapaxes(ber_and_minval_arrays[key][0], 0, 1), aspect='auto', origin='lower', vmin=np.min(ber_and_minval_arrays[key][1])+1E-30, vmax=z_max, cmap=cmap, norm=matplotlib.colors.LogNorm())



        cbar = plt.colorbar(im)
        cbar.ax.set_ylabel('Bit error rate')
        xlabel = 'TAP1' if groupby == 'TAP0' else 'TAP0'
        ylabel = 'TAP1' if groupby == 'TAP2' else 'TAP2'
        title = '%s = %i, BER lower limit: %s' % (groupby, key, '{:.1e}'.format(minvalue))
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_xticks(np.arange(len(xvalues)))
        ax.set_yticks(np.arange(len(yvalues)))
        ax.set_xticklabels(xvalues)
        ax.set_yticklabels(yvalues)
        plt.tight_layout()

        for i in range(len(xvalues)):
            for j in range(len(yvalues)):
                val = ber_and_minval_arrays[key][0][i,j]
                minvalue = ber_and_minval_arrays[key][1][i,j]
                print val, minvalue
                if val == minvalue:
                    color = 'green'
                elif math.log10(val) > 0.5 * (math.log10(minvalue) - math.log10(z_max)) + math.log10(z_max):
                    color = 'white'
                else:
                    color = 'black'
                ax.text(i, j, '{:.1e}'.format(val) if val else '0', ha='center', va='center', color=color)



        outfilename = os.path.join(plotfolder, 'ber_%s_%s_chip%i_pos%s_%s_%i.pdf' % (ring, module, chip, str(position), groupby, key))
        fig.savefig(outfilename)
        fig.savefig(outfilename.replace('.pdf', '.png'))
        plt.close(fig)







def run_ber_scan(modules, chips_per_module, ring, positions, tap_settings_per_module_and_chip, mode='time', value=10):

    # first, enable TAP1, TAP2

    for moduleidx, module in enumerate(modules):
        for chip in chips_per_module[module]:
            tap_settings = tap_settings_per_module_and_chip[module][chip]
            if ring == 'singleQuad':
                if not len(modules) == 1:
		    raise AttributeError('Trying to run BER in singleQuad mode with mode than one module')
                module = modules[0]
                xmlfile_for_ber = os.path.join(xmlfolder, 'CMSIT_%s_%s_%s.xml' % (ring, module, 'ber'))
                reset_singleQuad_xml_files(type='ber', modules=modules, chips = chips)
                prepare_singleQuad_xml_files(type_name='ber', type_setting='scurve', modules=modules)
	    elif ring == 'R1':
                xmlfile_for_ber = os.path.join(xmlfolder, 'CMSIT_disk%s_%s.xml' % (ring, 'ber'))
                reset_and_prepare_Ring_xml_file('ber', 'scurve', ids_and_chips_per_module_R1, ring)
            elif ring == 'R3':
                xmlfile_for_ber = os.path.join(xmlfolder, 'CMSIT_disk%s_%s.xml' % (ring, 'ber'))
            xmlobject = XMLInfo(xmlfile_for_ber)
            print module, chip
            xmlobject.keep_only_modules_by_modulename([module])
            xmlobject.keep_only_chips_by_modulename(module, [chip])



            # now, in a loop, set TAP values to scan through
            for tap0, tap1, tap2 in tap_settings:
                
                print(tap0, tap1, tap2)
                xmlobject.set_chip_setting_by_modulename(module, chip, 'CML_TAP0_BIAS', str(tap0))
                xmlobject.set_chip_setting_by_modulename(module, chip, 'CML_TAP1_BIAS', str(abs(tap1)) ) #inversion is in a separate config setting
                xmlobject.set_chip_setting_by_modulename(module, chip, 'CML_TAP2_BIAS', str(abs(tap2)) ) #inversion is in a separate Config setting
                #CML_CFG bits are used to set the inversion for tap0 and tap1
                cml_cfg = 63 
                if tap1 < 0:
                	cml_cfg += 64 #TAP1 inversion is 6th bit
                if tap2 < 0:
                	cml_cfg += 128 #TAP2 inversion is 7th bit
                xmlobject.set_chip_setting_by_modulename(module, chip, 'CML_CONFIG', str(cml_cfg) )
                xmlobject.save_xml_as(xmlfile_for_ber)

                # assemble the OS command
                if mode is 'time': tuningstepname = 'prbstime'
                elif mode is 'frames': tuningstepname = 'prbsframes'
                else: raise AttributeError('Function \'run_ber_scan()\' received invalid argument for \'mode\': %s. Must be \'time\' or \'frames\'' % mode)
                command_p = 'CMSITminiDAQ -f %s p' % (xmlfile_for_ber)
                command_ber = 'CMSITminiDAQ -f %s -c %s %i BE-FE 2>&1 | tee %s' % (xmlfile_for_ber, tuningstepname, value, os.path.join(logfolder, 'ber_%s_%s_chip%i_pos%s_%i_%i_%i.log' % (ring, module, chip, str(positions[moduleidx]), tap0, tap1, tap2)))

                # execute the OS command
                print(command_p)
                os.system(command_p)
                time.sleep(1)
                print(command_ber)
                os.system(command_ber)
                time.sleep(2)




def reset_all_settings():
    reset_txt_files()
    for type in daqsettings_per_xmltype:
        reset_singleQuad_xml_files(type=type, modules=modulelist)
        prepare_singleQuad_xml_files(type_name=type, type_setting=type, modules=modulelist)
        reset_and_prepare_Ring_xml_file(type, type, ids_and_chips_per_module_R1, 'R1')
        reset_and_prepare_Ring_xml_file(type, type, ids_and_chips_per_module_R3, 'R3')
    reset_and_prepare_Ring_xml_file('ber', 'scurve', ids_and_chips_per_module_R1, 'R1')
    reset_and_prepare_Ring_xml_file('ber', 'scurve', ids_and_chips_per_module_R3, 'R3')
    print('--> Reset all xml and txt settings.')


def reset_txt_files(modules=modulelist, chips=chiplist):
    for module in modules:
        for chip in chips:
            targetname = os.path.join(txtfolder, 'CMSIT_RD53_%s_chip%i_default.txt' % (module, chip))
            sh.copy2(txtfile_blueprint, targetname)




def reset_singleQuad_xml_files(type, modules=modulelist, chips=chiplist):
    xmlobject = XMLInfo(xmlfile_blueprint)
    xmlobject.set_module_attribute_by_moduleid(0, 'Id', 1)
    xmlobject.set_txtfilepath_by_moduleid(1, txtfolder)
    for chip in chiplist:
        if chip == 0: continue
        xmlobject.copy_chip_by_moduleid(1, 0, chip)
    for module in modules:
        targetname = os.path.join(xmlfolder,'CMSIT_singleQuad_%s_%s.xml' % (module, type))
        xmlobject.save_xml_as(targetname)




def reset_and_prepare_Ring_xml_file(type_name, type_setting, ids_and_chips_per_module, ring):

    xmlobject = XMLInfo(xmlfile_blueprint)

    for setting in daqsettings_per_xmltype[type_setting]:
        xmlobject.set_daq_settings(setting, daqsettings_per_xmltype[type_setting][setting])

    # set up all modules
    moduleids = []
    for mod in ids_and_chips_per_module:
        moduleids.append(ids_and_chips_per_module[mod][0])
    for id in moduleids:
        if id == 0: continue
        xmlobject.copy_module_by_moduleid(0, id)
        xmlobject.set_txtfilepath_by_moduleid(id, txtfolder)
    xmlobject.keep_only_modules_by_moduleid(moduleids)

    # set up chips per module
    for module in ids_and_chips_per_module:
        id = ids_and_chips_per_module[module][0]
        chips = ids_and_chips_per_module[module][1]

        # first create all chips, then delete the unwanted ones
        for chip in [0,1,2,3]:
            if not chip == 0:
                xmlobject.copy_chip_by_moduleid(id, 0, chip)
            if ring == 'R1':
                xmlobject.set_chip_attribute_by_moduleid(id, chip, 'Lane', str(chip))
            elif ring == 'R3':
                xmlobject.set_chip_attribute_by_moduleid(id, chip, 'Lane', 0)
            else: raise AttributeError('invalid ring specified: %s' % (str(ring)))
            xmlobject.set_chip_attribute_by_moduleid(id, chip, 'configfile', 'CMSIT_RD53_%s_chip%i_default.txt' % (module, chip))
            if chip in chip_settings[module]:
                settings = chip_settings[module][chip]
                for setting in settings:
                    xmlobject.set_chip_setting_by_modulename(module, chip, setting, settings[setting])
        xmlobject.keep_only_chips_by_moduleid(id, chips)

    targetname = os.path.join(xmlfolder,'CMSIT_disk%s_%s.xml' % (str(ring), type_name))
    xmlobject.save_xml_as(targetname)



#PREPARE
def prepare_singleQuad_xml_files(type_name, type_setting, modules=modulelist):
    for module in modules:
        xmlfilename = os.path.join(xmlfolder, 'CMSIT_singleQuad_%s_%s.xml' % (module, type_name))
        xmlobject = XMLInfo(xmlfilename)
        for setting in daqsettings_per_xmltype[type_setting]:
            xmlobject.set_daq_settings(setting, daqsettings_per_xmltype[type_setting][setting])
        for chip in chiplist:
            xmlobject.set_chip_attribute_by_moduleid(1, chip, 'Lane', str(chip)) # the lane corresponds to the chip ID on the single AB
            xmlobject.set_chip_attribute_by_moduleid(1, chip, 'configfile', 'CMSIT_RD53_%s_chip%i_default.txt' % (module, chip))

        chip_settings_thismodule = chip_settings[module]
        keepchips = []
        for chip in chip_settings_thismodule:
            settings = chip_settings_thismodule[chip]
            for setting in settings:
                xmlobject.set_chip_setting_by_modulename(module, chip, setting, settings[setting])
        xmlobject.keep_only_chips_by_modulename(module, chip_settings_thismodule.keys())
        xmlobject.save_xml_as(xmlfilename)







def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)


if __name__ == '__main__':
    main()
