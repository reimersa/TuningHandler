#!/usr/bin/env python3

import ROOT

import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import tuning_db as tdb
import os
import argparse
import glob

from utils import ensureDirectory

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


def plot_ber_vs_tap(db, ring, xval='TAP0', plotdir='plots/summary', do_cleaning=True, do_size=False, min_frames=1e11):
    '''make scatter plots showing the relationship between tap settings and the BER as a function 
        of pre-emphasis settings. Disaggregating data as function of other observables like the module id and position'''

    if not os.path.exists(plotdir):    
        os.makedirs(plotdir)

    df = db.get_info()
    if do_cleaning:
        df = clean_data(df, ring=ring, min_frames=min_frames)
    df['Error_Rate'] = tdb.calculate_bit_error_rates( df, allow_zero=False )
    #df = df[ df['Error_Rate'] >= 1e-20 ] #remove the zeros, but some zeros are stored as e-237 or something
    
    size_var = None
    if do_size:
        df['log $N_{frames}$'] = np.round(np.log10(df['NFrames']))
        size_var =  'log $N_{frames}$' 

    fg = sns.relplot( data=df, x=xval, y='Error_Rate', size=size_var,col='Pos',hue='Module', style='Chip', palette='Set2', alpha=0.9,  units='scan_index', kind='line', estimator=None)
    fg.set( yscale = 'log' )
    fg.set(ylim=(0.3*1/max(df['NFrames']), 1e-3))
    plot_name_base = f'BER_vs_{xval}_{ring}_summaries'
    full_plot_base = os.path.join(plotdir, plot_name_base)
    plt.savefig( f'{full_plot_base}.pdf'  )
    plt.savefig( f'{full_plot_base}.png'  )
    

def clean_data(df, ring, min_frames=1e11):
    '''remove data and scan points which may be considered problematic due to data taking conditions or quality.'''
    
    positions_per_ring = {
    'R1' : ['R11','R12','R13','R14','R15'],
    'R3' : ['R31','R32','R33','R34','R35', 'R36', 'R37', 'R38', 'R39']
    }
    new_df = df[ df['NFrames'] >= min_frames ]
    new_df = new_df[ new_df['Pos'].isin( positions_per_ring[ring] ) ]
    new_df = new_df[ (new_df['TAP1'] == 0) & (new_df['TAP2'] == 0) ]
    #new_df = new_df[ ~new_df['name'].isnull() ]
    new_df = new_df[ new_df['NBER'] < 10e6 ]
    return new_df

def plot_scurve_noise( df, plot_dir='./' ):
    #df = df[ (~df['Module'].isin(['modT03','modT09']) ) | (df['HV'] == -50) ]
    df = df[ (~df['Module'].str.contains('Sensor') ) | (df['HV'] == -50) ]
    fg = sns.catplot( x='Module', y='Mean Noise (electrons)', hue='Ring', data=df )
    fg.set_xticklabels(labels=fg.axes[-1][-1].get_xticklabels(), rotation=25, horizontalalignment='right')
    plt.savefig(os.path.join(plot_dir, 'test_noise_by_mod.pdf'), bbox_inches='tight')

def plot_scurve_noise_v_temp( df, plot_dir='./' ):
    #df = df[ (~df['Module'].isin(['modT03','modT09']) ) | (df['HV'] == -50) ]
    df = df[ (~df['Module'].str.contains('Sensor') ) | (df['HV'] == -50) ]
    df = df[ df['TargetThreshold_ele'] == 1500  ]
    fg = sns.relplot( x='TEMPSENS_AVG', y='Mean Noise (electrons)', hue='Module', col='Ring', data=df )
    plt.savefig(os.path.join(plot_dir, 'test_noise_by_temp.pdf'), bbox_inches='tight')

def plot_scurve_masked_pix_v_temp( df, plot_dir='./' ):
    #df = df[ (~df['Module'].isin(['modT03','modT09']) ) | (df['HV'] == -50) ]
    df = df[ (~df['Module'].str.contains('Sensor') ) | (df['HV'] == -50) ]
    df = df[ df['TargetThreshold_ele'] == 1500  ]
    df['Masked Pixels'] = df['InitMaskedPix']
    fg = sns.relplot( x='TEMPSENS_AVG', y='Masked Pixels', hue='Module', col='Ring', data=df )
    plt.savefig(os.path.join(plot_dir, 'test_masked_pix_by_temp.pdf'), bbox_inches='tight')

