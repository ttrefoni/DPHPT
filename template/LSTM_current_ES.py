import pandas as pd
import os
import numpy as np
import json
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import LSTM, Dense # type: ignore
from tensorflow.keras.optimizers import Adam # type: ignore
from tensorflow.keras.saving import register_keras_serializable
from keras.callbacks import EarlyStopping
from keras.callbacks import ModelCheckpoint
from keras import backend
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, r2_score
import tensorflow.keras.backend as K
from datetime import datetime 
import random

#find hyperparameters from collated  metrics 
#accept name of output file
# Function to get environment variable or use default value
def get_env_var(var_name):
    val = os.getenv(var_name)
    return val

# Get the environment variable "combos" or use a default value
combos = get_env_var("combos")
print(combos)
# Parse the JSON string
hps = json.loads(combos)
print(hps)

#function to convert to int unless it is null
def convert_to_int(value):
    if value is not None:
        try:
            value = int(value)
        except ValueError:
            # Handle the case where value is not convertible to an integer
            print("Value is not convertible to an integer")

    return value

# Pull out hyperparameters from the environment variable
epoch = convert_to_int(hps[0])
batchsize = convert_to_int(hps[1])
units1 = convert_to_int(hps[2])
units2 = convert_to_int(hps[3])
units3 = convert_to_int(hps[4])
lrate = hps[5]
layers=convert_to_int(hps[6])
# Perform operatins using hyperparameters

#read in numpy arrays
X_train=np.load("data/x_train_samp.npy")
X_test=np.load("data/x_test_samp.npy")
y_train=np.load("data/y_train_samp.npy")
y_test=np.load("data/y_test_samp.npy")

#use early stopping to determine epoch number for best combination of hps
#define callbacks for early stopping 
es = EarlyStopping(monitor='val_loss', mode='min', verbose=1,patience=5, restore_best_weights=True)

#Define model--change depending on how many layers 
if layers ==1:
    model = Sequential()
    model.add(LSTM(units1, return_sequences=False, input_shape=(X_train.shape[1], X_train.shape[2])))
    model.add(Dense(1))
    model.compile(optimizer=Adam(learning_rate=lrate), loss='mean_squared_error')
elif layers==2:
    model = Sequential()
    model.add(LSTM(units1, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
    model.add(LSTM(units2, return_sequences=False))  # Second LSTM layer with 100 units, return_sequences is False for the final LSTM layer
    model.add(Dense(1))
    model.compile(optimizer=Adam(learning_rate=lrate), loss='mean_squared_error')
elif layers ==3:
    model = Sequential()
    model.add(LSTM(units1, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
    model.add(LSTM(units2, return_sequences=True))  
    model.add(LSTM(units3, return_sequences=False))  
    model.add(Dense(1))
    model.compile(optimizer=Adam(learning_rate=lrate), loss='mean_squared_error')
# Train the model
start_time = datetime.now()
history = model.fit(X_train, y_train,validation_data=[X_test,y_test], epochs=epoch, batch_size=batchsize, verbose=2,callbacks=[es])
end_time = datetime.now() 
#calculate time to train
time_train=end_time-start_time

# Predict
start_time = datetime.now()
y_pred = model.predict(X_test)
end_time = datetime.now() 
time_test=end_time-start_time

# Calculate evaluation metrics
rmse_score = mean_squared_error(y_test, y_pred, squared=False)
r2 = r2_score(y_test,y_pred)

# Display metrics
print(f'R^2 Score: {r2}',f'RMSE Score: {rmse_score}')

#savve number of epochs run 
epoch=len(history.history['loss'])

#record model parameters and metrics
#save metrics
data = {'epoch': epoch, 
    'batch_size':batchsize,
    'units1': units1,
    'units2':units2,
    'lrate':lrate,
    'layers':[2],
    'rmse': [rmse_score],
    'r2': [r2],
    'time_train':[time_train],
    'time_test':[time_test]}

df = pd.DataFrame(data)

def convert_to_str(value):
    if value is not None:
        try:
            value = str(value)
            return value
        except ValueError:
            # Handle the case where value is not convertible to an integer
            print("Value is not convertible to an integer")
    else:
        return "NA"
    

# Save to CSV
base_fp = "Early_stopped" + "_" + convert_to_str(batchsize) + "_" + convert_to_str(units1) + "_"+ convert_to_str(units2)+"_"+convert_to_str(units3)+"_"+str(lrate)+"_"+convert_to_str(layers)

metric_fp="/app/output/metrics_" + base_fp +".csv"
df.to_csv(metric_fp, index=False)

#save model
model_fp="/app/output/model_" + base_fp + ".keras"

model.save(model_fp)
