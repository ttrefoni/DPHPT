#!/bin/bash

# Function to handle errors
handle_error() {
    echo "Error on line $1: $2"
    exit 1
}

# Trap errors and call handle_error with the line number and error message
trap 'handle_error $LINENO "$BASH_COMMAND"' ERR

# Accept user input for publisher name
echo "Enter the publisher name:"
read pub

# Accept user input for repository name
echo "Enter the repository name:"
read repository_name

# Accept user input for version number
echo "Enter the version number:"
read version_number

# Solicit output directory name 
echo "Enter tune name (output directory):"
read tune_name

# Solicit number of tunes to run at once 
echo "Enter number (int) of tunes to run at once on each instance:"
read num_tunes

# Define the list of Linux instances
INSTANCES=("ubuntu@10.192.20.201")
# Define pem location
pem="/Users/theodoretrefonides/Downloads/shyra.pem"

# Path to the mounted folder, if you adjusted the name of the mounted folder, change your path below
mounted_folder="/srv/samba/hp_tune_grid"
#create working directory 
directory="$mounted_folder/timer/RUNS_timer/$tune_name"
#create working directory and 
# Check if directory exists and create if not
if ssh -i "$pem" "${INSTANCES[0]}" "[ ! -d \"$directory\" ]"; then
  commands="
    # Make RUNS folder 
    mkdir -p $directory
    # Change to copy template at the location supplied by variable 
    cp -r $mounted_folder/timer/template_timer/. $directory 
    chmod -R 0777 $directory 
    echo 'Creating new working directory'
  "
  ssh -i "$pem" "${INSTANCES[0]}" "$commands" || { echo "Failed to create directory"; exit 1; }
fi

#install required packages on linux instances 
for INSTANCE in "${INSTANCES[@]}"; do
  #install required packages in each instance 
  commands="
    sudo apt-get update
    sudo apt-get install -y python3-pip
    pip install --no-cache-dir -r $directory/requirements.txt
    "
  echo "installing required packages on  $INSTANCE..."
  ssh -i $pem "$INSTANCE" "$commands"
done

# Define your Python scripts and Docker container
gen_comp="$directory/gen_comp_file_py_auto.py"
man_grid="$directory/man_hp_grid.py"
create_grid="$directory/create_hps_grid.py"

# Dry run manage script to ensure that hps available .csv exists 
ssh -i $pem "${INSTANCES[0]}" python3 $create_grid $directory

# Check if hps_available.csv exists, if not, use the base number of hps in the grid 
if ssh -i "$pem" "${INSTANCES[0]}" "[ -f \"$directory/hps_available.csv\" ]"; then
  hp_aval_ct=$(ssh -i "$pem" "${INSTANCES[0]}" "wc -l < \"$directory/hps_available.csv\"")
else
  hp_aval_ct=$(ssh -i "$pem" "${INSTANCES[0]}" "wc -l < \"$directory/hps_original_grid.csv\"")
fi

echo "Updating hps_tested.csv to hps from collate"

# Collate metrics--if there are results--sets available tunes 
echo "Collating metrics"
for INSTANCE in "${INSTANCES[@]}"; do
    collate_metrics="$directory/collate_metrics.py"
    commands="
      export TUNE_NAME=\"$tune_name\";
      hostname_var=\$(hostname);
      echo \$hostname_var;
      python3 $collate_metrics $tune_name $directory \$hostname_var;
    "
    echo "Collating metrics on ${INSTANCE}..."
    ssh -i $pem "$INSTANCE" "$commands"
done
echo "Collated"

# Compare hps available and collated output 
echo "Comparing collate with available"
comp_col_aval="$directory/compare_col_w_aval.py"
commands="
  export TUNE_NAME=\"$tune_name\";
  sudo python3 $comp_col_aval $tune_name $directory;
"
ssh -i $pem "${INSTANCES[0]}" "$commands"

og_ct=$(ssh -i "$pem" "${INSTANCES[0]}" "wc -l < \"$directory/hps_original_grid.csv\"")

# Check if the file exists and count the lines, otherwise set to 0
if ssh -i "$pem" "${INSTANCES[0]}" "[ -f \"$directory/output_py/COLLATE/{$tune_name_col}.csv\" ]"; then
  hps_tested_ct=$(ssh -i "$pem" "${INSTANCES[0]}" "wc -l < \"$directory/output_py/COLLATE/{$tune_name_col}.csv\"")
else
  hps_tested_ct=0
fi

hp_aval_ct=$(ssh -i "$pem" "${INSTANCES[0]}" "wc -l < \"$directory/hps_available.csv\"")

