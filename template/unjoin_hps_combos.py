import pandas as pd
import numpy as np
import os
import sys
import random

#read in all hps 
hps=pd.read_csv('hps_original_grid.csv')

#read previously tested hps 
hps_tested = pd.read_csv('hps_tested.csv')
#remove any values that are already tested 
hps_available = hps.merge(hps_tested, how='outer', indicator=True).query('_merge == "left_only"').drop('_merge', axis=1)

# Write available hps to file
hps_available.to_csv('hps_available.csv', index=False)
