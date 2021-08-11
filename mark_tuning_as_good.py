#!/usr/bin/env python3

import tuning_db as tdb
import os
import shutil
import re
import argparse

import plotting as pl


class RunAlreadyHasANameException(Exception):
    pass

class RunDoesntExist(Exception):
    pass


def check_runs_in_df(run_numbers, df):

    all_runs = df['RunNumber'].unique()
    for run in run_numbers:
        if run in all_runs:
            continue
        else:
            raise RunDoesntExist(f'Run {run} is not in the list of runnumbers in the database!')

def remove_names( db_file, run_numbers):

    db = tdb.TuningDataBase(db_file)    
    df = db.get_info()
    check_runs_in_df(run_numbers, df)

    row_spec = df['RunNumber'].isin(run_numbers)
    print(f'Removing names from runs {run_numbers}')
    print(f'their current names are {df[row_spec][["RunNumber","Name"]]}')
    df.loc[ df['RunNumber'].isin(run_numbers), 'Name'] = None
    db.overwrite_all( df )

def update_name( db_file, run_numbers, name):

    print(f'Naming runs {run_numbers} as "{name}"')
    db = tdb.TuningDataBase(db_file)    
    df = db.get_info()

    check_runs_in_df(run_numbers, df)
    row_spec = df['RunNumber'].isin(run_numbers)
    has_name = df[ row_spec ]['Name'].notnull().any()
    if has_name:
        raise RunAlreadyHasANameException(f'''Could not name all the runs, because some of them already
        have names. The runs selected runs/names are: \n {df[row_spec][["RunNumber","Name"]]}.''')
    df.loc[ df['RunNumber'].isin(run_numbers), 'Name'] = name
    db.overwrite_all( df )

def mark_runs_as_good_in_db( db_file, run_numbers, mark_bad=False):

    db = tdb.TuningDataBase(db_file)    
    df = db.get_info()
    check_runs_in_df(run_numbers, df)
    if 'IsArchived' in df.columns:
        if mark_bad:
            df['IsArchived'] = df['IsArchived'] & ( ~df['RunNumber'].isin(run_numbers) )
        else:
            df['IsArchived'] = df['IsArchived'] | ( df['RunNumber'].isin(run_numbers) )

    else:
        if mark_bad:
            df['IsArchived'] = False
        else:
            df['IsArchived'] = ( df['RunNumber'].isin(run_numbers) )
        
    db.overwrite_all( df )

class Archive():

    def __init__(self, main_dir):
        self._dir = main_dir

    @property
    def main_dir(self):
        return self._dir

    def run_dir(self, run):
        return os.path.join( self.main_dir, str(run) )

    def plot_dir(self, run):
        return os.path.join( self.run_dir(run), 'plots')

    def results_dir(self, run):
        return os.path.join( self.run_dir(run), 'Results')

    def make_run_dir(self, run, permissive=True):
        os.makedirs( self.run_dir(run), exist_ok=True)
        os.makedirs( self.plot_dir(run), exist_ok=True)
        os.makedirs( self.results_dir(run), exist_ok=True)

    def store_results(self, run, files ):
        for f in files:
           shutil.copy(f, self.results_dir(run) ) 

    #def store_plots(self, run, files):
    #    for f in files:
    #        shutil.copy(f, self.plot_dir(run) )


def archive_info( archive_dir, results_dir, run_numbers):
    archive = Archive(archive_dir)
    for run_number in run_numbers:
        archive.make_run_dir(run_number)

        results_files = get_result_files(run_number, results_dir )
        archive.store_results(run_number, results_files)

        make_plots( run_number, archive.plot_dir(run_number)  )

def get_result_files( run, results_dir):
    all_files = os.listdir(results_dir)
    run_files = [ f for f in all_files if re.search('Run0*{}'.format(run), f ) is not None ]
    full_paths = [ os.path.join(results_dir, f) for f in run_files ]
    return full_paths

def make_plots( run, output_dir):
    pl.plot_scurve_results(run,module_per_id='dummy',plotfoldername=output_dir)

        
    
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Mark a given run as good. Identify it in the database, and archive its files.')
    parser.add_argument('--db', dest='database', type=str, default='tuning_db/tuning.json',
            help='database file name. [default: %(default)s]')
    parser.add_argument('--plot-dir', default='plots/thresholds/default/',type=str, help='Directory with stored plots to archive. [default: %(default)s]' )
    parser.add_argument('--results',dest='results_dir', default='Results/', help='Directory with results files to archive. [default: %(default)s]')
    parser.add_argument('--archive',dest='archive_dir', default='archive/', help='Directory for archiving relevant files. [default: %(default)s]')
    parser.add_argument('--runs', dest='run_numbers', nargs='+', type=int, help='Space separated list of run numbers to mark as good.')
    parser.add_argument('--name', default=None, help="Mark these runs as bad instead of as good. [default: %(default)s]")
    parser.add_argument('--unname', action="store_true",default=False, help="Mark these runs as bad instead of as good. [default: %(default)s]")
    parser.add_argument('--bad', action="store_true", default=False, help="Mark these runs as bad instead of as good. [default: %(default)s]")
    
    args = parser.parse_args()
    db_fname = args.database

    if args.unname:
        remove_names(args.database, args.run_numbers)
    elif not args.name is None:
        update_name(args.database, args.run_numbers, args.name)
    else:
        mark_runs_as_good_in_db( args.database, args.run_numbers, mark_bad=args.bad)
        if not args.bad:
            archive_info( args.archive_dir, args.results_dir, args.run_numbers )
