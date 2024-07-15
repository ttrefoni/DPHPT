import pandas as pd
import os
import csv
import numpy as np
import json
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam
from keras.callbacks import Callback
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, r2_score
from datetime import datetime
import keras.backend as K

# Callback to stop training if loss is NaN
class NaNLossCallback(Callback):
    def on_epoch_end(self, epoch, logs=None):
        loss = logs.get('loss')
        if np.isnan(loss):
            print(f"Epoch {epoch}: Loss is NaN, stopping training.")
            self.model.stop_training = True

# Callback to stop training if loss exceeds a threshold at a specific epoch
# class LossThresholdCallback(Callback):
#     def __init__(self, threshold, epoch_to_check, lt_signifier):
#         super(LossThresholdCallback, self).__init__()
#         self.threshold = threshold
#         self.epoch_to_check = epoch_to_check
#         self.lt_signifier = lt_signifier
    
#     def on_epoch_end(self, epoch, logs=None):
#         if epoch == self.epoch_to_check:
#             val_loss = logs.get('val_loss')
#             if val_loss is not None and val_loss > self.threshold:
#                 self.lt_signifier[0] = True
#                 print(f"Epoch {epoch}: val_loss= {val_loss} which is above LT of {self.threshold}, stopping training.")
#                 self.model.stop_training = True

