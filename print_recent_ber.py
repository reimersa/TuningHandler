#!/usr/bin/env python3

import tuning_db as tdb
import pandas as pd

import argparse
    
def convert_val( val, to_type):
    return to_type(val)

def make_selections_dict( df, selection_strings ):

    selections = {}
    for expr in args.sel:
        col, val = expr.split(":")
        col_type = type(df[col].iloc[0])
        converted_val = convert_val( val, col_type )
        selections[col] = converted_val
    return selections
    
def select_by_dict( df, sel_strings):

    sel_dict = make_selections_dict(df, sel_strings)
    expr = True 
    for key, val in sel_dict.items():
        expr = expr & ( df[key] == val )
    return df[ expr ]

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Print most recent entries in the database')
    parser.add_argument('-n',  dest='nentries', type=int, default=10, 
            help='number of entries to show. [default :%(default)s]')
    parser.add_argument('--db', dest='database', type=str, default='ber_db/ber.json',
            help='database file name to query. [default: %(default)s]')
    parser.add_argument('-H', dest='show_columns', action='store_true', default=False, help='List all columns in database' )
    parser.add_argument('-c', dest='columns', default=None,help='comma separated list of columns to show' )
    parser.add_argument('--list-named', dest='list_named', action='store_true',default=False, help="list the scans with names and show some overview info about them.")
    parser.add_argument('--scans', dest='scan_numbers', default=None, help='comma separated list of scan numbers to display.')
    parser.add_argument('--sel', nargs='+',type=str,help='Select by column values, using the syntax "<COLUMN>:<VALUE>"')
    
    args = parser.parse_args()
    db_fname = args.database

    db = tdb.TuningDataBase(db_fname)
    df = db.get_info()

    if args.sel is not None:
        df = select_by_dict( df, args.sel )

    if args.show_columns:
        print(df.columns)
        exit(0)
    
    if args.list_named:
        for name, df_name in df.groupby('name'):
            index = df_name['scan_index'].iloc[0]
            start_time = df_name['start_time_human'].iloc[0]
            end_time   = df_name['end_time_human'].iloc[0]
            print(f'Scan "{name: <35}" - index: {int(index): >5} - start time: {start_time} - end time: {end_time} - entries: {df_name.shape[0]: >5} ')
            print('')
        exit(0)
    
    if args.scan_numbers is not None:
        scan_ids = [ float(scan) for scan in args.scan_numbers.split(',') ]
        df = df[ df[ 'scan_index' ].isin(scan_ids) ]
        
    if args.columns is not None:
        columns = args.columns.split(',')
        df = df[ columns ]
    else:
        suppress_columns = ['start_time','end_time','time_zone_human','end_time_human','name','Ring']
        for col in suppress_columns:
            if col in df.columns:
                df.drop([col], axis=1, inplace=True)
    pd.set_option('display.max_rows', args.nentries )
    print( df.head(args.nentries) )
