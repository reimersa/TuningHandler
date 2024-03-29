#! /usr/bin/env python3
import os, re, glob
import time, math
import numpy as np
import shutil as sh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import json
from yaml import safe_load

import ROOT
from ROOT import TFile, TH1D, TCanvas, TIter


from XMLInfo import *
from settings.typesettings import *
#from settings.chipsettings import *


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
    #'mod11': (1, [3]),
    #'mod9':  (2, [3]),
    #'mod10': (3, [3])
    #'mod3':   (1, [3]),
    'modT03': (2, [3]),
    'mod7':   (3, [3]),
}
















def main():
    
    mod_for_tuning = 'modT04'
    ring_for_tuning = 'singleQuad'
    prefix_plotfolder = 'modT04_coated'
    
    reset_all_settings()
    #run_reset(ring=ring_for_tuning, module=mod_for_tuning)
    #run_programming(ring=ring_for_tuning, module=mod_for_tuning)
    #run_calibration(ring=ring_for_tuning, module=mod_for_tuning, calib='physics')
    
    if ring_for_tuning == 'singleQuad': plotfolderpostfix = ''
    elif ring_for_tuning == 'R1': plotfolderpostfix = '_'.join([mod for mod in ids_and_chips_per_module_R1.keys()])
    elif ring_for_tuning == 'R3': plotfolderpostfix = '_'.join([mod for mod in ids_and_chips_per_module_R3.keys()])
    else: raise ValueError('Invalid \'ring_for_tuning\' specified: %s' % (ring_for_tuning))
    
    run_threshold_tuning(module=mod_for_tuning, ring=ring_for_tuning, plotfoldername=prefix_plotfolder+plotfolderpostfix)
    
    
    
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


def run_threshold_tuning(module, ring, plotfoldername):
	reset_xml_files()
	reset_txt_files()
	
	module_per_id = {}
	if not ring == "singleQuad":
		if ring == 'R1':
			id_per_module = ids_and_chips_per_module_R1
		elif ring == 'R3':
			id_per_module = ids_and_chips_per_module_R3
		else: raise ValueError('Invalid value of \'ring\': %s' % (ring))
		for modkey in id_per_module:
			id = id_per_module[modkey][0]
			module_per_id[id] = modkey
	else: 
		id_per_module = {module: 1} # single modules are always in J1 (second from the left)
		module_per_id = {1: module}
		
	# reset all VThreshold_LINs to 400
	for module in id_per_module:
		fresh_thresholds = {}
		if ring == 'SingleQuad':
			for chip in chiplist:
				fresh_thresholds[chip] = '400'
		elif ring == 'R1' or ring == 'R3':
			for chip in id_per_module[module][1]:
				fresh_thresholds[chip] = '400'
		set_thresholds_for_module(module=module, thresholds=fresh_thresholds)
	print('Reset all VThreshold_LIN to 400.')
	
	reset_xml_files()
	run_calibration(ring=ring, module=module, calib='pixelalive')
	#run_calibration(ring=ring, module=module, calib='threqu')
	#run_calibration(ring=ring, module=module, calib='noise')
	run_calibration(ring=ring, module=module, calib='thradj')
		
		
	thresholds_per_id_and_chip = get_thresholds_from_last()
	for id in thresholds_per_id_and_chip:
		set_thresholds_for_module(module=module_per_id[id], thresholds=thresholds_per_id_and_chip[id])
		print('set the following thresholds for module %s with id %s: '% (module_per_id[id], str(id)), thresholds_per_id_and_chip[id])
		
	reset_xml_files()
	run_calibration(ring=ring, module=module, calib='threqu')
	run_calibration(ring=ring, module=module, calib='noise')
	run_calibration(ring=ring, module=module, calib='scurve')
	plot_ph2acf_rootfile(runnr=get_last_runnr(), module_per_id=module_per_id, plotfoldername=plotfoldername)

def get_last_runnr():
	#file 'RunNumber.txt' contains number the next run would have, nothing else.
	with open('RunNumber.txt', 'r') as f:
		runnr = int(f.readlines()[0]) - 1
	return runnr

