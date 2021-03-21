import tuning_db
import run_tuning
import unittest
import os

class DBTester(unittest.TestCase):

    test_log_file_name = "log/example_ber_R7_mod987654321_chip12_pos200_2000_1800_90000.log"
    db_path = '.testing_db_path_do_not_use/'
    test_db_name = 'test_db.json'

    def setUp( self ):
        #create some directories
        if not os.path.exists( self.db_path ):
            os.mkdir( self.db_path )
        self.test_db_full_pathname = os.path.join( self.db_path, self.test_db_name)

        #make a db from the fake log file 
        self.info = run_tuning.get_all_info_from_logfile( self.test_log_file_name )
        self.db1  = tuning_db.TuningDataFrame()
        self.db1.add_new_data( [ self.info ]  )

    def test_add_data( self ):

        has_entries = self.db1.number_of_entries() > 0
        self.assertTrue( has_entries )

    def test_write( self ):

        if os.path.exists( self.test_db_full_pathname ): 
            os.remove( self.test_db_full_pathname )

        self.db1.write( self.test_db_full_pathname )
        file_is_written = os.path.exists( self.test_db_full_pathname)

        self.assertTrue( file_is_written )

    def test_write_and_read( self ):
        if os.path.exists( self.test_db_full_pathname ):
            os.remove( self.test_db_full_pathname )

        self.db1.write( self.test_db_full_pathname )
        db2 = tuning_db.TuningDataFrame()
        db2.add_from_file( self.test_db_full_pathname )

        db1_in_db2 = self.db1.isin( db2 ).all().all()

        self.assertTrue( db1_in_db2, f'The saved dbatabase,\n {self.db1}\n is not found in the loaded one,\n{db2}' )
    
    def test_overwrite( self ):
        if os.path.exists( self.test_db_full_pathname ):
            os.remove( self.test_db_full_pathname )
        self.db1.write( self.test_db_full_pathname )

        db2 = tuning_db.TuningDataFrame() 
        db2.add_new_data( [ self.info ] )
        db2.add_from_file( self.test_db_full_pathname )
        backup_name = db2.overwrite( self.test_db_full_pathname )

        #test that the backup is written
        backup_exists = os.path.exists( backup_name )
        self.assertTrue( backup_exists, f'did not find the expected backup file "{backup_name}".' )
        
        #test that the backup has the old data
        backup_db = tuning_db.TuningDataFrame()
        backup_db.add_from_file( backup_name )
        backup_is_stored = (backup_db == self.db1 ).all().all()
        self.assertTrue( backup_is_stored, f'the backup file data \n{backup_db}\n, did not match the expected from original_file \n{self.db1}.' )

        #test that the new file has the new db
        stored_db = tuning_db.TuningDataFrame()
        stored_db.add_from_file( self.test_db_full_pathname )
        new_file_matches_db = ( stored_db == db2 ).all().all()
        self.assertTrue( new_file_matches_db, f'the new file data \n {stored_db},\n did not match the expected \n {db2}\n' )

        


if __name__=='__main__':
    
    unittest.main()
