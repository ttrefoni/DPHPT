# A Docker Approach to Parallel Hyper-Parameter Tuning 

## Project Background 
The purpose of running multiple hyper-parameter (HP) tuning experiments simultaneously is to decrease the time required to find the optimal combination of hyperparameters for a specified model and training data set. As some of these models can take hours to train and users may want to consider hundreds of combinations of hyperparameters, training multiple sets of hyperparameters simultaneously can save hundreds of hours of computation time. 

Utilizing Docker, Python, and shell script this process solicits user input of hyperparameters, trains a model for each combination of hyperparameters and calculates metrics and predicted values for each model. Finally, it conducts an early stopping test to determine the optimal number of epochs for the best combination of hyper-parameters. This method was originally developed to tune long short-term memory models using Tensorflow for the purpose of calibrating purple air PM2.5 stations. However, with a few tweaks a similar approach can be applied to other machine learning tasks and models. 

## Table of Contents
1. [A Docker Approach to Parallel Hyper-Parameter Tuning](#a-docker-approach-to-parallel-hyper-parameter-tuning)
2. [Project Background](#project-background)
3. [Detailed Implementation Guidance](#detailed-implementation-guidance)
    - [Set Up](#set-up)
        - [Set Up Linux Environment](#set-up-linux-environment)
            - [Create a shared, mounted folder so that all Linux machines](#create-a-shared-mounted-folder-so-that-all-linux-machines)
            - [Create template and RUNS directories in the shared folder](#create-template-and-runs-directories-in-the-shared-folder)
        - [Set Up Docker](#set-up-docker)
            - [Create Docker Account](#create-docker-account)
            - [Identify or Create Docker Image](#identify-or-create-docker-image)
                - [Option 1: Use an already existing Docker image](#option-1-use-an-already-existing-docker-image)
                - [Option 2: Create your own Docker image](#option-2-create-your-own-docker-image)
    - [Set desired hyper-parameters](#set-desired-hyper-parameters)
    - [Initialize and Execute Using Shell Script](#initialize-and-execute)
    - [Wrapping Up](#wrapping-up)
4. [Appendix](#appendix)
    - [Section A, List of included scripts](#section-a-list-of-included-scripts)
    - [Section B, Sample Trainin Data](#sample-training-data)
    - [Section C, Application of Tmux](#section-b-application-of-tmux)
    - [Section D, FAQs](#Section-C-FAQs)
    

     

# Detailed Implementation Guidance

## Prerequisites

1. One or more Linux instances that can be accessed through an SSH command using a .pem file.
2. A local machine capable of running shell scirpt. Mac and Linux machines can natively run shell script but Windows users will need to install a Windows Subsystem for Linux. [See appendix B](#sample-training-data)
3. A relevent training dataset designed for use with an appropriate machine learning model. This repository includes some sample training data for use with an LSTM model. 

## Set Up

### Set Up Linux Environment 
This process is intended to leverage multiple large Linux instances to run dozens of computationally expensive tunes simultaneously. 

#### Create a shared, mounted folder so that all Linux machines:
If you have multiple instances where you want to run experiments, all machines need to be able to read the necessary Python scripts and maintain a database of tuning results. There are multiple ways to do this, but one popular solution is to use Samba. A basic tutorial is included below, but more information is available at [Samba Wiki](https://wiki.samba.org/index.php/Main_Page). If you plan to only use one machine, this step is not neccessary. 

For each Linux instance: 

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

Replace `sambausername` and `sambapassword` with your Samba credentials, `server-ip` with the IP address of your Samba server, and `sharename` with the name of your share.

To have the Samba share automatically mounted at boot, you'll edit the `/etc/fstab` file on each client machine:

1. Open `/etc/fstab` in a text editor with root privileges:

    ```bash
    sudo nano /etc/fstab
    ```
  	
2. Add a line for the Samba share at the end of the file:

    ```bash
    //server-ip/sharename /path/to/mountpoint cifs username=sambausername,password=sambapassword,iocharset=utf8 0 0
    ```
  	
Replace the placeholders with your actual data. This will allow you to access a shared folder across all instances. 

#### Create template and RUNS directories in the shared folder.

1. Download the [template](template) directory from this GitHub. This directory contains all the scripts necessary to build a Docker image, create a compose file to start Docker containers, and create and manage a hyper-parameter grid. Running the included shell script will copy this directory into a new folder for each run that you initialize. 

2. If you are using mulitple machines, copy the template directory as the root user to the shared directory created in the previous step. If you are not using multiple machines, simply copy to your working directory. 
   ```bash
   sudo su
   cp -r /path/to/template/ /path/to/mountpoint/template
   ```
   
3. Create a "RUNS" directory to store individual runs. This allows you to track each hyper-parameter tuning experiment and keep versions separate, for example, if you wish to adjust your model or change the hyperparameter grid. 
   ```bash
   sudo su
   cd /path/to/mountpoint/
   mkdir RUNS
   ```
   
To make changes for each run, simply adjust the scripts in the template folder as desired and re-run https://github.com/ttrefoni/pm25_docker/blob/run_on_shared/auto_docker_server_new_wait.sh. 

It is highly recommended that you maintain a backup version of the template directory that contains the original version of the scripts:
    ```bash
    sudo su
    cp -r /path/to/mountpoint/template /path/to/mountpoint/template_backup
    ```

## Set up Docker

### Create Docker Account 
1. Create a Docker account: https://docs.docker.com/docker-id/
2. Install Docker in your Linux environment: https://docs.docker.com/desktop/install/linux-install/
3. Log in to your Docker account 
    
    ```bash
    sudo su 
    docker login
    ```
### Identify or Create Docker Image 

#### Option 1: Use an already existing Docker image: 
For example, this is the Docker Hub repository for the LSTM used in the example below, if you pull this image, the included Dockerfile will run properly as is. 
<img width="1014" alt="docker_hub_sc" src="https://github.com/ttrefoni/pm25_docker/assets/162225698/0f034105-a20c-45e4-a146-ec8eeb837564">

#### Option 2: Create your own Docker image
If you are testing a different model, or would like to adjust the design of the LSTM model included in this example, you will need to build your own Docker image. 


1. Create a Dockerfile: 
A Dockerfile contains the instructions for how to build a Docker image, which is then accessed from each machine and used to train the ML model. The Dockerfile for the LSTM is included in the template folder.
```bash
    FROM python:3.9
    
    ENV DEBIAN_FRONTEND=noninteractive
    
    # installs required packages
    COPY requirements.txt /requirements.txt
    RUN pip install --no-cache-dir -r requirements.txt
    
    COPY data /data
    COPY LSTM_model_fit.py /LSTM_model_fit.py
    COPY LSTM_model_fit_ES.py /LSTM_model_fit_ES.py
```
This Dockerfile is quite simple and carries out the folloiwng: 
* Sets the Python image to the default Python 3.9 image from Docker Hub, then sets the environment as non-interactive to avoid additional messages related to package installation.
* Installs the required packages from the "requirements.txt" file using pip.
* Copies the training data and machine learning scripts from the local machine to the Docker container.
  
If you write your own machine learning script, be sure to place them in the "template" folder and adjust the "COPY" lines of the Dockerfile. 

2. Build the Docker Image
   ```bash
   docker build -t my-image-name:tag .
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

   e.g.:
   ```bash
   docker push ttrefogmu/pm25_pub:v6
   ```
   The Docker image is now hosted on the repository and ready to be pulled by the [shell script](auto_docker_server_new_wait.sh).
   
   
## Set desired hyper-parameters:
   
The example model, LSTM, uses the following hyper-parameters:

| LSTM /Deep Neural Network | Description |
| ---- | ---- |
| epochs | Number of training epochs |
| batch size | Size of each training batch |
| learning rate | Learning rate for optimizer |
| number layers | Number of LSTM layers |
| number of units layer 1 | Number of units in the first LSTM layer |
| number of units layer 2 | Number of units in the second LSTM layer |
| number of units layer 3 | Number of units in the third LSTM layer |

The hyper-parameter grid which will be used for the grid search is included in the script [create_hps_grid.py](template/create_hps_grid.py):

```python
# Define hyperparameters
epoch = [40]
batch_size = [32, 64, 128]
units1 = [20, 50, 100, 200]
units2 = [20, 50, 100]
units3 = [20, 50]
lrate = [0.00001, 0.001, 0.01]
layers = [1, 2, 3]
```

To adjust the hyper-parameters for an LSTM model, simply change the range of potential values. This method is intended to be used for LSTM models, but if you would like to train an alternative model with different hyper-parameters you will need to also adjust the following sections of the other scripts:

a. [create_hps_grid.py](template/create_hps_grid.py)
```python 
# line 24-28
# Create a data frame with all combinations of hyperparameters
hps = pd.DataFrame(np.array(np.meshgrid(epoch, batch_size, units1, units2, units3, lrate, layers)).T.reshape(-1, 7), columns=['epoch', 'batch_size', 'units1', 'units2', 'units3', 'lrate', 'layers'])
# Give NA values for layers that don't exist
hps.loc[hps['layers'] == 1, ['units3', 'units2']] = np.nan
hps.loc[hps['layers'] == 2, 'units3'] = np.nan
```

b.  [man_hp_grid.py](template/man_hp_grid.py)    
```python
# line 48
# Update available hps--remove any that are already tested from pool
hps_available = pd.merge(hps, hps_tested, on=['epoch', 'batch_size', 'units1', 'units2', 'units3', 'lrate', 'layers'], how='outer', indicator=True).query('_merge == "left_only"').drop('_merge', 1)
```

c.  The LSTM training scripts:
   
- [LSTM_model_fit_ES.py](template/LSTM_model_fit_ES.py)
    
- [LSTM_model_fit.py](template/LSTM_model_fit.py)

The above changes will enable you to train any ML model you desire. The Docker image includes everything you need to execute the code and grid search.

## Initialize and Execute
### Set up Shell script 
Adjust the following lines in the included shell script [auto_docker_server_new_wait.sh](auto_docker_server_new_wait.sh) to reflect your .pem file to access those servers and the ip adress of your servers. 

```bash
# Define the list of Linux instances
INSTANCES=("user@IP_Address1" "user@IP_Address2" "user@IP_Address3"...)
# Define pem location
pem="/path/to/.pem"
```

1. Initialize the hyper-parameter tuning process with the `auto_docker_server_new_wait.sh` script. This should be done on a local machine or on a seperate remote machine from the large instances in which the models will be trained. 
```bash
sudo su
chmod +x /path/to/auto_docker_server_new_wait.sh
/path/to/auto_docker_server_new_wait.sh
```

2. The script will prompt you for several pieces of information:

Prompt 1: Asks for the publisher name this is equivalent to your Docker username or the Docker username of the owner of the repository you wish to use. 
```bash
Enter the publisher name:
```

Sample response: 
```bash
ttrefogmu
```

Prompt 2: Equivalent to the Docker "tag" 
```bash
>> Enter the version number:
```

Sample response:
```bash
>> v6
```

Prompt 3: The output directory, which will be located at "/srv/samba/hp_tune_grid/RUNS/<tune_name>"
```bash
>> Enter tune name (output directory)
```

Sample response:
```bash
>> lstm_tune_run_v1
```

Prompt 4: The number of containers to run at once on each instance. The optimal number of tunes will be determined by the computing power available on your instance, the complexity of your model, and the size of your training dataset
```bash
>> Enter number (int) of tunes to run at once on each instance:
```

Sample response:
```bash
>> 20
```


This script will read the hyper-parameter grid and create a new folder for each combination of hyper-parameters within the RUNS directory. Each folder contains a Docker Compose file that initializes a container for the run, which executes the LSTM training script with the specified hyper-parameters. This process will continue until all potential hyper-parameters in the grid search have been tested. 

Results from each hyper-parameter set are stored in directories with the following path convention: 

```bash
/srv/samba/hp_tune_grid/RUNS/<tune_name>/output_py/TUNING/<host_short_name>/hprun_split_container_<containerID>_<num_tunes>
```

3. Throughout the tuning process you can monitor the progress of each run using Docker logs:
```bash
sudo su
docker ps
docker logs <container_id>
```
   
The above commands list the active Docker containers and display the logs for the specified container, allowing you to track the progress of the hyper-parameter tuning process.

4. Once all combinations have been tested, the shell script will run [collate_metrics.py](template/collate_metrics.py) which collects all of the output metrics from each hyper-parameter combination into a single csv file.

As the tuning process can take quite a long time, if the user would like to investigate overall results throughout the tuning process they can run [collate_metrics.py](template/collate_metrics.py) to combine all completed tuning results. This can be helpful to review progress. 

 
## Wrapping Up
Once all runs are complete, the tuning results will be stored in the shared, mounted folder, at /srv/samba/hp_tune_grid/RUNS/<tune_name>/COLLATE/<tune_name>_col.csv

# Appendix 
## Section A, list of included scripts

1: [auto_docker_server_new_wait.sh](auto_docker_server_new_wait.sh) 
    This script is used to initialize the overall hyper-parameter tuning process. It accepts user input over the Docker Image to use, the output location, and the number of tunes to run simultaneously. Next it runs the tuning process, monitors progress, and collects the output metrics. 

2: [create_hps_grid.py](template/create_hps_grid.py)
    This script creates the original hps grid for grid search. By updating the hps set in this script you can adjust the overall hps which will be tested. 
    
3: [man_hp_grid.py](template/man_hp_grid.py)
    This script is used to track which hyper-parameters have already been tested in order to ensure that a combination of hyper-parameters is not tested more than once. [auto_docker_server_new_wait.sh](auto_docker_server_new_wait.sh) will call this script throughout the tuning process to manage the .csv files which track which hyperparameters have already been tested and which are still available. 

4. [compare_col_w_aval.py](template/compare_col_w_aval.py)
    This script is used in [auto_docker_server_new_wait.sh](auto_docker_server_new_wait.sh) to check the hps_tested against those that are output in from [collate_metrics.py](template/collate_metrics.py). This helps to resolve issues that would come up if the tuning process gets interrupted. This script compares the potential hyperparameter combinations with those that have already been completed.

5. [gen_comp_file_py_auto.py](template/gen_comp_file_py_auto.py)
    This script creates the compose file (a .yml) which details the parameters for each Docker container. This includes the hyper-parameters, which port to be run, and the machine learning script to be run. It also creates the directories in which each container's output is stored and mounts the output of the Docker containers to those locations. As the tuning process is run by [auto_docker_server_new_wait.sh](auto_docker_server_new_wait.sh), this script is run once for each set of combinations.
    
6. [gen_comp_file_ES.py](template/gen_comp_file_ES.py)
    This script fulfills the same role as [gen_comp_file_py_auto.py](template/gen_comp_file_py_auto.py), but is designed to set up the .yml compose file for the early stopping portion of training.

7. [LSTM_current.py](template/LSTM_current.py)
    This script is run in a Docker Container, it ingests the given hyper-parameter combination, then trains an LSTM model using three fold cross validation, records the metrics (RMSE and RSquared) and training history and saves them to a .csv file in the mounted folder. 

8. [LSTM_current_ES.py](template/LSTM_current_ES.py)
   This script trains the LSTM with the best combination of hyper-parameters (by RSquared) using an early stopping method to determine the optimal number of epochs. 
    
## Section B, Application of Tmux
Becuase the hyper-parameter tuning process can take several days, it is highly recommended to run [autodocker_server_new_wait.sh](autodocker_server_new_wait.sh) in a detached terminal to avoid losing work if the terminal it is being ran on becomes disconnected. It is even better to run this shell script on a dedicated remote machine. One common way to run processes in the background is to use tmux. 

[Documentation for tmux](https://github.com/tmux/tmux/wiki)

[Helpful Quick Start guide](https://www.redhat.com/sysadmin/introduction-tmux-linux#:~:text=You%20can%20detach%20from%20your,detach%20from%20the%20current%20session.)

## Section C, Sample Training Data
Included on this repo is a folder with sample training data for the base LSTM model. This data is incldued so the user can test and explore the application of this Docker based Hyper-parameter tuning tool. 

This training data is intended to calibrate Purple Air sensors to regulatory performance. The covariates include Purple Air readings, relative humidty,and temperature. For the LSTM they are organized into numpy arrays with the shape [n,24,3] for input data and [n] for predicted data, where 3 is the number of covariates and 24 is the number of hours included in each sequence. No further pre-processing is needed to use this data for hyper-parameter tuning. 

## Section D, FAQs
1. Is it possible to run this proces in Windows or Mac computing enviornments?
   
This process was designed to be run on networked linux machines. You may need to adjust certain aspects of the process such as mounting a shared folder using Samba to run tuning on Windows or Mac. It is possible to run the included shell script which manages the training process on Windows or Mac. On a Windows machine you will likely need to isntall a [Windows Subsystem for Linux (WSL)](https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://learn.microsoft.com/en-us/windows/wsl/install&ved=2ahUKEwjBh8CF4IiHAxUpGVkFHQgZCSYQFnoECBgQAQ&usg=AOvVaw3NDNYJVUKnKqnP9DjgAR3M) to successfully run shell scripts. 

