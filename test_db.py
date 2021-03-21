import tuning_db
import run_tuning
import unittest
import os

class DBTester(unittest.TestCase):

    test_log_file_name = "log/example_ber_R7_mod987654321_chip12_pos200_2000_1800_90000.log"
    db_path = '.testing_db_path_do_not_use/'
    test_db_name = 'test_db.json'

    def setUp( self ):
        if not os.path.exists( self.db_path ):
            os.mkdir( self.db_path )
        self.test_db_full_pathname = os.path.join( self.db_path, self.test_db_name)

    def test_add_data( self ):
        db = tuning_db.TuningDataFrame() 
        info = run_tuning.get_all_info_from_logfile( self.test_log_file_name )
        db.add_data( [ info ] )

        self.assertEqual( db.number_of_entries(), 1 )

    def test_write( self ):

        info = run_tuning.get_all_info_from_logfile( self.test_log_file_name )
        db_1 = tuning_db.TuningDataFrame()
        db_1.add_data( [ info ] )

        if os.path.exists( self.test_db_full_pathname ): 
            os.remove( self.test_db_full_pathname )
        db_1.write( self.test_db_full_pathname )
        file_is_written = os.path.exists( self.test_db_full_pathname)

        self.assertTrue( file_is_written )

    def test_write_and_read( self ):
        info = run_tuning.get_all_info_from_logfile( self.test_log_file_name )
        db_1 = tuning_db.TuningDataFrame()
        db_1.add_data( [ info ] )
        db_1.write( self.test_db_full_pathname )
        
        db_2 = tuning_db.TuningDataFrame()
        db_2.add_from_file( self.test_db_full_pathname )
        db1_in_db2 = db_1.isin(db_2).all().all()

        self.assertTrue( db1_in_db2, f'The saved dbatabase,\n {db_1}\n is not found in the loaded one,\n{db_2}' )
    
            


if __name__=='__main__':
    
    unittest.main()
