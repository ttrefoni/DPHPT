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
   
#### Create a shared, mounted folder so that all Linux machines:
All machines need to be able to read the neccessary Python Scripts and maintain a database of tuning results. There are multiple ways to do this, but one popular solution is to use Samba. A basic tutorial is incldued below, but more information is availbale at https://wiki.samba.org/index.php/Main_Page

1. Create a directory on each Linux instance to mount the SMB share, in our case we created this at /srv/samba/hp_tune_grid/
2. Install the cifs-utils package if it's not already installed. This package is necessary for mounting SMB/CIFS shares. You can install it by running:

       bash
       sudo apt update && sudo apt install cifs-utils
   
4.  Create a mount point where you'll mount the shared directory:

       bash
       mkdir ~/samba-share
    
6.	Mount the share using the mount command. You'll need to specify the Samba share's path, the mount point, and your credentials:

  	    bash
        sudo mount -t cifs -o username=sambausername,password=sambapassword //server-ip/sharename ~/samba-share

Replace sambausername and sambapassword with your Samba credentials, server-ip with the IP address of your Samba server, and sharename with the name of your share.

To have the Samba share automatically mounted at boot, you'll edit the /etc/fstab file:
1.	Open /etc/fstab in a text editor with root privileges:

        bash
        sudo nano /etc/fstab
  	
3.	Add a line for the Samba share at the end of the file:

        //server-ip/sharename /path/to/mountpoint cifs username=sambausername,password=sambapassword,iocharset=utf8 0 0
  	
Replace the placeholders with your actual data. 


## Operationalizing Docker Process

### Idenfify or Create Docker Image 
**If a Docker Image Already Exisits for your purpose**
#### 1. Locate the Repository and Version Name 
    
    ![Caption: Sample Docker Repository](images/docker_hum_image)
#### 2. Ensure you know the Hyper-Parameters Relevent to your model 
   
This guide provides information an example modelm LSTM which uses the following Hyperparameters:

|LSTM /Deep Neural Network|
| ---- | 
|epochs|
|batch size|
|learning rate|
|number layers |
|number of units layer 1|
|number of units layer 2|
|          ...          |
|number of units layer ***n***|


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