def plot_scurve_width_v_temp( df, plot_dir='./' ):
    #df = df[ (~df['Module'].isin(['modT03','modT09']) ) | (df['HV'] == -50) ]
    df = df[ (~df['Module'].str.contains('Sensor') ) | (df['HV'] == -50) ]
    df = df[ df['TargetThreshold_ele'] == 1500  ]
    fg = sns.relplot( x='TEMPSENS_AVG', y=r'$\sigma$(Threshold) (electrons)', hue='Module', col='Ring', data=df )
    plt.savefig(os.path.join(plot_dir, 'test_width_by_temp.pdf'), bbox_inches='tight')

def plot_scurve_noise_v_temp_and_mod( df, plot_dir='./' ):
    fg = sns.relplot( x='TEMPSENS_AVG', y='Mean Noise (electrons)', col='Module', hue='Chip', row='HV',kind='line',data=df )
    plt.savefig(os.path.join(plot_dir, 'test_noise_by_temp_and_mod.pdf'), bbox_inches='tight')

def plot_scurve_noise_v_vdd( df, vtype='dig', plot_dir='./' ):
    fg = sns.relplot( x=f'VOUT_{vtype}_ShuLDO', y='Mean Noise (electrons)', hue='Module', data=df )
    plt.savefig(os.path.join(plot_dir, f'test_noise_by_vdd{vtype}.pdf'), bbox_inches='tight')


def get_hv_from_name( df ):

    name = df['Name']
    splits = name.split('_')
    voltage = 0
    for split in splits:
        if split.endswith('V'):
            
            voltage = int(split.rstrip('V').replace('minus','-'))
            break
    return voltage

def get_ambientT_from_name(df ):
    name = df['Name']
    splits = name.split('_')
    temp = -50
    for split in splits:
        if split.endswith('amb'):
            temp = int(split.rstrip('amb').replace('minus','-'))
            break
    return temp

def plot_scurve_masked_pix_by_temp( df, plot_dir='./' ):
    df['Masked Pixels'] = df['InitMaskedPix']
    fg = sns.relplot( x='TEMPSENS_AVG', y='Masked Pixels', col='Target Threshold (electrons)', hue='Module', row='HV', data=df )
    plt.savefig(os.path.join(plot_dir,'test_masked_pix_by_temp.pdf'), bbox_inches='tight')

def plot_scurve_masked_pix_by_threshold( df, plot_dir='./'):
    df = df[ df['Ambient Temperature'] == -50 ]
    #df = df[ (~df['Module'].isin(['modT03','modT09']) ) | (df['HV'] == -50) ]
    df = df[ (~df['Module'].str.contains('Sensor') ) | (df['HV'] == -50) ]
    df['Masked Pixels'] = df['InitMaskedPix']
    fg = sns.relplot( x='Target Threshold (electrons)',y='Masked Pixels',col='Ambient Temperature', hue='Module', data=df)
    plt.savefig(os.path.join(plot_dir, 'test_masked_pix_by_target.pdf'), bbox_inches='tight')

def plot_scurve_masked_pix_by_threshold_and_mod( df, plot_dir='./'):
    #df = df[ (~df['Module'].isin(['modT03','modT09']) ) | (df['HV'] == -50) ]
    df = df[ (~df['Module'].str.contains('Sensor') ) | (df['HV'] == -50) ]
    df['Masked Pixels'] = df['InitMaskedPix']
    fg = sns.relplot( x='Target Threshold (electrons)',y='Masked Pixels',col='Module', hue='Chip', col_wrap=4, kind='line', ci=None, data=df)
    plt.savefig(os.path.join(plot_dir, 'test_masked_pix_by_target_and_mod.pdf'), bbox_inches='tight')

def plot_scurve_masked_pix_by_threshold_mod_and_ring( df, plot_dir='./'):
    #df = df[ (~df['Module'].isin(['modT03','modT09']) ) | (df['HV'] == -50) ]
    df = df[ (~df['Module'].str.contains('Sensor') ) | (df['HV'] == -50) ]
    df['Masked Pixels'] = df['InitMaskedPix']
    fg = sns.relplot( x='Target Threshold (electrons)',y='Masked Pixels',col='Module', hue='Ring', style='Chip', col_wrap=4, kind='line', ci=None, data=df)
    plt.savefig(os.path.join(plot_dir, 'test_masked_pix_by_target_and_mod_and_ring.pdf'), bbox_inches='tight')