def set_thresholds_for_module(module, thresholds):
	# get chipsettings, change VThreshold_LIN, write chipsettings
	# 'thresholds' is a dictionary with one entry per chip, maximum 4 entries
	if len(thresholds.keys()) > 4: raise AttributeError('Threshold dictionary is too long for a single module.')
	settings = get_chipsettings_from_json()
	for chip in thresholds.keys():
		settings[module][str(chip)]['Vthreshold_LIN'] = str(thresholds[chip])
	write_chipsettings_to_json(settings)
	


def get_thresholds_from_last():
	# last run has highest run-number and must have 'ThrAdjustment' in name
	files = [f for f in glob.glob(os.path.join('Results', '*.root')) if 'ThrAdjustment' in f]
	
	# list is unordered
	runnrs = [int(n.split('_')[0].split('Run')[1]) for n in files]
	maxidx = runnrs.index(max(runnrs))
	lastfilename = files[maxidx]
	print(lastfilename)
	infile = TFile(lastfilename, 'READ')
	foldername = 'Detector/Board_0/OpticalGroup_0/'
	infile.cd(foldername)
	dir = ROOT.gDirectory
	iter = TIter(dir.GetListOfKeys())
	modules = [key.GetName() for key in ROOT.gDirectory.GetListOfKeys()]
	
	thresholds_per_id_and_chip = {}
	for module in modules:
		thresholds_per_id_and_chip[int(module.split('_')[1])] = {}
		histpath = foldername + module
		infile.cd()
		infile.cd(histpath)
		chips = [key.GetName() for key in ROOT.gDirectory.GetListOfKeys()]
		print(module, chips)
		
		for chip in chips:
			mod_dummy = module
			chip_dummy = chip
			fullhistpath = os.path.join(histpath, chip)
			infile.cd()
			infile.cd(fullhistpath)
			
			objs = [key.GetName() for key in ROOT.gDirectory.GetListOfKeys()]
			infile.cd()
			for objname in objs:
				if not 'Threhsold' in objname: continue
				canvas = infile.Get(os.path.join(fullhistpath, objname))
				hist = canvas.GetPrimitive(objname)
				vthresh = int(hist.GetBinCenter(hist.GetMaximumBin()) - hist.GetBinWidth(hist.GetMaximumBin())/2.)
				thresholds_per_id_and_chip[int(module.split('_')[1])][int(chip.split('_')[1])] = vthresh
	del infile
	return thresholds_per_id_and_chip
				
	

def write_chipsettings_to_json(settings):
	jsonname = os.path.join('settings','chipsettings.json')
	with open(jsonname, 'w') as j:
		json.dump(obj=settings, fp=j, indent=2, sort_keys = True)
		
def get_chipsettings_from_json():
	jsonname = os.path.join('settings','chipsettings.json')
	result = {}
	with open(jsonname, 'r') as j:
		result = safe_load(j)
	return result
	


