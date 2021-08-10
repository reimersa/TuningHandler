from abc import ABC, abstractmethod
import tuning_db as tdb

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

class TuningDBPersistifier(Persistifier):

    def __init__(self, db_file):
        self._db = tdb.TuningDataBase(db_file)

    def update(self, scan_data): 
        self._db.add_data( scan_data )
