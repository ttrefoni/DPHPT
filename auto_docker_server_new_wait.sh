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
INSTANCES=("ubuntu@10.192.20.214" "ubuntu@10.192.20.246" "ubuntu@10.192.20.217")
# Define pem 
pem="/home/cisc/TheoT10.pem"

# Create working directory for hps
directory="/srv/samba/hp_tune_grid/RUNS/$tune_name"

# Check if directory exists and create if not
if ssh -i "$pem" "${INSTANCES[0]}" "[ ! -d \"$directory\" ]"; then
  commands="
    mkdir -p $directory
    cp -r /srv/samba/hp_tune_grid/template/. $directory 
    chmod -R 0777 $directory 
    echo 'Creating new working directory'
  "
  ssh -i "$pem" "ubuntu@10.192.20.214" "$commands" || { echo "Failed to create directory"; exit 1; }
fi

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

echo updating hps_tested.csv to hps from collate
# Collate metrics--if there are results
echo "collating metrics"
collate_metrics="$directory/collate_metrics.py"
commands="
  export TUNE_NAME=\"$tune_name\";
  sudo python3 $collate_metrics $tune_name $directory;
"
echo "Collating metrics on ${INSTANCES[0]}..."
ssh -i $pem "${INSTANCES[0]}" "$commands"
echo "collated"

#compare hps available and collated output 
echo "ccomparing collate with aval"
comp_col_aval="$directory/compare_col_w_aval.py"
commands="
  export TUNE_NAME=\"$tune_name\";
  sudo python3 $comp_col_aval $tune_name $directory;
"
ssh -i $pem "${INSTANCES[0]}" "$commands"

og_ct=$(ssh -i "$pem" "${INSTANCES[0]}" "wc -l < \"$directory/hps_original_grid.csv\"")
hps_tested_ct=$(ssh -i "$pem" "${INSTANCES[0]}" "wc -l < \"$directory/output_py/COLLATE/v5_try_col.csv\"")
hp_aval_ct=$(ssh -i "$pem" "${INSTANCES[0]}" "wc -l < \"$directory/hps_available.csv\"")
echo original hp count = $og_ct
echo hps_tested count = $hps_tested_ct
echo hps aval now = $hp_aval_ct 


q=1
docker_name="${pub}/${repository_name}:${version_number}"
echo $docker_name

# Function to check if all Docker containers are finished
check_containers() {
  for INSTANCE in "${INSTANCES[@]}"; do
    while true; do
      running_containers=$(ssh -i "$pem" "$INSTANCE" "sudo docker ps -q | wc -l")
      if [ "$running_containers" -eq 0 ]; then
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
      cd /home/ubuntu/LSTM_PY/; 
      sudo docker pull \$DOCKER_NAME; 
      sudo docker compose up --remove-orphans --detach; 
    "
    echo "Activating Docker on $INSTANCE..."
    ssh -i $pem "$INSTANCE" "$commands"
  done
  
  check_containers

  hp_count=$(ssh -i $pem "${INSTANCES[0]}" "cat $directory/hps_available.csv | wc -l")
  echo "after training hp count=" $hp_count
  echo "completed hp tune $q of $(( hp_count / (${#INSTANCES[@]} * num_tunes) ))"
  q=$((q + 1))
done

echo "all original hps calculated"

# Collate metrics
echo "collating metrics"
collate_metrics="$directory/collate_metrics.py"
commands="
  export TUNE_NAME=\"$tune_name\";
  cd /srv/samba/hp_tune_grid/PY;
  sudo python3 $collate_metrics $tune_name $directory;
"
echo "Collating metrics on ${INSTANCES[0]}..."
ssh -i $pem "${INSTANCES[0]}" "$commands"
echo "collated"

gen_comp="$directory/gen_comp_file_ES.py"
# Run early stopping
echo $docker_name
commands="
  export tune_name=\"$tune_name\";
  export docker_name=\"$docker_name\"
  python3 $gen_comp $tune_name $directory $docker_name;
  cd /home/ubuntu/LSTM_PY/;
  echo $docker_name
  sudo docker pull \$docker_name; 
  sudo docker compose up --remove-orphans;
"
echo "Running Early Stopping on ${INSTANCES[0]}"
ssh -i $pem "${INSTANCES[0]}" "$commands"
