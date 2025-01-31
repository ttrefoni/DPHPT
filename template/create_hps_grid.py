import pandas as pd
import numpy as np
import os
import sys
import random


#epoch should always be just one value 

# Define hyperparameters
epoch=[40]
batch_size = [32,64,128]
units1 = [20,50,100,200]
units2 = [20,50,100]
units3=[20,50]
lrate = [0.00001,0.001,0.01]
layers = [1,2,3]


output_file=sys.argv[1]
# Print message
print("hps set")

# Create a data frame with all combinations of hyperparameters
hps = pd.DataFrame(np.array(np.meshgrid(epoch,batch_size, units1, units2, units3, lrate, layers)).T.reshape(-1, 7), columns=['epoch','batch_size', 'units1', 'units2', 'units3','lrate', 'layers'])
# Give NA values for layers that don't exist
hps.loc[hps['layers'] == 1, ['units3', 'units2']] = np.nan
hps.loc[hps['layers'] == 2, 'units3'] = np.nan

# Remove duplicates
hps = hps.drop_duplicates()
print(hps.shape[0])
print(" possible combinations")

# Write to file
hps.to_csv(f'{output_file}/hps_original_grid.csv', index=False)