# Save history callback to save history to file
class SaveHistory(keras.callbacks.Callback):
    def __init__(self, history_dir, history_fp):
        super(SaveHistory, self).__init__()
        self.history_dir = history_dir
        self.history_fp = history_fp

    def on_epoch_end(self, epoch, logs=None):
        if 'lr' not in logs.keys():
            logs['lr'] = K.get_value(self.model.optimizer.lr)

        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)

        history_path = os.path.join(self.history_dir, self.history_fp)
        
        file_exists = os.path.isfile(history_path)
        
        with open(history_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=logs.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(logs)

# Read in training data
X_train = np.load("data/x_train_samp.npy")
X_test = np.load("data/x_test_samp.npy")
y_train = np.load("data/y_train_samp.npy")
y_test = np.load("data/y_test_samp.npy")

# Ensure consistent data types for inputs and labels
X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
y_train = y_train.astype('float32')
y_test = y_test.astype('float32')

# Function to get environment variable or use default value
def get_env_var(var_name):
    val = os.getenv(var_name)
    if val is None:
        raise ValueError(f"Environment variable {var_name} not set.")
    return val

# Get the environment variable "combos" or use a default value
combos = get_env_var("combos")

# Parse the JSON string
hps = json.loads(combos)

# Function to convert to int unless it is null
def convert_to_int(value):
    if value is not None:
        try:
            value = int(value)
        except ValueError:
            # Handle the case where value is not convertible to an integer
            print("Value is not convertible to an integer")
    return value

#  Define the loss threshold and epoch to check at-- this is to exit poor performers quickly 
# loss_threshold = 25  # Set your threshold here
# epoch_to_check = 10  # Set the specific epoch you want to check

# Function to convert to str unless it is null
def convert_to_str(value):
    if value is not None:
        try:
            value = str(value)
            return value
        except ValueError:
            # Handle the case where value is not convertible to a string
            print("Value is not convertible to a string")
    else:
        return "NA"

# Start for loop for number of combos
for i in range(len(hps)):
    # Pull out hyperparameters from the environment variable
    epoch = convert_to_int(hps[i][0])  
    batchsize = convert_to_int(hps[i][1])
    units1 = convert_to_int(hps[i][2])
    units2 = convert_to_int(hps[i][3])
    units3 = convert_to_int(hps[i][4])
    lrate = hps[i][5]
    layers = convert_to_int(hps[i][6])

    # Perform operations using hyperparameters
    print(epoch, batchsize, units1, units2, units3, lrate, layers)

    # Use CV to find the best combination of hps
    # Define the number of folds
    num_folds = 3
    seed = 42
    # Initialize KFold
    kf = KFold(n_splits=num_folds, shuffle=True, random_state=seed)
    # Initialize lists to store evaluation metrics
    rmse_values = []
    r2_scores = []
    times_train = []
    times_test = []

    #set early stop to false as default,
    # LT = [False]

    # Loop over the folds
    for fold, (train_index, test_index) in enumerate(kf.split(X_train)):
        #if Loss Threshold callback is activated, break folds loop 
        # if LT[0]:
        #     print("Loss Threshold exceeded, exiting fold loop early.")
        #     break

        # Define callbacks for early stopping     
        print(f"Fold {fold+1}/{num_folds}")
        # Split data into train and test sets for this fold
        X_train_cv, X_test_cv = X_train[train_index], X_train[test_index]
        y_train_cv, y_test_cv = y_train[train_index], y_train[test_index]

        # Ensure consistent data types for cross-validation splits
        X_train_cv = X_train_cv.astype('float32')
        X_test_cv = X_test_cv.astype('float32')
        y_train_cv = y_train_cv.astype('float32')
        y_test_cv = y_test_cv.astype('float32')

        # Define model--change depending on how many layers
        if layers == 1:
            model = Sequential()
            model.add(LSTM(units1, return_sequences=False, input_shape=(X_train.shape[1], X_train.shape[2])))
            model.add(Dense(1))
        elif layers == 2:
            model = Sequential()
            model.add(LSTM(units1, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
            model.add(LSTM(units2, return_sequences=False))  # Second LSTM layer
            model.add(Dense(1))
        elif layers == 3:
            model = Sequential()
            model.add(LSTM(units1, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
            model.add(LSTM(units2, return_sequences=True))  
            model.add(LSTM(units3, return_sequences=False))  
            model.add(Dense(1))
        
        model.compile(optimizer=Adam(learning_rate=lrate), loss='mean_squared_error', metrics=[tf.keras.metrics.RootMeanSquaredError()])

        # Set history file path 
        history_dir = "/app/output/"
        history_fp= f"history_{convert_to_str(epoch)}_{convert_to_str(batchsize)}_{convert_to_str(units1)}_{convert_to_str(units2)}_{convert_to_str(units3)}_{str(lrate)}_{convert_to_str(layers)}_fold_{convert_to_str(fold)}.csv"

        # Train the model with the custom callbacks
        start_time = datetime.now()
        history = model.fit(
            X_train_cv, y_train_cv,
            validation_data=(X_test_cv, y_test_cv),
            epochs=epoch,
            batch_size=batchsize,
            verbose=1,
            callbacks=[
                NaNLossCallback(),
                #LossThresholdCallback(threshold=loss_threshold, epoch_to_check=epoch_to_check, lt_signifier=LT),
                SaveHistory(history_dir, history_fp)
            ]
        )

        end_time = datetime.now() 
        # Calculate time to train
        time_train = end_time - start_time

        # Predict
        start_time = datetime.now()
        y_pred = model.predict(X_test_cv)
        end_time = datetime.now() 
        time_test = end_time - start_time

        mse_value = mean_squared_error(y_test_cv, y_pred)
        if np.isnan(mse_value) or mse_value < 0:
            print("Warning: MSE is NaN or negative, setting RMSE to NaN.")
            rmse_value = np.nan
        else:
            rmse_value = np.sqrt(mse_value)

        # Calculate R2
        r2 = r2_score(y_test_cv, y_pred)
        # Append metrics to lists
        rmse_values.append(rmse_value)
        r2_scores.append(r2)
        times_train.append(time_train)
        times_test.append(time_test)
        # Display metrics
        print(f'R^2 Score: {r2}', f'RMSE Score: {rmse_value}')

    #define output fp
    base_fp = convert_to_str(epoch) + "_" + convert_to_str(batchsize) + "_" + convert_to_str(units1) + "_"+ convert_to_str(units2)+"_"+convert_to_str(units3)+"_"+str(lrate)+"_"+convert_to_str(layers)

    # After all folds, print average metrics
    #need to account for nan
    if np.isnan(rmse_values).any():
        print(f'RMSE is nan')
        rmse_mean = "NA"
        r2_mean = "NA"
        time_tr_mean = "NA"
        time_tst_mean = "NA"
    elif np.isnan(r2_scores).any():
        print(f'R2 is nan')
        rmse_mean = "NA"
        r2_mean = "NA"
        time_tr_mean = "NA"
        time_tst_mean = "NA"
    #if early stop is activated, note it 
    # elif LT[0]:
    #     print(f'LT activated, not considering')
    #     rmse_mean = "NA"
    #     r2_mean = "NA"
    #     time_tr_mean = "NA"
    #     time_tst_mean = "NA"
    else:
        print(f'Average RMSE across all folds: {np.mean(rmse_values)}')
        print(f'Average R^2 across all folds: {np.mean(r2_scores)}')
        rmse_mean = np.mean(rmse_values)
        r2_mean = np.mean(r2_scores)
        time_tr_mean = np.mean(times_train)
        time_tst_mean = np.mean(times_test)
        # Save metrics from all folds
        data_fld = {'fold': list(range(1, num_folds + 1)), 'rmse': rmse_values, 'r2': r2_scores}
        print(data_fld)

        df_fld = pd.DataFrame(data_fld)
        #save folds record 
        fold_fp = os.path.join("/app/output", "fold_" + base_fp + ".csv")
        df_fld.to_csv(fold_fp, index=False)

    # Record model parameters and metrics
    # Save metrics
    data = {'epoch': epoch, 
            'batch_size': batchsize,
            'units1': units1,
            'units2': units2,
            'units3': units3,
            'lrate': lrate,
            'layers': [layers],
            'rmse': [rmse_mean],
            'r2': [r2_mean],
            'time_train': [time_tr_mean],
            'time_test': [time_tst_mean]}

    df = pd.DataFrame(data)

    # Save to CSV
    base_fp = f"{convert_to_str(epoch)}_{convert_to_str(batchsize)}_{convert_to_str(units1)}_{convert_to_str(units2)}_{convert_to_str(units3)}_{str(lrate)}_{convert_to_str(layers)}"
    metric_fp = os.path.join("/app/output", f"metrics_{base_fp}.csv")
    df.to_csv(metric_fp, index=False)
