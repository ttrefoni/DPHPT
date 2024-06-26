import pandas as pd
import numpy as np
import os
import sys
import random

#read in file path 
grid_file=sys.argv[2]
print(grid_file)
hps=pd.read_csv(f'{grid_file}/hps_original_grid.csv')

# Read previously tested hps if the file exists
hp_tested_fp = f'{grid_file}/hps_tested.csv'

if os.path.exists(hp_tested_fp):
    hps_tested = pd.read_csv(hp_tested_fp)
    #remove any values that are already tested 
    hps_available = hps.merge(hps_tested, how='outer', indicator=True).query('_merge == "left_only"').drop('_merge', axis=1)
else:
    hps_available = hps

# Specify the number of hps to test
to_test = int(sys.argv[1])

print(to_test)
# Take a random sample of hps
if len(hps_available)>=to_test:
    hps_to_test = hps_available.sample(n=to_test)
else:
    hps_to_test=hps_available
print(hps_to_test)
# Get hostname
hostname = os.popen('hostname').read().strip()


# %%

# Write tested hps to a separate file
if os.path.exists(hp_tested_fp):
    hps_tested = pd.concat([hps_tested, hps_to_test], ignore_index=True)
    hps_tested.to_csv(hp_tested_fp, index=False)
else:
    hps_tested = hps_to_test
    hps_tested.to_csv(hp_tested_fp, index=False)

hps_tested
# Update available hps--remove any that are already tested from pool
hps_available = pd.merge(hps, hps_tested, on=['epoch','batch_size', 'units1', 'units2', 'units3', 'lrate', 'layers'], how='outer', indicator=True).query('_merge == "left_only"').drop('_merge', axis=1)

# Write available hps to file
hps_available.to_csv(f'{grid_file}/hps_available.csv', index=False)

# %%
hps_tested


# %%
hps_available

# %%
# Convert NA values to null for reading in JSON
hps_to_test['units1'] = hps_to_test['units1'].apply(lambda x: str(x) if not pd.isna(x) else 'null')
hps_to_test['units2'] = hps_to_test['units2'].apply(lambda x: str(x) if not pd.isna(x) else 'null')
hps_to_test['units3'] = hps_to_test['units3'].apply(lambda x: str(x) if not pd.isna(x) else 'null')

# Write selected hps to file
hps_to_test.to_csv(f'{grid_file}/hps_selected_{hostname}.csv', index=False)