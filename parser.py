import ROOT
import re
from abc import abstractmethod
import utils as uu



class Parser():
    """Parse sources of information and return relevant info in a dictionary format."""

    def __init__(self, attribute_getters):
        self._getters = attribute_getters
        self._info = {}

    def parse(self, data):
        for getter in self._getters: 
            self._info[getter.name] = getter.get(data) 
        return self._info

class LogFileParser(Parser):
    
    def parse(self, logfile_name):
        with open(logfile_name, 'r') as f:
            lines = None
            try:
                lines = f.readlines()
            except Exception as e:
                print(f'''Caught an exception while reading log file {logfile_fname}.
                        The error was:\n{e}''')

            if lines is not None:
                for l in lines:
                    l = uu.escape_ansi(l)
                    for getter in self._getters:
                        getter.read_line(l)

        self._info[getter.name] = getter.get(None)
        return self._info


class InfoGetter():
    """Simple class with a routine for retrieving a single piece of information, and a name for that information."""

    def __init__(self, name):    
        self.name = name

    @abstractmethod
    def get(self, data):
        pass

class LogFileGetter(InfoGetter):
    """InfoGetter for getting information out of LogFiles. Initializes to a default value of None, which can be updated in the read_line method."""

    def __init__(self, name):
        super().__init__(name)
        self._value = None

    def get(self, data):
        return self._value

    @abstractmethod
    def read_line(self, line):
        pass
    

class ThresholdGetter(InfoGetter):
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
   
class RunNumberGetter(InfoGetter):
    """Get the last RunNumber."""
    
    def get(self, data):
        return uu.get_last_runnr()

class BERGetter(LogFileGetter):
    """Get Number of Bit Errors from a BER test Log File."""

    def read_line(self, l):
        if 'Final counter:' in line:
            self._value = uu.safe_convert( l.split()[-4], int, 'NBER') 

class NFramesGetter(LogFileGetter):
    """Get Number of Frames sent in a BER test from a Log File."""

    def read_line(self, l):
        if 'Final number of PRBS frames sent:' in l:
           self._value = uu.safe_convert( l.split()[-1], int, 'NFrames')

class UplinkSpeedGetter(LogFileGetter):
    """Get the Uplink Speed from a Log File."""

    def read_line(self, line):
        if 'Up-link speed:' in l:
            speed = uu.safe_convert( l.split()[-2], float, 'Up-link Speed')
            units = l.split(' ')[-1].strip() #should be either Gbit/s or Mbit/s 
            if units == 'Gbit/s':
            	pass #use 'Gbit/s as default unit'
            elif units == 'Mbit/s':
            	speed /= 1000
            else:
                speed = -1	
        self._value = speed
                    
class BERMetaDataGetter(InfoGetter):

    def get(self, fname):
        basename_no_ext = os.path.splitext(os.path.basename( fname ))[0]
        fields = basename_no_ext.split("_")

        #index from the back so things can be added to the front
        settings = {
            'TAP2' : uu.safe_convert(fields[-1], int, 'TAP2'),    
            'TAP1' : uu.safe_convert(fields[-2], int, 'TAP1'),
            'TAP0' : uu.safe_convert(fields[-3], int, 'TAP0'),
            'Pos'  : fields[-4].strip('pos'),
            'Chip' : uu.safe_convert(fields[-5].strip('chip'), int, 'Chip' ),
            'Module' : fields[-6],
            'Ring'   : fields[-7]
            }
        return settings

class ChipSpecificLogFileGetter(LogFileGetter):
    "For getting information identified with particular chips from a log file."

    default_chipId = (-1, -1, -1, -1)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._chipId = self.default_chipId
        self._value = {}

    def read_line(self, l):
        self.check_for_chip_id( l ) 
        if self.has_valid_chip_id():
            self.update_values( l )

    def has_valid_chip_id(self):
        return all( _id >= 0 for _id in self._chipId )

    @abstractmethod
    def check_for_chip_id(self, l ):
        pass

    @abstractmethod
    def update_values(self, l ):
        pass

class InitMaskedPixGetter(ChipSpecificLogFileGetter):
    """Get the number of initially masked pixels for a given chip, at the time of scan configuration, from a log file."""

    default_chipId = (-1, -1, 0, 0)

    def check_for_chip_id(self, l):
        if 'Configuring chip of hybrid:' in l: #Identifying the hybrid
            hybrid = uu.safe_convert(l.split()[-1], int, 'hybridId')
            self._chipId = ( self._chipId[0], hybrid, self._chipId[2], self._chipId[3])
        
        elif 'Configuring RD53:' in l: #Identifying the chip

            chip = uu.safe_convert(l.split()[-1], int, 'chipId')
            self._chipId = ( chip, self._chipId[1], self._chipId[2], self._chipId[3])

    def update_values(self, l):
        if 'Number of masked pixels:' in l: #masked pixels
                if not self._chipId in self._value.keys():
                    self._value[self._chipId] = {}
                self._value[self._chipId] = uu.safe_convert(l.split()[-1], int, 'maskedPixels')

class MonitorLogGetter(ChipSpecificLogFileGetter):

    def check_for_chip_id( self, l):
        if 'Monitor data for' in l: #Identifying the chip
            m = re.search('(?P<board>\d*)/(?P<og>\d*)/(?P<hybrid>\d*)/(?P<chip>\d*)', l )
            if m is not None:
                ids = tuple([  uu.safe_convert( m.group(obj), int, obj) for obj in ['board','og','hybrid','chip'] ])
                if not None in ids:
                    self._chipId = ids
                else:
                    #this shouldn't ever happen, if it does reset to default IDs, since we don't know the status
                    print(f'WARNING: There may be an issue with the regex parsing of chip IDs')
                    self._chipId = self.default_chipId

class TemperatureGetter(MonitorLogGetter):
    """Gets Temperatures of all sensors stored in a Monitoring Log File."""
    
    def update_values(self, l):
        if 'TEMPSENS_' in l: 
            m = re.search('(?P<sensid>TEMPSENS_\d):(?P<temp>[^+]*)', l)
            if m is not None:
                sens = m.group('sensid')
                temp = uu.safe_convert( m.group('temp').strip(), float, 'temp') 
                if temp is not None:
                    if not self._chipId in self._value:
                        self._value[self._chipId] = {}
                    self._value[self._chipId][sens] = temp
            else:
                #This shouldn't ever happen
                print(f'WARNING: There may be an issue with the regex parsing of temperatures')
        
class VoltageGetter(MonitorLogGetter):
    """Gets Voltages (VDDD/VDDA) of all chips stored in a Monitoring Log File."""
    
    def update_values(self, l):
        if 'VOUT_' in l: #shuntLDO values
            m = re.search('(?P<Vtype>VOUT[^:\s]*ShuLDO):(?P<voltage>[^+]*)', l)
            if m is not None:
                vsource = m.group('Vtype')
                voltage = uu.safe_convert( m.group('voltage').strip(), float,  'voltage')
                if voltage is not None: 
                    voltage *= 2 #multiply by 2 because for some reason the printed values are half of the actual ones?
                    if not self._chipId in self._value:
                        self._value[self._chipId] = {}
                    self._value[self._chipId][vsource] = voltage
            else:
                #there are some messages printed about the VOUT which don't actually containt the info, we want 
                #"	--> Hybrid voltage: 0.000 V (corresponds to half VOUT_dig_ShuLDO of the chip)"
                pass
        
