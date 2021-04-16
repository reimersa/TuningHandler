import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import tuning_db as tdb
import os

def plot_all_taps_from_scan( db, scan_index, plotdir='plots/test/', 
                                group_on = ['Module','Chip','TAP0'], cmap = sns.cm.rocket_r):

    df = db.get_info()
    df = df[ df['scan_index'] == scan_index ]
    df['Error_Rate'] = tdb.calculate_bit_error_rates( df )

    #should be unique anyway
    pos = df['Pos'].unique()[0]
    ring = df['Ring'].unique()[0]

    f = plt.figure()

    pivots = ['TAP0','TAP1','TAP2','Chip','Module']
    for group in group_on:
        if not group in pivots:
            raise ValueError(f'Cannot group on unknown value: {group}. must be one of {pivots}')
        pivots.remove(group)

    for (g1name, g2name, g3name), g3_group in df.groupby(group_on):

                    #In principle there can be a different limit for each point shown in the plot
                    #Might be nice to handle that somehow
                    min_limit = 1./g3_group['NFrames'].max()

                    try:
                        #If there are multiple entries with the same settings, but different error rates then the pivot won't work
                        pivot = g3_group.pivot( pivots[0], pivots[1],'Error_Rate')

                    except Exception as e:

                        #in this case we can recalculate the total Error Rate by summing up the cases appropriately
                        print(f'Combining mulitple runs for {group_on[0]}={g1name},{group_on[1]}={g2name},{group_on[2]}={g3name}')
                        print(f'The Original data is:\n {g3_group.to_string()}')
                        print(f'Calculating combined BER')
                        g3_group = tdb.combine_ber_measurements( g3_group, pivots)
                        g3_group['Error_Rate'] = tdb.calculate_bit_error_rates( g3_group )
                        print(f'The new Data is: \n{g3_group.to_string()}')
                        pivot = g3_group.pivot( pivots[0], pivots[1], 'Error_Rate')

                    mask  = pivot.isna()
                    pivot = pivot.fillna(2)

                    min_val = pivot.values.min()
                    max_val = max(min_val*10, pivot.values.max())
                    colbar_norm = LogNorm(vmin=min_val, vmax=max_val)

                    ax = sns.heatmap(pivot, annot=True, norm=colbar_norm, cmap=cmap, linewidth=0.5, mask= mask )
                    
                    title = f'{group_on[0]} = {g1name}, {group_on[1]} = {g2name}, {group_on[2]} = {g3name} | BER lower limit: {min_limit:.1e}' 
                    ax.set_title(title)

                    pltname_base = os.path.join(plotdir, f'BER_{ring}_{group_on[0]}.{g1name}_{group_on[1]}.{g2name}_pos{pos}_{group_on[2]}.{g3name}')

                    plt.savefig(f'{pltname_base}.png')
                    plt.savefig(f'{pltname_base}.pdf')
                    f.clear()



if __name__ == '__main__':

    import tuning_db as tdb
    db = tdb.TuningDataBase('db/ber.json')
    plot_all_taps_from_scan(db, 34, group_on=['Module','TAP1','TAP2'])
