import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import tuning_db as tdb
import os

def plot_all_taps_from_scan( db, scan_index, plotdir='plots/test/', 
                                group_on_tap = 'TAP0', cmap = sns.cm.rocket_r):

    df = db.get_info()
    df = df[ df['scan_index'] == scan_index ]
    df['Error_Rate'] = tdb.calculate_bit_error_rates( df )

    #should be unique anyway
    pos = df['Pos'].unique()[0]
    ring = df['Ring'].unique()[0]

    f = plt.figure()

    pivots = ['TAP0','TAP1','TAP2']
    if not group_on_tap in pivots:
        raise ValueError(f'Cannot group on unknown value: {group_on_tap}. must be one of {pivots}')
    pivots.remove(group_on_tap)

    for modname, mod_group in df.groupby('Module'):
            for chipname, chip_group in mod_group.groupby('Chip'):
                for tapname, tap_group in chip_group.groupby(group_on_tap):

                    min_limit = 1./tap_group['NFrames'].max()
                    pivot = tap_group.pivot( pivots[0], pivots[1],'Error_Rate')

                    min_val = pivot.values.min()
                    max_val = max(min_val*10, pivot.values.max())
                    colbar_norm = LogNorm(vmin=min_val, v_max=max_val)
                    ax = sns.heatmap(pivot, annot=True, norm=cbar_norm, cmap=cmap, linewidth=0.5 )
                    
                    title = f'{group_on_tap} = {tapname}, BER lower limit: {min_limit:.1e}' 
                    ax.set_title(title)

                    pltname = os.path.join(plotdir, f'BER_{ring}_{modname}_chip{chipname}_pos{pos}_{group_on_tap}_{tapname}.png')
                    plt.savefig(pltname)
                    f.clear()



if __name__ == '__main__':

    import tuning_db as tdb
    db = tdb.TuningDataBase('db/ber.json')
    plot_all_taps_from_scan(db, 12)
