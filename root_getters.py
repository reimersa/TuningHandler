import ROOT

import utils as uu
import parser as pp

class ThresholdGetter(pp.InfoGetter):
    """Gets the suggested threshold from the most recent Threshold Adjustment Scan"""

    def get(self, data=None):
        lastfilename = uu.get_last_scan_file('ThrAdjustment')
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
   
