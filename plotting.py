#!/usr/bin/env python3

import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import tuning_db as tdb
import os
import argparse

def plot_all_ber_from_scan(  db, scan_index, plotdir='plots/', 
                                group_on = ['Module','Chip','TAP0'], cmap = sns.cm.rocket_r, grid=[None, None]):
    '''Plot heatmaps of relevant quantities from a particular BER scan index.
    can choose how to orient between Module, Chip, TAP0, TAP1, TAP2, the three 
    quantities which are "grouped_on" will get be grouped into separate files,
    the two remaining quantities will form the x and y-axis of the heat-map plot.'''

    df = db.get_info()
    df = df[ df['scan_index'] == scan_index ]
    df['Error_Rate'] = tdb.calculate_bit_error_rates( df )



    pivots = ['TAP0','TAP1','TAP2','Chip','Module']
    for group in group_on:
        if not group in pivots:
            raise ValueError(f'Cannot group on unknown value: {group}. must be one of {pivots}')
        pivots.remove(group)

    
    axes = [None, None]
    for idx, axis in enumerate(grid):
        if axis is None:
            continue
        if axis not in group_on:
            raise ValueError(f'Cannot use {axis} as a grid axis, must be one of the "grouped on" values: {group_on}')
        if idx > 1:
            raise ValueError(f'grid can only have two axes (at most columns and rows), but found {grid} with {len(grid)} axes')
        axes[idx] =  axis 
    
    for axis in axes:
        if not axis is None:
            group_on.remove(axis)
        else:
            grid.remove(None)
        

    for group_values, file_group in df.groupby(group_on):
        #should be unique anyway since we have already selected the scan
        #modules don't move mid scan
        ring = file_group['Ring'].unique()[0]
        pos  = file_group['Pos'].unique()[0]

        #make sure group_values is always a tuple and not just a string
        if len(group_on) <= 1:
            group_values = tuple( [group_values] ) 

        #In principle there can be a different limit for each point shown in the plot
        #Might be nice to handle that somehow
        min_limit = 1./file_group['NFrames'].max()
        param_value_string = ', '.join([ f'{param} = {value}' for param, value in zip(group_on, group_values) ])
        title = f'{param_value_string}, Position {pos} \n BER lower limit: {min_limit:.2e}' 

        colour_norm = get_heatmap_ber_norms( file_group )

        fig = None
        do_single_plot = ( len(grid) == 0 )

        if do_single_plot: 
            fig = plt.figure()
            ax = make_ber_heatmap(  pivots, data=file_group,  norm=colour_norm, cmap=cmap) 
            ax.set_title(title)
            fig.tight_layout()

        else: #do a heatmap grid
            fg = do_facetgrid_heatmaps( file_group, pivots, title, col=axes[0], row=axes[1],  norm=colour_norm, cmap=cmap )
            fig = fg.fig

        param_value_string = '_'.join([ f'{param}.{value}' for param, value in zip(group_on, group_values) ])
        pltname_base = os.path.join(plotdir, f'BER_Scan{int(scan_index)}_{ring}_{pos}_{param_value_string}')
        plt.savefig(f'{pltname_base}.png')
        plt.savefig(f'{pltname_base}.pdf')

        if fig is not None:
            fig.clear()
        

        
def do_facetgrid_heatmaps( dataframe, pivots, title, col, row, **kwargs ):

    do_sharex = ( pivots[0] == 'Chip' )
    do_sharey = ( pivots[1] == 'Chip' )
    fg = sns.FacetGrid( dataframe, col=col, row=row, margin_titles=True, sharex=do_sharex, sharey=do_sharey)

    cbar_rect = [ .96, .07, .02, .86 ]
    main_rect = [ 0, 0, cbar_rect[0] - 0.02, 1 ]
    cbar_ax = cbar_ax = fg.fig.add_axes( cbar_rect) 
    fg.map_dataframe(make_ber_heatmap, pivots, cbar_ax=cbar_ax, **kwargs)
    fg.fig.suptitle( title )

    fg.fig.subplots_adjust( right=main_rect[2] )
    fg.fig.tight_layout( rect=main_rect )
    fig = fg.fig
    return fg 
           

