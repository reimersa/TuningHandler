from .events import subscribe, post_event 

class scan_parser(ABC):

    @abstractmethod
    def parse_data(scan, data): -> dict
        pass


    