def plot_temp_correlations(df, plot_dir='./'):
    for sens_no in ['1','2','3','4']:
        df[f'tdiff_{sens_no}'] = df['TEMPSENS_2'] - df[f'TEMPSENS_{sens_no}']
    fg = sns.pairplot( df[['tdiff_1','tdiff_2','tdiff_3','tdiff_4']])
    plt.savefig(os.path.join(plot_dir,'test_temperature_sensor_correlations.pdf'), bbox_inches='tight')

def plot_temp_by_ambient_and_module(df, plot_dir='./'):
    fg = sns.catplot( x='Ambient Temperature', y='TEMPSENS_AVG', hue='Ring', col='Module', data=df)
    plt.savefig(os.path.join(plot_dir, 'test_mod_temp_by_ambient_and_pos.pdf'), bbox_inches='tight')


def plot_vddd_vdda_by_ring( df, plot_dir='./'):
    fg = sns.relplot( x=f'VOUT_dig_ShuLDO', y='VOUT_ana_ShuLDO', hue='Ring', data=df )
    plt.savefig( os.path.join(plot_dir, 'test_mod_vddd_vs_ring.pdf'), bbox_inches='tight')

def plot_temp_by_ambient(df, plot_dir='./'):
    fg = sns.catplot( x='Ambient Temperature', y='Measured Chip Temperature', hue='Ring', data=df)
    plt.savefig(os.path.join(plot_dir, 'test_mod_temp_by_ambient.pdf'), bbox_inches='tight')

def plot_scurve_threshold_by_target(df, plot_dir='./'):
    fg = sns.catplot( x='Target Threshold (electrons)', y='Mean Threshold (electrons)', hue='Ring', data=df)
    plt.savefig(os.path.join(plot_dir, 'test_mod_threshold_by_target.pdf'), bbox_inches='tight')

def plot_scurve_noise_by_module( df, plot_dir='./'):
    fg = sns.catplot( x='Ring', y='Mean Noise (electrons)', col='Module', hue='Name', data=df )
    plt.savefig(os.path.join(plot_dir,'test_noise_by_mod_and_name.pdf'), bbox_inches='tight')

def plot_scurve_noise_by_module( df, plot_dir='./'):
    fg = sns.catplot( x='Ring', y='Mean Noise (electrons)', col='Module', hue='Name', data=df )
    plt.savefig(os.path.join(plot_dir,'test_noise_by_mod_and_name.pdf'), bbox_inches='tight')

def plot_scurve_width( df, plot_dir='./'):
    #df = df[ (~df['Module'].isin(['modT03','modT09']) ) | (df['HV'] == -50) ]
    df = df[ (~df['Module'].str.contains('Sensor') ) | (df['HV'] == -50) ]
    fg = sns.catplot( x='Module', y=r'$\sigma$(Threshold) (electrons)', hue='Ring', data=df )
    fg.set_xticklabels(labels=fg.axes[-1][-1].get_xticklabels(), rotation=25, horizontalalignment='right')
    plt.savefig(os.path.join(plot_dir,'test_threshold_dispersion_by_mod.pdf'), bbox_inches='tight')

def plot_scurve_masked_pix( df, plot_dir='./'):
    #df = df[ (~df['Module'].isin(['modT03','modT09']) ) | (df['HV'] == -50) ]
    df = df[ (~df['Module'].str.contains('Sensor') ) | (df['HV'] == -50) ]
    df = df[ df['Ambient Temperature'] == -50 ]
    df['Masked Pixels'] = df['InitMaskedPix']
    fg = sns.catplot( x='Module', y='Masked Pixels', hue='Ring', col='Target Threshold (electrons)', data=df )
    fg.set_xticklabels(labels=fg.axes[-1][-1].get_xticklabels(), rotation=25, horizontalalignment='right')
    plt.savefig(os.path.join(plot_dir,'test_threshold_masked_pix_by_mod.pdf'), bbox_inches='tight')

def plot_scurve_target_difference( df, plot_dir='./' ):
    df['ThresholdDiff'] = df['ThresholdMean_ele'] - df['TargetThreshold_ele']
    fg = sns.catplot( x='Module', y='ThresholdDiff', hue='Ring', data=df)
    fg.set_xticklabels(labels=fg.axes[-1][-1].get_xticklabels(), rotation=25, horizontalalignment='right')
    plt.savefig(os.path.join(plot_dir, 'test_threshold_difference_from_target.pdf'), bbox_inches='tight')

