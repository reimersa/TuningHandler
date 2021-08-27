import ROOT
from dataclasses import dataclass
import os

@dataclass
class ChipId:
    chip: int
    hybrid: int
    board: int
    optical_group: int

class OpenRoot:

    def __init__(self, fname, mode):
        self.fhandle = ROOT.TFile.Open(fname, mode)

    def __enter__(self):
        return self.fhandle

    def __exit__(self, type, value, traceback):
        self.fhandle.Close()
    


class CanvasNotFoundError(Exception):
    pass

@dataclass
class RootScanResult:
    run_number: int
    scan_type: str
    directory: str = './'


    @property
    def filename(self):
        return os.path.join( self.directory, f'Run{self.run_number:06d}_{self.scan_type}.root')

    _hist_types = { }
    #def _get_scan_type(self):
    #    return self.flename.split('_')[-1][:-5]
    #
    #def _get_run_number(self):
    #    return self.fname.split('Run')[0].split('_')[0]

    def _get_directory_name( self, chip=0, hybrid=0, optical_group=0, board=0):
        return f'Detector/Board_{board}/OpticalGroup_{optical_group}/Hybrid_{hybrid}/Chip_{chip}' 

    def _get_hist_name(self, hist_type, chip=0, hybrid=0, optical_group=0, board=0  ):
        base_name = f'D_B({board})_O({optical_group})_H({hybrid})'
        chip_name = f'Chip({chip})'
        scan_name = self._hist_types.get(hist_type, hist_type)
        return f'{base_name}_{scan_name}_{chip_name}'

    def get_hist(self, hist_type, **chipId):
        histname = self._get_hist_name( hist_type, **chipId )
        tcanvas = self._get_canvas( hist_type, **chipId) #rf.Get( canvasname )
        try:
            hist = tcanvas.GetPrimitive( histname )    
        except AttributeError as e:
            raise CanvasNotFoundError(f'While Trying to access TCanvas {canvasname} in file {self.filename}, encountered the following error {e}')
        hist.SetDirectory(0)
        return hist

    def _get_canvas(self, hist_type, **chipId):
        dirname = self._get_directory_name( **chipId )
        histname = self._get_hist_name( hist_type, **chipId )
        canvasname = f'{dirname}/{histname}'
        with OpenRoot(self.filename, "READ") as rf:
            tcanvas = rf.Get( canvasname )
        return tcanvas
        
    def _get_tgaxis_axis( self, scan_type, **chipId):
        tcanvas = self._get_canvas( scan_type, **chipId)
        primitives =  tcanvas.GetListOfPrimitives()
        ret = None
        for prim in primitives:
            if isinstance(prim, ROOT.TGaxis):
                ret = prim
        return ret


    class NoVcalToEleConversionForScanError(Exception):
        pass

    def get_vcal_to_ele_function( self, scan_type, **chipId):
        known_scans = ['Noise1D','Threshold1D']
        if not scan_type in known_scans:
            raise NoVcalToEleConversionForScanError(f'''vcal to ele conversion cant be done for scan_type {scan_type},
                                                         only known types are {known_scans}''')
        axis = self._get_tgaxis_axis( scan_type, **chipId )
        ele_min = axis.GetWmin()
        ele_max = axis.GetWmax()
        vcal_min = axis.GetX1()
        vcal_max = axis.GetX2()
        ele_to_vcal_ratio = (ele_max - ele_min) / (vcal_max - vcal_min)
        def vcal_to_ele( vcal ):
            vcal_loc = vcal - vcal_min
            ele = (vcal_loc * ele_to_vcal_ratio) + ele_min
            return ele
        return vcal_to_ele
        


if __name__=='__main__':

    fname = 'archive/68925/Results/Run068925_SCurve.root'
    scan_result = RootScanResult(68925,'SCurve','archive/68925/Results/')
    for chip in [0,1,2]:
        noise_hist = scan_result.get_hist( 'Threshold1D', chip=chip, hybrid=0, board=0, optical_group=0 )
        mean = noise_hist.GetMean()
        print(f'{mean} +/- {noise_hist.GetStdDev()}')
        convert_func = scan_result.get_vcal_to_ele_function( chip=chip )
        ele_mean = convert_func(mean)
        ele_dev = convert_func(noise_hist.GetStdDev())
        print(f'in electrons: {ele_mean} +/- {ele_dev}')