def plot_ph2acf_rootfile(runnr, module_per_id, plotfoldername, tag=''):
	ROOT.gROOT.SetBatch(True)
	
	runnrstr = '%06i' % runnr
	infilepattern = 'Results/Run%s_*.root' % runnrstr
	
	matches = glob.glob(infilepattern)
	if len(matches) > 1:
		raise ValueError('Trying to plot histograms in rootfile for runnr. %i, but there is more than one file found with the pattern \'Run%s_*.root\': '% (runnrstr) + matches )
	infilename = matches[0]
	
	infile = TFile(infilename, 'READ')
	foldername = 'Detector/Board_0/OpticalGroup_0/'
	infile.cd(foldername)
	dir = ROOT.gDirectory
	iter = TIter(dir.GetListOfKeys())
	modules = [key.GetName() for key in ROOT.gDirectory.GetListOfKeys()]
	
	for module in modules:
		histpath = foldername + module
		moduleid = int(module.replace('Hybrid_', ''))
		modulename = module_per_id[moduleid]
		infile.cd()
		infile.cd(histpath)
		chips = [key.GetName() for key in ROOT.gDirectory.GetListOfKeys()]
		
		for chip in chips:
			chip_dummy = chip
			fullhistpath = os.path.join(histpath, chip)
			infile.cd()
			infile.cd(fullhistpath)
			
			canvases = [key.GetName() for key in ROOT.gDirectory.GetListOfKeys()]
			infile.cd()
			for canvasname in canvases:
				if canvasname == 'Channel': continue
				canvas = infile.Get(os.path.join(fullhistpath, canvasname))
				hist   = canvas.GetPrimitive(canvasname)
				canvastitle = canvasname.split('_')[4] + '_' + chip
				outcanvas = TCanvas('c', canvastitle, 500, 500)
				if 'SCurves' in canvastitle:
					ROOT.gPad.SetLogz()
				hist.Draw('colz')
				ROOT.gStyle.SetOptStat(0);
				outdir = os.path.join('plots', 'thresholds', plotfoldername, '')
				outfilename = canvastitle + tag + '.pdf'
				outfilename = outfilename.replace('Chip_', '%s_chip' % (modulename))
				ensureDirectory(outdir)
				outcanvas.SaveAs(outdir + outfilename)
				outcanvas.SaveAs(outdir + outfilename.replace('pdf', 'png'))
	del infile
	


def run_programming(ring, module):
	xmlfilename = get_xmlfile_name(ring=ring, module=module, calib='scurve')
	command = 'CMSITminiDAQ -f %s -p' % (os.path.join(xmlfolder, xmlfilename))
	print(command)
	os.system(command)
	
def run_reset(ring, module):
	xmlfilename = get_xmlfile_name(ring=ring, module=module, calib='scurve')
	command = 'CMSITminiDAQ -f %s -r' % (os.path.join(xmlfolder, xmlfilename))
	print(command)
	os.system(command)
	
def run_calibration(ring, module, calib):
	xmlfilename = get_xmlfile_name(ring=ring, module=module, calib=xmltype_per_calibration[calib])
	command = 'CMSITminiDAQ -f %s -c %s' % (os.path.join(xmlfolder, xmlfilename), calib)
	print(command)
	os.system(command)


def get_results_from_logfile( fname ):

    nframes = -1
    nber    = -1
    with open( fname, 'r') as f:
        lines = f.readlines()
        for l in lines:
            l = escape_ansi(l)
            if 'Final number of PRBS frames sent:' in l:
                nframes = int(l.split(' ')[-1])
            elif 'Final BER counter:' in l:
                nber = int(l.split(' ')[-1])
    return (nframes, nber)

def get_settings_from_logfile( fname ):
    basename_no_ext = os.path.splitext(os.path.basename( fname ))[0]
    fields = basename_no_ext.split("_")

    #index from the back so things can be added to the front
    settings = {
        'TAP2' : int(fields[-1]),    
        'TAP1' : int(fields[-2]),
        'TAP0' : int(fields[-3]),
        'Pos'  : fields[-4].strip('pos'),
        'Chip' : int(fields[-5].strip('chip')),
        'Module' : fields[-6],
        'Ring'   : fields[-7]
        }
    return settings

def get_all_info_from_logfile( fname ):

    all_info = get_settings_from_logfile( fname )
    nframes, nber = get_results_from_logfile( fname )
    all_info.update( { 'NFrames' : nframes, 'NBER' : nber} )

    return all_info
    