echo "Original hp count = $og_ct"
echo "hps_tested count = $hps_tested_ct"
echo "hps available now = $hp_aval_ct"

#counter for calculating how many tune runs to complete 
q=1
docker_name="${pub}/${repository_name}:${version_number}"
echo $docker_name

# Function to check if all Docker containers are finished
check_containers() {
  for INSTANCE in "${INSTANCES[@]}"; do
    while true; do
    #wait ten seconds to allow containers to initialize
      sleep 10
      # Check if there are any running containers
      running_containers=$(ssh -i "$pem" "$INSTANCE" "sudo docker ps -q | wc -l")
      
      # If no containers are running, check their exit status
      if [ "$running_containers" -eq 0 ]; then
        exited_containers=$(ssh -i "$pem" "$INSTANCE" "sudo docker ps -a --filter 'status=exited' --format '{{.ID}} {{.Status}}'")
        
        # If there are exited containers, check their exit codes
        if [ -n "$exited_containers" ]; then
          while read -r container_id status; do
            exit_code=$(ssh -i "$pem" "$INSTANCE" "sudo docker inspect $container_id --format '{{.State.ExitCode}}'")
            if [ "$exit_code" -ne 0 ]; then
              echo "Container $container_id on $INSTANCE exited with code $exit_code"
              exit 1
            fi
          done <<< "$exited_containers"
        fi
        break
      fi

      echo "Waiting for containers to finish on $INSTANCE..."
      sleep 30  # Adjust the sleep time as necessary
    done
  done
}

# Main loop to run hps
while [ $hp_aval_ct -gt 1 ]; do
  for INSTANCE in "${INSTANCES[@]}"; do
    if [ $hp_count -lt $(($num_tunes * ${#INSTANCES[@]})) ]; then
      echo "Less hps than containers*instances: splitting evenly"
      num_tunes=$(( ($hp_count / ${#INSTANCES[@]}) + ($hp_count % ${#INSTANCES[@]} > 0) ))
      echo $num_tunes
    fi

    # Define the commands to be executed
    commands="
      export TUNE_NAME=\"$tune_name\";
      export num_tunes=\"$num_tunes\";
      export img_name=\"$docker_name\";
      python3 $man_grid \"$num_tunes\" \"$directory\";
      python3 $gen_comp $num_tunes $tune_name $docker_name $directory;
    "
    echo "Prepping compose file and hp grid on $INSTANCE..."
    ssh -i $pem "$INSTANCE" "$commands"
  done

  for INSTANCE in "${INSTANCES[@]}"; do
      commands="
        export DOCKER_NAME=\"$docker_name\";
        hostname=\$(hostname);
        echo \$hostname;
        cd $directory/compose_files/\$hostname; 
        sudo docker login;
        sudo docker pull \$DOCKER_NAME; 
        sudo docker compose up --remove-orphans --detach; 
      "
      echo "Activating Docker on $INSTANCE..."
      ssh -i $pem "$INSTANCE" "$commands"
  done
  
  check_containers

  hp_count=$(ssh -i $pem "${INSTANCES[0]}" "cat $directory/hps_available.csv | wc -l")
  echo "After training hp count=" $hp_count
  echo "Completed hp tune $q of $(( hp_count / (${#INSTANCES[@]} * num_tunes) ))"
  q=$((q + 1))
done

echo "All original hps calculated"

# Collate metrics--if there are results--sets available tunes 
echo "Collating metrics"
for INSTANCE in "${INSTANCES[@]}"; do
    collate_metrics="$directory/collate_metrics.py"
    commands="
      export TUNE_NAME=\"$tune_name\";
      hostname_var=\$(hostname);
      echo \$hostname_var;
      python3 $collate_metrics $tune_name $directory \$hostname_var;
    "
    echo "Collating metrics on ${INSTANCE}..."
    ssh -i $pem "$INSTANCE" "$commands"
done
echo "Collated"

gen_comp="$directory/gen_comp_file_ES.py"
# Run early stopping
echo $docker_name
commands="
  export tune_name=\"$tune_name\";
  export docker_name=\"$docker_name\"
  python3 $gen_comp $tune_name $directory $docker_name;
  cd /home/ubuntu/LSTM_PY/;
  echo $docker_name
  sudo docker login;
  sudo docker pull \$docker_name; 
  sudo docker compose up --remove-orphans;
"
echo "Running Early Stopping on ${INSTANCES[0]}"
ssh -i $pem "${INSTANCES[0]}" "$commands"
