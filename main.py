from abc import ABC
        
def run_scan( execute, parser, updater, persistifier):

    scan_output = executer.run()
    parsed_data = parser.parse(scan_output)
    updater.update( scan_output )
    persistifier.update( parsed_data )

class Scan(ABC):
    
    @abstractmethod
    def run(self):
        pass

class CMSItDAQScan(Scan):

    def __init__(self, scan_type, xml_file, log_file):
        self._type = scan_type
        self._xml_file = xml_file
        self._log_file

    def run(self):
        cmd = 'CMSITminiDAQ -f {sw_config.xml_file()} -c {self._type}'
        log_cmd = '| tee {self._log_file}'
        os.system(f'{cmd} {log_cmd}')
        return self._log_file
        

def BERScanFactory( hw_setup, 

if __name__ == '__main__':

    log_file_name = 
    execute = CMSItDAQScan( 'ber', 