def get_module_positions( df ):
    ''' get lists of modules, ring, positions'''

    mdf = df[['Module','Ring','Pos']] #No need for other columns
    mods = []
    rings = []
    positions = []
    for modname, mod_group in df.groupby('Module'):
            mods += [ modname ]
            rings = [ mod_group['Ring'].unqiue() ]
            positions =[ mod_group['Pos'].unique() ]
    return (mods, rings, positions)
            
def get_heatmap_ber_norms( df ):
    '''figure out the scaling to be used for heatmaps, 
    based on the Bit Error Rates and NFrames. return a norm object'''

    ber_vals = df['Error_Rate'].fillna(2) # need positive values for log scale, real values should be < 1
    min_val = ber_vals.min()
    max_val = 10e6/df['NFrames'].max() #Ph2_ACF reports a maximum of 10M errors, so this should be the highest reports value)
    max_val = max( max_val, min_val) #should only happen if 'NFrames' was -1 for all scans, i.e. scan didn't work
                                     # but do this to avoid a crash.
    colbar_norm = LogNorm(vmin=min_val, vmax=max_val)

    return colbar_norm

    
            

def make_ber_heatmap(  pivots, **kwargs ):
    '''make a single Bit Error Rate heatmap object from a dataframe, as a function of the two
    variables specified by "pivots".'''

    df = kwargs.pop('data')

    try:
        #If there are multiple entries with the same settings, but different error rates then the pivot won't work
        pivot = df.pivot( pivots[0], pivots[1],'Error_Rate')
        pivot_nber = df.pivot( pivots[0], pivots[1], 'NBER')

    except Exception as e:

        print(f' Encountered exception while creating pivots for heatmap \n{e}')

        #in this case we can try recalculate the total Error Rate by summing up the cases appropriately
        print(f'Trying to combine mulitple runs.')
        print(f'The original data was:\n {df.to_string()}')
        print(f'Calculating combined BER')
        df = tdb.combine_ber_measurements( df, pivots)
        df['Error_Rate'] = tdb.calculate_bit_error_rates( df )
        print(f'The new Data is: \n{df.to_string()}')
        pivot = df.pivot( pivots[0], pivots[1], 'Error_Rate')

    mask  = pivot.isna() 
    mask_nonzero = (pivot_nber > 0.)
    ax = sns.heatmap(pivot, annot=True, annot_kws={'fontsize':'xx-small'}, fmt='.2e',  linewidth=0.5, mask= mask, **kwargs )
    ax = sns.heatmap(pivot, annot=True, annot_kws={'fontsize':'xx-small', 'color':'green'}, fmt='.2e',  linewidth=0.5, cbar=False, mask= mask_nonzero, **kwargs )
    
    return ax


def plot_voltages_from_scan( db, scan_index, xval='TAP0', plotdir='plots/voltages'):
    '''Make a grid of Scatter plots of VDDD and VDDA values from a scan'''

    if not os.path.exists(plotdir):    
        os.makedirs(plotdir)

    df = db.get_info()
    df = df[ df['scan_index'] == scan_index ]
    df_voltsD = df.copy()
    df_voltsD['VoltageType'] = 'Digital'
    df_voltsD['Voltage'] = df_voltsD['VOUT_dig_ShuLDO']

    df_voltsA = df
    df_voltsA['VoltageType'] = 'Analog'
    df_voltsA['Voltage']  = df_voltsA['VOUT_ana_ShuLDO']

    df = pd.concat([df_voltsA, df_voltsD])
    fg = sns.relplot(data=df,x=xval,y='Voltage',hue='Chip',col='Module',style='VoltageType', palette='Set2',alpha=0.9)
    plot_name_base = f'BER_scan{int(scan_index)}_voltages'
    full_plot_base = os.path.join(plotdir, plot_name_base)
    plt.savefig( f'{full_plot_base}.pdf'  )
    plt.savefig( f'{full_plot_base}.png'  )

    fg.set(ylim=(1.0,1.4))
    plt.savefig( f'{full_plot_base}_zoomed.pdf'  )
    plt.savefig( f'{full_plot_base}_zoomed.png'  )