def get_generic_module_name( df ):

    module_name_dict = { 'modT03':'Sensor Module 1',
                         'modT09':'Sensor Module 2',
                         'mod7':'Digital Module 1',
                         'mod9':'Digital Module 2',
                         'mod10':'Digital Module 3',
                         'mod11':'Digital Module 4',
                         'mod12':'Digital Module 5' }
    module = df['Module']
    return module_name_dict[module]

def plot_scurve_summaries( scurve_df, plot_dir='plots/scurves' ):

    if not os.path.exists(plot_dir):
        os.mkdir(plot_dir)

    scurve_df = scurve_df[ ~(scurve_df['Module'] == 'modT14') ] #should find a better way to exclude this
    scurve_df['Module'] = scurve_df.apply( lambda x: get_generic_module_name(x), axis=1 )
    scurve_df['HV'] = scurve_df.apply( lambda x: get_hv_from_name(x), axis=1 )
    scurve_df['Ambient Temperature'] = scurve_df.apply( lambda x: get_ambientT_from_name(x), axis=1)
    scurve_df['TEMPSENS_AVG'] = (scurve_df['TEMPSENS_1'] + scurve_df['TEMPSENS_2'] + scurve_df['TEMPSENS_3'] + scurve_df['TEMPSENS_4'])/4
    scurve_df['Measured Chip Temperature'] = scurve_df['TEMPSENS_AVG']
    scurve_df['Mean Noise (electrons)'] = scurve_df['NoiseMean_ele']
    scurve_df[r'$\sigma$(Threshold) (electrons)'] = scurve_df['ThresholdStdDev_ele']
    scurve_df['Target Threshold (electrons)'] = scurve_df['TargetThreshold_ele']
    scurve_df['Mean Threshold (electrons)'] = scurve_df['ThresholdMean_ele']
    #scurve_df = scurve_df[ scurve_df['TargetThreshold_ele'] == 1500 ]
    #scurve_df = scurve_df[ scurve_df['Ambient Temperature'] == -50 ]
    plot_scurve_noise(scurve_df, plot_dir)
    plot_scurve_noise_by_module(scurve_df, plot_dir,)
    plot_scurve_width(scurve_df, plot_dir)
    plot_scurve_target_difference( scurve_df, plot_dir)
    plot_scurve_threshold_by_target(scurve_df, plot_dir)
    plot_scurve_masked_pix_by_temp(scurve_df, plot_dir)
    plot_scurve_noise_v_temp( scurve_df, plot_dir )
    plot_scurve_noise_v_temp_and_mod( scurve_df, plot_dir )
    plot_scurve_masked_pix(scurve_df, plot_dir )
    plot_temp_correlations( scurve_df,plot_dir )
    plot_scurve_masked_pix_v_temp( scurve_df, plot_dir )
    plot_scurve_masked_pix_by_threshold(scurve_df, plot_dir )
    plot_scurve_masked_pix_by_threshold_and_mod(scurve_df, plot_dir )
    plot_scurve_masked_pix_by_threshold_mod_and_ring(scurve_df, plot_dir)
    plot_temp_by_ambient_and_module(scurve_df, plot_dir)
    plot_temp_by_ambient(scurve_df, plot_dir)
    plot_scurve_width_v_temp(scurve_df, plot_dir) 
    plot_vddd_vdda_by_ring( scurve_df, plot_dir)
    plot_scurve_noise_v_vdd( scurve_df, vtype='dig', plot_dir=plot_dir )
    plot_scurve_noise_v_vdd( scurve_df, vtype='ana',plot_dir=plot_dir )
    

class NoUniqueMaskedPixValuesError(Exception):
    pass

def get_masked_pixels(runnr, moduleId, chip, df):

    sel_df = df[ ( df['RunNumber'] == runnr ) & ( df['Port'] == int(moduleId) ) & ( df['Chip'] == int(chip) ) ]
    values = sel_df['InitMaskedPix'].unique()
    if not len(values) == 1:
        raise NoUniqueMaskedPixValuesError(f'''Expected exactly one value of InitMaskedPix with run number {runnr}, module {moduleId} and chip {chip}, but found {len(values)}, the dataframe is {sel_df}''')
    return values[0]

