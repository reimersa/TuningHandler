import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import tuning_db as tdb
import os

def plot_all_taps_from_scan( db, scan_index, plotdir='plots/test/', 
                                group_on = ['Module','Chip','TAP0'], cmap = sns.cm.rocket_r, grid=[]):
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
        if axis not in group_on:
            raise ValueError(f'Cannot use {axis} as a grid axis, must be one of the "grouped on" values: {group_on}')
        if idx > 1:
            raise ValueError(f'grid can only have two axes (at most columns and rows), but found {grid} with {len(grid)} axes')
        axes[idx] =  axis 
    
    for axis in axes:
        if not axis is None:
            group_on.remove(axis)
        

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
        title = f'{param_value_string}, Position {pos}| BER lower limit: {min_limit:.1e}' 

        fig = None
        do_single_plot = ( len(grid) == 0 )
        if do_single_plot: 
            fig = plt.figure()

            ax = make_ber_heatmap(  pivots, data=file_group, cmap=cmap) 
            ax.set_title(title)

        else: #do a heatmap grid
            fg = sns.FacetGrid(file_group, col=axes[0], row=axes[1], margin_titles=True)
            fg.map_dataframe(make_ber_heatmap, pivots, cmap=cmap)
            fg.fig.suptitle( title )
            fg.fig.tight_layout()
            fig = fg.fig
            

        param_value_string = '_'.join([ f'{param}.{value}' for param, value in zip(group_on, group_values) ])
        pltname_base = os.path.join(plotdir, f'BER_{ring}_{pos}_{param_value_string}')
        plt.savefig(f'{pltname_base}.png')
        plt.savefig(f'{pltname_base}.pdf')

        if fig is not None:
            fig.clear()
        


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
            
            

def make_ber_heatmap(  pivots, **kwargs ):
    '''make a single Bit Error Rate heatmap object from a dataframe, as a function of the two
    variables specified by "pivots".'''

    df = kwargs.pop('data')

    try:
        #If there are multiple entries with the same settings, but different error rates then the pivot won't work
        pivot = df.pivot( pivots[0], pivots[1],'Error_Rate')

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
    pivot = pivot.fillna(2)

    min_val = pivot.values.min()
    max_val = 10000000/df['NFrames'].max() #Ph2_ACF reports a maximum of 10M errors, so this is the highest value that will be reported #max(min_val*10, pivot.values.max())
    colbar_norm = LogNorm(vmin=min_val, vmax=max_val)

    ax = sns.heatmap(pivot, annot=True, annot_kws={'fontsize':'xx-small'}, fmt='.0e', norm=colbar_norm, linewidth=0.5, mask= mask, **kwargs )
    return ax



           
if __name__ == '__main__':

    import tuning_db as tdb
    db = tdb.TuningDataBase('db/ber.json')
    plot_all_taps_from_scan(db, 39, group_on=['Module','Chip','TAP0'], grid=['TAP0','Chip'])