def plot_ber_results(module, chip, ring, position, tap_settings, groupby = 'TAP0'):

    # group by tap0
    tapdict = {}
    xvalues = []
    yvalues = []
    for tap0, tap1, tap2 in sorted(tap_settings):
        logfilename = os.path.join(logfolder, 'ber_%s_%s_chip%i_pos%s_%i_%i_%i.log' % (ring, module, chip, str(position), tap0, tap1, tap2))
        nframes, nber = get_results_from_logfile( logfilename )

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
            print( key1, key2, ber_abs)

            if nframes <= 0 or ber_abs < 0:
                ber_rel = -1
                minvalue = -1
            else:
                minvalue = np.float64(1)/np.float64(nframes)
                ber_rel = np.float64(max(minvalue, (np.float64(ber_abs) / np.float64(nframes))))
                print('components: ', np.float64(ber_abs), np.float64(nframes), minvalue, np.float64(1), minvalue, ber_rel)
                
            ordered_list.append((ber_rel, minvalue))
        ber_and_minval_arrays[key] = (np.array([tup[0] for tup in ordered_list], dtype=np.float64).reshape(len(xvalues), len(yvalues)), np.array([tup[1] for tup in ordered_list], dtype=np.float64).reshape(len(xvalues), len(yvalues)))
        print( ber_and_minval_arrays[key])

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
                print( val, minvalue)
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
            print( module, chip)
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
                if mode == 'time': 
                    tuningstepname = 'prbstime'
                elif mode == 'frames': 
                    tuningstepname = 'prbsframes'
                else: 
                    raise AttributeError('Function \'run_ber_scan()\' received invalid argument for \'mode\': %s. Must be \'time\' or \'frames\'' % mode)
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
    reset_xml_files()


def reset_txt_files(modules=modulelist, chips=chiplist):
    for module in modules:
        for chip in chips:
            targetname = os.path.join(txtfolder, 'CMSIT_RD53_%s_chip%i_default.txt' % (module, chip))
            sh.copy2(txtfile_blueprint, targetname)
    print('--> Reset txt files')
            
def reset_xml_files():
    for type in daqsettings_per_xmltype:
        reset_singleQuad_xml_files(type=type, modules=modulelist)
        prepare_singleQuad_xml_files(type_name=type, type_setting=type, modules=modulelist)
        reset_and_prepare_Ring_xml_file(type, type, ids_and_chips_per_module_R1, 'R1')
        reset_and_prepare_Ring_xml_file(type, type, ids_and_chips_per_module_R3, 'R3')
    reset_and_prepare_Ring_xml_file('ber', 'scurve', ids_and_chips_per_module_R1, 'R1')
    reset_and_prepare_Ring_xml_file('ber', 'scurve', ids_and_chips_per_module_R3, 'R3')
    print('--> Reset XML files')




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
        if not id == 0: xmlobject.copy_module_by_moduleid(0, id)
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
                xmlobject.set_chip_attribute_by_moduleid(id, chip, 'Lane', str(0))
            else: raise AttributeError('invalid ring specified: %s' % (str(ring)))
            xmlobject.set_chip_attribute_by_moduleid(id, chip, 'configfile', 'CMSIT_RD53_%s_chip%i_default.txt' % (module, chip))
            chip_settings = get_chipsettings_from_json()
            if str(chip) in chip_settings[module]:
                settings = chip_settings[module][str(chip)]
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
        chip_settings = get_chipsettings_from_json()
        chip_settings_thismodule = chip_settings[module]
        keepchips = []
        for chip in chip_settings_thismodule:
            settings = chip_settings_thismodule[chip]
            for setting in settings:
                xmlobject.set_chip_setting_by_modulename(module, int(chip), setting, settings[setting])
        xmlobject.keep_only_chips_by_modulename(module, [int(c) for c in chip_settings_thismodule.keys()])
        xmlobject.save_xml_as(xmlfilename)



def get_xmlfile_name(ring, module, calib):
	modstr = ''
	ringstr = 'disk' + ring
	
	if ring == 'singleQuad':
		return '_'.join(['CMSIT', ring, module, calib]) + '.xml'
	else:
		return '_'.join(['CMSIT', 'disk' + ring, calib]) + '.xml'

def ensureDirectory(dirname):
	if not os.path.exists(dirname):
		os.makedirs(dirname)
		if not os.path.exists(dirname):
			print('--> Failed to create directory \'%s\'' % dirname)

def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)


if __name__ == '__main__':
    main()