def get_module_name(runnr, moduleId, chip, df):

    sel_df = df[ ( df['RunNumber'] == runnr ) & ( df['Port'] == int(moduleId) ) & ( df['Chip'] == int(chip) ) ]
    values = sel_df['Module'].unique()
    if not len(values) == 1:
        raise NoUniqueMaskedPixValuesError(f'''Expected exactly one value of Module Name with run number {runnr}, module {moduleId} and chip {chip}, but found {len(values)}, the dataframe is {sel_df}''')
    return values[0]

def get_position(runnr, moduleId, chip, df):

    sel_df = df[ ( df['RunNumber'] == runnr ) & ( df['Port'] == int(moduleId) ) & ( df['Chip'] == int(chip) ) ]
    values = sel_df['Ring'].unique()
    if not len(values) == 1:
        raise NoUniqueMaskedPixValuesError(f'''Expected exactly one value of Module Name with run number {runnr}, module {moduleId} and chip {chip}, but found {len(values)}, the dataframe is {sel_df}''')
    return values[0]

def plot_scurve_results(runnr, module_per_id, plotfoldername='plots/thresholds/', tag='', tuning_db=None):
    ROOT.gROOT.SetBatch(True)
    
    runnrstr = '%06i' % runnr
    infilepattern = 'Results/Run%s_*.root' % runnrstr
    
    matches = glob.glob(infilepattern)
    if len(matches) > 1:
        raise ValueError('Trying to plot histograms in rootfile for runnr. %i, but there is more than one file found with the pattern \'Run%s_*.root\': '% (runnrstr) + matches )
    elif len(matches) < 1:
        infilepattern = f'archive/{runnr}/Results/Run{runnr:06d}_*.root'
        matches = glob.glob(infilepattern)
    infilename = matches[0]
    
    infile = ROOT.TFile(infilename, 'READ')
    foldername = 'Detector/Board_0/OpticalGroup_0/'
    infile.cd(foldername)
    dir = ROOT.gDirectory
    iter = ROOT.TIter(dir.GetListOfKeys())
    modules = [key.GetName() for key in ROOT.gDirectory.GetListOfKeys()]
    
    for module in modules:
        histpath = foldername + module
        moduleid = int(module.replace('Hybrid_', ''))
        #modulename = module_per_id[moduleid]
        infile.cd()
        infile.cd(histpath)
        chips = [key.GetName() for key in ROOT.gDirectory.GetListOfKeys()]
        
        for chip in chips:
            chip_dummy = chip
            fullhistpath = os.path.join(histpath, chip)
            infile.cd()
            infile.cd(fullhistpath)
            nmasked_pix = None
            module_name = module
            ring = ''
            if not tuning_db is None:
                df = tuning_db.get_info()
                chipId = chip.replace('Chip_','')
                nmasked_pix = get_masked_pixels( runnr, moduleid, chipId,df)
                module_name = get_module_name( runnr, moduleid, chipId,df)
                ring  = get_position( runnr, moduleid, chipId,df)
            
            canvases = [key.GetName() for key in ROOT.gDirectory.GetListOfKeys()]
            infile.cd()
            for canvasname in canvases:
                if canvasname == 'Channel': continue
                canvas = infile.Get(os.path.join(fullhistpath, canvasname))
                hist   = canvas.GetPrimitive(canvasname)
                plot_type = canvasname.split('_')[4]
                canvastitle = plot_type + '_' + chip
                hist.SetTitle(f'{plot_type}: {module_name} {chip.replace("_","")} - Ring:{ring}')
                outcanvas = ROOT.TCanvas('c', canvastitle, 650, 500)
                if 'SCurves' in canvastitle:
                    ROOT.gPad.SetLogz()
                hist.Draw('colz')
                if ( ('SCurves' in canvastitle) or ('1D' in canvastitle) ) and not (nmasked_pix is None):
                  latex = ROOT.TLatex()
                  latex.SetTextSize( latex.GetTextSize()*0.65)
                  latex.DrawLatexNDC( 0.5,0.2,f'Masked Pixels = {nmasked_pix:.0f}')
                if '1D' in canvastitle:
                  hist.GetYaxis().SetTitle('Channels')
                  
                for prim in canvas.GetListOfPrimitives():
                    if isinstance( prim, ROOT.TGaxis ):
                        prim.SetTitleOffset(-1)
                        prim.SetTitle(f'{prim.GetTitle()}   ')
                        prim.SetTitleColor(ROOT.kRed)
                        prim.Draw()
                ROOT.gStyle.SetOptStat(0);
                outdir = os.path.join(plotfoldername, '')
                outfilename = canvastitle  + tag + '_' + module_name + '_' + runnrstr + '.pdf'
                #outfilename = outfilename.replace('Chip_', '%s_chip' % (modulename))
                ensureDirectory(outdir)
                outcanvas.SaveAs(outdir + outfilename)
                outcanvas.SaveAs(outdir + outfilename.replace('pdf', 'png'))
    del infile
    
