# A Docker Approach to Parallel Hyper-Parameter Tuning 

## Project Background 

## Table of Contents
1. [Project Background](#project-background)
2. [Table of Contents](#table-of-contents)
3. [Implementation Guidance](#implementation-guidance)
    - [Docker Background](#docker-background)
    - [Set Up Linux Environment](#set-up-linux-environment)
        - [Set up Docker](#set-up-docker)
        - [Create a shared, mounted folder](#create-a-shared-mounted-folder)
    - [Operationalizing Docker Process](#operationalizing-docker-process)
        - [Create template and RUNS directories](#create-template-and-runs-directories)
        - [Identify or Create Docker Image](#identify-or-create-docker-image)
            - [Use an already existing Docker image](#use-an-already-existing-docker-image)
            - [Create your own Docker image](#create-your-own-docker-image)
        - [Set desired hyper-parameters](#set-desired-hyper-parameters)
        - [Initialize and Execute](#initialize-and-execute)
        - [Wrapping Up](#wrapping-up)
# **Implementation Guidance**

## Docker Background

## Set Up Linux Environment 
This process is intended to leverage multiple large Linux instances to run dozens of computationally expensive tunes simultaneously. 

### Set up Docker
1. Create a Docker account: https://docs.docker.com/docker-id/
2. Install Docker in your Linux environment: https://docs.docker.com/desktop/install/linux-install/
3. Log in to your Docker account 
    
    ```bash
    sudo su 
    docker login
    ```

### Create a shared, mounted folder so that all Linux machines:
If you have multiple instances where you want to run experiments, all machines need to be able to read the necessary Python scripts and maintain a database of tuning results. There are multiple ways to do this, but one popular solution is to use Samba. A basic tutorial is included below, but more information is available at [Samba Wiki](https://wiki.samba.org/index.php/Main_Page).

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

## Operationalizing Docker Process
### Create template and RUNS directories in the shared folder.

1. Download the 'template' directory from this GitHub (link). This directory contains all the scripts necessary to build a Docker image, create a compose file to start Docker containers, and create and manage a hyper-parameter grid. Running the included shell script will copy this directory into a new folder for each run that you initialize. 
2. Copy the template directory as the root user. 
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


### Identify or Create Docker Image 

#### Option 1: Use an already existing Docker image: 
For example, this is the Docker Hub repository for the LSTM used in the example below, if you pull this image, the included Dockerfile will run properly as is. 
<img width="1014" alt="docker_hub_sc" src="https://github.com/ttrefoni/pm25_docker/assets/162225698/0f034105-a20c-45e4-a146-ec8eeb837564">

#### Option 2: Create your own Docker image

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
This Dockerfile is quite simple. It first sets the Python image to the default Python 3.9 image from Docker Hub, then sets the environment as non-interactive to avoid additional messages related to package installation. It then installs the required packages from the "requirements.txt" file using pip. Finally, it copies the training data and machine learning scripts from the local machine to the Docker container. If you write your own machine learning script, be sure to place them in the "template" folder and adjust the "COPY" lines of the Dockerfile. 

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
   
   
#### Set desired hyper-parameters:
   
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
    * [LSTM_model_fit_ES.py](template/LSTM_model_fit_ES.py)
    * [LSTM_model_fit.py](template/LSTM_model_fit.py)

The above changes will enable you to train any ML model you desire. The Docker image includes everything you need to execute the code and grid search.

### Initialize and Execute
1. Initialize the hyper-parameter tuning process with the `auto_docker_server_new_wait.sh` script. 
   ```bash
   sudo su
   /path/to/mountpoint/template/auto_docker_server_new_wait.sh
   ```
2. The script will prompt you for several pieces of information:

Prompt 1: Asks for the publisher name this is equivalent to your Docker username or the Docker username of the owner of the repository you wish to use. 
```bash
Enter the publisher name:
```

Sample response: 
```bash
ttregogmu
```

Prompt 2: Equivalent to the Docker "tag" 
```bash
Enter the version number:
```

Sample response:
```bash
v6
```

Prompt 3: The output directory, which will be located at "/srv/samba/hp_tune_grid/RUNS/<tune_name>"
```bash
Enter tune name (output directory)
```

Sample response:
```bash
lstm_tune_run_v1
```

Prompt 4: The number of containers to run at once on each instance. The optimal number of tunes will be determined by the computing power available on your instance, the complexity of your model, and the size of your training dataset
```bash
Enter number (int) of tunes to run at once on each instance:
```

Sample response:
```bash
20
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

As the tuning process can take quite a long time, if the user would like to investigate overall results throughout the tuning process they can run [collate_metrics.py](template/collate_metrics.py to combine all completed tuning results. This can be helpful to review progress. 

 
### Wrapping Up
Once all runs are complete, the tuning results will be stored in the shared, mounted folder, at /srv/samba/hp_tune_grid/RUNS/<tune_name>/COLLATE/<tune_name>_col.csv
