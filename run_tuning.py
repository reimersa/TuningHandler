#! /usr/bin/env python
import os, re
import time
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
# xmlfile_blueprint = '/home/tepx/Desktop/Arne_fresh/Ph2_ACF/settings/CMSIT.xml'
xmlfile_blueprint = 'xml/CMSIT.xml'
# txtfile_blueprint = '/home/tepx/Desktop/Arne_fresh/Ph2_ACF/settings/RD53Files/CMSIT_RD53.txt'
txtfile_blueprint = 'txt/CMSIT_RD53.txt'


chiplist = [0, 1, 2, 3]
modulelist = ['mod3', 'mod4', 'mod6', 'mod7', 'modT01', 'modT02', 'modT03', 'modT04']


ids_and_chips_per_module_R1 = {
    'mod4': (0, [0]),
    'mod6': (2, [0]),
    'mod7': (1, [0, 1, 2])
}

ids_and_chips_per_module_R3 = {
    'mod7': (1, [3])
}
















def main():

    # reset_all_settings()


    # now run many BER tests
    tap_settings = []
    #for tap0 in ([80, 90] + range(100, 1000, 100) + [1023]):
    for tap0 in [80, 90, 100]:
        for tap1 in range(0, 100+1, 25):
            #if tap1 > tap0: continue
            for tap2 in range(0, 100+1, 25):
                #if tap2 > tap0 or tap2 > tap1: continue
                tap_settings.append((tap0, tap1, tap2))
    run_ber_scan(modules=['mod7'], chips=[0], ring='R1', tap_settings=tap_settings)
    # plot_ber_results(module=module_for_ber, chip=chip_for_ber, tap_settings=tap_settings)
















def plot_ber_results(module, chip, tap_settings, groupby = 'TAP0'):

    # group by tap0
    tapdict = {}
    xvalues = []
    yvalues = []
    for tap0, tap1, tap2 in sorted(tap_settings):
        logfilename = os.path.join(logfolder, 'ber_%i_%i_%i.log' % (tap0, tap1, tap2))
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
    ber_arrays = {}
    for key in tapdict.keys():
        ordered_list = []
        for(key1, key2) in sorted(tapdict[key].keys()):
            nframes = tapdict[key][(key1, key2)][0]
            ber_abs = tapdict[key][(key1, key2)][1]

            if nframes <= 0 or ber_abs < 0:
                ber_rel = -1
                minvalue = -1
            else:
                minvalue = np.float64(1)/np.float64(nframes)
                ber_rel = max(minvalue, (np.float64(ber_abs) / np.float64(nframes)))
            #ordered_list.append(tapdict[key][(key1, key2)][1])
            ordered_list.append(ber_rel)
        ber_arrays[key] = (np.array(ordered_list).reshape(len(xvalues), len(yvalues)))
        print ber_arrays[key]

        fig, ax = plt.subplots(figsize=(12,4))
        im = ax.imshow(ber_arrays[key], aspect='auto', origin='lower', cmap=plt.cm.get_cmap('Blues', 100))
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
                val = ber_arrays[key][i,j]
                if val > 0.6 * np.max(ber_arrays[key]):
                    color = 'white'
                else:
                    color = 'black'
                ax.text(i, j, '{:.1e}'.format(val) if val else '0', ha='center', va='center', color=color)



        outfilename = os.path.join(plotfolder, 'BER_%s_%i.pdf' % (groupby, key))
        fig.savefig(outfilename)
        fig.savefig(outfilename.replace('.pdf', '.png'))
        plt.close(fig)







def run_ber_scan(modules, chips, ring, tap_settings=[], mode='time', value=10):

    # first, enable TAP1, TAP2
    if ring == 'singleQuad':
        if not len(modules) == 1: raise AttributeError('Trying to run BER in singleQuad mode with mode than one module')
        module = modules[0]
        xmlfile_for_ber = os.path.join(xmlfolder, 'CMSIT_%s_%s_%s.xml' % (ring, module, 'ber'))
        reset_singleQuad_xml_files(type='ber', modules=modules, chips = chips)
        prepare_singleQuad_xml_files(type_name='ber', type_setting='scurve', modules=modules)
    elif ring == 'R1' or ring == 'R3':
        xmlfile_for_ber = os.path.join(xmlfolder, 'CMSIT_disk%s_%s.xml' % (ring, 'ber'))
        reset_and_prepare_Ring_xml_file('ber', 'scurve', ids_and_chips_per_module_R1, ring)

    xmlobject = XMLInfo(xmlfile_for_ber)
    xmlobject.keep_only_modules_by_modulename(modules)
    for module in modules:
        xmlobject.keep_only_chips_by_modulename(module, chips)
        for chip in chips:
            xmlobject.set_chip_setting_by_modulename(module, chip, 'CML_CONFIG', '127')

    # now, in a loop, set TAP values to scan through
    for tap0, tap1, tap2 in tap_settings:
        print(tap0, tap1, tap2)
        for module in modules:
            for chip in chips:
                xmlobject.set_chip_setting_by_modulename(module, chip, 'CML_TAP0_BIAS', str(tap0))
                xmlobject.set_chip_setting_by_modulename(module, chip, 'CML_TAP1_BIAS', str(tap1))
                xmlobject.set_chip_setting_by_modulename(module, chip, 'CML_TAP2_BIAS', str(tap2))
        xmlobject.save_xml_as(xmlfile_for_ber)

        # assemble the OS command
        if mode is 'time': tuningstepname = 'prbstime'
        elif mode is 'frames': tuningstepname = 'prbsframes'
        else: raise AttributeError('Function \'run_ber_scan()\' received invalid argument for \'mode\': %s. Must be \'time\' or \'frames\'' % mode)
        command = 'CMSITminiDAQ -f %s -c %s %i 2>&1 | tee %s' % (xmlfile_for_ber, tuningstepname, value, os.path.join(logfolder, 'ber_%s_%i_%i_%i.log' % (ring, tap0, tap1, tap2)))

        # execute the OS command
        print(command)
        # os.system(command)
        # time.sleep(2)




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
        for chip in chip_settings_thismodule:
            settings = chip_settings_thismodule[chip]
            for setting in settings:
                xmlobject.set_chip_setting_by_modulename(module, chip, setting, settings[setting])
        xmlobject.save_xml_as(xmlfilename)







def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)


if __name__ == '__main__':
    main()
