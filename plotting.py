import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

import tuning_db as tdb
import os

def plot_all_tap0s_from_scan( db, last_index, plotdir='plots/test/'):

    df = db.get_info()
    df = df[ df['scan_index'] == last_index ]
    df['Error_Rate'] = tdb.calculate_bit_error_rates( df )

    #should be unique anyway
    pos = df['Pos'].unique()[0]
    ring = df['Ring'].unique()[0]

    for modname, mod_group in df.groupby('Module'):
            for chipname, chip_group in mod_group.groupby('Chip'):
                for tap0name, tap0_group in chip_group.groupby('TAP0'):
                    pivot = tap0_group.pivot('TAP1','TAP2','Error_Rate')
                    sns.heatmap(pivot)
                    pltname = os.path.join(plotdir, f'BER_{ring}_{modname}_chip{chipname}_pos{pos}_TAP0_{tap0name}.png')
                    plt.savefig(pltname)
                    #plt.show()

