from abc import ABC, abstractmethod

class Persistifier(ABC):

    @abstractmethod
    def update(self, scan_data):
        pass

class DummyPersistifier(Persistifier):

    def update(self, scan_data):
        pass

class PrintPersistifier(Persistifier):

    def update(self, scan_data):
        print(scan_data)
