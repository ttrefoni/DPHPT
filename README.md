# A Docker Approach to Parallel Hyper-Parameter Tuning 

## Project Background 

## ProjectGoal
The purpose of running multiple hyper-parameter (HP) tuning experiments simultaneously is to decrease the time required to find the optimal combination of hyperparameters for a specified model and training data set. As some of these models can take hours to train and users may want to consider hundreds of combinations of hyperparameters, training multiple sets of hyperparameters simultaneously can save hundreds of hours of computation time. Utilizing Docker, Python, and shell script this process solicits user input of hyperparameters, trains a model for each combination of hyperparameters and calculates metrics and predicted values for each model. This method was originally developed to tune long short-term memory models using Tensorflow for the purpose of calibrating purple air PM2.5 stations.  

## (table of Contents)

# **Implementation Guidence**

## Docker Background

## Set Up Linux Envionrment 
This process is intended to leverage multiple large Linux instances to run dozens of computationally expensive tunes simultaneously. 
### Set up Docker
1. Create a docker account account: https://docs.docker.com/docker-id/
2. Install Docker in your Linux Enviornment: https://docs.docker.com/desktop/install/linux-install/
3. Log in to your Docker account 
    
        Sudo su 

        Docker login
   
### Create a shared, mounted folder so that all Linux machines:
If you have multiple instances where you want to run experiments, all machines need to be able to read the necessary Python scripts and maintain a database of tuning results. There are multiple ways to do this, but one popular solution is to use Samba. A basic tutorial is included below, but more information is available at [Samba Wiki](https://wiki.samba.org/index.php/Main_Page).

For each Linux Instance: 

1. Create a directory to mount the SMB share. In our case, we created this at `/srv/samba/hp_tune_grid/`.

2. Install the `cifs-utils` package if it's not already installed. This package is necessary for mounting SMB/CIFS shares. You can install it by running:

    ```bash
    sudo apt update && sudo apt install cifs-utils
    ```

3. Create a mount point where you'll mount the shared directory:

    ```bash
    mkdir ~/samba-share
    ```

4. Mount the share using the `mount` command on each client machine. You'll need to specify the Samba share's path, the mount point, and your credentials:

    ```bash
    sudo mount -t cifs -o username=sambausername,password=sambapassword //server-ip/sharename ~/samba-share
    ```

Replace sambausername and sambapassword with your Samba credentials, server-ip with the IP address of your Samba server, and sharename with the name of your share.

To have the Samba share automatically mounted at boot, you'll edit the /etc/fstab file, on each client machine:

1.	Open /etc/fstab in a text editor with root privileges:

  	 ```bash
    sudo nano /etc/fstab
    ```
  	
3.	Add a line for the Samba share at the end of the file:

    ```bash
    //server-ip/sharename /path/to/mountpoint cifs username=sambausername,password=sambapassword,iocharset=utf8 0 0
    ```
  	
Replace the placeholders with your actual data. This will allow you to access a shared folder across all instances. 

## Operationalizing Docker Process
### Create template and RUNS directories in the shared folder.

1. Download the 'template' directory from this github (link). This directory contains all the scripts neccessary to build a Docker image, create a compose file to start Docker containers, and create and manage a hyper-parameter grid. Running the included shell script will copy this directory into a new folder for each run that you initialize. 
3. Copy the template directory as root user. 
   ```bash
   sudo su
   cp -r /path/to/template/ /path/to/mountpoint/template
   ```
   
4. Create a "RUNS" directory to store individual runs. This allows you to track each hyper-parameter tuning experiment and keep versions seperate, for example if you wish to adjust your model or change the hyperparameter grid. 
   ```bash
   sudo su
   cd /path/to/mountpoint/
   mkdir RUNS
   ```
   
In order to make changes for each run, simply adjust the scripts in the template folder as desired and re-run https://github.com/ttrefoni/pm25_docker/blob/run_on_shared/auto_docker_server_new_wait.sh. 

It is highly reccomended that you maintain a backup version of the template directory that contians the orginal version of the scripts:
```bash
   sudo su
   cp -r /path/to/mountpoint/template /path/to/mountpoint/template_backup
```


### Idenfify or Create Docker Image 
**Example with LSTM**

#### Option 1: Use an already exisiting Docker image: 
For example, this is the Docker Hub repository for the LSTM used in the example below, if you pull this image, the included Dockerfile will run properly as is. 
<img width="1014" alt="docker_hub_sc" src="https://github.com/ttrefoni/pm25_docker/assets/162225698/0f034105-a20c-45e4-a146-ec8eeb837564">

#### Option 2: Create your own Docker image

1. Create a Dockerfile: 
A Dockerfile contains the instructions for how to build a Docker image, which is then accessed from each machine and used to train the ML model. The Dockerfile for the LSTM is incldued in the template folder.
```bash
    FROM python:3.9
    
    ENV DEBIAN_FRONTEND=noninteractive
    
    #installs requirment packages
    COPY requirements.txt /requirements.txt
    RUN pip install --no-cache-dir -r requirements.txt
    
    COPY data /data
    COPY LSTM_model_fit.py /LSTM_model_fit.py
    COPY LSTM_model_fit_ES.py /LSTM_model_fit_ES.py
```
This Dockerfile is quite simple, it first sets the Python image to the default Python 3.9 image from Docker Hub, then sets the enviornment as a noninteractive to avoid addtional messages related to package installation, then it installs the requried pacakges from the "requriments.txt" file using pip. Finally it copies the training data and machine learning scripts from the local machine to the Docker container. If you write your own machine leanring script, be sure to place them in the "template" folder and adjust the "COPY" lines of the Dockerfile. 

2. Build the Docker Image
   ```bash
   docker build <my-image-name:tag> .
   ```
This command builds the Docker image on your local machine.

3. Create a repository on Docker Hub to access for each run:
   a. Log in or create an account at https://hub.docker.com
   b. Create a repository for your project:
   <img width="921" alt="docker_repos_create" src="https://github.com/ttrefoni/pm25_docker/assets/162225698/2d722ee7-9c43-4d47-92b1-e5411d19424b">
   c: Push your image to the repository
   ```bash
   docker push your-dockerhub-username/my-python-app:latest
   ```

   eg:
   ```bash
   docker push ttrefogmu/pm25_pub:v6
   ```
   The docker image is now hosted on the repository and ready to be pulled by the [shell script](auto_docker_server_new_wait.sh)
   
   
#### Set desired hyper-parameters:
   
The example model, LSTM, uses the following Hyperparameters:

|LSTM /Deep Neural Network|
| ---- | 
|epochs|
|batch size|
|learning rate|
|number layers |
|number of units layer 1|
|number of units layer 2|
|number of units layer 3|

The hyper-parameter grid which will be used for the grid search is included in the script [create_hps_grid.py](template/create_hps_grid.py)

```python
# Define hyperparameters
epoch=[40]
batch_size = [32,64,128]
units1 = [20,50,100,200]
units2 = [20,50,100]
units3=[20,50]
lrate = [0.00001,0.001,0.01]
layers = [1,2,3]
```
To adjust the hyper-parameters for an LSTM model, simply change the range of potential values. This method is intended to be used for LSTM models, but if you would like to train an alternative model with different hyper-parameters you will need to also adjust the following sections of the other scripts:

a. [create_hps_grid.py](template/create_hps_grid.py)
    ```python 
    #line 24-28
    # Create a data frame with all combinations of hyperparameters
    hps = pd.DataFrame(np.array(np.meshgrid(epoch,batch_size, units1, units2, units3, lrate, layers)).T.reshape(-1, 7), columns=['epoch','batch_size', 'units1', 'units2', 'units3','lrate', 'layers'])
    # Give NA values for layers that don't exist
    hps.loc[hps['layers'] == 1, ['units3', 'units2']] = np.nan
    hps.loc[hps['layers'] == 2, 'units3'] = np.nan
    ```

b.  [man_hp_grid.py](template/man_hp_grid.py)
    ```python
    #line 48
    #Update available hps--remove any that are already tested from pool
    hps_available = pd.merge(hps, hps_tested, on=['epoch','batch_size', 'units1', 'units2', 'units3', 'lrate', 'layers'], how='outer', indicator=True).query('_merge == "left_only"').drop('_merge', axis=1)
    #lines 61-65
    # Convert NA values to null for reading in JSON
    hps_to_test['units1'] = hps_to_test['units1'].apply(lambda x: str(x) if not pd.isna(x) else 'null')
    hps_to_test['units2'] = hps_to_test['units2'].apply(lambda x: str(x) if not pd.isna(x) else 'null')
    hps_to_test['units3'] = hps_to_test['units3'].apply(lambda x: str(x) if not pd.isna(x) else 'null')
    ```

c. [compare_col_w_aval.py](template/compare_col_w_aval.py)
    ```python
    #line 21
    hps_tested=hps_tested[["epoch","batch_size","units1","units2","units3","lrate","layers"]]
    ```

d. [LSTM_current.py](template/LSTM_current.py)
Your machine learning script should accept hyper-parameters from the environment variable. In the included LSTM script this is achieved by the following:
    ```python
    #Function to get environment variable or use default value
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
    ```


**If you want to create your own Docker Image:**  
1. First, upload your machine learning script to your Linux instance
    
    A. Ensure that your machine learning training script is set up to recieve Hyper-Parameters in .json format
      
    >Examples of how to read in Hyper-Parameters: 
    ```r
                #R
                   library(jsonlite)

                    #This tool will always save a varible named "combos" to the Container envionrment
                    combos <- Sys.getenv("combos")
                    print(combos)

                    # Parse JSON string
                    hps <- fromJSON(combos)

                    #start for loop for number of comobs--allows user to send multiple sets of hps to each container
                    
                    for(i in c(1:nrow(hps))){
                    # pull out hp from env varible
                    epoch <- hps[i,1] 
                    batch <- hps[i,2] 
                    units1 <- hps[i,3] 
                    units2 <- hps[i,4] 
                    units3 <- hps[i,5]
                    lrate <- hps[i,6]
                    layers <- hps[i,7]
                    
                    ...
                    #continue model training script as desired
                    }
    ```          

    ```python
            #Python:   (double check this--test logic in python)
                import os
                import json

                # Get the 'combos' environment variable
                combos = os.getenv("combos")
                print(combos)

                # Parse JSON string
                hps = json.loads(combos)
                # Iterate over the rows of hps
                for row in hps:
                    epoch = row[0]
                    batch = row[1]
                    units1 = row[2]
                    units2 = row[3]
                    units3 = row[4]
                    lrate = row[5]
                    layers = row[6]

                    # Now you can use these variables as needed in your Python code
                    print(epoch, batch, units1, units2, units3, lrate, layers)
                    
                    #continue model training script as desired
    ```
    B. Pass Envionrment Varibles to Model as Hyper-Parameters 
        
    >Examples: 
    
    ```r
            #R
            lstm_model %>%
            layer_lstm(units = units1, return_sequences = TRUE, input_shape = input_shape) %>%
            #additional lstm layer
            layer_lstm(units = units2) %>%
            # Dense layer
            layer_dense(units = 1) %>%
            # Compile the model
            compile(optimizer = optimizer_adam(learning_rate = lrate),
                    metrics = list("r2"=custom_r_squared),
                    loss = 'mean_squared_error')

            lstm_model %>%
            layer_lstm(units = FLAGS$units1, return_sequences = TRUE, input_shape = input_shape) %>%
            #additional lstm layer
            layer_lstm(units = FLAGS$units2) %>%
            # Dense layer
            layer_dense(units = 1) %>%
            # Compile the model
            compile(optimizer = optimizer_adam(learning_rate = 0.001),
                    metrics = list("r2"=custom_r_squared),
                    loss = 'mean_squared_error')                   
    ```

2. Create Dockerfile:
A Base Dockerfile for LSTM is included in this application "/Dockerfile/ 


3. Prepare .csv of Potential Hyper-Parameters 
    
    Two options are availible, either the user can provide their own pre-detemined list of hyper-parameters, or they can use the applications in-built method of prepaing a dataframe of hyper-parameters for grid search. 

    **Option 1:** Provide a Pre-Prepared .csv
    The csv must have hyper-parameters as the column headers and individual combinations as rows: 
    
    Example: 
   
    |epochs|batch_size|units1|units2|lrate|layers
    | ---- | ---- | ----| ----| ----| ----|
    |50|64|100|50|0.001|2|
    |40|128|125|50|0.001|2|
    |30|32|75|50|0.001|2|
    

    **Option 2:** Use the in-built logic for grid search
    When Prompted, (elaborate here) 