def merge_scurve_and_tuning_df( scurve_df, tuning_df ):
    scurve_df = scurve_df.merge( tuning_df, how='left', on=['RunNumber','Module','Chip'])
    return scurve_df

if __name__=='__main__':

    sns.set_palette('hls',8)
    ber_variables = ['TAP0','TAP1','TAP2','Module','Chip']
    parser = argparse.ArgumentParser(description='Print most recent entries in the database')
    parser.add_argument('--db', dest='database', type=str, default='ber_db/ber.json',
            help='database file name to query. [default: %(default)s]')
    parser.add_argument('--scan', dest='scan_number', type=int, default=None, help='scan number to plot. [default: most recent]')
    parser.add_argument('--group-on', dest='group_on', nargs=3, choices=ber_variables, default=['Module','Chip','TAP0'],
                        help="Values to separate the plots by, each heatmap will represent scans with one value of each of these three settings [default: %(default)s")
    parser.add_argument('--xgrid', dest='xgrid', choices=ber_variables + ['None'], default='TAP0', help='variable for x-axis of facet grid [default %(default)s ]')
    parser.add_argument('--ygrid', dest='ygrid', choices=ber_variables + ['None'], default='Chip', help='variable for y-axis of facet grid [default %(default)s ]')
    parser.add_argument('--voltages', action='store_true', default=False, help='Plot the VDDD and VDDA values from the scan as a function of TAP0')
    parser.add_argument('--summary', action='store_true', default=False, help='Make a summary plot showing BER vs. TAP0 from all scans in the DB')
    parser.add_argument('--min-frames', type=float, default=1e11, help='Minimum number of frames required for a scan to be considered in the summary plot. [default %(default)s]')
    parser.add_argument('--ring', type=str, default='R1', choices=['R1', 'R3', 'R5'], help='Ring to plot summary of. [default %(default)s]')
    parser.add_argument('--do-size', action='store_true', default=False, help='Scale line size to the number of frames in the scan when doing summary plots. [default %(default)s]')
    parser.add_argument('--scurve-summary', action='store_true', default=False, help='Plot SCurve summary plots from the scurve and tuning databases')
    parser.add_argument('--plot-tuning', type=int, default=None, help='Plot SCurve plots for a given run number [default %(default)s]')
    
    args = parser.parse_args()
    db_fname = args.database

    db = tdb.TuningDataBase(db_fname)



    if args.scurve_summary:
        tuning_db = 'tuning_db/tuning.json'
        scurve_db = 'tuning_db/scurves.json'
        tuning_df = tdb.TuningDataBase( tuning_db).get_info()
        scurve_df = tdb.TuningDataBase( scurve_db).get_info()
        scurve_df = merge_scurve_and_tuning_df( scurve_df, tuning_df )
        print(scurve_df)
        plot_scurve_summaries(scurve_df)
    elif not args.plot_tuning is None:
        tuning_db = tdb.TuningDataBase('tuning_db/tuning.json')
        plot_scurve_results( args.plot_tuning, 'dummy', plotfoldername=f'./plots/tuning_run_{args.plot_tuning}/', tuning_db=tuning_db)

    elif args.summary:
        plot_ber_vs_tap(db, ring = args.ring, min_frames = args.min_frames, do_size=args.do_size)
    else:
        scan_number = int(args.scan_number) if args.scan_number is not None else db.get_last_scan_id()
        if args.voltages:
            plot_voltages_from_scan(db, scan_number)
        else:    
            if args.xgrid == 'None':
                args.xgrid = None
            if args.ygrid == 'None':
                args.ygrid = None
            plot_all_ber_from_scan(db, scan_number, group_on=args.group_on, grid=[args.xgrid, args.ygrid])
    
