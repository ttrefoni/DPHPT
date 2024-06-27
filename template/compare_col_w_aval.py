import pandas as pd
import numpy as np
import os
import sys
import random

# Read in tune name from system argument
tune_name=str(sys.argv[1])
grid_file=str(sys.argv[2])
hps=pd.read_csv(f'{grid_file}/hps_original_grid.csv')

# Read previously tested hps if the file exists
hp_tested_fp = f'{grid_file}/hps_tested.csv'

# Write the combined data frame to a new CSV file
base_output_file = f'{grid_file}/output_py/COLLATE'
output_file=f"{base_output_file}/{tune_name}_col.csv"

if os.path.exists(output_file):
    hps_tested = pd.read_csv(output_file)
    hps_tested=hps_tested[["epoch","batch_size","units1","units2","units3","lrate","layers"]]
    #print(hps_tested)
    #remove any values that are already tested 
    hps_available = hps.merge(hps_tested, how='outer', indicator=True).query('_merge == "left_only"').drop('_merge', axis=1)
else:
    hps_available = hps

# Write available hps to file
hps_available.to_csv(f'{grid_file}/hps_available.csv', index=False)