def plot_ber_vs_tap(db, xval='TAP0', plotdir='plots/summary', do_cleaning=True):
    '''make scatter plots showing the relationship between tap settings and the BER as a function 
        of pre-emphasis settings. Disaggregating data as function of other observables like the module id and position'''

    if not os.path.exists(plotdir):    
        os.makedirs(plotdir)

    df = db.get_info()
    if do_cleaning:
        df = clean_data(df)
    df['Error_Rate'] = tdb.calculate_bit_error_rates( df, allow_zero=True )
    df['Error_error'] = df['Error_Rate']*4
    fg = sns.relplot( data=df, x=xval, y='Error_Rate', col='Pos',hue='Module', style='Chip', palette='Set2', alpha=0.9, units='scan_index', kind='line', estimator=None)
    fg.set( yscale = 'log' )
    plot_name_base = f'BER_vs_{xval}_summaries'
    full_plot_base = os.path.join(plotdir, plot_name_base)
    plt.savefig( f'{full_plot_base}.pdf'  )
    plt.savefig( f'{full_plot_base}.png'  )
    

def clean_data(df, min_frames=1e4):
    '''remove data and scan points which may be considered problematic due to data taking conditions or quality.'''
    new_df = df[ df['NFrames'] >= min_frames ]
    new_df = new_df[ new_df['Pos'].isin( ['R11','R12','R13','R14','R15'] ) ]
    new_df = new_df[ (new_df['TAP1'] == 0) & (new_df['TAP2'] == 0) ]
    #new_df = new_df[ ~new_df['name'].isnull() ]
    new_df = new_df[ new_df['NBER'] < 10e6 ]
    return new_df

if __name__=='__main__':

    ber_variables = ['TAP0','TAP1','TAP2','Module','Chip']
    parser = argparse.ArgumentParser(description='Print most recent entries in the database')
    parser.add_argument('--db', dest='database', type=str, default='db/ber.json',
            help='database file name to query. [default: %(default)s]')
    parser.add_argument('--scan', dest='scan_number', type=int, default=None, help='scan number to plot. [default: most recent]')
    parser.add_argument('--group-on', dest='group_on', nargs=3, choices=ber_variables, default=['Module','Chip','TAP0'],
                        help="Values to separate the plots by, each heatmap will represent scans with one value of each of these three settings [default: %(default)s")
    parser.add_argument('--xgrid', dest='xgrid', choices=ber_variables + ['None'], default='TAP0', help='variable for x-axis of facet grid [default %(default)s ]')
    parser.add_argument('--ygrid', dest='ygrid', choices=ber_variables + ['None'], default='Chip', help='variable for y-axis of facet grid [default %(default)s ]')
    parser.add_argument('--voltages', action='store_true', default=False, help='Plot the VDDD and VDDA values from the scan as a function of TAP0')
    parser.add_argument('--summary', action='store_true', default=False, help='Make a summary plot showing BER vs. TAP0 from all scans in the DB')
    
    args = parser.parse_args()
    db_fname = args.database

    db = tdb.TuningDataBase(db_fname)

    scan_number = int(args.scan_number) if args.scan_number is not None else db.get_last_scan_id()


    if args.summary:
        plot_ber_vs_tap(db)
    elif args.voltages:
        plot_voltages_from_scan(db, scan_number)
    else:    
        if args.xgrid == 'None':
            args.xgrid = None
        if args.ygrid == 'None':
            args.ygrid = None
        plot_all_ber_from_scan(db, scan_number, group_on=args.group_on, grid=[args.xgrid, args.ygrid])

